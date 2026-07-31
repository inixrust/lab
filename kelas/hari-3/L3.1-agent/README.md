# L3.1-agent  -  Agent yang Memanggil Alat Sendiri

**Hari 3 - AI Agents, Orchestration, dan Deployment**

> Agent = SEBUAH LINGKARAN: model memilih alat, kita jalankan, hasil kembali, ulangi sampai selesai.

## Cara menjalankan

```bash
# 1. (sekali) buat & aktifkan venv, lalu:
pip install -r requirements.txt
python agen.py "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
python agen.py "Berapa panjang minimum kata sandi sistem internal?"
```

## Yang harus terlihat

- Agent memanggil cari_kebijakan (ambil besaran) LALU hitung (kalikan) - dua langkah.
- Tiap langkah tercetak: nama alat, argumen, dan hasilnya.

## Catatan

Isi TODO L3.1-1 (lingkaran agent: bind_tools + loop panggil/eksekusi/kembalikan). Butuh model dengan tool-calling; MODE_TIRUAN jatuh ke satu panggilan RAG.

## Berkas yang Anda kerjakan (starter/)

Cari komentar `# TODO` pada berkas berikut, lengkapi, lalu bandingkan dengan `solution/`:

- `agen.py`

## Struktur

- `starter/` - kerangka dengan `# TODO`; **kerjakan di sini**.
- `solution/` - acuan lengkap yang sudah jalan.
- Setiap folder mandiri: dokumen & set_uji sudah disertakan.
