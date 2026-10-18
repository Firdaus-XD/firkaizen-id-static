#!/usr/bin/env python3
"""Sisipkan node FAQPage ke JSON-LD halaman statis, diambil dari markup halaman itu sendiri.

Q&A dibaca dari `<details><summary>pertanyaan</summary><p>jawaban</p></details>`,
bukan dikarang — isi structured data wajib sama dengan yang terlihat pembaca.

Idempoten: node FAQPage lama dibuang dulu, jadi aman dijalankan berulang.

Pakai: python3 ops/tambah-faq-schema.py <berkas.html> [berkas2.html ...]
"""
import html as htmllib
import json
import os
import re
import shutil
import sys
import time

FAQSEL = re.compile(
    r"<details\b[^>]*>\s*<summary\b[^>]*>(.*?)</summary>\s*<p\b[^>]*>(.*?)</p>", re.S
)
LD = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)


def bersih(t):
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", htmllib.unescape(t)).strip()


def main():
    for path in sys.argv[1:]:
        if not os.path.isfile(path):
            print(f"  SKIP  {path}: tidak ada")
            continue
        s = open(path, encoding="utf-8").read()
        faqs = [(bersih(q), bersih(a)) for q, a in FAQSEL.findall(s)]
        if not faqs:
            print(f"  SKIP  {path}: tidak ada pola <details><summary>")
            continue
        m = LD.search(s)
        if not m:
            print(f"  SKIP  {path}: tidak ada blok JSON-LD")
            continue
        try:
            data = json.loads(m.group(2))
        except json.JSONDecodeError as e:
            print(f"  GAGAL {path}: JSON-LD tidak valid ({e})")
            continue

        graph = data.setdefault("@graph", [])
        sebelum = [n.get("@type") for n in graph]
        graph[:] = [n for n in graph if n.get("@type") != "FAQPage"]
        graph.append(
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a},
                    }
                    for q, a in faqs
                ],
            }
        )
        body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        s = s[: m.start()] + m.group(1) + body + m.group(3) + s[m.end():]

        shutil.copy2(path, path + ".bak-faq-" + time.strftime("%Y%m%d-%H%M%S"))
        with open(path, "w", encoding="utf-8") as f:
            f.write(s)

        print(f"  OK    {os.path.basename(path)}: {len(faqs)} Q&A")
        print(f"          @type sebelum: {sebelum}")
        print(f"          @type sesudah: {[n.get('@type') for n in graph]}")
        for q, _ in faqs:
            print(f"          Q: {q[:74]}")


if __name__ == "__main__":
    main()