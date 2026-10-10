#!/usr/bin/env python3
"""Bikin 4 OG image 1200x630 untuk firkaizen.id (hub, paving, batako, gapura).

Latar: foto proyek yang relevan (cover-crop) + panel gelap transparan + teks.
Teks dirender lokal pakai DejaVu (bukan webfont) supaya deterministik.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.expanduser("~/.hermes/cache/scratch/fk-static-repo")
OUT = os.path.join(ROOT, "images", "og")
os.makedirs(OUT, exist_ok=True)

W, H = 1200, 630
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

CARDS = [
    dict(slug="default", src="images/paving/pabrik_yard.webp",
         eyebrow="PT FIRKAIZEN DIGITAL SOLUTIONS",
         head="Material & Konstruksi",
         sub="Paving block · Batako & bata ringan · Gapura Majapahit"),
    dict(slug="paving", src="images/paving/proyek_pasang.webp",
         eyebrow="FIRKAIZEN PAVING BLOCK",
         head="Paving Block K-300",
         sub="Produsen & jasa pasang borongan · Solo Raya"),
    dict(slug="batako", src="images/batako/img_9.webp",
         eyebrow="FIRKAIZEN BATA RINGAN & BATAKO",
         head="Bata Ringan & Batako",
         sub="Material kubikan & paket borongan pasang"),
    dict(slug="gapura", src="images/gapura/hero-gapura-majapahit.webp",
         eyebrow="FIRKAIZEN GAPURA MAJAPAHIT",
         head="Gapura Bata Expose",
         sub="Ukiran relief klasik · 2,5m s/d 6m · Custom"),
]


def cover(im, w, h):
    """Crop-tengah ke rasio target lalu resize."""
    tr = w / h
    sr = im.width / im.height
    if sr > tr:
        nw = int(im.height * tr)
        im = im.crop(((im.width - nw) // 2, 0, (im.width - nw) // 2 + nw, im.height))
    else:
        nh = int(im.width / tr)
        im = im.crop((0, (im.height - nh) // 2, im.width, (im.height - nh) // 2 + nh))
    return im.resize((w, h), Image.LANCZOS)


def scrim(w, h):  # overlay gelap: bawah penuh, kiri tambahan
    """Gradasi gelap dari bawah + sedikit dari kiri, biar teks kebaca."""
    g = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(g)
    for y in range(h):
        # makin ke bawah makin gelap
        d.line([(0, y), (w, y)], fill=int(min(242, 120 + 135 * (y / h) ** 1.15)))
    g2 = Image.new("L", (w, h), 0)
    d2 = ImageDraw.Draw(g2)
    for x in range(w):
        d2.line([(x, 0), (x, h)], fill=int(150 * max(0.0, 1 - x / (w * 0.78))))
    return Image.blend(g, g2, 0.5)


def build(card):
    src = os.path.join(ROOT, card["src"])
    im = Image.open(src).convert("RGB")
    im = cover(im, W, H).filter(ImageFilter.GaussianBlur(0.4))
    overlay = Image.new("RGB", (W, H), (8, 12, 22))
    im = Image.composite(overlay, im, scrim(W, H)).convert("RGB")
    d = ImageDraw.Draw(im)

    f_eye = ImageFont.truetype(BOLD, 24)
    f_head = ImageFont.truetype(BOLD, 72)
    f_sub = ImageFont.truetype(REG, 33)
    f_url = ImageFont.truetype(BOLD, 28)

    pad = 74
    y_eye = 210

    # Panel gelap di belakang teks -> kontras dijamin, tidak tergantung kecerahan foto.
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle(
        [pad - 34, y_eye - 34, W - pad + 20, H - 54],
        radius=18, fill=(8, 12, 22, 205),
    )
    im = Image.alpha_composite(im.convert("RGBA"), panel).convert("RGB")
    d = ImageDraw.Draw(im)

    def txt(xy, text, font, fill):
        """Teks + shadow tipis biar tetap kebaca kalau panel ditimpa apa pun."""
        d.text((xy[0] + 2, xy[1] + 2), text, font=font, fill=(0, 0, 0))
        d.text(xy, text, font=font, fill=fill)

    txt((pad, y_eye), card["eyebrow"], f_eye, (125, 211, 252))
    d.rectangle([pad, y_eye + 36, pad + 56, y_eye + 40], fill=(37, 99, 235))
    d.rectangle([pad + 56, y_eye + 36, pad + 96, y_eye + 40], fill=(6, 182, 212))
    y_head = y_eye + 62
    txt((pad, y_head), card["head"], f_head, (255, 255, 255))
    y_sub = y_head + 96
    txt((pad, y_sub), card["sub"], f_sub, (203, 213, 225))
    txt((pad, H - 92), "firkaizen.id", f_url, (255, 255, 255))

    # garis aksen biru-cyan
    d.rectangle([pad, H - 124, pad + 104, H - 118], fill=(37, 99, 235))
    d.rectangle([pad + 104, H - 124, pad + 168, H - 118], fill=(6, 182, 212))

    p = os.path.join(OUT, f"{card['slug']}.webp")
    im.save(p, "WEBP", quality=86, method=6)
    print(f"  {card['slug']:<8} {im.size} {os.path.getsize(p)//1024} KB  <- {card['src']}")


if __name__ == "__main__":
    for c in CARDS:
        build(c)
