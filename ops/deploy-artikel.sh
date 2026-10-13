#!/bin/bash
# Terbitkan artikel firkaizen.id -> server, dengan backup + checksum.
# Pemakaian (dari root repo):  bash ops/deploy-artikel.sh
set -e
set -a; . ~/.hermes/.secrets/servers.env; set +a
cd "$(dirname "$0")/.."

SCP="sshpass -e scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
HOST=ubuntu@43.157.211.236
W=/www/wwwroot/firkaizen.id

echo "=== 1. periksa dulu (batalkan kalau ada pelanggaran) ==="
python3 ops/check-artikel.py || { echo "CEK GAGAL - deploy dibatalkan"; exit 1; }

echo
echo "=== 2. susun + kirim berkas ==="
rm -rf /tmp/fksend /tmp/fk-pasang.sh
mkdir -p /tmp/fksend
cp -r artikel /tmp/fksend/
cp sitemap.xml /tmp/fksend/
# Thumbnail ikut dalam perintah yang SAMA. Sempat dipisah dan akibatnya nyata: HTML
# artikel terkirim lebih dulu menunjuk /images/thumb/*.webp yang belum ada di server,
# jadi 15 halaman live bergambar rusak tanpa satu pun error yang kelihatan.
if [ -d images/thumb ]; then
  mkdir -p /tmp/fksend/images
  cp -r images/thumb /tmp/fksend/images/
fi
cat > /tmp/fk-pasang.sh <<EOS
#!/bin/bash
set -e
cp -r $W/artikel $W/.artikel.bak-\$(date +%Y%m%d-%H%M%S)
cp -r /tmp/fksend/artikel/. $W/artikel/
cp /tmp/fksend/sitemap.xml $W/sitemap.xml
if [ -d /tmp/fksend/images/thumb ]; then
  mkdir -p $W/images/thumb
  cp -r /tmp/fksend/images/thumb/. $W/images/thumb/
  chown -R www:www $W/images/thumb
  echo "thumbnail terpasang: \$(ls $W/images/thumb/*.webp 2>/dev/null | wc -l)"
fi
chown -R www:www $W/artikel $W/sitemap.xml
rm -rf /tmp/fksend
echo "artikel terpasang: \$(find $W/artikel -name index.html | wc -l)"
EOS
$SCP -r /tmp/fksend $HOST:/tmp/ >/dev/null
$SCP /tmp/fk-pasang.sh $HOST:/tmp/ >/dev/null

echo
echo "=== 3. pasang di server (backup dulu) ==="
$SSH $HOST "sudo bash /tmp/fk-pasang.sh; rm -f /tmp/fk-pasang.sh"

echo
echo "=== 4. checksum lokal vs server ==="
beda=0
while IFS= read -r p; do
  L=$(md5sum "artikel/$p" | cut -c1-32)
  R=$($SSH $HOST "sudo md5sum $W/artikel/$p 2>/dev/null | cut -c1-32")
  if [ "$L" != "$R" ]; then echo "  BEDA artikel/$p"; beda=$((beda+1)); fi
done < <(cd artikel && find . -name index.html | sed 's|^\./||' | sort)
L=$(md5sum sitemap.xml | cut -c1-32)
R=$($SSH $HOST "sudo md5sum $W/sitemap.xml | cut -c1-32")
[ "$L" != "$R" ] && { echo "  BEDA sitemap.xml"; beda=$((beda+1)); }

# Thumbnail: cek md5 juga, plus pastikan bisa diambil lewat HTTP. md5 cocok tapi berkas
# tidak terbaca (izin salah) tetap = gambar rusak di mata pengunjung.
if [ -d images/thumb ]; then
  for f in images/thumb/*.webp; do
    b=$(basename "$f")
    L=$(md5sum "$f" | cut -c1-32)
    R=$($SSH $HOST "sudo md5sum $W/images/thumb/$b 2>/dev/null | cut -c1-32")
    [ "$L" != "$R" ] && { echo "  BEDA images/thumb/$b"; beda=$((beda+1)); }
  done
fi
echo "  beda: $beda"

echo
echo "=== 5. URL live ==="
curl -s -o /dev/null -w "  /artikel/  %{http_code}\n" https://firkaizen.id/artikel/
echo "  artikel di sitemap: $(curl -s https://firkaizen.id/sitemap.xml | grep -c 'artikel/')"
# Gambar rusak tidak kelihatan dari md5: periksa satu per satu lewat HTTP.
if [ -d images/thumb ]; then
  g=0
  for f in images/thumb/*.webp; do
    c=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "https://firkaizen.id/$f")
    [ "$c" != "200" ] && { echo "  GAMBAR RUSAK $c $f"; g=$((g+1)); }
  done
  echo "  thumbnail: $(ls images/thumb/*.webp | wc -l) berkas, rusak=$g"
  beda=$((beda+g))
fi
[ "$beda" -eq 0 ] || exit 1