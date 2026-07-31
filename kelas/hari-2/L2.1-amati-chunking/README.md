# L2.1-amati-chunking  -  Mengamati Bagaimana Dokumen Dipotong

**Hari 2 - Building Blocks: Vector DB, Enhancement, Prompt, Evaluasi**

> Satu strategi chunk tak cukup. Potong peraturan di batas Pasal; sisipkan jalur judul ke ISI potongan.

## Cara menjalankan

```bash
# 1. (sekali) buat & aktifkan venv, lalu:
pip install -r requirements.txt
python indeks.py --ulang   # bangun ulang dengan chunking per-jenis
python muat.py             # perhatikan awalan [sumber > bab > bagian] di isi potongan
```

## Yang harus terlihat

- Potongan SOP terpotong rapi di batas Pasal, bukan di tengah kalimat.
- Tiap potongan diawali konteks [sumber > ...] YANG IKUT di-embed.

## Catatan

Isi TODO L2.1-1 (pemisah per jenis) & L2.1-2 (sisip konteks induk ke page_content).

## Berkas yang Anda kerjakan (starter/)

Cari komentar `# TODO` pada berkas berikut, lengkapi, lalu bandingkan dengan `solution/`:

- `muat.py`

## Struktur

- `starter/` - kerangka dengan `# TODO`; **kerjakan di sini**.
- `solution/` - acuan lengkap yang sudah jalan.
- Setiap folder mandiri: dokumen & set_uji sudah disertakan.
