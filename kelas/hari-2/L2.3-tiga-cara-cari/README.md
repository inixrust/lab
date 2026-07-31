# L2.3-tiga-cara-cari  -  Tiga Cara Mencari, Berdampingan

**Hari 2 - Building Blocks: Vector DB, Enhancement, Prompt, Evaluasi**

> Vektor lemah pada nomor surat & singkatan. Tambah BM25 -> RRF -> reranker, dan perluasan singkatan.

## Cara menjalankan

```bash
# 1. (sekali) buat & aktifkan venv, lalu:
pip install -r requirements.txt
python cari.py "isi SE-12 tentang apa?"
python cari.py "berapa uang harian SPPD golongan Manajer?"
```

## Yang harus terlihat

- Tiga blok hasil: VEKTOR SAJA, HYBRID, HYBRID + SUSUN ULANG.
- Pertanyaan ber-singkatan/nomor surat membaik nyata pada hybrid.

## Catatan

Isi TODO L2.3-1 (perluas singkatan), L2.3-2 (RRF), L2.3-3 (hybrid), L2.3-4 (rerank). Reranker berat: matikan dengan PAKAI_RERANKER=0 bila RAM 8 GB.

## Berkas yang Anda kerjakan (starter/)

Cari komentar `# TODO` pada berkas berikut, lengkapi, lalu bandingkan dengan `solution/`:

- `cari.py`

## Struktur

- `starter/` - kerangka dengan `# TODO`; **kerjakan di sini**.
- `solution/` - acuan lengkap yang sudah jalan.
- Setiap folder mandiri: dokumen & set_uji sudah disertakan.
