#!/usr/bin/env python3
"""Generate sitemap.xml firkaizen.id dari folder yang punya index.html.

Dijalankan ulang setiap kali halaman ditambah. Otomatis mengecualikan:
  - halaman privat (admin/, api/, links/)
  - halaman noindex
"""
import os, re, datetime, glob

ROOT = os.path.expanduser("~/.hermes/cache/scratch/fk-static-repo")
BASE = "https://firkaizen.id"
EXCLUDE = {"admin", "api", "links", ".git", "ops", "images", "fonts"}

# prioritas per halaman
PRIO = {"/": "1.0", "/paving/": "0.9", "/batako/": "0.9", "/gapura/": "0.9", "/porto/": "0.7"}
FREQ = {"/": "weekly", "/paving/": "weekly", "/batako/": "weekly", "/gapura/": "weekly", "/porto/": "monthly"}


def pages():
    out = []
    for f in glob.glob(os.path.join(ROOT, "**", "index.html"), recursive=True):
        rel = os.path.relpath(f, ROOT)
        parts = rel.split(os.sep)
        if any(p in EXCLUDE or p.startswith(".") for p in parts[:-1]):
            continue
        s = open(f, encoding="utf-8", errors="ignore").read()
        if re.search(r'name="robots"[^>]+content="[^"]*noindex', s, re.I):
            continue
        loc = "/" if len(parts) == 1 else "/" + "/".join(parts[:-1]) + "/"
        out.append(loc)
    return sorted(set(out), key=lambda p: (p != "/", p))


if __name__ == "__main__":
    today = datetime.date.today().isoformat()
    urls = pages()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc in urls:
        lines += [
            "  <url>",
            f"    <loc>{BASE}{loc}</loc>",
            f"    <lastmod>{today}</lastmod>",
            f"    <changefreq>{FREQ.get(loc, 'monthly')}</changefreq>",
            f"    <priority>{PRIO.get(loc, '0.6')}</priority>",
            "  </url>",
        ]
    lines.append("</urlset>")
    p = os.path.join(ROOT, "sitemap.xml")
    open(p, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"sitemap.xml: {len(urls)} URL")
    for u in urls:
        print(f"  {u}")