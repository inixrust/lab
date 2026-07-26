# Bahan Lab — Korpus PT Nusantara Cipta Solusi

Dokumen fiktif berbahasa Indonesia untuk seluruh lab kelas TX-AI11. Dibuat sendiri,
jadi bebas dibagikan ke peserta tanpa masalah kerahasiaan atau hak cipta.

## Isi

```
lab/
├── dokumen/
│   ├── sop/
│   │   ├── SOP-01-Kepegawaian.pdf              3 hal · berpasal · ada tabel
│   │   ├── SOP-02-Pengadaan.pdf                2 hal · berpasal · ada tabel
│   │   ├── SOP-05-Keamanan-Informasi.pdf       1 hal · BERLAKU
│   │   └── SOP-03-Keamanan-Informasi-DICABUT.pdf  1 hal · DICABUT
│   ├── edaran/
│   │   └── SE-12-2026-Perjalanan-Dinas.pdf     2 hal · penuh singkatan
│   └── notulen/
│       └── NR-04-2026-Rapat-Koordinasi-TI.md   prosa · Markdown berheading
├── set_uji.json                                24 kasus uji
└── src/buat_dokumen.py                         pembangkit ulang dokumen
```

## Kenapa korpus ini dirancang begini

Setiap berkas ada untuk membuktikan satu pelajaran. Bukan sekadar "dokumen contoh".

| Berkas | Membuktikan | Modul |
|---|---|---|
| SOP-01, SOP-02 | Struktur berpasal — chunking harus mengikuti `Pasal`, bukan jumlah karakter | B2 |
| Tabel di SOP-01 &amp; SE-12 | Tabel rusak bila dipotong sembarangan | B2 |
| SE-12 (SPPD, SIMPEG, nomor surat) | Pencarian vektor gagal pada singkatan dan kode | B4 |
| Notulen (`.md`) | Satu korpus, beberapa jenis sumber, strategi chunking berbeda | B7 |
| SOP-03 vs SOP-05 | **Penyaringan metadata status** | B3 |

### Perangkap yang sengaja dipasang

**SOP-03 (dicabut) dan SOP-05 (berlaku) saling bertentangan pada tiga hal:**

| Hal | SOP-03 — DICABUT | SOP-05 — BERLAKU |
|---|---|---|
| Panjang kata sandi | 8 karakter | **14 karakter** |
| Ganti berkala | Wajib tiap 90 hari | **Tidak diwajibkan** |
| Perangkat pribadi | Boleh untuk email | **Dilarang** |

Kalau sistem peserta menjawab "8 karakter", ia membaca dokumen yang sudah dicabut —
persis kegagalan yang dibahas di B3. Ini demo yang tidak bisa dipalsukan: peserta
melihat sistemnya memberi jawaban yang <em>salah secara organisasi</em>, bukan sekadar
kurang tepat.

**Notulen merujuk ke SOP lain** (SOP-01, SOP-02, SOP-05) — bahan untuk pertanyaan
multi-hop yang butuh dua dokumen sekaligus.

## set_uji.json

24 kasus, dikelompokkan menurut apa yang diujinya:

| Jenis | Jumlah | Menguji |
|---|---|---|
| `mudah` | 5 | Dasar — kosakata pertanyaan mirip dokumen |
| `parafrasa` | 4 | Kualitas embedding (B1) |
| `singkatan` · `nomor_dokumen` | 4 | Hybrid search (B4) |
| `sulit` | 2 | Multi-hop, butuh gabungan dua ketentuan |
| `pengecualian` | 2 | Mutu chunking — syarat tak boleh terpisah (B2) |
| `versi` | 3 | Penyaringan metadata status (B3) |
| `penolakan` | 4 | Sistem berani mengaku tidak tahu (B5) |

**Nomor halaman memakai indeks mulai 0**, sesuai `PyPDFLoader` LangChain — halaman
pertama bernomor `0`. Jangan tergoda mengubahnya agar "sesuai" nomor cetak di footer.

## Cara memakai

```bash
# Bangun ulang dokumen bila perlu diubah
pip install reportlab
python src/buat_dokumen.py

# Uji keterbacaan SEBELUM dipakai di kelas — kebiasaan dari F4
python -c "
from pypdf import PdfReader
import glob
for f in glob.glob('dokumen/**/*.pdf', recursive=True):
    r = PdfReader(f)
    print(f, [len((p.extract_text() or '').strip()) for p in r.pages])
"
```

Kalau ada halaman yang jumlah karakternya nyaris nol, PDF-nya gambar dan butuh OCR.
Seluruh berkas di sini sudah diverifikasi terbaca (966–2.290 karakter per halaman).

## Menyesuaikan untuk peserta tertentu

Berkas `src/buat_dokumen.py` sengaja dibuat mudah diubah. Kalau kelas Anda datang dari
satu instansi, ganti nama perusahaan, istilah, dan singkatan agar terasa dekat — lalu
jalankan ulang. Sistem `Jangkar` mencatat nomor halaman secara otomatis, jadi
`set_uji.json` tinggal disesuaikan tanpa menghitung halaman manual.

> Catatan: PT Nusantara Cipta Solusi dan seluruh isinya adalah fiktif. Nama, nomor
> dokumen, dan angka dikarang untuk keperluan pelatihan.
