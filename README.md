# Loop "Cek 1% Kepemilikan Saham IDX"

Sistem otomatis untuk memantau data kepemilikan saham ≥1% yang dipublikasi IDX
tiap bulan di <https://www.idx.co.id/id/perusahaan-tercatat/data-kepemilikan-saham/>.

## Cara kerja

```
Tiap hari 08:00 WIB (cron, setelah di-approve)
        │
        ▼
fetch_idx.py check ──► tidak ada file baru? ──► selesai (catat log)
        │ ada file satu-persen baru
        ▼
unduh xlsx baru + bulan sebelumnya ──► hitung fakta (facts/*.json)
        ▼
MAKER (Claude) tulis draft laporan dari facts
        ▼
CHECKER (AI kedua, prompt auditor) verifikasi angka vs facts + xlsx mentah
        ▼
PASS → output/draft-*.md (DRAFT, tunggu approval Patrick)
FAIL → revisi 1x → masih FAIL → rejected/ + alasan (tidak dideliver)
```

## File & folder

| Path | Isi |
|---|---|
| `fetch_idx.py` | Mesin fetch + diff + hitung fakta (Python, gratis, lokal) |
| `1% kepemilikan saham.json` | **State/memory** — pengumuman yang sudah diproses, tidak diproses 2x |
| `CRON_PROMPT.md` | Runbook agent terjadwal (maker/checker + guardrails) |
| `data/` | Cache xlsx hasil unduhan IDX |
| `facts/` | Fakta terhitung per periode (sumber kebenaran draft) |
| `output/` | Draft laporan yang LOLOS checker (max 1/hari) |
| `rejected/` | Draft gagal checker + alasannya |
| `logs.txt` | Catatan tiap run |

## Guardrails

- Maksimal **1 output per hari** (dijaga di script via `last_output_date`).
- Tidak pernah kirim ke publik, tidak keluar uang, tidak hapus data.
- Semua hasil hanya **DRAFT lokal** menunggu approval Patrick.
- Draft yang gagal checker 2x dibuang ke `rejected/` + alasan, tidak dideliver.

## Dashboard "Meja 1%"

Dashboard lokal untuk cek cepat tiap hari + approve/tolak draft:

```bash
cd "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Claude Code/idx-1persen"
python3 dashboard.py        # → buka http://localhost:8126
```

- **Kabar pagi**: verdict 5 detik (beres / perlu perhatian / belum aktif) + 4 kartu metrik.
- **Antrian Keputusan**: draft yang menunggu → "Baca & Putuskan" → Setujui/Tolak.
  Keputusan dicatat di `keputusan.json` (file milik dashboard, state pipeline tak disentuh).
- **Denyut Sistem**: tahap pipeline run terakhir + strip 30 hari + status jadwal.
- **Sorotan Data Bulanan**: edisi per bulan, headline otomatis, tab top movers.
- Server read-only kecuali `keputusan.json`; tidak ada koneksi keluar.

## Perintah manual

```bash
cd "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Claude Code/idx-1persen"
python3 fetch_idx.py check --dry-run   # tes tanpa mengubah state
python3 fetch_idx.py check             # run normal
python3 fetch_idx.py status            # lihat state
```

## Aktivasi jadwal (belum aktif!)

Jadwal cron **sengaja belum dibuat** — menunggu approval Patrick atas hasil
dry-run. Setelah approve, bilang ke Claude: *"aktifkan cron idx-1persen"* →
Claude akan membuat cron harian `0 8 * * *` (08:00 WIB, timezone Mac sudah WIB)
yang menjalankan runbook `CRON_PROMPT.md`.

Catatan: data satu-persen terbit **bulanan**, jadi sebagian besar hari hasilnya
`NO_NEW_DATA` — itu normal dan murah (1x fetch halaman saja).

## Dependensi

`python3` bawaan macOS + `pip install --user cloudscraper openpyxl` (sudah terpasang).
