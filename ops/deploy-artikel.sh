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
cat > /tmp/fk-pasang.sh <<EOS
#!/bin/bash
set -e
cp -r $W/artikel $W/.artikel.bak-\$(date +%Y%m%d-%H%M%S)
cp -r /tmp/fksend/artikel/. $W/artikel/
cp /tmp/fksend/sitemap.xml $W/sitemap.xml
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
echo "  beda: $beda"

echo
echo "=== 5. URL live ==="
curl -s -o /dev/null -w "  /artikel/  %{http_code}\n" https://firkaizen.id/artikel/
echo "  artikel di sitemap: $(curl -s https://firkaizen.id/sitemap.xml | grep -c 'artikel/')"
[ "$beda" -eq 0 ] || exit 1