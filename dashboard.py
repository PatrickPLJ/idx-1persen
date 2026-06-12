#!/usr/bin/env python3
"""
Dashboard lokal loop "Cek 1% Kepemilikan Saham IDX".

Jalankan:  python3 dashboard.py   →  http://localhost:8126

Server read-only (stdlib saja, tanpa dependensi): hanya membaca file di
folder ini dan menyajikannya ke dashboard.html. Tidak mengubah apa pun.
"""
import datetime
import json
import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

BASE = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", 8126))

STATE_FILE = BASE / "1% kepemilikan saham.json"
SCHEDULE_FILE = BASE / "schedule.json"   # dibuat saat cron diaktifkan
SAFE_NAME = re.compile(r"^[\w\-. %]+$")


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def list_md(folder):
    out = []
    for p in sorted(folder.glob("*.md"), reverse=True):
        out.append({"name": p.name, "mtime": p.stat().st_mtime})
    return out


def overview():
    logs = []
    logs_file = BASE / "logs.txt"
    if logs_file.exists():
        logs = [l for l in logs_file.read_text().splitlines() if l.strip()]
    rejected = []
    rej_dir = BASE / "rejected"
    for p in sorted(rej_dir.glob("*.md"), reverse=True):
        alasan_file = rej_dir / (p.stem + "-alasan.txt")
        rejected.append({
            "name": p.name,
            "alasan": alasan_file.read_text().strip() if alasan_file.exists() else None,
        })
    return {
        "state": read_json(STATE_FILE),
        "schedule": read_json(SCHEDULE_FILE),
        "keputusan": read_json(BASE / "keputusan.json") or {},
        "logs": logs[-30:],
        "facts": sorted((p.name for p in (BASE / "facts").glob("facts-*.json")),
                        reverse=True),
        "drafts": list_md(BASE / "output"),
        "rejected": rejected,
    }


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(
            body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def safe_file(self, folder, name, suffix):
        if not SAFE_NAME.match(name) or not name.endswith(suffix):
            return None
        path = (BASE / folder / name).resolve()
        if path.parent != (BASE / folder).resolve() or not path.exists():
            return None
        return path

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            html = (BASE / "dashboard.html").read_bytes()
            self.send(200, html, "text/html; charset=utf-8")
        elif path == "/api/overview":
            self.send(200, overview())
        elif path.startswith("/api/facts/"):
            f = self.safe_file("facts", path.rsplit("/", 1)[1], ".json")
            self.send(200, read_json(f)) if f else self.send(404, {"error": "tidak ada"})
        elif path.startswith("/api/draft/"):
            f = self.safe_file("output", path.rsplit("/", 1)[1], ".md")
            if f:
                self.send(200, {"name": f.name, "markdown": f.read_text()})
            else:
                self.send(404, {"error": "tidak ada"})
        elif path.startswith("/api/rejected/"):
            f = self.safe_file("rejected", path.rsplit("/", 1)[1], ".md")
            if f:
                self.send(200, {"name": f.name, "markdown": f.read_text()})
            else:
                self.send(404, {"error": "tidak ada"})
        else:
            self.send(404, {"error": "tidak ada"})

    def do_POST(self):
        # Satu-satunya tulisan dashboard: catatan keputusan Patrick di
        # keputusan.json milik dashboard sendiri — state pipeline tak disentuh.
        if self.path.split("?")[0] != "/api/keputusan":
            return self.send(404, {"error": "tidak ada"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n))
            draft = body["draft"]
            putusan = body["keputusan"]
            assert SAFE_NAME.match(draft) and draft.endswith(".md")
            assert putusan in ("disetujui", "ditolak")
        except Exception:
            return self.send(400, {"error": "permintaan tidak valid"})
        kfile = BASE / "keputusan.json"
        semua = read_json(kfile) or {}
        semua[draft] = {
            "keputusan": putusan,
            "alasan": (body.get("alasan") or "").strip() or None,
            "tanggal": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        kfile.write_text(json.dumps(semua, indent=2, ensure_ascii=False))
        self.send(200, {"ok": True})

    def log_message(self, *args):
        pass  # jangan berisik di terminal


if __name__ == "__main__":
    print(f"Dashboard IDX 1% → http://localhost:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
