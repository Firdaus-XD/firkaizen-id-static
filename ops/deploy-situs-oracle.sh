#!/bin/bash
# Deploy situs mandiri (pavingblockjatim.my.id + gapuramajapahit.web.id) ke VPS Oracle.
#
# Kredensial: ~/.hermes/.secrets/oracle.env berisi SSHPASS=<password root Oracle>.
# Jangan pernah menaruh password di skrip ini atau di repo.
#
# Pakai: bash ops/deploy-situs-oracle.sh [paving|gapura|semua]
set -euo pipefail

HOST=168.110.218.93
PORT=1842
USER=root
ROOT_REPO="$(cd "$(dirname "$0")/.." && pwd)"
SCRATCH="$HOME/.hermes/cache/scratch"
SECRETS="$HOME/.hermes/.secrets/oracle.env"

if [ ! -f "$SECRETS" ]; then
  echo "GAGAL: $SECRETS tidak ada (isi: SSHPASS=<password root Oracle>)" >&2
  exit 1
fi
set -a
# shellcheck disable=SC1090
. "$SECRETS"
set +a
export SSHPASS

SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p $PORT $USER@$HOST"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P $PORT"

target="${1:-semua}"

if [ "$target" = "paving" ] || [ "$target" = "semua" ]; then
  echo "== pavingblockjatim.my.id =="
  SRC="$SCRATCH/paving-fkid"
  DST="/www/wwwroot/pavingblockjatim.my.id"
  $SSH "mkdir -p $DST"
  $SCP "$SRC/index.html" "$SRC/robots.txt" "$SRC/sitemap.xml" "$USER@$HOST:$DST/"
  $SSH "chown www:www $DST/index.html $DST/robots.txt $DST/sitemap.xml && chmod 644 $DST/index.html $DST/robots.txt $DST/sitemap.xml"
fi

if [ "$target" = "gapura" ] || [ "$target" = "semua" ]; then
  echo "== gapuramajapahit.web.id (hasil build) =="
  SRC="$SCRATCH/gapura-situs"
  DST="/www/wwwroot/gapuramajapahit.web.id"
  $SSH "mkdir -p $DST"
  $SCP -r "$SRC/index.html" "$SRC/robots.txt" "$SRC/sitemap.xml" "$USER@$HOST:$DST/"
  $SSH "chown www:www $DST/index.html $DST/robots.txt $DST/sitemap.xml && chmod 644 $DST/index.html $DST/robots.txt $DST/sitemap.xml"
fi

echo "selesai. verifikasi:"
for d in pavingblockjatim.my.id gapuramajapahit.web.id; do
  printf "  %-26s %s\n" "$d" "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 "https://$d/")"
done