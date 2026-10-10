#!/usr/bin/env bash
set -eo pipefail

DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/var/backups/vps1"
STAGING="$BACKUP_DIR/staging_$DATE"
ARCHIVE="$BACKUP_DIR/vps1-backup-$DATE.tar.gz"
LOG_FILE="/var/log/fk-vps1-backup.log"
KEEP_TARBALLS=5
R2_REMOTE="fkr2:firkaizen-backup/vps1"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "=== STARTING VPS1 OFFSITE BACKUP ==="
mkdir -p "$STAGING" "$BACKUP_DIR"

# 1. MySQL All Databases Dump
log "Dumping MySQL databases..."
MYSQL_SOCK="/tmp/mysql.sock"
if [ ! -S "$MYSQL_SOCK" ]; then
    MYSQL_SOCK="/var/run/mysqld/mysqld.sock"
fi

if [ -S "$MYSQL_SOCK" ]; then
    MYSQL_DEFAULTS="/root/.fk-mysql.cnf"
    if [ ! -f "$MYSQL_DEFAULTS" ]; then
        umask 077
        printf '[client]\nuser=root\npassword=%s\n' "$FK_MYSQL_PASSWORD" > "$MYSQL_DEFAULTS"
    fi
    mysqldump --defaults-extra-file="$MYSQL_DEFAULTS" --socket="$MYSQL_SOCK" --all-databases --single-transaction --quick 2>/dev/null | gzip > "$STAGING/mysql_all_databases.sql.gz" || log "Warning: MySQL dump partial"
fi

# 2. PostgreSQL Databases Dump
log "Dumping PostgreSQL databases..."
mkdir -p "$STAGING/postgres"
for db in villa_prod kaizenbyte; do
    if sudo -u postgres psql -lqt | cut -d '|' -f 1 | grep -qw "$db"; then
        sudo -u postgres pg_dump -Fc "$db" > "$STAGING/postgres/$db.dump" 2>/dev/null || log "Warning: pg_dump $db partial"
    fi
done

# 3. Nginx Vhosts and SSL Configs
log "Archiving Nginx configs and SSL certs..."
mkdir -p "$STAGING/configs"
tar -czf "$STAGING/configs/nginx_and_certs.tar.gz" -C /www/server/panel/vhost . 2>/dev/null || true
cp /www/server/panel/data/default.db "$STAGING/configs/panel_default.db" 2>/dev/null || true
cp /etc/hosts "$STAGING/configs/hosts" 2>/dev/null || true
crontab -l > "$STAGING/configs/root_crontab.txt" 2>/dev/null || true

# 4. Hermes Agent State
log "Archiving Hermes Agent configuration and profiles..."
tar --exclude='.hermes/cache'     --exclude='.hermes/hermes-agent'     --exclude='*.sock'     --exclude='.hermes/audio_cache'     -czf "$STAGING/hermes_agent_state.tar.gz" -C /home/hermesagent .hermes 2>/dev/null || true

# 5. Active Hub Projects
log "Archiving active projects..."
tar --exclude='node_modules' --exclude='.next' --exclude='.output' --exclude='.git'     -czf "$STAGING/active_projects.tar.gz"     -C /home/hermesagent labs-firkaizen firkaizen-hub 2>/dev/null || true
tar --exclude="node_modules" --exclude=".output" --exclude=".git" -czf "$STAGING/opt_explore_tawangmangu.tar.gz" -C /opt explore-tawangmangu 2>/dev/null || true

# 6. Compress whole snapshot
log "Compressing backup snapshot..."
tar -czf "$ARCHIVE" -C "$STAGING" .
rm -rf "$STAGING"
ARCHIVE_SIZE=$(du -h "$ARCHIVE" | cut -f1)
log "Snapshot created: $ARCHIVE ($ARCHIVE_SIZE)"

# 7. Upload to Cloudflare R2
log "Uploading to Cloudflare R2..."
rclone copy "$ARCHIVE" "$R2_REMOTE/" --fast-list

# 8. Retention: Prune older than 14 days in R2
# Media villa di-mirror ke GDrive oleh job terpisah di TENCENT (fk-villa-mirror),
# karena remote fkbackup hanya terkonfigurasi di sana. Di sini tidak ada remote itu,
# jadi mencoba sync di sini hanya menghasilkan kegagalan diam-diam.

log "Pruning R2 tarballs, keeping newest $KEEP_TARBALLS..."
rclone lsf "$R2_REMOTE/" --files-only 2>/dev/null | grep -E '^vps1-backup-.*\.tar\.gz$' | sort -r | tail -n +$((KEEP_TARBALLS+1)) | while read -r old; do
    rclone deletefile "$R2_REMOTE/$old" 2>/dev/null || true
    log "Pruned old tarball: $old"
done

# 9. Prune local archives (keep only last 2)
cd "$BACKUP_DIR"
ls -t vps1-backup-*.tar.gz | tail -n +3 | xargs -r rm -f

log "=== BACKUP FINISHED SUCCESSFULLY ==="
