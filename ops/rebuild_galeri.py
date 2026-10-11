#!/usr/bin/env python3
"""Bangun ulang bagian GALERI di gapura/index.html dari STOK FOTO YANG ADA.

Sumber: images/gapura/galeri-*.webp  (dari folder Drive mitra; nama berkas
menyimpan tinggi gapura).  Thumbnail 640px dibuat di images/gapura/thumb/,
versi penuh tetap dipakai lightbox.

Dijalankan ulang setiap kali stok foto bertambah:
    python3 ops/rebuild_galeri.py
"""
import pathlib, re, sys
from PIL import Image

repo = pathlib.Path(__file__).resolve().parent.parent
img  = repo / 'images' / 'gapura'
thum = img / 'thumb'
html = repo / 'gapura' / 'index.html'
thum.mkdir(exist_ok=True)

# 'galeri-2-5m-...' -> '2.5'   'galeri-4m-...' -> '4'
def tinggi(nama):
    """'galeri-2.5m-001' -> '2.5'   'galeri-4m-007' -> '4'."""
    m = re.match(r'galeri-(\d)(?:[.-](\d))?m', nama)
    if not m:
        return None
    return f"{m.group(1)}.{m.group(2)}" if m.group(2) else m.group(1)

kartu = []
for f in sorted(img.glob('galeri-*.webp')):
    t = tinggi(f.stem)
    if t is None:
        continue
    # thumbnail untuk grid
    th = thum / f.name
    if not th.exists():
        im = Image.open(f).convert('RGB')
        w, h = im.size
        s = 640 / max(w, h)
        if s < 1:
            im = im.resize((max(1, round(w*s)), max(1, round(h*s))), Image.LANCZOS)
        im.save(th, 'WEBP', quality=76, method=5)
    else:
        im = Image.open(th)
    w, h = im.size
    kartu.append({'src': f.name, 't': t, 'w': w, 'h': h, 'port': h > w})

urut = {'2.5': 0, '3': 1, '4': 2, '5': 3, '6': 4}
kartu.sort(key=lambda k: (urut.get(k['t'], 9), not k['port'], k['src']))

def kartu_html(k):
    label = f"Gapura bata expose tinggi {k['t']} m"
    ori   = 'P' if k['port'] else 'L'
    return f"""        <figure class="gal-card" data-size="{k['t']}" data-ori="{ori}">
          <button type="button" class="gal-btn" data-src="/images/gapura/{k['src']}" data-cap="{label}">
            <img src="/images/gapura/thumb/{k['src']}" alt="{label}" loading="lazy" decoding="async" width="{k['w']}" height="{k['h']}"/>
            <span class="gal-badge">{k['t']} m</span>
          </button>
        </figure>"""

chips = [('semua', 'Semua', len(kartu))] + [
    (t, f'{t} m', sum(1 for k in kartu if k['t'] == t))
    for t in ('2.5', '3', '4', '5', '6') if any(k['t'] == t for k in kartu)
]
chip_html = "\n".join(
    f'<button type="button" class="gal-chip{" is-on" if v == "semua" else ""}" data-filter="{v}">{lbl} <span class="gal-n">{n}</span></button>'
    for v, lbl, n in chips
)

seksi = f"""<!-- ================= GALERI ================= -->
    <section id="galeri" class="container-clean space-y-6 scroll-mt-20">
      <div class="text-center max-w-2xl mx-auto space-y-1.5">
        <span class="text-xs font-extrabold text-electric uppercase tracking-wider">DOKUMENTASI TIM MITRA</span>
        <h2 class="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white">Portofolio Pengerjaan Gapura</h2>
        <p class="text-xs sm:text-sm text-slate-500">Foto asli dari lokasi proyek, dikerjakan tim mitra pengrajin bata expose di Ponorogo. Klik foto untuk melihat versi besar.</p>
      </div>

      <div class="flex flex-wrap justify-center gap-2">
{chip_html}
      </div>

      <div id="galGrid" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
{chr(10).join(kartu_html(k) for k in kartu)}
      </div>

      <div class="card-clean p-4 sm:p-5 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="text-center sm:text-left">
          <div class="text-sm font-extrabold text-slate-900 dark:text-white">Mau lihat foto ukuran tertentu lebih banyak?</div>
          <p class="text-xs text-slate-500">Sebutkan tinggi dan model yang Anda rencanakan, kami kirimkan dokumentasi yang paling mendekati.</p>
        </div>
        <a href="https://wa.me/6285196135691?text=Halo%20FirKaizen%20Gapura,%20saya%20ingin%20melihat%20dokumentasi%20gapura%20tinggi%20tertentu" target="_blank" rel="noopener" class="btn-outline py-2.5 px-4 text-xs shrink-0">Minta Foto Tambahan</a>
      </div>

      <div id="galBox" role="dialog" aria-modal="true" aria-label="Foto portofolio gapura">
        <button type="button" class="gal-x" aria-label="Tutup">&times;</button>
        <button type="button" class="gal-nav gal-prev" aria-label="Foto sebelumnya">&#8249;</button>
        <img id="galImg" src="" alt="Foto portofolio gapura" width="1600" height="1200"/>
        <button type="button" class="gal-nav gal-next" aria-label="Foto berikutnya">&#8250;</button>
        <div class="gal-cap" id="galCap"></div>
      </div>
    </section>"""

s = html.read_text(encoding='utf-8')
a = s.index('<!-- ================= GALERI ================= -->')
b = s.index('<!-- ================= ALUR PENGERJAAN ================= -->')
html.write_text(s[:a] + seksi + "\n\n    " + s[b:], encoding='utf-8')
print(f"GALERI dibangun: {len(kartu)} foto, {len(chips)-1} ukuran")
for t in ('2.5', '3', '4', '5', '6'):
    n = sum(1 for k in kartu if k['t'] == t)
    print(f"  {t} m: {n}")
print(f"  thumbnail: {len(list(thum.glob('*.webp')))}")
print(f"  ukuran index.html: {html.stat().st_size} byte")