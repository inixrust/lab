# L1.3-tanya-baca-potongan  -  Bertanya & Membaca Potongan Sebelum Jawaban

**Hari 1 - Fondasi: AI Knowledge Stack & RAG**

> Ajukan pertanyaan; LIHAT potongan yang terambil lebih dulu, baru jawaban model.

## Cara menjalankan

```bash
# 1. (sekali) buat & aktifkan venv, lalu:
pip install -r requirements.txt
python cari.py "Berapa lama masa percobaan karyawan baru?"
python jawab.py "Berapa lama masa percobaan karyawan baru?"
```

## Yang harus terlihat

- cari.py menampilkan 4 potongan teratas beserta sumbernya.
- jawab.py menampilkan potongan DULU, lalu jawaban ber-sitasi angka [1]/[2].

## Catatan

Isi TODO L1.3-1 (similarity_search), L1.3-2 (prompt sistem), L1.3-3 (penomoran konteks).

## Berkas yang Anda kerjakan (starter/)

Cari komentar `# TODO` pada berkas berikut, lengkapi, lalu bandingkan dengan `solution/`:

- `cari.py`
- `jawab.py`

## Struktur

- `starter/` - kerangka dengan `# TODO`; **kerjakan di sini**.
- `solution/` - acuan lengkap yang sudah jalan.
- Setiap folder mandiri: dokumen & set_uji sudah disertakan.
