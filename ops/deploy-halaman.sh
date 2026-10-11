#!/bin/bash
# Terbitkan HALAMAN STATIS firkaizen.id (mis. gapura/) -> server, backup + checksum.
# Pemakaian (dari root repo):  bash ops/deploy-halaman.sh gapura
#
# deploy-artikel.sh hanya mengirim artikel/. Halaman layanan seperti gapura/
# diedit di repo tapi tidak pernah ikut terkirim, sehingga harga lama tetap
# tayang. Skrip ini menutup celah itu.
#
# SENGAJA hanya mengirim path yang disebut. /www/wwwroot/firkaizen.id juga
# berisi api/index.php dan data/database.sqlite milik dashboard -- sinkronisasi
# menyeluruh akan menimpanya.
set -e
[ $# -ge 1 ] || { echo "pakai: bash ops/deploy-halaman.sh <dir> [dir...]"; exit 1; }

set -a; . ~/.hermes/.secrets/servers.env; set +a
cd "$(dirname "$0")/.."

SCP="sshpass -e scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
HOST=ubuntu@43.157.211.236
W=/www/wwwroot/firkaizen.id

# hanya path yang benar-benar ada di repo
DIRS=()
for d in "$@"; do
  if [ -d "$d" ]; then DIRS+=("$d"); else echo "  LEWAT (bukan direktori): $d"; fi
done
[ ${#DIRS[@]} -ge 1 ] || { echo "tidak ada direktori yang bisa dikirim"; exit 1; }
echo "=== dikirim: ${DIRS[*]} ==="

echo
echo "=== 1. kirim ==="
rm -rf /tmp/fkhsend
mkdir -p /tmp/fkhsend
for d in "${DIRS[@]}"; do cp -r "$d" /tmp/fkhsend/; done
$SCP -r /tmp/fkhsend $HOST:/tmp/ >/dev/null

echo
echo "=== 2. pasang (backup dulu) ==="
PASANG="/tmp/fk-halaman.sh"
: > "$PASANG"
echo "#!/bin/bash" >> "$PASANG"
echo "set -e" >> "$PASANG"
STAMP=$(date +%Y%m%d-%H%M%S)
for d in "${DIRS[@]}"; do
  echo "cp -r $W/$d $W/.$d.bak-$STAMP" >> "$PASANG"
  echo "cp -r /tmp/fkhsend/$d/. $W/$d/" >> "$PASANG"
  echo "chown -R www:www $W/$d" >> "$PASANG"
done
echo "rm -rf /tmp/fkhsend" >> "$PASANG"
$SCP "$PASANG" $HOST:/tmp/ >/dev/null
$SSH $HOST "sudo bash $PASANG; rm -f $PASANG"

echo
echo "=== 3. checksum lokal vs server ==="
beda=0
for d in "${DIRS[@]}"; do
  while IFS= read -r p; do
    L=$(md5sum "$d/$p" | cut -c1-32)
    R=$($SSH $HOST "sudo md5sum $W/$d/$p 2>/dev/null | cut -c1-32" || true)
    if [ "$L" != "$R" ]; then echo "  BEDA $d/$p"; beda=$((beda+1)); fi
  done < <(cd "$d" && find . -type f | sed 's|^\./||' | sort)
done
echo "  beda: $beda"

echo
echo "=== 4. URL live ==="
for d in "${DIRS[@]}"; do
  curl -s -o /dev/null -w "  /$d/  %{http_code}\n" "https://firkaizen.id/$d/"
done
[ "$beda" -eq 0 ] || exit 1