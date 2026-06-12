#!/usr/bin/env python3
"""
Buat snapshot statis dashboard untuk GitHub Pages → folder docs/.

Jalankan manual (atau lewat Claude) SETELAH ada perubahan yang mau
dipublikasikan, lalu commit + push. Sengaja TIDAK dipanggil otomatis oleh
loop cron — guardrail: loop tidak boleh mengirim apa pun ke publik sendiri.

    python3 publish_snapshot.py
    git add docs && git commit -m "snapshot" && git push
"""
import datetime
import json
import shutil

from dashboard import BASE, overview

DOCS = BASE / "docs"
DOCS.mkdir(exist_ok=True)

ov = overview()
snap = {
    "dibuat": datetime.datetime.now().strftime("%Y-%m-%d %H:%M WIB"),
    "overview": ov,
    "facts_isi": {n: json.loads((BASE / "facts" / n).read_text()) for n in ov["facts"]},
    "draft_isi": {d["name"]: (BASE / "output" / d["name"]).read_text() for d in ov["drafts"]},
    "rejected_isi": {r["name"]: (BASE / "rejected" / r["name"]).read_text() for r in ov["rejected"]},
}
(DOCS / "snapshot.json").write_text(json.dumps(snap, ensure_ascii=False))
shutil.copy(BASE / "dashboard.html", DOCS / "index.html")
print(f"OK — docs/ siap: index.html + snapshot.json ({snap['dibuat']})")
print(f"     {len(ov['facts'])} facts, {len(ov['drafts'])} draft, {len(ov['rejected'])} rejected")
