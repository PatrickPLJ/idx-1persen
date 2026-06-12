# Runbook: Loop Harian "Cek 1% Kepemilikan Saham IDX"

Kamu adalah agent terjadwal. Jalankan langkah-langkah ini PERSIS berurutan.
Folder kerja: `~/Library/Mobile Documents/com~apple~CloudDocs/Claude Code/idx-1persen/`

## GUARDRAILS (mutlak, tidak bisa dinego)

1. **Maksimal 1 output per hari.** Script sudah menjaga ini (`STATUS: DAILY_LIMIT`) — patuhi.
2. **DILARANG** mengirim apa pun ke publik/eksternal (email, Telegram, API, dsb).
3. **DILARANG** mengeluarkan uang atau memanggil layanan berbayar.
4. **DILARANG** menghapus data apa pun (file data/, facts/, output/, state).
5. Semua hasil = **DRAFT lokal** untuk di-approve Patrick. Tidak ada pengecualian.
6. Jangan deliver draft yang tidak lolos checker.

## LANGKAH

### 1. Fetch
```bash
cd "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Claude Code/idx-1persen"
python3 fetch_idx.py check
```
- `STATUS: NO_NEW_DATA` atau `STATUS: DAILY_LIMIT` → tulis 1 baris ke `logs.txt`
  (`tanggal — status`), lalu SELESAI. Jangan lakukan apa pun lagi.
- `STATUS: NEW_DATA` → catat `ID`, `FACTS`, `XLSX`, lanjut ke langkah 2.

### 2. MAKER — tulis draft laporan
Baca file `FACTS` (JSON). Tulis draft `output/draft-<periode>.md` dalam Bahasa
Indonesia santai-tapi-rapi, HANYA berdasarkan angka di facts JSON:

- Judul + banner: `> ⚠️ DRAFT — belum diverifikasi penuh, butuh approval Patrick.`
- Ringkasan periode: jumlah emiten, jumlah baris, lokal vs asing, perubahan vs bulan lalu.
- Tabel **investor baru masuk ≥1%** (top, dari `top_investor_masuk`).
- Tabel **investor keluar dari daftar** (top, dari `top_investor_keluar`).
- Tabel **kenaikan & penurunan terbesar** (pakai `pct_sebelum`, `pct_sesudah`, `delta_pct`).
- Emiten baru muncul / hilang dari daftar (kalau ada).
- Catatan metodologi singkat + sumber (URL IDX).

ATURAN MAKER: jangan mengarang angka, jangan beri saran beli/jual saham,
jangan berspekulasi soal alasan di balik pergerakan. Murni deskriptif.

### 3. CHECKER — AI kedua dengan prompt berbeda
Spawn subagent (Agent tool) dengan prompt ini (JANGAN diubah jadi prompt maker):

> Kamu auditor independen yang skeptis. Tugasmu MENCARI KESALAHAN, bukan
> menyetujui. Audit file draft `<path draft>` terhadap sumber data
> `<path facts JSON>` dan file mentah `<path xlsx>` (boleh pakai python3 +
> openpyxl untuk spot-check minimal 5 angka acak langsung dari xlsx).
> Periksa: (1) setiap angka di draft cocok dengan facts/xlsx, (2) tidak ada
> klaim yang tidak didukung data, (3) tidak ada saran investasi/spekulasi,
> (4) ada banner DRAFT, (5) periode & sumber benar. Balas HANYA JSON:
> `{"verdict": "PASS"|"FAIL", "issues": ["..."], "spot_checks": ["..."]}`

### 4. Keputusan
- **PASS** → `python3 fetch_idx.py mark <ID> delivered` lalu catat di `logs.txt`.
- **FAIL** → revisi draft SEKALI berdasarkan `issues`, ulangi checker (subagent
  baru, prompt sama).
  - PASS setelah revisi → mark delivered.
  - Masih FAIL → pindahkan draft ke `rejected/` (pakai `mv`, bukan hapus),
    tulis alasan ke `rejected/<nama>-alasan.txt`,
    `python3 fetch_idx.py mark <ID> rejected "<ringkasan issues>"`,
    catat di `logs.txt`. JANGAN taruh apa pun di `output/`.

### 5. Selesai
Akhiri dengan ringkasan 2-3 kalimat di `logs.txt`: apa yang ditemukan,
lolos/tidak, lokasi file.
