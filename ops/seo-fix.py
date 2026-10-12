#!/usr/bin/env python3
"""SEO fix firkaizen.id: title/desc, OG/Twitter, JSON-LD, duplikat, privacy/terms.

Idempoten: aman dijalankan berulang (block yang sudah ada diganti, bukan ditumpuk).
"""
import os, re, html, shutil, datetime

ROOT = os.path.expanduser("~/.hermes/cache/scratch/fk-static-repo")
BASE = "https://firkaizen.id"
PHONE = "+6285196135691"
WA = "https://wa.me/6285196135691"
EMAIL = "founder@firkaizen.com"
TODAY = datetime.date.today().isoformat()

# Wilayah per jenis halaman. Gapura dikerjakan tim mitra di Ponorogo dan dijangkau
# se-Pulau Jawa; lini material berpusat di Solo Raya.
#
# Tanpa ini skrip ini MEMBALIKKAN perbaikan wilayah: ia menulis ulang seluruh blok <head>
# dari satu templat, jadi areaServed gapura kembali berbunyi "Solo Raya" -- persis
# kontradiksi yang dulu dilaporkan pemilik ("kenapa ngarang di solo kan tempat gapuranya
# di ponorogo"). Halaman layanan tidak dihasilkan generator artikel, jadi tidak ada yang
# menahannya kalau wilayahnya tidak dinyatakan di sini.
WILAYAH = {
    "default":    {"label": "Solo Raya & Jawa Tengah",
                   "area": ["Solo Raya", "Jawa Tengah", "Jawa Timur"]},
    "pulau-jawa": {"label": "Pulau Jawa", "area": ["Pulau Jawa"]},
}

# slug -> (title<=60, desc 140..160, og_image slug, path)
PAGES = {
    "index.html": dict(
        path="/", t="FirKaizen Material & Konstruksi Solo Raya",
        d="Supplier material precast beton, genteng pres atap, dan jasa kontraktor fisik terpadu tangan pertama di Solo Raya.",
        og="default", kind="hub"),
    "paving/index.html": dict(
        path="/paving/", t="Pabrik Paving Block Solo Raya — Jasa Pasang",
        d="Produsen paving block K-300 press hidrolik & jasa pasang borongan di Solo Raya. Paving bata, segi enam, cacing, kanstin.",
        og="paving", kind="service"),
    "batako/index.html": dict(
        path="/batako/", t="Pabrik Bata Ringan AAC & Batako Solo Raya",
        d="Distributor bata ringan AAC (hebel) presisi & batako semen hidrolik di Solo Raya. Material kubikan atau paket borongan pasang.",
        og="batako", kind="service"),
    "gapura/index.html": dict(
        path="/gapura/", t="Jasa Pembuatan Gapura Majapahit Bata Expose",
        d="Jasa pembuatan gapura Majapahit bata expose ukiran relief klasik. Ukuran 2,5m hingga 6m dan custom. Melayani seluruh Pulau Jawa.",
        og="gapura", kind="service", wilayah="pulau-jawa"),
    "porto/index.html": dict(
        path="/porto/", t="Portofolio & Kontak FirKaizen",
        d="Portofolio dan kontak resmi PT FirKaizen Digital Solutions. Konsultasi langsung dengan tim engineer di Solo Raya.",
        og="default", kind="hub"),
    "privacy/index.html": dict(
        path="/privacy/", t="Kebijakan Privasi — PT FirKaizen Digital Solutions",
        d="Kebijakan privasi PT FirKaizen Digital Solutions: data apa yang dikumpulkan, cara pemakaian, dan hak pengguna.",
        og="default", kind="legal"),
    "terms/index.html": dict(
        path="/terms/", t="Syarat & Ketentuan — PT FirKaizen Digital Solutions",
        d="Syarat dan ketentuan layanan PT FirKaizen Digital Solutions untuk penggunaan situs, penawaran, dan pengerjaan proyek.",
        og="default", kind="legal"),
}

META_START = "<!-- FK-SEO:START -->"
META_END = "<!-- FK-SEO:END -->"


def esc(s):
    return html.escape(s, quote=True)


def ld_for(slug, cfg):
    """JSON-LD sesuai jenis halaman.

    areaServed diambil dari wilayah halaman ini, bukan satu nilai tetap -- dan diletakkan
    di Organization MAUPUN Service. Dulu keduanya bertabrakan (Organization bilang Jawa
    Timur, Service bilang Solo Raya) sementara teks halaman bilang se-Pulau Jawa.
    """
    w = WILAYAH[cfg.get("wilayah", "default")]
    org = {
        "@type": "Organization",
        "@id": BASE + "/#organization",
        "name": "PT FirKaizen Digital Solutions",
        "url": BASE + "/",
        "logo": BASE + "/logo.webp",
        "email": EMAIL,
        "telephone": PHONE,
        "address": {"@type": "PostalAddress", "addressRegion": "Jawa Tengah", "addressLocality": "Solo Raya", "addressCountry": "ID"},
        "areaServed": list(w["area"]),
    }
    graph = [org]
    if cfg["kind"] == "service":
        graph.append({
            "@type": "Service",
            "name": cfg["t"].split(" — ")[0],
            "description": cfg["d"],
            "serviceType": cfg["t"].split(" — ")[0],
            "provider": {"@id": BASE + "/#organization"},
            "areaServed": list(w["area"]),
            "offers": {"@type": "Offer", "priceCurrency": "IDR", "availability": "https://schema.org/InStock"},
        })
        graph.append({
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Beranda", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": cfg["t"].split(" — ")[0], "item": BASE + cfg["path"]},
            ],
        })
    elif cfg["kind"] == "hub":
        graph.append({
            "@type": "WebSite", "name": "FirKaizen", "url": BASE + "/",
            "publisher": {"@id": BASE + "/#organization"},
        })
    return {"@context": "https://schema.org", "@graph": graph}


def build_head(slug, cfg):
    og = f"{BASE}/images/og/{cfg['og']}.webp"
    canon = BASE + cfg["path"]
    blocks = [
        META_START,
        f'<title>{esc(cfg["t"])}</title>',
        f'<meta name="description" content="{esc(cfg["d"])}"/>',
        f'<link rel="canonical" href="{canon}"/>',
        '<meta name="robots" content="index, follow, max-image-preview:large"/>',
        "",
        f'<meta property="og:type" content="website"/>',
        f'<meta property="og:site_name" content="FirKaizen"/>',
        f'<meta property="og:locale" content="id_ID"/>',
        f'<meta property="og:url" content="{canon}"/>',
        f'<meta property="og:title" content="{esc(cfg["t"])}"/>',
        f'<meta property="og:description" content="{esc(cfg["d"])}"/>',
        f'<meta property="og:image" content="{og}"/>',
        f'<meta property="og:image:width" content="1200"/>',
        f'<meta property="og:image:height" content="630"/>',
        "",
        f'<meta name="twitter:card" content="summary_large_image"/>',
        f'<meta name="twitter:title" content="{esc(cfg["t"])}"/>',
        f'<meta name="twitter:description" content="{esc(cfg["d"])}"/>',
        f'<meta name="twitter:image" content="{og}"/>',
        "",
        f'<script type="application/ld+json">{__import__("json").dumps(ld_for(slug, cfg), ensure_ascii=False, separators=(",", ":"))}</script>',
        META_END,
    ]
    return "\n".join(blocks)


def patch(slug, cfg):
    p = os.path.join(ROOT, slug)
    s = open(p, encoding="utf-8").read()
    orig = s
    new_head = build_head(slug, cfg)

    # 1) buang blok FK lama kalau ada (idempoten)
    s = re.sub(re.escape(META_START) + r".*?" + re.escape(META_END) + r"\n?", "", s, flags=re.S)

    # 2) buang tag SEO lama yang sekarang dikelola blok (hindari duplikat)
    for pat in [
        r'<title[^>]*>.*?</title>\s*',
        r'<meta[^>]+name="description"[^>]*>\s*',
        r'<link[^>]+rel="canonical"[^>]*>\s*',
        r'<meta[^>]+name="robots"[^>]*>\s*',
    ]:
        s = re.sub(pat, "", s, count=1, flags=re.S | re.I)

    # 3) sisipkan blok baru tepat setelah <head>
    m = re.search(r'<head[^>]*>', s, re.I)
    assert m, f"{slug}: <head> tidak ketemu"
    s = s[:m.end()] + "\n" + new_head + "\n" + s[m.end():]

    # 4) language: privacy/terms masih en
    if cfg["kind"] == "legal":
        s = re.sub(r'<html([^>]*?)lang="en"', r'<html\1lang="id"', s, flags=re.I)

    if s != orig:
        open(p, "w", encoding="utf-8").write(s)
        return True
    return False


if __name__ == "__main__":
    # backup dulu
    # Di LUAR repo: cadangan di dalam repo ikut ter-commit dan ter-mirror ke R2, dan
    # berkas .bak di repo bisa tersalin balik ke halaman baru (lihat skill). Simpan di
    # samping repo.
    bdir = os.path.join(os.path.dirname(ROOT.rstrip("/")),
                        f"fk-arsip-seo-{datetime.datetime.now():%Y%m%d-%H%M%S}")
    for slug in list(PAGES) + ["link/index.html", "links/index.html"]:
        src = os.path.join(ROOT, slug)
        if os.path.exists(src):
            dst = os.path.join(bdir, slug)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    print(f"backup -> {bdir}")

    for slug, cfg in PAGES.items():
        print(f"  {'patched' if patch(slug, cfg) else 'unchanged'}  {slug}")

    # 5) link/ -> hapus, links/ jadi satu-satunya (canonical + noindex sudah di robots.txt)
    for d in ["link", "links"]:
        print(f"  ada: {d}/index.html = {os.path.exists(os.path.join(ROOT, d, 'index.html'))}")