#!/usr/bin/env python3
"""Bangun halaman mandiri gapuramajapahit.web.id dari gapura/index.html.

Halaman /gapura/ di firkaizen.id berisi path RELATIF (`../css/...`) dan link
internal ke firkaizen.id. Kalau berkas itu dipasang apa adanya di root domain
baru, CSS-nya keluar dari root (404) dan semua link balik jadi salah.

Skrip ini menulis salinan yang sudah disesuaikan ke ~/.hermes/cache/scratch/gapura-situs/:
  index.html, css/, logo.webp, images/gapura/ (termasuk thumb/), images/og/, robots.txt, sitemap.xml

Jalankan ulang tiap kali gapura/index.html diubah:
    python3 ops/build-situs-gapura.py
lalu kirim ke server (lihat skill firkaizen-id-static-lp).
"""
import os, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "gapura", "index.html")
OUT = os.path.expanduser("~/.hermes/cache/scratch/gapura-situs")
BARU = "https://gapuramajapahit.web.id"
INDUK = "https://firkaizen.id"

# Berkas verifikasi Google (dan sejenisnya) disimpan di situs/gapuramajapahit.web.id/
# dan disalin ke output tiap build — kalau tidak, `rmtree` di bawah menghapusnya.
EKSTRA_DIR = os.path.join("situs", "gapuramajapahit.web.id")
DIBUAT_SENDIRI = {"index.html", "robots.txt", "sitemap.xml", "README.md"}

# Token milik akun Google pemilik situs. Google menerima lebih dari satu meta
# verifikasi; token lama di gapura/index.html SENGAJA tidak dihapus supaya
# verifikasi akun yang sudah ada tidak putus.
VERIF = [
    '<meta name="google-site-verification" content="9UJ-FZG4q2DCjINsbJDMPuZtJZMLmjy9GQL6gSZYFU4" />',
]

# urutan penting: link spesifik dulu, `href="/"` terakhir
REPLACEMENTS = [
    ('href="../css/tw-9c68816f.css"', 'href="/css/tw-9c68816f.css"'),
    ('rel="canonical" href="https://firkaizen.id/gapura/"', f'rel="canonical" href="{BARU}/"'),
    ('property="og:url" content="https://firkaizen.id/gapura/"', f'property="og:url" content="{BARU}/"'),
    ('content="https://firkaizen.id/images/og/gapura.webp"', f'content="{BARU}/images/og/gapura.webp"'),
    ('"item":"https://firkaizen.id/gapura/"', f'"item":"{BARU}/"'),
    ('href="/artikel/"', f'href="{INDUK}/artikel/"'),
    ('href="/batako/"', f'href="{INDUK}/batako/"'),
    ('href="/"', f'href="{INDUK}/"'),
    ('href="/gapura/"', 'href="/"'),
]

ROBOTS = """User-agent: *
Allow: /

Sitemap: {base}/sitemap.xml
"""

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base}/</loc>
    <lastmod>{tgl}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""


def main():
    import datetime
    shutil.rmtree(OUT, ignore_errors=True)
    html = open(SRC, encoding="utf-8").read()
    for old, new in REPLACEMENTS:
        n = html.count(old)
        assert n, f"tidak ketemu di {SRC}: {old}"
        html = html.replace(old, new)
        print(f"  {n:>2}x  {old[:52]}")

    # meta verifikasi Google: sisipkan tepat setelah <head>
    assert "<head>\n" in html, "tag <head> tidak ketemu"
    html = html.replace(
        "<head>\n", "<head>\n" + "".join(f"  {m}\n" for m in VERIF), 1)
    print(f"  {len(VERIF):>2}x  meta verifikasi Google disisipkan")

    # aset: path absolut -> berkas di repo; path relatif -> relatif ke gapura/
    aset = {"images/og/gapura.webp"}
    for m in re.finditer(r'(?:src|href)="((?!https?:|#|data:|mailto:|tel:)[^"]+)"', html):
        a = m.group(1)
        a = os.path.normpath(os.path.join("gapura", a)) if a.startswith("../") else a.lstrip("/")
        if a and not a.startswith(("/", "http")):
            aset.add(a)

    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(html)
    open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(ROBOTS.format(base=BARU))
    open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
        SITEMAP.format(base=BARU, tgl=datetime.date.today().isoformat()))

    n = 0
    for a in sorted(aset):
        src = os.path.join(ROOT, a)
        if not os.path.isfile(src):
            print(f"  HILANG: {a}")
            continue
        dst = os.path.join(OUT, a)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    print(f"  {n} aset + index.html + robots.txt + sitemap.xml -> {OUT}")

    # berkas tambahan (verifikasi Google dll) ikut ke output
    ekstra = os.path.join(ROOT, EKSTRA_DIR)
    if os.path.isdir(ekstra):
        for f in sorted(os.listdir(ekstra)):
            if f in DIBUAT_SENDIRI:
                continue
            shutil.copy2(os.path.join(ekstra, f), os.path.join(OUT, f))
            print(f"   +  {f}")


if __name__ == "__main__":
    main()