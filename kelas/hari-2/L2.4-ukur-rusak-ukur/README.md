# L2.4-ukur-rusak-ukur  -  Ukur, Lalu Rusak dan Ukur Lagi

**Hari 2 - Building Blocks: Vector DB, Enhancement, Prompt, Evaluasi**

> Ubah 'rasanya lebih baik' jadi angka recall. Lalu RUSAK satu komponen dan ukur lagi.

## Cara menjalankan

```bash
# 1. (sekali) buat & aktifkan venv, lalu:
pip install -r requirements.txt
python nilai.py              # recall per metode + penyaringan status
python nilai.py --penolakan  # uji keberanian menolak (butuh model)
```

## Yang harus terlihat

- recall@4 naik dari VEKTOR SAJA -> HYBRID -> HYBRID+SUSUN ULANG.
- Kebocoran dokumen dicabut turun ke 0 dengan penyaring.
- Rusak: set MODE_TIRUAN=1, indeks --ulang, jalankan nilai.py -> recall jatuh TANPA galat.

## Catatan

Isi TODO L2.4-1 (periksa_sitasi di jawab.py) & L2.4-2 (_cocok di nilai.py).

## Berkas yang Anda kerjakan (starter/)

Cari komentar `# TODO` pada berkas berikut, lengkapi, lalu bandingkan dengan `solution/`:

- `jawab.py`
- `nilai.py`

## Struktur

- `starter/` - kerangka dengan `# TODO`; **kerjakan di sini**.
- `solution/` - acuan lengkap yang sudah jalan.
- Setiap folder mandiri: dokumen & set_uji sudah disertakan.
