# L3.2-antarmuka  -  Membungkus Pipeline Jadi Antarmuka

**Hari 3 - AI Agents, Orchestration, dan Deployment**

> Terminal tak meyakinkan atasan. Bungkus pipeline jadi antarmuka Streamlit yang bisa diklik.

## Cara menjalankan

```bash
# 1. (sekali) buat & aktifkan venv, lalu:
pip install -r requirements.txt
streamlit run app.py
# on-premise via Docker: lihat DEPLOY.md
```

## Yang harus terlihat

- Kotak tanya-jawab; tiap jawaban punya sumber yang bisa dibuka.
- Penanda saat sistem menolak, dan keterangan 'semua berjalan lokal'.
- **Tiap sitasi `[1]`..`[4]` adalah kotak yang bisa diklik.** Membukanya
  menampilkan **halaman asli** dari dokumen sungguhan, dengan bagian yang
  dibaca model **disorot** di tengah teks sekitarnya.
- Sumbernya **baca saja** — tidak ada tombol unduh, dan memang tidak bisa ada:
  yang dikirim ke peramban hanya teks halaman itu, tidak pernah berkasnya.

## Catatan

Isi TODO L3.2-1 (panggil jawab() dan tampilkan hasilnya). Berkas Docker disertakan untuk deploy on-prem.

### Kenapa halaman asli, bukan potongan yang tersimpan?

Ini kelanjutan alasan yang sudah ditulis panjang di `util.lokasi()`:
*sitasi yang tidak bisa dicek sama saja dengan tidak ada sitasi.*

Menampilkan cuplikan dari indeks terasa cukup, padahal ia memeriksa sistem
dengan datanya sendiri. Kalau potongannya keliru — salah halaman, terpotong di
tempat yang salah, atau berasal dari dokumen yang sudah dicabut — cuplikannya
akan ikut keliru, dan tidak ada satu pun yang bisa menangkapnya.

`sumber.py` karena itu membaca ulang berkas aslinya dari `dokumen/`, bukan dari
indeks. Yang dilihat pengguna adalah halaman sungguhan; potongan yang dipakai
model hanyalah bagian yang disorot di dalamnya. Dengan begitu pengguna bisa
melihat **konteks di sekitarnya** juga — dan di situlah kekeliruan pemotongan
biasanya ketahuan.

Tidak ada paket baru: `pypdf` memang sudah dipakai `muat.py` untuk mengindeks.

### Boleh diperiksa, tidak boleh dibawa pulang

Memeriksa sitasi dan mengunduh dokumen adalah dua kebutuhan yang berbeda, dan
hanya yang pertama yang dijanjikan sistem ini. Menampilkan **satu halaman**
sudah cukup untuk memastikan jawabannya benar; memberi **berkas utuh** berarti
menyebarkan salinan dokumen internal yang tidak bisa ditarik kembali begitu ia
ada di laptop orang.

Perhatikan **bagaimana** batas itu ditegakkan: bukan dengan menyembunyikan
tombol, melainkan dengan tidak pernah mengirim isi berkasnya ke peramban sama
sekali. Yang dikirim hanya teks halaman yang bersangkutan. Ini prinsip yang
sama dengan penyaring di `cari.py` — yang tidak pernah dikirim tidak bisa
diambil, dan tidak ada tombol tersembunyi yang bisa ditemukan kembali lewat
"inspect element".

Batasnya tetap jujur: teks yang ditampilkan tentu bisa disalin dan
dipotret layar. Yang dicegah adalah pengunduhan berkas utuh dengan satu klik,
bukan penyalinan oleh orang yang memang sudah berhak membacanya.

Jalankan `python sumber.py` untuk memastikan **setiap** potongan di korpus Anda
masih bisa ditemukan kembali di dokumen aslinya:

```
29/29 potongan tersorot di halaman aslinya.
```

Angka yang tidak penuh berarti indeks Anda dibangun dari versi dokumen yang
berbeda dengan yang ada di `dokumen/` sekarang — dan sitasi yang ditampilkan
ke pengguna tidak lagi bisa dipertanggungjawabkan. Bangun ulang indeksnya.

## Berkas yang Anda kerjakan (starter/)

Cari komentar `# TODO` pada berkas berikut, lengkapi, lalu bandingkan dengan `solution/`:

- `app.py`

Berkas pendukung yang **sudah** lengkap: `sumber.py` — pembuka dokumen asli di
balik sitasi. Layak dibaca, tapi bukan bagian dari TODO.

## Struktur

- `starter/` - kerangka dengan `# TODO`; **kerjakan di sini**.
- `solution/` - acuan lengkap yang sudah jalan.
- Setiap folder mandiri: dokumen & set_uji sudah disertakan.
