#!/usr/bin/env bash
# Mirror bucket R2 villa (media.firkaizen.id) -> GDrive (provider berbeda).
# Media villa tidak ada di tarball VPS1 (tarball hanya kode), jadi ini satu-satunya
# salinan kedua. Jalan harian via cron.
set -uo pipefail
LOG=/var/log/fk-villa-mirror.log
log(){ echo "[$(date +"%Y-%m-%d %H:%M:%S")] $*" | tee -a "$LOG"; }

log "=== VILLA MEDIA MIRROR START ==="
if rclone sync fkr2:villa fkbackup:villa-mirror/ --fast-list --transfers 8 --checkers 16 >>"$LOG" 2>&1; then
  log "sync OK"
else
  log "ERROR: sync gagal (exit $?)"
fi
rclone check fkr2:villa fkbackup:villa-mirror/ --size-only --one-way >>"$LOG" 2>&1 && log "verify: 0 differences" || log "WARN: ada perbedaan"
log "=== VILLA MEDIA MIRROR DONE ==="
