# pavingblockjatim.my.id

Halaman mandiri untuk lini paving block, dipisah dari `firkaizen.id/paving/`
(yang sekarang 301 ke sini). Domain milik FirKaizen; `pavingblockjatim.my.id`
(tanpa `.web.id`) adalah pesaing — jangan tertukar.

Isi: `index.html`, `robots.txt`, `sitemap.xml`. Tidak ada skrip build: halaman ini
sudah memakai canonical/OG domainnya sendiri, jadi sunting `index.html` langsung
lalu deploy.

Deploy (butuh `~/.hermes/.secrets/oracle.env` berisi `SSHPASS=<password root>`):

    bash ops/deploy-situs-oracle.sh paving

Server: Oracle `168.110.218.93:1842`, root `/www/wwwroot/pavingblockjatim.my.id`.

Catatan SEO:
- `robots.txt` WAJIB ada. Tanpa berkas itu aaPanel/Cloudflare hanya menyajikan
  blok komentar *content signals* tanpa baris `Sitemap:`, jadi sitemap tidak
  pernah ditemukan lewat robots.txt.
- Meta description memuat harga dasar `Rp 43.000/m²` (paving 6 cm K-275). Kalau
  harga itu naik, perbarui description-nya juga — angka basi di hasil pencarian
  lebih buruk daripada tidak ada angka.