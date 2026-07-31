# L1.2-indeks-pertama  -  Membangun Indeks Pertama

**Hari 1 - Fondasi: AI Knowledge Stack & RAG**

> Muat dokumen -> potong -> embed -> simpan. Bangun basis data vektor pertama Anda.

## Cara menjalankan

```bash
# 1. (sekali) buat & aktifkan venv, lalu:
pip install -r requirements.txt
python muat.py        # lihat satu contoh potongan
python indeks.py      # bangun indeks (butuh Ollama untuk embedding)
```

## Yang harus terlihat

- muat.py mencetak jumlah potongan per berkas lalu TOTAL.
- indeks.py melaporkan jumlah vektor tersimpan di chroma_db/.

## Catatan

Isi TODO L1.2-1 (buat pemotong), L1.2-2 (potong dokumen), L1.2-3 (bangun Chroma).

## Berkas yang Anda kerjakan (starter/)

Cari komentar `# TODO` pada berkas berikut, lengkapi, lalu bandingkan dengan `solution/`:

- `muat.py`
- `indeks.py`

## Struktur

- `starter/` - kerangka dengan `# TODO`; **kerjakan di sini**.
- `solution/` - acuan lengkap yang sudah jalan.
- Setiap folder mandiri: dokumen & set_uji sudah disertakan.
