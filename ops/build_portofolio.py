#!/usr/bin/env python3
"""Bangun stok portofolio gapura dari SEMUA sumber foto mitra -> webp siap pasang.

Sumber:
  1. ~/.hermes/cache/scratch/gapura_id/new_raw/    (unduhan folder "FOTO GAPURA NEW")
  2. ~/.hermes/cache/scratch/gapura_id/bysize/*/    (unduhan folder "GAPURA <ukuran>")

Keluaran: images/gapura/galeri-<ukuran>m-<urut>.webp  (maks 1600px, q82)
Duplikat dibuang lewat perceptual hash (foto sama dari dua folder = sekali saja).

Jalankan: python3 ops/build_portofolio.py
"""
import pathlib, re, shutil
from PIL import Image

repo = pathlib.Path(__file__).resolve().parent.parent
out  = repo / 'images' / 'gapura'
src1 = pathlib.Path.home() / '.hermes/cache/scratch/gapura_id/new_raw'
src2 = pathlib.Path.home() / '.hermes/cache/scratch/gapura_id/bysize'

def ukuran_dari_nama(nama):
    """Ambil tinggi gapura (meter) dari nama berkas. None kalau tak dikenali."""
    n = nama.lower()
    m = re.match(r'^(\d)\.?(\d?)m-', n)          # 2.5m-xxx / 25m-xxx / 3m-xxx
    if m:
        return f"{m.group(1)}.{m.group(2)}" if m.group(2) else m.group(1)
    for folder, val in (('2.5m', '2.5'), ('3m', '3'), ('4m', '4'), ('5m', '5'), ('6m', '6')):
        if n.startswith(folder + '-') or n.startswith('galeri-' + folder + '-'):
            return val
    return None

def ahash(p):
    im = Image.open(p).convert('L').resize((8, 8), Image.LANCZOS)
    px = list(im.getdata()); avg = sum(px) / len(px)
    return sum(1 << i for i, v in enumerate(px) if v > avg)

IMG_EXT = ('.png', '.jpg', '.jpeg', '.webp')

def kebaca_gambar(p):
    """Berkas unduhan Drive sering TANPA ekstensi -- jangan andalkan suffix."""
    try:
        Image.open(p).verify()
        return True
    except Exception:
        return False

# --- kumpulkan kandidat (abaikan berkas uji & bukan gambar) ---
kandidat = []
for f in sorted(src1.iterdir()) if src1.exists() else []:
    if f.is_file() and not f.name.startswith('test_') and kebaca_gambar(f):
        kandidat.append((ukuran_dari_nama(f.name), f))
for f in sorted(src2.rglob('*')) if src2.exists() else []:
    if f.is_file() and f.suffix.lower() in IMG_EXT and not f.name.startswith('test_'):
        kandidat.append((ukuran_dari_nama(f.parent.name + '-'), f))

segar = [(u, f) for u, f in kandidat if u]
print(f"kandidat: {len(kandidat)}  |  ukuran terbaca: {len(segar)}")

# --- buang duplikat (perceptual hash) ---
hash_ada, unik = [], []
for u, f in segar:
    try:
        h = ahash(f)
    except Exception:
        continue
    if any(bin(h ^ x).count('1') <= 5 for x in hash_ada):
        continue
    hash_ada.append(h); unik.append((u, f))
print(f"setelah buang duplikat: {len(unik)}")

# --- konversi, urut per ukuran ---
for f in out.glob('galeri-*.webp'):
    f.unlink()
# thumb/ TIDAK disentuh di sini -- pembuatnya rebuild_galeri.py. Menghapusnya di
# sini meninggalkan grid tanpa thumbnail sampai rebuild_galeri dijalankan.

urut = {'2.5': 0, '3': 1, '4': 2, '5': 3, '6': 4}
unik.sort(key=lambda x: (urut.get(x[0], 9), str(x[1])))
hitung = {}
for u, f in unik:
    hitung[u] = hitung.get(u, 0) + 1
    dst = out / f"galeri-{u}m-{hitung[u]:03d}.webp"
    im = Image.open(f).convert('RGB')
    w, h = im.size
    if max(w, h) > 1600:
        s = 1600 / max(w, h)
        im = im.resize((max(1, round(w*s)), max(1, round(h*s))), Image.LANCZOS)
    im.save(dst, 'WEBP', quality=82, method=6)

tot = sum(hitung.values())
print(f"\nSELESAI: {tot} foto webp")
for k in ('2.5', '3', '4', '5', '6'):
    print(f"  {k} m: {hitung.get(k, 0)}")
print(f"  ukuran folder: {sum(f.stat().st_size for f in out.glob('galeri-*.webp'))//1024//1024} MB")

# --- bersihkan sisa pola nama lama yang masih dirujuk HTML ---
# Nama galeri pernah berbentuk 'galeri-2-5m-f1.webp'; sisa berkas dari pola lama
# tetap tertinggal di folder dan ikut ter-deploy tanpa dirujuk siapa pun.
html_txt = "\n".join(p.read_text(encoding='utf-8') for p in repo.rglob('*.html')
                     if '.backup' not in str(p) and '_arsip' not in str(p))
sisa = [f for f in out.glob('galeri-*.webp') if f.name not in html_txt]
for f in sisa:
    f.unlink()
    t = out / 'thumb' / f.name
    if t.exists():
        t.unlink()
print(f"  sisa pola lama dibuang: {len(sisa)}")
for f in sisa:
    print(f"    {f.name}")