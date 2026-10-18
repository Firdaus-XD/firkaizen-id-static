#!/usr/bin/env python3
"""Generate halaman artikel firkaizen.id dari file markdown + frontmatter.

Sumber:  content/artikel/<slug>.md   (frontmatter YAML-ish + markdown)
Output:  artikel/index.html          (daftar artikel)
         artikel/<slug>/index.html   (halaman artikel)

Alasan pakai generator, bukan tulis HTML tangan: menambah artikel = tambah 1 file .md,
lalu jalankan script. Tidak ada salinan nav/footer/head yang bisa jadi tidak sinkron.

Tata letak artikel mengikuti halaman artikel firkaizen.com: breadcrumb, judul besar,
baris penulis + aksi, panel ringkasan, daftar isi bernomor, prosa satu kolom, navigasi
artikel, blok penulis, artikel terkait, lalu ajakan. Diterapkan di generator supaya
seluruh artikel ikut sekaligus -- bukan disunting satu per satu.
"""
import os, re, html, json, datetime, glob, urllib.parse

import markdown

ROOT = os.path.expanduser("~/.hermes/cache/scratch/fk-static-repo")
SRC = os.path.join(ROOT, "content", "artikel")
OUT = os.path.join(ROOT, "artikel")
BASE = "https://firkaizen.id"
WA = "https://wa.me/6285196135691"
TODAY = datetime.date.today().isoformat()

BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]

# Gambar depan per artikel. Dipilih dari stok nyata lewat contact sheet + inspeksi visual,
# TIDAK ditebak dari nama berkas. og_image per kategori cuma ada empat (gapura/paving/
# batako/default), jadi tanpa pilihan ini tiga kartu "artikel terkait" bergambar identik.
# Thumbnail ringannya dibuat `ops/build_thumb.py` dari peta yang sama.
PILIH_THUMB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thumb_pilih.json")
with open(PILIH_THUMB, encoding="utf-8") as _f:
    GAMBAR_DEPAN = json.load(_f)


def tanggal_id(iso):
    """2026-10-12 -> '12 Oktober 2026'."""
    try:
        y, m, d = iso.split("-")
        return f"{int(d)} {BULAN[int(m)]} {y}"
    except (ValueError, IndexError):
        return iso


# ---------- aset bersama ----------
#
# Warna dipindah ke variabel CSS (--surface, --heading, ...). Sebelumnya setiap aturan
# butuh dua baris (.x dan .dark .x); dengan variabel satu aturan cukup, dan aturan yang
# lupa varian .dark-nya tidak lagi membuat halaman gelap-separuh.

STYLE = """    :root {
      --surface: #FFFFFF;
      --surface-2: #F1F5F9;
      --border: #E2E8F0;
      --heading: #0F172A;
      --body: #334155;
      --soft: #64748B;
      --page: #F8FAFC;
    }
    .dark {
      --surface: #111827;
      --surface-2: #0F1729;
      --border: #1F2937;
      --heading: #F8FAFC;
      --body: #CBD5E1;
      --soft: #94A3B8;
      --page: #0A0F1D;
    }

    body {
      background-color: var(--page);
      color: var(--body);
      font-size: 15px;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }

    .t-heading { color: var(--heading); }
    .t-body { color: var(--body); }
    .t-soft { color: var(--soft); }

    .container-clean {
      width: 100%; max-width: 68rem; margin-left: auto; margin-right: auto;
      padding-left: 1.25rem; padding-right: 1.25rem;
    }

    .prose-clean { max-width: 48rem; }

    .prose-article h2 {
      font-size: 1.5rem; font-weight: 800; margin-top: 2.75rem; margin-bottom: 0.85rem;
      color: var(--heading); letter-spacing: -0.015em; line-height: 1.25;
      scroll-margin-top: 6rem;
    }
    .prose-article h3 {
      font-size: 1.15rem; font-weight: 700; margin-top: 2rem; margin-bottom: 0.6rem;
      color: var(--heading); scroll-margin-top: 6rem;
    }
    .prose-article p { margin-bottom: 1.15rem; font-size: 1rem; line-height: 1.75; }
    .prose-article ul, .prose-article ol { margin: 0 0 1.15rem 1.35rem; }
    .prose-article ul { list-style: disc; }
    .prose-article ol { list-style: decimal; }
    .prose-article li { margin-bottom: 0.5rem; line-height: 1.7; }
    .prose-article a { color: #0B6BFF; font-weight: 600; text-decoration: underline;
                       text-underline-offset: 3px; }
    .prose-article a:hover { color: #0A5AD6; }
    .prose-article strong { font-weight: 700; color: var(--heading); }
    .prose-article img { border-radius: 1rem; margin: 1.75rem 0; }
    .prose-article table {
      width: 100%; border-collapse: collapse; margin: 1.5rem 0; font-size: 0.9rem;
    }
    .prose-article th, .prose-article td {
      border: 1px solid var(--border); padding: 0.7rem 0.85rem; text-align: left;
    }
    .prose-article th {
      background-color: var(--surface-2); font-weight: 700; color: var(--heading);
    }
    .prose-article blockquote {
      border-left: 3px solid #0B6BFF; padding-left: 1.15rem; margin: 1.5rem 0;
      color: var(--soft); font-style: italic;
    }
    /* Tabel lebar di HP: bisa digeser, bukan memaksa seluruh halaman melebar. */
    .tabel-bungkus { overflow-x: auto; margin: 1.5rem 0; }

    .card-clean {
      background-color: var(--surface); border: 1px solid var(--border);
      border-radius: 1.25rem; box-shadow: 0 4px 20px -4px rgba(7, 25, 82, 0.05);
    }
    .dark .card-clean { box-shadow: none; }

    .panel-soft {
      background-color: var(--surface-2); border: 1px solid var(--border);
      border-radius: 1.25rem;
    }
    .panel-ringkas {
      background-color: rgba(11, 107, 255, 0.04);
      border: 1px solid rgba(11, 107, 255, 0.25);
      border-radius: 1.25rem;
    }

    .teks-judul {
      font-size: 1.875rem; font-weight: 800; letter-spacing: -0.02em;
      line-height: 1.2; color: var(--heading);
    }
    @media (min-width: 640px) { .teks-judul { font-size: 2.25rem; } }
    @media (min-width: 1024px) { .teks-judul { font-size: 2.625rem; } }

    .tombol-halus {
      display: inline-flex; align-items: center; gap: 0.4rem;
      border: 1px solid var(--border); background-color: var(--surface);
      border-radius: 9999px; padding: 0.4rem 0.85rem;
      font-size: 12px; font-weight: 600; color: var(--body);
      transition: border-color 0.15s ease, color 0.15s ease;
    }
    .tombol-halus:hover { border-color: #0B6BFF; color: #0B6BFF; }

    .avatar-fk {
      display: grid; place-items: center; height: 2.5rem; width: 2.5rem;
      flex-shrink: 0; border-radius: 9999px;
      background-color: rgba(11, 107, 255, 0.1); color: #0B6BFF;
      font-weight: 800; font-size: 0.8rem; letter-spacing: 0.02em;
    }

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

    .pita-baca {
      position: fixed; top: 0; left: 0; right: 0; height: 3px; z-index: 50;
      background: transparent; pointer-events: none;
    }
    .pita-baca > div {
      height: 100%; width: 0%; background-color: #0B6BFF;
      box-shadow: 0 0 8px rgba(11, 107, 255, 0.6);
      transition: width 75ms ease-out;
    }

    .pola-grid {
      background-image:
        linear-gradient(to right, rgba(11, 107, 255, 0.16) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(11, 107, 255, 0.16) 1px, transparent 1px);
      background-size: 44px 44px;
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
        <a href="https://pavingblockjatim.my.id/" class="px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800">Paving</a>
        <a href="/batako/" class="px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800">Batako</a>
        <a href="https://gapuramajapahit.web.id/" class="px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800">Gapura</a>
        <a href="/artikel/" class="px-3 py-1.5 rounded-lg text-electric font-black">Artikel</a>
      </div>

      <div class="flex items-center gap-2">
        <button type="button" aria-label="Ganti tema" onclick="toggleTheme()" class="grid h-9 w-9 place-items-center rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200">
          <svg id="sunIcon" class="h-4 w-4 hidden" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>
          <svg id="moonIcon" class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
        </button>
        <a href="https://wa.me/6285196135691?text=Halo%20FirKaizen%2C%20saya%20ingin%20konsultasi" target="_blank" rel="noopener" class="btn-wa text-xs px-3.5 py-1.5 !rounded-lg whitespace-nowrap shrink-0">
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
            <li><a href="https://pavingblockjatim.my.id/" class="hover:text-electric font-semibold">Paving Block &amp; Kanstin</a></li>
            <li><a href="/batako/" class="hover:text-electric font-semibold">Bata Ringan AAC &amp; Batako</a></li>
            <li><a href="https://gapuramajapahit.web.id/" class="hover:text-electric font-semibold">Gapura Majapahit</a></li>
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

    // Pita kemajuan baca.
    const pita = document.querySelector('#pitaBaca > div');
    const isi = document.querySelector('.prose-article');
    if (pita && isi) {
      const update = () => {
        const tinggi = isi.offsetHeight - window.innerHeight;
        const lewat = window.scrollY - isi.offsetTop;
        pita.style.width = Math.min(100, Math.max(0, (lewat / tinggi) * 100)) + '%';
      };
      window.addEventListener('scroll', update, { passive: true });
      window.addEventListener('resize', update);
      update();
    }

    // Salin tautan: tanpa ini tombolnya cuma hiasan.
    function salinTautan(btn) {
      const asli = btn.innerHTML;
      const beres = () => {
        btn.innerHTML = 'Tautan disalin';
        setTimeout(() => { btn.innerHTML = asli; }, 1600);
      };
      if (navigator.clipboard) {
        navigator.clipboard.writeText(location.href).then(beres, () => {});
      } else {
        const t = document.createElement('textarea');
        t.value = location.href; document.body.appendChild(t); t.select();
        try { document.execCommand('copy'); beres(); } catch (e) {}
        document.body.removeChild(t);
      }
    }

    // Tabel lebar di HP: bungkus supaya bisa digeser, bukan memaksa halaman melebar.
    document.querySelectorAll('.prose-article table').forEach(t => {
      if (t.parentElement.classList.contains('tabel-bungkus')) return;
      const w = document.createElement('div'); w.className = 'tabel-bungkus';
      t.parentNode.insertBefore(w, t); w.appendChild(t);
    });
  </script>"""


# ---------- wilayah layanan ----------
# Gapura dikerjakan tim mitra di Ponorogo dan dilayani se-Pulau Jawa. Lini material
# (paving/batako/bata ringan) berpusat di Solo Raya. Menuliskan "Solo Raya" di artikel
# gapura salah dan menyesatkan -- wilayah ditentukan per artikel, bukan satu templat
# untuk semua. Bisa ditimpa dari frontmatter `wilayah: ...`.
DEFAULT_WILAYAH = {"label": "Solo Raya & Jawa Tengah",
                   "area": ["Solo Raya", "Jawa Tengah", "Jawa Timur"],
                   "ringkas": "Solo Raya dan Jawa Tengah"}
WILAYAH = {
    # Gapura dikerjakan tim mitra di Ponorogo -- jangan sebut Solo (itu lini material).
    "pulau-jawa": {"label": "Ponorogo, Jawa Timur",
                   "area": ["Pulau Jawa"],
                   "ringkas": "seluruh Pulau Jawa"},
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
                "telephone": "+628****5691",
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

  <div class="pita-baca" id="pitaBaca" aria-hidden="true"><div></div></div>

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


# ---------- komponen halaman artikel ----------

def thumb(slug):
    """Gambar depan satu artikel; None kalau tidak terdaftar.

    Dipakai kartu daftar dan kartu "artikel terkait". Kalau berkasnya tidak ada, kembalikan
    None supaya kartunya jatuh ke tampilan tanpa gambar -- lebih baik daripada <img> rusak
    yang bisa bikin pelompatnya memblokir render.
    """
    src = GAMBAR_DEPAN.get(slug)
    if not src:
        return None
    kecil = os.path.join(ROOT, "images", "thumb", f"{slug}.webp")
    if os.path.exists(kecil):
        return f"/images/thumb/{slug}.webp"
    return "/" + src.lstrip("/") if os.path.exists(os.path.join(ROOT, src)) else None


def kartu_gambar(slug, alt, kelas="aspect-[16/10]"):
    """Blok gambar untuk kartu artikel. Kosong kalau tidak ada gambar.

    Foto gapura dari HP hampir semuanya PORTRAIT (~0.56). Memaksa `object-cover` ke kotak
    16:10 membuang dua pertiga gambar: yang tersisa cuma potongan pilar, bukan gapuranya.
    Jadi: gambar ditampilkan utuh (`object-contain`) di tengah, dan sisi kosongnya diisi
    versi blur dari foto yang sama (`object-cover`) -- pola yang sama dipakai kartu produk
    di halaman layanan. Nol dependensi, satu berkas sumber.
    """
    g = thumb(slug)
    if not g:
        return ""
    return (
        f'<div class="relative overflow-hidden border-b {kelas}" '
        f'style="border-color:var(--border);background-color:var(--surface-2)">'
        f'<img src="{g}" alt="" aria-hidden="true" loading="lazy" '
        f'class="absolute inset-0 h-full w-full object-cover blur-3xl scale-125"/>'
        f'<img src="{g}" alt="{html.escape(alt)}" loading="lazy" '
        f'class="absolute inset-0 h-full w-full object-contain transition-transform duration-300 group-hover:scale-[1.03]"/>'
        f"</div>"
    )


def rasio_kotak(slug):
    """Kelas aspect-ratio untuk gambar utama, mengikuti rasio foto sumbernya.

    Foto gapura dari HP banyak yang potret (rasio 0.46-0.75). Memaksa semuanya ke kotak
    lebar membuat gapuranya menyusut jadi strip kecil di tengah -- terlihat rusak, bukan
    "gambar penuh". Kotak yang mengikuti rasio sumber menampilkan foto hampir penuh.
    """
    # Kotak mengikuti rasio foto sedekat mungkin, karena `object-contain` menyisakan
    # bantalan di sisi yang tidak cocok. Satu kotak potret untuk semua tidak cukup: foto
    # 0.75 di kotak 9/16 (0.5625) justru menyisakan bantalan ATAS-BAWAH ~22% tinggi.
    # Dua tingkat: potret tinggi (0.46-0.65) dan potret sedang (0.65-0.85).
    kelas_potret_tinggi = "aspect-[9/16] sm:aspect-[4/5]"
    kelas_potret = "aspect-[3/4]"
    kelas_landai = "aspect-[4/3] sm:aspect-[3/2]"
    kelas_lebar = "aspect-[4/3] sm:aspect-[16/9]"
    src = GAMBAR_DEPAN.get(slug)
    if not src:
        return kelas_landai
    try:
        from PIL import Image as _I
        with _I.open(os.path.join(ROOT, src)) as im:
            r = im.width / im.height
    except Exception:
        return kelas_landai
    if r < 0.65:
        return kelas_potret_tinggi
    if r < 0.85:
        return kelas_potret
    if r < 1.5:
        return kelas_landai
    return kelas_lebar


def daftar_isi(body_html):
    """Daftar isi dari h2 yang diberi id oleh ekstensi `toc` markdown.

    Nomor dua digit (01, 02, ...) mengikuti halaman artikel firkaizen.com: pembaca tahu
    panjang artikelnya sejak awal. Tanpa h2 sama sekali hasilnya string kosong -- bukan
    panel kosong yang membingungkan.
    """
    judul = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body_html, re.S)
    if not judul:
        return ""
    item = []
    for i, (sid, teks) in enumerate(judul, 1):
        bersih = html.unescape(re.sub(r"<[^>]+>", "", teks)).strip()
        item.append(
            f'<li><a href="#{sid}" class="group flex items-start gap-2.5 t-body hover:text-electric transition-colors">'
            f'<span class="mt-0.5 text-xs font-mono font-bold" style="color:rgba(11,107,255,0.7)">{i:02d}. </span>'
            f'<span class="group-hover:underline underline-offset-4 leading-snug">{html.escape(bersih)}</span>'
            f"</a></li>"
        )
    return (
        '<div class="panel-soft mt-8 p-5 sm:p-6">'
        '<div class="flex items-center gap-2 text-sm font-bold t-heading">'
        '<svg class="h-4 w-4 text-electric" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/></svg>'
        "<span>Daftar Isi Artikel</span></div>"
        '<ul class="mt-3.5 space-y-2.5 text-sm">' + "".join(item) + "</ul></div>"
    )


def blok_bagikan(tag, title, canonical, tags=None):
    """Blok bagi + daftar topik. Mengikuti halaman artikel firkaizen.com.

    Ditaruh sesudah prosa, sebelum navigasi: pembaca yang selesai membaca langsung punya
    tombol untuk menyebarkannya, tanpa harus menggulir sampai bawah.
    """
    daftar = tags or [tag]
    if isinstance(daftar, str):
        daftar = [t.strip() for t in daftar.split(",") if t.strip()]
    if tag not in daftar:
        daftar.insert(0, tag)
    teks = urllib.parse.quote(f"{title}\n\nBaca selengkapnya di:\n{canonical}")
    pil = "".join(
        f'<span class="rounded-lg border px-2.5 py-1 text-xs font-medium t-body" '
        f'style="border-color:var(--border);background-color:var(--surface)">#{html.escape(t)}</span>'
        for t in daftar
    )
    return (
        '<div class="mt-14 flex flex-col justify-between gap-4 border-t pt-6 sm:flex-row sm:items-center" '
        'style="border-color:var(--border)">'
        '<div class="text-xs font-semibold uppercase tracking-wider t-soft">'
        "Suka artikel ini? Bagikan ke rekan Anda:</div>"
        '<div class="flex items-center gap-2">'
        f'<a href="https://api.whatsapp.com/send?text={teks}" target="_blank" rel="noopener noreferrer" '
        'class="tombol-halus no-underline">'
        '<svg class="h-4 w-4" style="color:#25D366" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>Bagikan via WhatsApp</a>'
        '<button type="button" onclick="salinTautan(this)" class="tombol-halus">'
        '<svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>'
        '<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>'
        "<span>Salin Tautan</span></button></div></div>"
        '<div class="mt-8 flex flex-wrap items-center gap-2 border-t pt-6" style="border-color:var(--border)">'
        '<span class="text-xs font-semibold uppercase tracking-wider t-soft">Topik Terkait:</span>'
        + pil + "</div>"
    )


def navigasi_artikel(semua, slug):
    """Artikel sebelumnya / berikutnya menurut tanggal.

    Tanpa ini pembaca buntu di ujung halaman, padahal artikel di sini saling menjawab
    pertanyaan yang berdekatan.

    `semua` HARUS memuat artikel yang sedang dibuka -- mencari `slug` di dalam daftar yang
    sudah dikecualikan membuat indeksnya tidak pernah ketemu dan blok ini diam-diam kosong.
    """
    if len(semua) < 2:
        return ""
    urut = sorted(semua, key=lambda a: (a["date"], a["slug"]), reverse=True)
    idx = next((i for i, a in enumerate(urut) if a["slug"] == slug), None)
    if idx is None:
        return ""
    lebih_baru = urut[idx - 1] if idx > 0 else None
    lebih_lama = urut[idx + 1] if idx + 1 < len(urut) else None

    def kartu(a, arah):
        if not a:
            return ""
        panah = "&larr;" if arah == "baru" else "&rarr;"
        rata = "" if arah == "baru" else " sm:text-right"
        return (
            f'<a href="/artikel/{a["slug"]}/" class="group block flex-1 rounded-2xl border p-4 transition-colors" '
            f'style="border-color:var(--border);background-color:var(--surface)">'
            f'<div class="text-[11px] font-bold uppercase tracking-wider t-soft">{panah} '
            f'{"Lebih baru" if arah == "baru" else "Sebelumnya"}</div>'
            f'<div class="mt-1.5 text-sm font-bold t-heading group-hover:text-electric transition-colors{rata}">'
            f'{html.escape(a["title"])}</div></a>'
        )

    return (
        '<div class="mt-14 flex flex-col gap-4 border-t pt-8 sm:flex-row" '
        'style="border-color:var(--border)">'
        + kartu(lebih_baru, "baru") + kartu(lebih_lama, "lama") + "</div>"
    )


def blok_penulis(tag, wilayah):
    """Blok penulis.

    Tidak memakai klaim yang tidak bisa dibuktikan (jumlah tahun pengalaman, jumlah
    proyek) -- hanya divisi dan cakupan layanan yang memang benar. Aturan yang sama
    seperti artikel: klaim tanpa sumber dilarang.
    """
    return (
        '<div class="panel-soft mt-8 p-6 sm:p-8">'
        '<div class="flex flex-col items-start gap-5 sm:flex-row sm:items-center">'
        '<div class="avatar-fk h-14 w-14 text-base">FK</div>'
        '<div class="flex-1">'
        '<h3 class="text-base font-bold t-heading">PT FirKaizen Digital Solutions</h3>'
        '<p class="mt-1.5 text-sm t-body">Divisi konstruksi fisik: gapura Majapahit bata '
        'expose, paving block, batako, dan bata ringan. Untuk topik '
        f'<strong class="t-heading">{html.escape(tag)}</strong>, layanan kami mencakup '
        f"{html.escape(wilayah['ringkas'])}.</p>"
        '<div class="mt-4 flex flex-wrap items-center gap-2">'
        f'<a href="{WA}?text=Halo%20FirKaizen,%20saya%20ingin%20bertanya" '
        'target="_blank" rel="noopener" class="tombol-halus no-underline">Tanya lewat WhatsApp</a>'
        '<a href="/artikel/" class="tombol-halus no-underline">Semua artikel</a>'
        "</div></div></div></div>"
    )


def kartu_terkait(lain, slug, tag):
    """Artikel lain dengan tag sama; kalau kurang dari tiga, ditambal artikel terbaru."""
    senada = [a for a in lain if a["tag"] == tag]
    tambahan = [a for a in sorted(lain, key=lambda x: x["date"], reverse=True)
                if a["tag"] != tag]
    pilihan = (senada + tambahan)[:3]
    if not pilihan:
        return ""
    kartu = []
    for a in pilihan:
        kartu.append(
            f'<a href="/artikel/{a["slug"]}/" class="group flex flex-col overflow-hidden rounded-2xl border transition-colors" '
            f'style="border-color:var(--border);background-color:var(--surface)">'
            + kartu_gambar(a["slug"], a["title"]) +
            f'<div class="flex flex-1 flex-col p-5">'
            f'<div class="flex items-center gap-2 text-[12px] t-soft">'
            f'<span>{html.escape(a["tag"])}</span><span>&middot;</span>'
            f'<span>{a["read_min"]} menit baca</span></div>'
            f'<h3 class="mt-2.5 text-base font-bold leading-snug t-heading group-hover:text-electric transition-colors">'
            f'{html.escape(a["title"])}</h3>'
            + (f'<p class="mt-2 flex-1 text-sm t-body">{html.escape(a["description"])}</p>'
               if a.get("description") else "")
            + f'<div class="mt-4 flex items-center gap-1.5 text-xs font-semibold text-electric">Baca artikel &rarr;</div>'
            f"</div></a>"
        )
    return (
        '<div class="container-clean mt-16 max-w-4xl">'
        '<div class="flex items-center justify-between">'
        '<h2 class="text-xl font-bold t-heading">Artikel terkait</h2>'
        '<a href="/artikel/" class="text-xs font-semibold text-electric hover:underline">Lihat semua</a></div>'
        '<div class="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">'
        + "".join(kartu) + "</div></div>"
    )


def hero_cta(wilayah):
    return (
        '<div class="container-clean mt-16 max-w-4xl">'
        '<section class="relative overflow-hidden rounded-3xl" style="background-color:#071952">'
        '<div class="pola-grid absolute inset-0 opacity-60"></div>'
        '<div class="relative px-6 py-10 sm:px-12 sm:py-16">'
        '<div class="mx-auto max-w-2xl text-center">'
        '<h2 class="text-2xl font-bold text-white sm:text-4xl">Butuh hitungan untuk proyek Anda?</h2>'
        '<p class="mt-3 text-sm text-slate-300 sm:text-base">Kirim ukuran dan lokasi, tim kami '
        f"hitungkan kebutuhan material dan gambaran biaya untuk {html.escape(wilayah['ringkas'])}. "
        'Ketentuan survei dijelaskan saat konsultasi.</p>'
        '<div class="mt-6 flex flex-col items-center justify-center gap-2.5 sm:flex-row sm:gap-3">'
        f'<a href="{WA}?text=Halo%20FirKaizen,%20saya%20ingin%20konsultasi%20proyek" '
        'target="_blank" rel="noopener" class="btn-wa px-6 py-3 text-sm no-underline">Konsultasi via WhatsApp</a>'
        '<a href="/" class="rounded-xl border border-white/25 px-6 py-3 text-sm font-semibold text-white no-underline transition-colors hover:bg-white/10">Lihat layanan lain</a>'
        "</div></div></div></section></div>"
    )


def render_article(md_path, semua):
    meta, body_md = parse_front(open(md_path, encoding="utf-8").read())
    slug = meta["slug"]
    title = meta["title"]
    desc = meta["description"]
    og = meta.get("og_image", f"{BASE}/images/og/default.webp")
    canonical = f"{BASE}/artikel/{slug}/"
    date = meta.get("date", TODAY)
    tag = meta.get("tag", "Artikel")
    read_min = max(1, round(len(body_md.split()) / 220))
    wilayah = pilih_wilayah(meta)

    body_html = markdown.markdown(
        body_md, extensions=["extra", "sane_lists", "toc"], output_format="html"
    )
    lain = [a for a in semua if a["slug"] != slug]
    g = thumb(slug)
    gambar_utama = (
        '<div class="relative mt-8 overflow-hidden rounded-2xl border" '
        'style="border-color:var(--border);background-color:var(--surface-2)">'
        f'<div class="relative {rasio_kotak(slug)} w-full">'
        f'<img src="{g}" alt="" aria-hidden="true" '
        'class="absolute inset-0 h-full w-full object-cover blur-3xl scale-125"/>'
        f'<img src="{g}" alt="{html.escape(title)}" width="1200" height="900" '
        'class="absolute inset-0 h-full w-full object-contain"/>'
        "</div></div>"
    ) if g else ""

    header_html = f"""    <div class="container-clean">
      <nav class="flex items-center gap-2 text-[12px] t-soft" aria-label="Breadcrumb">
        <a href="/" class="transition-colors hover:text-electric">Beranda</a>
        <span>/</span>
        <a href="/artikel/" class="transition-colors hover:text-electric">Artikel</a>
        <span>/</span>
        <span class="truncate max-w-[200px] sm:max-w-md t-heading">{html.escape(tag)}</span>
      </nav>
    </div>

    <article class="container-clean prose-clean mt-8 max-w-3xl">
      <div class="flex flex-wrap items-center gap-2.5">
        <span class="pill-badge bg-electric/10 text-electric">{html.escape(tag)}</span>
        <span class="text-xs t-soft">&middot;</span>
        <span class="inline-flex items-center gap-1 text-xs t-soft">
          <svg class="h-3.5 w-3.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          {read_min} menit baca
        </span>
      </div>

      <h1 class="teks-judul mt-5">{html.escape(title)}</h1>

      <div class="mt-8 flex flex-wrap items-center justify-between gap-4 border-y py-4 text-sm" style="border-color:var(--border)">
        <div class="flex items-center gap-3">
          <div class="avatar-fk">FK</div>
          <div>
            <div class="font-semibold t-heading">PT FirKaizen Digital Solutions</div>
            <div class="text-xs t-soft">Dipublikasikan pada {tanggal_id(date)}</div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button type="button" onclick="salinTautan(this)" class="tombol-halus">
            <svg class="h-3.5 w-3.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
            <span>Salin Tautan</span>
          </button>
          <a href="{WA}?text=Halo%20FirKaizen,%20saya%20ingin%20konsultasi" target="_blank" rel="noopener" class="tombol-halus no-underline">
            <svg class="h-3.5 w-3.5" style="color:#25D366" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>
            <span>Tanya Tim</span>
          </a>
        </div>
      </div>

      {gambar_utama}

      <div class="panel-ringkas mt-8 p-5 sm:p-6">
        <div class="mb-2.5 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-electric">
          <span class="inline-block h-2 w-2 rounded-full bg-electric animate-pulse"></span>
          Inti &amp; Ringkasan Pembahasan
        </div>
        <p class="text-[15px] font-medium leading-relaxed t-heading sm:text-base">{html.escape(desc)}</p>
      </div>

      {daftar_isi(body_html)}

      <div class="prose-article mt-10">
{body_html}
      </div>

      {blok_bagikan(tag, title, canonical, meta.get("tags"))}
      {navigasi_artikel(semua, slug)}
      {blok_penulis(tag, wilayah)}
    </article>

{kartu_terkait(lain, slug, tag)}

{hero_cta(wilayah)}"""

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
        wilayah=wilayah,
    ), meta


PAGE_SIZE = 12


def render_pagination(current_page, total_pages):
    if total_pages <= 1:
        return ""
    items = []

    # Tombol Sebelumnya
    if current_page > 1:
        prev_url = "/artikel/" if current_page == 2 else f"/artikel/page/{current_page - 1}/"
        items.append(
            f'<a href="{prev_url}" class="rounded-xl border px-3.5 py-2 text-xs sm:text-sm font-semibold transition-colors hover:border-electric hover:text-electric" '
            f'style="border-color:var(--border);background-color:var(--surface);color:var(--heading)">&larr; Sebelumnya</a>'
        )
    else:
        items.append(
            f'<span class="rounded-xl border px-3.5 py-2 text-xs sm:text-sm font-semibold opacity-40 cursor-not-allowed" '
            f'style="border-color:var(--border);background-color:var(--surface);color:var(--soft)">&larr; Sebelumnya</span>'
        )

    # Nomor Halaman
    for p in range(1, total_pages + 1):
        p_url = "/artikel/" if p == 1 else f"/artikel/page/{p}/"
        if p == current_page:
            items.append(
                f'<span class="rounded-xl border px-3.5 py-2 text-xs sm:text-sm font-bold text-white bg-electric" '
                f'style="border-color:var(--electric)">{p}</span>'
            )
        else:
            items.append(
                f'<a href="{p_url}" class="rounded-xl border px-3.5 py-2 text-xs sm:text-sm font-semibold transition-colors hover:border-electric hover:text-electric" '
                f'style="border-color:var(--border);background-color:var(--surface);color:var(--heading)">{p}</a>'
            )

    # Tombol Selanjutnya
    if current_page < total_pages:
        next_url = f"/artikel/page/{current_page + 1}/"
        items.append(
            f'<a href="{next_url}" class="rounded-xl border px-3.5 py-2 text-xs sm:text-sm font-semibold transition-colors hover:border-electric hover:text-electric" '
            f'style="border-color:var(--border);background-color:var(--surface);color:var(--heading)">Selanjutnya &rarr;</a>'
        )
    else:
        items.append(
            f'<span class="rounded-xl border px-3.5 py-2 text-xs sm:text-sm font-semibold opacity-40 cursor-not-allowed" '
            f'style="border-color:var(--border);background-color:var(--surface);color:var(--soft)">Selanjutnya &rarr;</span>'
        )

    return (
        f'<div class="mt-12 flex flex-wrap items-center justify-center gap-2">'
        + "".join(items)
        + "</div>"
    )


def render_index(articles, current_page=1, total_pages=1):
    """Halaman /artikel/ -- daftar artikel dengan pagination (12 per halaman)."""
    sorted_articles = sorted(articles, key=lambda x: (x["date"], x["slug"]), reverse=True)
    start_idx = (current_page - 1) * PAGE_SIZE
    if current_page == total_pages:
        end_idx = len(sorted_articles)
    else:
        end_idx = start_idx + PAGE_SIZE
    page_articles = sorted_articles[start_idx:end_idx]

    kartu = []
    for a in page_articles:
        kartu.append(
            f'<a href="/artikel/{a["slug"]}/" class="group flex flex-col overflow-hidden rounded-2xl border transition-colors" '
            f'style="border-color:var(--border);background-color:var(--surface)">'
            + kartu_gambar(a["slug"], a["title"]) +
            f'<div class="flex flex-1 flex-col p-5">'
            f'<div class="flex items-center gap-2 text-[12px] t-soft">'
            f'<span class="pill-badge bg-electric/10 text-electric">{html.escape(a["tag"])}</span>'
            f'<span>{tanggal_id(a["date"])}</span></div>'
            f'<h3 class="mt-3 text-lg font-bold leading-snug t-heading group-hover:text-electric transition-colors">'
            f'{html.escape(a["title"])}</h3>'
            f'<p class="mt-2 flex-1 text-sm t-body">{html.escape(a["description"])}</p>'
            f'<div class="mt-4 flex items-center gap-1.5 text-xs font-semibold text-electric">Baca &rarr;</div>'
            f"</div></a>"
        )

    pagination_html = render_pagination(current_page, total_pages)
    hal_text = f" (Halaman {current_page})" if current_page > 1 else ""
    breadcrumb_last = f"Artikel Hal. {current_page}" if current_page > 1 else "Artikel"

    body = f"""    <div class="container-clean">
      <nav class="flex items-center gap-2 text-[12px] t-soft" aria-label="Breadcrumb">
        <a href="/" class="transition-colors hover:text-electric">Beranda</a>
        <span>/</span>
        <span class="t-heading">{breadcrumb_last}</span>
      </nav>
      <h1 class="teks-judul mt-5">Artikel &amp; Wawasan{hal_text}</h1>
      <p class="mt-4 max-w-2xl text-sm t-body sm:text-base">
        Hitungan biaya, perbandingan material, dan hal yang sering terlewat sebelum
        memesan paving, batako, atau gapura Majapahit. Menampilkan {len(page_articles)} dari total {len(articles)} artikel.
      </p>
    </div>

    <div class="container-clean mt-10">
      <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
{chr(10).join(kartu) if kartu else '        <p class="t-soft">Belum ada artikel.</p>'}
      </div>
      {pagination_html}
    </div>"""

    page_canonical = f"{BASE}/artikel/" if current_page == 1 else f"{BASE}/artikel/page/{current_page}/"
    ld_extra = {
        "@type": "CollectionPage",
        "name": f"Artikel & Wawasan FirKaizen{hal_text}",
        "url": page_canonical,
        "inLanguage": "id-ID"
    }
    breadcrumb = [("Beranda", BASE + "/")]
    if current_page == 1:
        breadcrumb.append(("Artikel", f"{BASE}/artikel/"))
    else:
        breadcrumb.append(("Artikel", f"{BASE}/artikel/"))
        breadcrumb.append((f"Halaman {current_page}", page_canonical))

    ada_gapura = any(str(a.get("tag", "")).strip().lower() == "gapura" for a in articles)
    w_index = ({"label": "Ponorogo & Solo Raya",
                "area": ["Pulau Jawa", "Jawa Tengah", "Jawa Timur"],
                "ringkas": "seluruh Pulau Jawa dan Solo Raya"}
               if ada_gapura else DEFAULT_WILAYAH)

    return page_shell(
        title=f"Artikel & Wawasan Material Konstruksi{hal_text}",
        desc=(f"Panduan dan hitungan biaya paving block, batako, bata ringan, dan gapura "
              f"Majapahit dari FirKaizen.{hal_text}"),
        slug="artikel" if current_page == 1 else f"artikel-page-{current_page}",
        body=body, ld_extra=ld_extra, breadcrumb=breadcrumb,
        canonical=page_canonical, og_image=f"{BASE}/images/og/default.webp",
        wilayah=w_index,
    )


def main():
    files = sorted(glob.glob(os.path.join(SRC, "*.md")))
    if not files:
        raise SystemExit(f"tidak ada .md di {SRC}")

    # Dua lintasan: ringkasan semua artikel dibaca dulu supaya navigasi dan "artikel
    # terkait" bisa disusun tanpa membaca ulang berkas.
    semua = []
    for f in files:
        meta, body_md = parse_front(open(f, encoding="utf-8").read())
        semua.append({
            "slug": meta["slug"], "title": meta["title"],
            "description": meta.get("description", ""), "date": meta.get("date", TODAY),
            "tag": meta.get("tag", "Artikel"),
            "read_min": max(1, round(len(body_md.split()) / 220)),
            "path": f,
        })

    os.makedirs(OUT, exist_ok=True)
    for a in semua:
        slug, html_out, _ = render_article(a["path"], semua)
        d = os.path.join(OUT, slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(html_out)
        print(f"  artikel/{slug}/index.html  ({len(html_out)//1024} KB)")

    total_pages = max(1, len(semua) // PAGE_SIZE)
    if (len(semua) % PAGE_SIZE) > 3:
        total_pages += 1
    # Page 1
    konten_hal1 = render_index(semua, current_page=1, total_pages=total_pages)
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(konten_hal1)
    print(f"  artikel/index.html  (Halaman 1/{total_pages}, {len(semua)} artikel)")

    # Page 2..N
    for p in range(2, total_pages + 1):
        p_dir = os.path.join(OUT, "page", str(p))
        os.makedirs(p_dir, exist_ok=True)
        konten_hal_p = render_index(semua, current_page=p, total_pages=total_pages)
        with open(os.path.join(p_dir, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(konten_hal_p)
        print(f"  artikel/page/{p}/index.html  (Halaman {p}/{total_pages})")


if __name__ == "__main__":
    main()