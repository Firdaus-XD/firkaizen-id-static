#!/usr/bin/env python3
"""Periksa semua artikel firkaizen.id terhadap aturan skill artikel-promosi-firkaizen.

Dipakai setelah make-artikel.py, SEBELUM deploy. Keluar dengan kode !=0 kalau ada
pelanggaran, supaya bisa dipasang di alur otomatis.

    python3 ops/check-artikel.py
"""
import re, sys, glob, os, html, json

ROOT = os.path.expanduser("~/.hermes/cache/scratch/fk-static-repo")
SRC = os.path.join(ROOT, "content", "artikel")
OUT = os.path.join(ROOT, "artikel")

# angka yang boleh muncul: dibaca dari referensi harga (semua digit panjang di sana)
REF = os.path.expanduser(
    "~/.hermes/skills/software-development/artikel-promosi-firkaizen/"
    "references/harga-dan-fakta.md")

BATAS_JUDUL, BATAS_DESC = 60, 160
KATA_MIN, KATA_MAKS = 600, 1200

GAGAL = []


def gagal(f, pesan):
    GAGAL.append(f"{os.path.basename(f)}: {pesan}")


def front(t):
    m = re.match(r"\s*---\s*\n(.*?)\n---\s*\n(.*)$", t, re.S)
    if not m:
        return None, None
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip("'\"")
    return meta, m.group(2)


def main():
    files = sorted(glob.glob(os.path.join(SRC, "*.md")))
    if not files:
        sys.exit("GAGAL: tidak ada .md")

    ref = open(REF, encoding="utf-8").read() if os.path.exists(REF) else ""
    # harga rupiah yang sah, HANYA dari referensi. "Rp 33 juta" tidak ada di sana
    # -> langsung ketahuan sebelum deploy. Dua bentuk: "Rp 30 juta" dan "Rp 65.000 /m2".
    harga_sah = set()
    for n, sat in re.findall(r"Rp\s*([\d][\d.,]*)\s*(juta|miliar)?", ref):
        n = n.rstrip(".,")
        harga_sah.add(f"{n} {sat}" if sat else n)

    print(f"Memeriksa {len(files)} artikel\n" + "-" * 62)
    for f in files:
        t = open(f, encoding="utf-8").read()
        meta, body = front(t)
        if not meta or body is None:
            gagal(f, "frontmatter '---' tidak ditemukan")
            continue
        body = body or ""

        for k in ("slug", "title", "description", "date", "tag", "og_image"):
            if k not in meta:
                gagal(f, f"frontmatter kehilangan '{k}'")

        nama = os.path.basename(f)[:-3]
        if meta.get("slug") != nama:
            gagal(f, f"slug '{meta.get('slug')}' != nama berkas '{nama}'")

        tl, dl = len(meta.get("title", "")), len(meta.get("description", ""))
        if tl > BATAS_JUDUL:
            gagal(f, f"judul {tl} char > {BATAS_JUDUL}")
        if not (130 <= dl <= BATAS_DESC):
            gagal(f, f"deskripsi {dl} char (harus 130-{BATAS_DESC})")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", meta.get("date", "")):
            gagal(f, f"date '{meta.get('date')}' bukan YYYY-MM-DD")

        kata = len(body.split())
        if not (KATA_MIN <= kata <= KATA_MAKS):
            gagal(f, f"{kata} kata di luar {KATA_MIN}-{KATA_MAKS}")

        if re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", t):
            gagal(f, "mengandung emoji")

        # tautan internal
        links = re.findall(r"\]\((/[^)]*)\)", body)
        if len(links) < 2:
            gagal(f, f"hanya {len(links)} tautan internal (minimal 2)")

        # pembuka bertele-tele
        pembuka = body.strip().split("\n\n")[0].lower()
        for frasa in ("di era modern", "tidak dapat dipungkiri", "seiring perkembangan",
                      "pada zaman", "dewasa ini"):
            if frasa in pembuka:
                gagal(f, f"pembuka bertele-tele: '{frasa}'")

        # badan hukum
        if "FirKaizen Solutions" in body and "PT FirKaizen Digital Solutions" not in body:
            gagal(f, "menulis 'FirKaizen Solutions' tanpa 'PT FirKaizen Digital Solutions'")

# Janji berlebihan
        for frasa in ("dijamin halaman 1", "pasti termurah", "nomor 1 di google"):
            if frasa in body.lower():
                gagal(f, f"klaim berlebihan: '{frasa}'")

        # Harga WAJIB sama dengan supplier. Tanpa ini, artikel bisa mengarang angka
        # apa saja dan checker tetap bilang lulus (angka_sah dulu dikumpulkan tapi
        # tidak pernah dipakai).
        for sumber, teks in (("badan artikel", body), ("deskripsi", meta.get("description", "")),
                             ("judul", meta.get("title", ""))):
            for m in re.finditer(r"Rp\s*([\d][\d.,]*)\s*(juta|miliar)?", teks):
                n = m.group(1).rstrip(".,")
                satuan = (m.group(2) or "").lower()
                if satuan:
                    kunci = f"{n} {satuan}"
                else:
                    kunci = n
                if kunci not in harga_sah:
                    gagal(f, f"{sumber}: harga '{m.group(0).strip()}' tidak ada di referensi")

        # klaim terlarang (belum ada sumbernya dari mitra)
        for frasa in ("garansi", "survei gratis", "survey gratis", "gratis survey",
                      "pengrajin kami", "tukang kami", "tim mandor kami",
                      "cakar ayam", "lung-lungan", "puluhan tahun", "bebas lumut",
                      "tidak mudah berlumut"):
            if frasa in body.lower():
                gagal(f, f"klaim tanpa sumber: '{frasa}'")

        # keluaran HTML ada?
        htmlf = os.path.join(OUT, meta.get("slug", nama), "index.html")
        if not os.path.exists(htmlf):
            gagal(f, "HTML belum dirakit (jalankan make-artikel.py)")
        else:
            h = open(htmlf, encoding="utf-8").read()
            if h.count("<title>") != 1:
                gagal(f, f"<title> muncul {h.count('<title>')}x (harus 1)")
            if '"@type": "Article"' not in h.replace(" ", ' ') and '"@type":"Article"' not in h:
                gagal(f, "JSON-LD Article tidak ada di HTML")
            if 'rel="canonical"' not in h:
                gagal(f, "canonical tidak ada di HTML")

        print(f"  {'OK ' if not GAGAL else '   '} {nama[:52]:<52} {tl:>3}/{dl:>3} char  {kata:>4} kata")

    # Gambar depan: setiap artikel harus punya gambar SENDIRI yang berkasnya sudah ada.
    # Tanpa pemeriksaan ini artikel baru tayang tanpa sampul dan kartunya jadi teks kosong
    # di antara kartu bergambar -- dan itu tidak terlihat sebagai kegagalan apa pun.
    # Pernah terjadi: HTML terkirim lebih dulu menunjuk gambar yang belum ada, 15 halaman
    # bergambar rusak.
    try:
        import json as _json
        _tp = os.path.join(ROOT, "ops", "thumb_pilih.json")
        peta_gambar = _json.load(open(_tp, encoding="utf-8")) if os.path.exists(_tp) else {}
    except Exception as e:
        peta_gambar = {}
        GAGAL.append(f"ops/thumb_pilih.json tidak terbaca: {e}")

    dipakai = {}
    for f in files:
        meta, _ = front(open(f, encoding="utf-8").read())
        s = (meta or {}).get("slug", "")
        src = peta_gambar.get(s)
        if not src:
            GAGAL.append(f"gambar depan: '{s}' belum punya entri di ops/thumb_pilih.json")
        elif not os.path.exists(os.path.join(ROOT, src)):
            GAGAL.append(f"gambar depan '{s}': berkas sumber tidak ada -> {src}")
        else:
            dipakai.setdefault(src, []).append(s)
        h = os.path.join(ROOT, "artikel", s, "index.html")
        if os.path.exists(h):
            if f"/images/thumb/{s}.webp" not in open(h, encoding="utf-8").read():
                GAGAL.append(f"gambar depan '{s}': HTML tidak menunjuk /images/thumb/{s}.webp")
            if not os.path.exists(os.path.join(ROOT, "images", "thumb", f"{s}.webp")):
                GAGAL.append(f"gambar depan '{s}': images/thumb/{s}.webp belum dibuat (jalankan build_thumb.py)")

    for src, slugs in dipakai.items():
        if len(slugs) > 1:
            GAGAL.append(f"gambar depan kembar, dipakai {len(slugs)} artikel -> {src} :: {', '.join(slugs)}")

    print(f"  gambar depan: {len(files)} artikel, {len(dipakai)} gambar unik")

    # sitemap memuat semua slug?
    sm = os.path.join(ROOT, "sitemap.xml")
    if os.path.exists(sm):
        x = open(sm, encoding="utf-8").read()
        for f in files:
            meta, _ = front(open(f, encoding="utf-8").read())
            s = (meta or {}).get("slug", "")
            if s and f"/artikel/{s}/" not in x:
                GAGAL.append(f"sitemap: /artikel/{s}/ belum terdaftar")
    else:
        GAGAL.append("sitemap.xml tidak ada (jalankan make-sitemap.py)")

    print("-" * 62)
    if GAGAL:
        print(f"GAGAL: {len(GAGAL)} masalah")
        for g in GAGAL:
            print("  x", g)
        return 1
    print(f"LULUS: {len(files)} artikel siap deploy")
    return 0


if __name__ == "__main__":
    sys.exit(main())