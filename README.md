# firkaizen-id-static

Landing pages statis **firkaizen.id** — divisi material & konstruksi fisik **PT FirKaizen Digital Solutions**.

Repo ini adalah sumber (source of truth) untuk seluruh halaman statis yang di-serve dari `/www/wwwroot/firkaizen.id` di server produksi.

## Struktur

```
index.html            # Hub portal material & konstruksi
gapura/index.html     # LP Gapura Majapahit bata expose
paving/index.html     # LP paving block & kanstin
batako/index.html     # LP bata ringan AAC & batako
porto/                # Halaman portofolio
privacy/  terms/      # Halaman legal + verifikasi TikTok developer
link/  links/         # Halaman link-in-bio
admin/                # Panel admin (login + kelola lead)
api/index.php         # API PHP: lead, produk, settings (SQLite)
images/               # Aset gambar halaman
fonts/                # Font self-hosted
logo.webp
```

## Yang TIDAK di-commit

| Path | Alasan |
|---|---|
| `data/` | SQLite runtime (`database.sqlite`) — berisi lead pelanggan + hash password admin |
| `.well-known/` | ACME challenge Let's Encrypt, digenerate server |
| `*.bak-*` | Backup deploy sementara |

Password admin awal diambil dari env `FK_ADMIN_DEFAULT_PASSWORD` (fallback: random). Tidak ada credential hardcoded di repo.

## Aturan domain

- `firkaizen.id` → layanan **fisik/konstruksi** (paving, batako, gapura, material)
- `firkaizen.com` → layanan **tech/AI/software**

Jangan taruh konten fisik di `.com` atau sebaliknya.

## Deploy

Server produksi: `/www/wwwroot/firkaizen.id` (aaPanel + nginx, user `www`).

```bash
# sinkron dari repo ke server (di server, sebagai user www)
rsync -a --exclude data/ --exclude .well-known/ --exclude '*.bak-*' ./ /www/wwwroot/firkaizen.id/
chown -R www:www /www/wwwroot/firkaizen.id
```

`data/` sengaja dikecualikan supaya database lead produksi tidak tertimpa.

Backup harian offsite otomatis ke Cloudflare R2 (`fkr2:firkaizen-backup`, retensi 14 hari) via `/usr/local/sbin/fk-backup`.