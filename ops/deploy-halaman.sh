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
  if [ -e "$d" ]; then DIRS+=("$d"); else echo "  LEWAT (tidak ada): $d"; fi
done
[ ${#DIRS[@]} -ge 1 ] || { echo "tidak ada direktori yang bisa dikirim"; exit 1; }
echo "=== dikirim: ${DIRS[*]} ==="

echo
echo "=== 1. kirim ==="
rm -rf /tmp/fkhsend
mkdir -p /tmp/fkhsend
for d in "${DIRS[@]}"; do
  # 'cp -r images/gapura /tmp/fkhsend/' membuang level 'images/', sehingga
  # kiriman mendarat di /tmp/fkhsend/gapura sementara server mengharapkan
  # /tmp/fkhsend/images/gapura -> cp gagal, pemasangan batal diam-diam.
  ibu=$(dirname "$d")
  [ "$ibu" = "." ] || mkdir -p "/tmp/fkhsend/$ibu"
  cp -r "$d" "/tmp/fkhsend/$ibu/"
done
jumlah=$(find /tmp/fkhsend -type f | wc -l)
echo "  berkas terkumpul: $jumlah"
# sisa kiriman lama di server bikin scp MENGGABUNG, bukan menimpa -> hitungan
# jadi tidak cocok dan berkas basi ikut terpasang.
$SSH $HOST "rm -rf /tmp/fkhsend" >/dev/null 2>&1 || true
$SCP -r /tmp/fkhsend $HOST:/tmp/ >/dev/null
kirim=$($SSH $HOST "find /tmp/fkhsend -type f | wc -l" 2>/dev/null)
echo "  berkas di server: $kirim"
[ "$jumlah" = "$kirim" ] || { echo "  KIRIMAN TIDAK UTUH -- batal"; exit 1; }

echo
echo "=== 2. pasang (backup dulu) ==="
PASANG="/tmp/fk-halaman.sh"
: > "$PASANG"
echo "#!/bin/bash" >> "$PASANG"
echo "set -e" >> "$PASANG"
STAMP=$(date +%Y%m%d-%H%M%S)
for d in "${DIRS[@]}"; do
  # $W/.images/ belum ada -> cp cadangan gagal -> set -e membatalkan seluruh
  # pemasangan tanpa pesan. Sediakan dulu induk direktori cadangannya.
  ibu=$(dirname "$d"); [ "$ibu" = "." ] && ibu=""
  echo "mkdir -p $W/.$ibu" >> "$PASANG"
  # Cadangan hanya kalau tujuannya SUDAH ada. Tanpa penjaga ini, memasang direktori BARU
  # (mis. images/thumb yang belum pernah ada di server) membuat cp gagal, `set -e` di
  # server membatalkan SELURUH pemasangan, dan yang terlihat cuma "GAGAL pasang" --
  # sementara HTML sudah kelanjur terkirim di langkah sebelumnya, jadi halaman live
  # menunjuk gambar yang belum ada.
  echo "[ -e $W/$d ] && cp -r $W/$d $W/.$d.bak-$STAMP || true" >> "$PASANG"
  # File tunggal (mis. index.html): 'mkdir -p' atas file yang sudah ada ERROR,
  # set -e membatalkan seluruh pemasangan; 'cp -r file/.' juga gagal. Rute beda.
  if [ -f "$d" ]; then
    echo "cp /tmp/fkhsend/$d $W/$d" >> "$PASANG"
  else
    echo "mkdir -p $W/$d" >> "$PASANG"
    echo "cp -r /tmp/fkhsend/$d/. $W/$d/" >> "$PASANG"
  fi
  echo "chown -R www:www $W/$d" >> "$PASANG"
done
echo "rm -rf /tmp/fkhsend" >> "$PASANG"
$SCP "$PASANG" $HOST:/tmp/ >/dev/null
$SSH $HOST "sudo bash $PASANG && rm -f $PASANG || echo '  GAGAL pasang -- skrip disimpan: $PASANG'"

echo
echo "=== 3. checksum lokal vs server ==="
beda=0
for d in "${DIRS[@]}"; do
  # satu panggilan SSH per direktori; loop per-berkas bikin nggantung kalau
  # berkasnya ratusan (galeri foto).
  if [ -f "$d" ]; then
    md5sum "$d" > /tmp/fk-md5-lokal.txt
    $SSH $HOST "cd $W && md5sum $d" > /tmp/fk-md5-server.txt 2>/dev/null || true
  else
    (cd "$d" && find . -type f -exec md5sum {} + | sed 's| \./| |' | sort -k2) > /tmp/fk-md5-lokal.txt
    $SSH $HOST "cd $W/$d && sudo find . -type f -exec md5sum {} + | sed 's| \\./| |' | sort -k2" > /tmp/fk-md5-server.txt 2>/dev/null || true
  fi
  # hanya berkas LOKAL yang diperiksa: berkas lama yang sengaja dibiarkan di
  # server (supaya HTML lama di cache browser tidak 404) tidak dihitung beda.
  n=$(awk 'NR==FNR { s[$2]=$1; next } { if (s[$2] != $1) print "  BEDA " $2 }' /tmp/fk-md5-server.txt /tmp/fk-md5-lokal.txt | tee /dev/stderr | grep -c BEDA || true)
  echo "  $d: beda=$n"
  beda=$((beda + n))
done

echo
echo "=== 4. URL live ==="
for d in "${DIRS[@]}"; do
  # file tunggal: '/index.html/' (trailing slash) cuma bikin redirect, bukan
  # status halaman. URL file = path apa adanya.
  if [ -f "$d" ]; then
    curl -s -o /dev/null -w "  /$d  %{http_code}\n" "https://firkaizen.id/$d"
  else
    curl -s -o /dev/null -w "  /$d/  %{http_code}\n" "https://firkaizen.id/$d/"
  fi
done
[ "$beda" -eq 0 ] || exit 1