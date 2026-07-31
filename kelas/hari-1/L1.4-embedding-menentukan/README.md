# L1.4-embedding-menentukan  -  Membuktikan Pilihan Embedding Menentukan

**Hari 1 - Fondasi: AI Knowledge Stack & RAG**

> Buktikan sendiri: mengganti embedding tanpa indeks ulang membuat hasil ACAK - tanpa galat.

## Cara menjalankan

```bash
# 1. (sekali) buat & aktifkan venv, lalu:
pip install -r requirements.txt
python jawab.py "Aturan penggantian biaya perjalanan dinas?"    # dengan bge-m3
# lalu tiru embedding buruk: set MODE_TIRUAN=1 (lihat README), indeks ULANG, ulangi
python indeks.py --ulang
python jawab.py "Aturan penggantian biaya perjalanan dinas?"
```

## Yang harus terlihat

- Dengan bge-m3: potongan relevan. Dengan mode tiruan: potongan melenceng, jawaban memburuk.
- Pelajaran F3: embedding indeks & kueri WAJIB sama; ganti embedding = WAJIB indeks ulang.

## Catatan

Tidak ada berkas baru - ini eksperimen setelan. Cara menyetel MODE_TIRUAN ada di README.

## Struktur

- `starter/` - kerangka dengan `# TODO`; **kerjakan di sini**.
- `solution/` - acuan lengkap yang sudah jalan.
- Setiap folder mandiri: dokumen & set_uji sudah disertakan.

## Menyetel MODE_TIRUAN (untuk eksperimen)

```bash
# PowerShell:
$env:MODE_TIRUAN=1;  python indeks.py --ulang
# cmd:
set MODE_TIRUAN=1 && python indeks.py --ulang
# bash:
MODE_TIRUAN=1 python indeks.py --ulang
```
