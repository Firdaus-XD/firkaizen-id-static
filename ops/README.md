# ops/ — script operasional server (TENCENT 43.157.211.236)

Salinan dari `/usr/local/sbin/` di server. Server adalah deployment target; **repo ini source of truth**.
Kalau server mati, script di sini yang dipakai untuk membangun ulang.

| File | Server path | Cron | Fungsi |
|---|---|---|---|
| `fk-backup` | `/usr/local/sbin/fk-backup` | `0 20 * * *` (03:00 WIB) | Snapshot seluruh host: dump Postgres, MariaDB, `/opt/*`, web root, config/.env/vhost/cert → upload ke `fkr2enc:` (R2, retensi 14) **dan** `fkbackup:` (Google Drive, arsip) |
| `fk-tenant-backup` | `/usr/local/sbin/fk-tenant-backup` | `0 21 * * *` (04:00 WIB) | Backup DATA PELANGGAN: docker volume agent tiap tenant (`hermes-data-<id>`) dari host DAHONO + DIGICORE → `fkr2enc:tenants` |
| `fk-server-health` | `/usr/local/sbin/fk-server-health` | `0 * * * *` | Cek kesehatan server tiap jam + laporan Telegram |

## Kenapa script ini ada di repo

Script yang hanya hidup di `/usr/local/sbin/` pada host yang mati **tidak bisa** dipakai membangun pengganti.
Kalau `/usr/local/sbin/fk-backup` hilang bersamaan dengan host, backup yang sudah terupload jadi tidak bisa direplikasi ke server baru.

## Yang SENGAJA tidak ikut dicadangkan

`rclone.conf` (isi password `crypt` yang membuka arsip di R2) **tidak** dimasukkan ke dalam snapshot.
Kalau ikut, satu kebakaran host membakar arsip dan kuncinya sekaligus.
Kunci hidup di **kit pemulihan di luar server** (password manager / cetakan fisik). Tanpa itu restore MUSTAHIL.

## Pitfall yang sudah kena (jangan diulang)

**`set -euo pipefail` + pipeline yang gagal = backup abort diam-diam.**
Fase dump MariaDB dulu:

```bash
DBS="$(mysql ... show databases; | grep -vE '^(information_schema|...)$')"
```

Di host yang **tidak punya user database**, `grep` tidak menemukan apa pun → exit 1 → `pipefail` + `set -e`
menghentikan **seluruh** backup pada detik yang sama. Hasilnya snapshot 400 KB (kosong) dan status `failed`,
tanpa error yang menyebut barisnya.

Fix: `|| true` **di luar** subshell.

```bash
DBS="$(mysql ... | grep -vE '...' || true)"
```

Sama seperti larangan `[ tes ] && cmd`: pakai `if ...; then ...; fi`.

Syntax-check setiap patch ke script produksi pakai `bash -n` sebelum menimpa, dan simpan `.bak-<timestamp>`.

## Deploy perubahan script ke server

```bash
scp ops/fk-backup ubuntu@43.157.211.236:/tmp/
ssh ubuntu@43.157.211.236 'sudo cp /usr/local/sbin/fk-backup /usr/local/sbin/fk-backup.bak-$(date +%F-%H%M%S) \
  && sudo cp /tmp/fk-backup /usr/local/sbin/fk-backup \
  && sudo chmod 700 /usr/local/sbin/fk-backup \
  && sudo bash -n /usr/local/sbin/fk-backup \
  && sudo /usr/local/sbin/fk-backup --trigger=manual'
```

Jalankan manual setelah tiap perubahan, lalu baca `/var/lib/fk-backup/state.json`:
`status` harus `success`, `exitCode` 0, dan harus ada **dua** baris `upload ok ->` di `backup.log`.

## Verifikasi

```bash
sudo cat /var/lib/fk-backup/state.json          # status/exitCode per run
sudo tail -40 /var/lib/fk-backup/backup.log     # cari 'upload ok ->' per remote
sudo rclone lsf fkr2enc:VM-24-173-ubuntu/ --dirs-only   # generasi di R2
```

Exit code 0 bukan bukti backup benar. Bukti = restore drill: tarik satu snapshot dari remote, bandingkan checksum.
## fk-vps1-backup.sh (VPS1)

Offsite backup VPS1 1x/hari (cron 20:30 UTC / 03:30 WIB).

- Snapshot berisi: MySQL all-DB dump, PostgreSQL (`villa_prod`, `kaizenbyte`),
  nginx vhost + SSL cert, panel db, hosts, root crontab, Hermes Agent state,
  `labs-firkaizen` + `firkaizen-hub` + `/opt/explore-tawangmangu`.
- **Tarball hanya berisi kode. Media upload user TIDAK ada di sini** — media villa
  hidup di bucket R2 `villa` (lihat `fk-villa-mirror.sh`).
- Retensi berbasis **jumlah file** (`KEEP_TARBALLS=5`, ±246 MB per file ±1,2 GB),
  BUKAN `--min-age`. Alasan: `rclone delete --min-age` bersifat rekursif dan pernah
  ikut menghapus `media-exploretawangmangu/` lalu upload ulang tiap run — bocor
  ~542 MB/run dan tarball menumpuk sampai 1,9 GB.
- Kredensial MySQL dibaca dari `/root/.fk-mysql.cnf` (mode 600), BUKAN inline di script.

## fk-villa-mirror.sh (TENCENT)

Mirror bucket R2 `villa` (`media.firkaizen.id`) ke GDrive `fkbackup:villa-mirror/`
1x/hari (cron 21:45 UTC). Jalan di TENCENT karena remote `fkbackup` hanya
terkonfigurasi di sana.

- Media villa = 1.370 file / 880 MB dan **tidak ada di tarball VPS1**. Tanpa job ini
  media hanya punya satu salinan (bucket R2 sendiri).
- Verifikasi: `rclone check --size-only --one-way`.
  Catatan: GDrive tidak mendukung hash sama sekali (`Hashes: []`), jadi `rclone md5sum`
  di sana selalu gagal dan `rclone check` tanpa `--size-only` memakai ukuran saja.
