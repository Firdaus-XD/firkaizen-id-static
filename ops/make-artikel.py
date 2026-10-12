#!/usr/bin/env python3
"""Generate halaman artikel firkaizen.id dari file markdown + frontmatter.

Sumber:  content/artikel/<slug>.md   (frontmatter YAML-ish + markdown)
Output:  artikel/index.html          (daftar artikel)
         artikel/<slug>/index.html   (halaman artikel)

Alasan pakai generator, bukan tulis HTML tangan: menambah artikel = tambah 1 file .md,
lalu jalankan script. Tidak ada salinan nav/footer/head yang bisa jadi tidak sinkron.
"""
import os, re, html, json, datetime, glob, shutil

import markdown

ROOT = os.path.expanduser("~/.hermes/cache/scratch/fk-static-repo")
SRC = os.path.join(ROOT, "content", "artikel")
OUT = os.path.join(ROOT, "artikel")
BASE = "https://firkaizen.id"
WA = "https://wa.me/6285196135691"
TODAY = datetime.date.today().isoformat()

# ---------- aset bersama (disalin dari halaman yang sudah ada supaya konsisten) ----------

STYLE = """    body {
      background-color: #F8FAFC;
      color: #334155;
      font-size: 15px;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }
    .dark body { background-color: #0A0F1D; color: #CBD5E1; }

    .container-clean {
      width: 100%; max-width: 68rem; margin-left: auto; margin-right: auto;
      padding-left: 1.25rem; padding-right: 1.25rem;
    }
    .prose-clean { max-width: 46rem; }
    .prose-clean h2 {
      font-size: 1.35rem; font-weight: 900; margin-top: 2.25rem; margin-bottom: 0.75rem;
      color: #0F172A; letter-spacing: -0.01em; scroll-margin-top: 5rem;
    }
    .dark .prose-clean h2 { color: #F8FAFC; }
    .prose-clean h3 {
      font-size: 1.1rem; font-weight: 800; margin-top: 1.75rem; margin-bottom: 0.5rem;
      color: #0F172A; scroll-margin-top: 5rem;
    }
    .dark .prose-clean h3 { color: #F1F5F9; }
    .prose-clean p { margin-bottom: 1rem; }
    .prose-clean ul, .prose-clean ol { margin: 0 0 1rem 1.25rem; }
    .prose-clean ul { list-style: disc; }
    .prose-clean ol { list-style: decimal; }
    .prose-clean li { margin-bottom: 0.4rem; }
    .prose-clean a { color: #0B6BFF; font-weight: 600; text-decoration: underline; }
    .prose-clean strong { font-weight: 800; color: #0F172A; }
    .dark .prose-clean strong { color: #F8FAFC; }
    .prose-clean table {
      width: 100%; border-collapse: collapse; margin: 1.25rem 0; font-size: 0.875rem;
    }
    .prose-clean th, .prose-clean td {
      border: 1px solid #E2E8F0; padding: 0.6rem 0.75rem; text-align: left;
    }
    .dark .prose-clean th, .dark .prose-clean td { border-color: #1F2937; }
    .prose-clean th { background-color: #F1F5F9; font-weight: 800; }
    .dark .prose-clean th { background-color: #111827; }
    .prose-clean blockquote {
      border-left: 3px solid #0B6BFF; padding-left: 1rem; margin: 1.25rem 0;
      color: #475569; font-style: italic;
    }
    .dark .prose-clean blockquote { color: #94A3B8; }

    .card-clean {
      background-color: #FFFFFF; border: 1px solid #E2E8F0;
      border-radius: 1.25rem; box-shadow: 0 4px 20px -4px rgba(7, 25, 82, 0.05);
    }
    .dark .card-clean { background-color: #111827; border-color: #1F2937; box-shadow: none; }

    .btn-wa {
      display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
      background-color: #25D366; color: #06281A; font-weight: 800;
      border-radius: 0.875rem; box-shadow: 0 4px 14px rgba(37, 211, 102, 0.35);
      transition: all 0.15s ease;
    }
    .btn-wa:hover { background-color: #22C45E; transform: translateY(-1px); }

    .pill-badge {
      display: inline-flex; align-items: center; gap: 0.375rem; border-radius: 9999px;
      padding: 0.25rem 0.75rem; font-size: 11px; font-weight: 800;
      text-transform: uppercase; letter-spacing: 0.06em;
    }

    .wa-float {
      position: fixed; right: 1rem; bottom: 1rem; z-index: 50;
      opacity: 0; pointer-events: none; transition: opacity 0.25s ease;
    }
    .wa-float.is-visible { opacity: 1; pointer-events: auto; }"""

TWAILWIND = """  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            navy: '#071952', navydark: '#0B1536', electric: '#0B6BFF',
            amberc: '#F59E0B', amberdark: '#D97706', wagreen: '#25D366',
          },
          fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
        },
      },
    };
  </script>"""

HEADER = """  <header class="sticky top-0 z-40 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
    <div class="container-clean flex h-16 items-center justify-between gap-3">
      <a href="/" class="flex items-center gap-2.5">
        <img src="/logo.webp" alt="PT FirKaizen Digital Solutions" class="h-9 w-9 shrink-0 object-contain" width="36" height="36"/>
        <div class="flex flex-col">
          <span class="text-base font-extrabold text-slate-900 dark:text-white leading-tight">FirKaizen</span>
          <span class="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Artikel &amp; Wawasan</span>
        </div>
      </a>

      <div class="hidden md:flex items-center gap-1 text-xs font-bold text-slate-600 dark:text-slate-300">
        <a href="/" class="px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800">Hub Portal</a>
        <a href="/paving/" class="px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800">Paving</a>
        <a href="/batako/" class="px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800">Batako</a>
        <a href="/gapura/" class="px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800">Gapura</a>
        <a href="/artikel/" class="px-3 py-1.5 rounded-lg text-electric font-black">Artikel</a>
      </div>

      <div class="flex items-center gap-2">
        <button type="button" aria-label="Ganti tema" onclick="toggleTheme()" class="grid h-9 w-9 place-items-center rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200">
          <svg id="sunIcon" class="h-4 w-4 hidden" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>
          <svg id="moonIcon" class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
        </button>
        <a href="__WA_CONSULT__" target="_blank" rel="noopener" class="btn-wa text-xs px-3.5 py-1.5 !rounded-lg whitespace-nowrap shrink-0">
          <svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>
          <span>Chat WA</span>
        </a>
      </div>
    </div>
  </header>"""

FOOTER = """  <footer class="mt-14 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs text-slate-500">
    <div class="container-clean py-10">
      <div class="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
        <div class="lg:col-span-2 max-w-sm">
          <div class="flex items-center gap-2.5">
            <img src="/logo.webp" alt="PT FirKaizen Digital Solutions" class="h-9 w-9 shrink-0 object-contain" width="36" height="36" loading="lazy"/>
            <span class="text-sm font-bold text-slate-900 dark:text-white">PT FirKaizen Digital Solutions</span>
          </div>
          <p class="mt-3 leading-relaxed">Divisi konstruksi fisik: pengerjaan gapura Majapahit bata expose, paving block, bata ringan, dan jasa kontraktor terpadu.</p>
          <p class="mt-2 font-semibold text-slate-700 dark:text-slate-300">Jam pelayanan: setiap hari 07.00&ndash;20.00 WIB</p>
        </div>

        <div>
          <h3 class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Divisi Layanan</h3>
          <ul class="mt-3 space-y-2">
            <li><a href="/paving/" class="hover:text-electric font-semibold">Paving Block &amp; Kanstin</a></li>
            <li><a href="/batako/" class="hover:text-electric font-semibold">Bata Ringan AAC &amp; Batako</a></li>
            <li><a href="/gapura/" class="hover:text-electric font-semibold">Gapura Majapahit</a></li>
            <li><a href="/artikel/" class="text-electric font-bold">Artikel &amp; Wawasan</a></li>
            <li><a href="/" class="hover:text-electric">Hub Portal Material</a></li>
          </ul>
        </div>

        <div>
          <h3 class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Kontak Resmi</h3>
          <ul class="mt-3 space-y-2">
            <li><a href="tel:085196135691" class="font-bold text-slate-900 dark:text-white hover:underline">0851-9613-5691</a></li>
            <li>halo@firkaizen.com</li>
            <li>__WILAYAH__, Indonesia</li>
          </ul>
        </div>
      </div>

      <div class="mt-8 flex flex-col gap-3 border-t border-slate-200 dark:border-slate-800 pt-6 sm:flex-row sm:items-center sm:justify-between">
        <p>&copy; 2026 PT FirKaizen Digital Solutions. Seluruh hak cipta dilindungi.</p>
        <div class="flex gap-4">
          <a href="/privacy/" class="hover:text-electric">Kebijakan Privasi</a>
          <a href="/terms/" class="hover:text-electric">Syarat &amp; Ketentuan</a>
        </div>
      </div>
    </div>
  </footer>"""

SCRIPT = """  <script>
    (function () {
      const stored = localStorage.getItem('theme');
      const dark = stored ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.classList.toggle('dark', dark);
    })();
    function toggleTheme() {
      const isDark = document.documentElement.classList.toggle('dark');
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
      syncIcons();
    }
    function syncIcons() {
      const d = document.documentElement.classList.contains('dark');
      document.getElementById('sunIcon').classList.toggle('hidden', !d);
      document.getElementById('moonIcon').classList.toggle('hidden', d);
    }
    syncIcons();

    const float = document.getElementById('waFloat');
    if (float) {
      const onScroll = () => float.classList.toggle('is-visible', window.scrollY > 500);
      window.addEventListener('scroll', onScroll, { passive: true });
      onScroll();
    }
  </script>"""


# ---------- wilayah layanan ----------
# Gapura dikerjakan tim mitra di Ponorogo dan dilayani se-Pulau Jawa. Lini material
# (paving/batako/bata ringan) berpusat di Solo Raya. Menuliskan "Solo Raya" di artikel
# gapura salah dan menyesatkan -- wilayah ditentukan per artikel, bukan satu templat
# untuk semua. Bisa ditimpa dari frontmatter `wilayah: ...`.
DEFAULT_WILAYAH = {"label": "Solo Raya & Jawa Tengah",
                   "area": ["Solo Raya", "Jawa Tengah", "Jawa Timur"]}
WILAYAH = {
    # Gapura dikerjakan tim mitra di Ponorogo -- jangan sebut Solo (itu lini material).
    "pulau-jawa": {"label": "Ponorogo, Jawa Timur",
                   "area": ["Pulau Jawa"]},
    "solo-jateng": DEFAULT_WILAYAH,
}

def pilih_wilayah(meta):
    w = meta.get("wilayah")
    if w:
        return WILAYAH.get(w, DEFAULT_WILAYAH)
    if str(meta.get("tag", "")).strip().lower() == "gapura":
        return WILAYAH["pulau-jawa"]
    return DEFAULT_WILAYAH


# ---------- frontmatter ----------

def parse_front(text):
    """Frontmatter sederhana: 'key: value' di antara '---'."""
    m = re.match(r"\s*---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        raise ValueError("frontmatter '---' tidak ditemukan")
    meta = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k.strip()] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        else:
            meta[k.strip()] = v.strip("'\"")
    return meta, m.group(2)


def page_shell(*, title, desc, slug, body, ld_extra, breadcrumb, canonical,
               og_image, meta_extra="", wilayah=DEFAULT_WILAYAH):
    """HTML lengkap satu halaman.

    `wilayah` = daerah yang BENAR-BENAR dilayani untuk topik artikel ini:
    {'label': teks di footer kontak, 'area': daftar areaServed JSON-LD}.
    """
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization", "@id": BASE + "/#organization",
                "name": "PT FirKaizen Digital Solutions", "url": BASE + "/",
                "logo": BASE + "/logo.webp", "email": "halo@firkaizen.com",
                "telephone": "+6285196135691",
                "address": {"@type": "PostalAddress", "addressRegion": "Jawa Tengah",
                            "addressLocality": "Solo Raya", "addressCountry": "ID"},
                "areaServed": list(wilayah["area"]),
            },
            ld_extra,
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": i + 1, "name": n, "item": u}
                    for i, (n, u) in enumerate(breadcrumb)
                ],
            },
        ],
    }
    wa_consult = (WA + "?text=Halo%20FirKaizen,%20saya%20ingin%20konsultasi%20"
                  "tentang%20material%20dan%20jasa%20konstruksi")
    FOOTER_WILAYAH = FOOTER.replace("__WILAYAH__", html.escape(wilayah["label"]))
    return f"""<!DOCTYPE html>
<html lang="id" class="scroll-smooth">
<head>
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}"/>
<link rel="canonical" href="{canonical}"/>
<meta name="robots" content="index, follow, max-image-preview:large"/>

<meta property="og:type" content="article"/>
<meta property="og:site_name" content="FirKaizen"/>
<meta property="og:locale" content="id_ID"/>
<meta property="og:url" content="{canonical}"/>
<meta property="og:title" content="{html.escape(title)}"/>
<meta property="og:description" content="{html.escape(desc)}"/>
<meta property="og:image" content="{og_image}"/>
<meta property="og:image:width" content="1200"/>
<meta property="og:image:height" content="630"/>

<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{html.escape(title)}"/>
<meta name="twitter:description" content="{html.escape(desc)}"/>
<meta name="twitter:image" content="{og_image}"/>

<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>
{meta_extra}
  <meta name="google-site-verification" content="4y-QK0-_Wj-QUO62PKwyyV5zOIwRaCRmKspIfmjASwY" />
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0"/>
  <link rel="icon" type="image/webp" href="/logo.webp"/>

  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet"/>

{TWAILWIND}

  <style>
{STYLE}
  </style>
</head>
<body>
{HEADER}

  <main class="py-8 sm:py-12">
{body}
  </main>

{FOOTER_WILAYAH}

  <div id="waFloat" class="wa-float">
    <a href="{wa_consult}" target="_blank" rel="noopener" aria-label="Chat WhatsApp" class="btn-wa h-14 w-14 !rounded-full shadow-lg">
      <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>
    </a>
  </div>

{SCRIPT}
</body>
</html>
"""


def render_article(md_path):
    meta, body_md = parse_front(open(md_path, encoding="utf-8").read())
    slug = meta["slug"]
    title = meta["title"]
    desc = meta["description"]
    og = meta.get("og_image", f"{BASE}/images/og/default.webp")
    canonical = f"{BASE}/artikel/{slug}/"
    date = meta.get("date", TODAY)
    tag = meta.get("tag", "Artikel")
    read_min = max(1, round(len(body_md.split()) / 220))

    body_html = markdown.markdown(
        body_md, extensions=["extra", "sane_lists", "toc"], output_format="html"
    )

    header_html = f"""    <div class="container-clean">
      <div class="prose-clean mx-auto">
        <nav class="mb-4 text-xs font-semibold text-slate-500" aria-label="Breadcrumb">
          <a href="/" class="hover:text-electric">Beranda</a>
          <span class="mx-1.5">/</span>
          <a href="/artikel/" class="hover:text-electric">Artikel</a>
          <span class="mx-1.5">/</span>
          <span class="text-slate-700 dark:text-slate-300">{html.escape(tag)}</span>
        </nav>

        <span class="pill-badge bg-electric/10 text-electric">{html.escape(tag)}</span>
        <h1 class="mt-3 text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-snug">
          {html.escape(title)}
        </h1>
        <p class="mt-3 text-sm text-slate-500">
          <time datetime="{date}">{date}</time> · {read_min} menit baca · PT FirKaizen Digital Solutions
        </p>
      </div>
    </div>

    <div class="container-clean mt-8">
      <article class="card-clean prose-clean mx-auto p-6 sm:p-9">
{body_html}
      </article>
    </div>

    <div class="container-clean mt-8">
      <div class="prose-clean mx-auto rounded-2xl bg-navy p-6 text-white sm:p-8">
        <h2 class="!mt-0 !text-white text-xl font-black">Butuh hitungan untuk proyek Anda?</h2>
        <p class="!mb-4 text-slate-300">Kirim ukuran dan lokasi, tim kami hitungkan kebutuhan material dan gambaran biaya. Ketentuan survei dijelaskan saat konsultasi.</p>
        <a href="{WA}?text=Halo%20FirKaizen,%20saya%20ingin%20konsultasi%20proyek" target="_blank" rel="noopener" class="btn-wa px-5 py-3 text-sm no-underline">
          Konsultasi via WhatsApp
        </a>
      </div>
    </div>"""

    ld_extra = {
        "@type": "Article",
        "headline": title,
        "description": desc,
        "datePublished": date,
        "dateModified": date,
        "inLanguage": "id-ID",
        "image": og,
        "author": {"@type": "Organization", "name": "PT FirKaizen Digital Solutions"},
        "publisher": {"@type": "Organization", "name": "PT FirKaizen Digital Solutions",
                      "logo": {"@type": "ImageObject", "url": f"{BASE}/logo.webp"}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
    }
    breadcrumb = [("Beranda", BASE + "/"), ("Artikel", BASE + "/artikel/"),
                  (title, canonical)]

    return slug, page_shell(
        title=title, desc=desc, slug=slug, body=header_html,
        ld_extra=ld_extra, breadcrumb=breadcrumb, canonical=canonical, og_image=og,
        wilayah=pilih_wilayah(meta),
    ), meta


def render_index(articles):
    """Halaman daftar artikel."""
    cards = []
    for a in sorted(articles, key=lambda x: x["date"], reverse=True):
        cards.append(f"""        <a href="/artikel/{a['slug']}/" class="card-clean group flex flex-col p-6 transition hover:border-electric">
          <span class="pill-badge bg-electric/10 text-electric self-start">{html.escape(a['tag'])}</span>
          <h2 class="mt-3 text-lg font-black text-slate-900 dark:text-white group-hover:text-electric">{html.escape(a['title'])}</h2>
          <p class="mt-2 text-sm text-slate-500 line-clamp-3">{html.escape(a['description'])}</p>
          <span class="mt-4 text-xs font-bold text-slate-400">{a['date']} · baca selengkapnya</span>
        </a>""")

    body = f"""    <div class="container-clean">
      <div class="prose-clean mx-auto text-center">
        <span class="pill-badge bg-electric/10 text-electric">Artikel &amp; Wawasan</span>
        <h1 class="mt-3 text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Panduan Material &amp; Pengerjaan
        </h1>
        <p class="mt-3 text-slate-500">
          Hitungan biaya, perbandingan material, dan hal yang sering terlewat sebelum
          memesan paving, batako, atau gapura.
        </p>
      </div>
    </div>

    <div class="container-clean mt-10">
      <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
{chr(10).join(cards) if cards else '        <p class="text-slate-500">Belum ada artikel.</p>'}
      </div>
    </div>"""

    ld_extra = {"@type": "CollectionPage", "name": "Artikel & Wawasan FirKaizen",
                "url": f"{BASE}/artikel/", "inLanguage": "id-ID"}
    breadcrumb = [("Beranda", BASE + "/"), ("Artikel", BASE + "/artikel/")]
    # halaman ini memuat artikel gapura (se-Pulau Jawa) dan material (Solo Raya) --
    # areaServed yang benar adalah gabungannya, bukan salah satu.
    ada_gapura = any(str(a.get("tag", "")).strip().lower() == "gapura" for a in articles)
    w_index = ({"label": "Ponorogo & Solo Raya",
                "area": ["Pulau Jawa", "Jawa Tengah", "Jawa Timur"]}
               if ada_gapura else DEFAULT_WILAYAH)
    return page_shell(
        title="Artikel & Wawasan Material Konstruksi",
        desc="Panduan dan hitungan biaya paving block, batako, bata ringan, dan gapura Majapahit dari FirKaizen.",
        slug="artikel", body=body, ld_extra=ld_extra, breadcrumb=breadcrumb,
        canonical=f"{BASE}/artikel/", og_image=f"{BASE}/images/og/default.webp",
        wilayah=w_index,
    )


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    files = sorted(glob.glob(os.path.join(SRC, "*.md")))
    if not files:
        raise SystemExit(f"tidak ada .md di {SRC}")
    metas = []
    for f in files:
        slug, out, meta = render_article(f)
        d = os.path.join(OUT, slug)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(out)
        meta["slug"] = slug
        metas.append(meta)
        print(f"  artikel/{slug}/index.html  ({len(out)//1024} KB)")
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
        render_index(metas))
    print(f"  artikel/index.html  ({len(metas)} artikel)")