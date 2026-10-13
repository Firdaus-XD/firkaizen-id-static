#!/usr/bin/env python3
"""Pilih satu gambar depan per artikel + bikin versi ringan untuk kartu.

Kenapa perlu dipilih, bukan sekadar memakai og_image: og_image per kategori cuma ada
EMPAT (gapura/paving/batako/default), jadi kartu "artikel terkait" yang semua tag-nya sama
akan menampilkan gambar identik tiga kali -- terbaca seperti gambar rusak.

Pilihan disimpan di `ops/thumb_pilih.json` supaya:
  - bisa ditinjau dan ditukar tanpa menyentuh generator,
  - keputusannya tidak hilang saat generator dijalankan ulang,
  - kontraknya jelas: satu artikel satu gambar, berkasnya harus ada.

Versi ringan (lebar 640) ditulis ke images/thumb/<slug>.webp. Tanpa itu satu kartu
menarik gambar 60-107 KB; pada halaman dengan 3 kartu + 1 gambar badan jumlahnya membengkak
dan pemilih otomatis file bisa tertunda di HP.
"""
import json, os, sys

ROOT = os.path.expanduser("~/.hermes/cache/scratch/fk-static-repo")
PILIH = os.path.join(ROOT, "ops", "thumb_pilih.json")
THUMB = os.path.join(ROOT, "images", "thumb")
LEBAR = 640
MUTU = 82


def main():
    with open(PILIH, encoding="utf-8") as f:
        pilih = json.load(f)

    from PIL import Image, ImageOps

    os.makedirs(THUMB, exist_ok=True)
    hilang, dibuat = [], 0

    for slug, src in sorted(pilih.items()):
        asal = os.path.join(ROOT, src)
        if not os.path.exists(asal):
            hilang.append(f"{slug} -> {src}")
            continue
        tujuan = os.path.join(THUMB, f"{slug}.webp")
        # Lewati kalau sudah ada dan lebih baru dari sumbernya.
        if os.path.exists(tujuan) and os.path.getmtime(tujuan) >= os.path.getmtime(asal):
            continue
        with Image.open(asal) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            if im.width > LEBAR:
                im = im.resize((LEBAR, round(im.height * LEBAR / im.width)), Image.Resampling.LANCZOS)
            im.save(tujuan, "WEBP", quality=MUTU, method=6)
        dibuat += 1

    if hilang:
        print("GAGAL: gambar sumber tidak ada:", file=sys.stderr)
        for h in hilang:
            print("  " + h, file=sys.stderr)
        return 1

    ukuran = {f: os.path.getsize(os.path.join(THUMB, f)) for f in os.listdir(THUMB)}
    print(f"  thumbnail: {len(pilih)} artikel, {dibuat} dibuat ulang, "
          f"{len(ukuran)} berkas")
    semua = sorted(ukuran.values())
    if semua:
        print(f"  ukuran berkas: {semua[0]//1024}-{semua[-1]//1024} KB "
              f"(rata-rata {sum(semua)//len(semua)//1024} KB)")

    # Kontrak: satu berkas per artikel, tidak ada yang kembar.
    dari = {}
    for slug, src in pilih.items():
        dari.setdefault(src, []).append(slug)
    kembar = {k: v for k, v in dari.items() if len(v) > 1}
    if kembar:
        print(f"  PERINGATAN: {len(kembar)} gambar dipakai lebih dari satu artikel:")
        for k, v in sorted(kembar.items()):
            print(f"    {os.path.basename(k):30} {len(v)}x  {', '.join(s[:30] for s in v)}")
    else:
        print("  semua artikel pakai gambar berbeda")
    return 0


if __name__ == "__main__":
    sys.exit(main())