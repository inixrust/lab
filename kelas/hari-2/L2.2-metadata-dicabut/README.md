# L2.2-metadata-dicabut  -  Jebakan Dokumen yang Sudah Dicabut

**Hari 2 - Building Blocks: Vector DB, Enhancement, Prompt, Evaluasi**

> SOP-03 (DICABUT) & SOP-05 (BERLAKU) bertentangan. Cegah yang dicabut masuk konteks - di KODE, bukan prompt.

## Cara menjalankan

```bash
# 1. (sekali) buat & aktifkan venv, lalu:
pip install -r requirements.txt
python cari.py --semua "panjang minimum kata sandi?"   # tanpa filter: dicabut bocor
python cari.py "panjang minimum kata sandi?"           # bawaan: hanya berlaku
```

## Yang harus terlihat

- Tanpa filter: potongan status=dicabut ikut muncul.
- Dengan filter bawaan: hanya status=berlaku yang lolos.

## Catatan

Isi TODO L2.2-1 (penyaring status bawaan). Aturan keras ditegakkan di retrieval, bukan prompt.

## Berkas yang Anda kerjakan (starter/)

Cari komentar `# TODO` pada berkas berikut, lengkapi, lalu bandingkan dengan `solution/`:

- `cari.py`

## Struktur

- `starter/` - kerangka dengan `# TODO`; **kerjakan di sini**.
- `solution/` - acuan lengkap yang sudah jalan.
- Setiap folder mandiri: dokumen & set_uji sudah disertakan.
