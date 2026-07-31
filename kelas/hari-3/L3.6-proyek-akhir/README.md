# L3.6-proyek-akhir - Proyek Akhir: Pilih Dua Peningkatan, Lalu Ukur

**Hari 3 - AI Agents, Orchestration, dan Deployment**

> Pilih DUA peningkatan, pasang, lalu UKUR dampaknya.
> Yang dinilai: alasan memilih + bukti angka — bukan banyaknya fitur.

Ini **snapshot lengkap seluruh kelas**: Hari 1 (indeks, embedding), Hari 2
(chunking, metadata, hybrid, evaluasi), dan Hari 3 (agent, graph, multi-agent,
guardrail, cache, jejak, human-in-the-loop). Semuanya sudah berjalan. Tugas Anda
bukan membangun dari nol, melainkan **memperbaiki sesuatu dan membuktikannya**.

## Cara menjalankan

```bash
# 1. (sekali) buat & aktifkan venv, lalu:
pip install -r requirements.txt
python indeks.py

# 2. catat angka SEBELUM — ini garis dasar Anda
python nilai.py

# 3. pasang dua peningkatan (menu di bawah); bangun ulang indeks bila perlu
python indeks.py --ulang

# 4. catat angka SESUDAH, pada set uji yang SAMA
python nilai.py
```

## Yang harus terlihat

- Angka recall/penolakan **sebelum & sesudah** pada set uji yang sama.
- Alasan memilih kedua peningkatan itu, bukan yang lain.
- **Kejujuran saat angka tidak membaik dinilai penuh.** Peningkatan yang
  ternyata tak berdampak adalah temuan yang sah — asalkan Anda mengukurnya dan
  mengatakannya. Yang tidak dinilai adalah perubahan tanpa angka.

## Menu peningkatan

Ambil **dua**. Kolom terakhir menunjukkan dengan apa dampaknya dibuktikan.

| #   | Peningkatan                           | Berkas         | Dibuktikan dengan                |
| --- | ------------------------------------- | -------------- | -------------------------------- |
| 1   | Ganti atau tambah korpus dokumen      | `dokumen/`     | `nilai.py`                       |
| 2   | Perluas kamus singkatan organisasi    | `cari.py`      | `nilai.py`                       |
| 3   | Setel ulang ukuran potongan / pemisah | `konfig.py`    | `nilai.py`                       |
| 4   | Perluas set uji                       | `set_uji.json` | `nilai.py`                       |
| 5   | Tambah peran atau klasifikasi dokumen | `izin.py`      | `tanya.py --bandingkan`          |
| 6   | Tambah alat baru untuk agent          | `agen.py`      | `agen.py` / `graf.py`            |
| 7   | Tambah anggota tim spesialis          | `tim.py`       | jejak langkah `tim.py`           |
| 8   | Tambah simpul **pasti** baru di alur  | `alur.py`      | jejak audit `alur.py`            |
| 9   | Setel ambang eskalasi ke manusia      | `konfig.py`    | `alur.py --set-uji` + `jejak.py` |

Nomor 1-4 menggeser **mutu pengambilan**. Nomor 5-9 menggeser **perilaku
sistem** — dan itu tidak terlihat oleh `nilai.py`, jadi harus diukur dengan alat
yang tepat.

## Mengukur yang bukan recall

`nilai.py` hanya menjawab satu pertanyaan: apakah potongan yang benar terambil.
Sejak L3.4 Anda punya dua alat ukur lain, dan peningkatan di sisi keamanan atau
orkestrasi **harus** dibuktikan dengan alat yang sesuai:

```bash
# perilaku hak akses: pertanyaan sama, semua peran, hasilnya harus berbeda
python tanya.py --bandingkan "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"

# perilaku sistem setelah dipakai: p50/p95, rasio penolakan, rasio cache,
# rasio eskalasi, dan SEBAB eskalasinya
python jejak.py
python jejak.py --akhir 5
python jejak.py --eskalasi

# campuran langkah pasti vs model, dan kapan manusia dilibatkan
python alur.py --peran staf "pertanyaan Anda"

# berapa banyak pertanyaan yang berhenti untuk manusia, pada set uji yang sama
python alur.py --set-uji --otomatis setuju
```

Contoh laporan yang **baik** untuk peningkatan nomor 9:

> Ambang cakupan diturunkan 0,7 → 0,5. Sebelum: 6 dari 20 pertanyaan
> dieskalasi ke penyelia. Sesudah: 2 dari 20. Recall tidak berubah
> (100% → 100%, memang tidak disentuh). Kami memilih ini karena penyelia
> mengeluh kebanjiran, dan angka 6/20 membenarkan keluhan itu.

Perhatikan bentuknya: **angka sebelum, angka sesudah, set uji yang sama, dan
alasannya.** Itu yang dinilai — bukan panjang laporannya.

## Aturan main

1. **Ukur dulu, baru ubah.** Garis dasar yang dicatat setelah perubahan bukan
   garis dasar.
2. **Satu perubahan pada satu waktu.** Dua perubahan sekaligus lalu satu angka
   membaik — Anda tidak tahu yang mana penyebabnya.
3. **Set uji tidak boleh berubah di tengah jalan.** Kalau `set_uji.json`
   diperluas (peningkatan nomor 4), ukur ulang garis dasarnya juga.
4. **Ganti embedding atau ukuran potongan = indeks wajib dibangun ulang.**
   Sidik jari di `indeks_meta.json` akan memperingatkan; jangan diabaikan.

## Peta berkas

Semuanya sudah lengkap dan berjalan. Yang paling mungkin Anda sentuh ditandai ←.

| Berkas                          | Isi                                           | Dari     |
| ------------------------------- | --------------------------------------------- | -------- |
| `muat.py` `indeks.py` `meta.py` | memuat, memotong, mengindeks                  | Hari 1-2 |
| `cari.py` ←                     | vektor + BM25 + RRF + susun ulang             | Hari 2   |
| `jawab.py`                      | prompt, sitasi, penolakan                     | Hari 2   |
| `nilai.py`                      | recall & penolakan pada set uji               | Hari 2   |
| `agen.py` ←                     | agent + alat (lingkaran tulisan tangan)       | L3.1     |
| `app.py` `sumber.py`            | antarmuka; sitasi yang bisa dibuka, baca saja | L3.2     |
| `graf.py` `tim.py` ←            | agent sebagai graph; tim multi-agent          | L3.3     |
| `izin.py` ←                     | hak akses ditegakkan di kode                  | L3.4     |
| `singgahan.py` `jejak.py`       | cache per hak akses; observability            | L3.4     |
| `tanya.py`                      | izin → singgahan → cari → jawab → periksa     | L3.4     |
| `alur.py` ←                     | graf berkeadaan + human-in-the-loop           | L3.5     |
| `konfig.py` ←                   | seluruh setelan, termasuk ambang eskalasi     | semua    |

Semua setelan angka di `konfig.py` bisa ditimpa lewat variabel lingkungan, jadi
penyapuan nilai tidak menuntut penyuntingan berkas:

```bash
UKURAN_POTONGAN=500 python indeks.py --ulang && python nilai.py
JUMLAH_KANDIDAT=8 python nilai.py
AMBANG_ESKALASI=0.7 python alur.py --set-uji
```

## Struktur

- **`starter/` — garis dasar.** Snapshot lengkap seluruh kelas, tanpa `# TODO`.
  Di sinilah Anda bekerja, dan inilah angka "sebelum" Anda.
- **`solution/` — contoh penerapan KESEMBILAN peningkatan**, lengkap dengan
  cara mengukur tiap-tiapnya. Bacalah `solution/PENINGKATAN.md` lebih dulu: ia
  memuat angka sebelum/sesudah yang sebenarnya, termasuk **dua peningkatan yang
  ternyata tidak memperbaiki apa pun** — dan itu sengaja tidak disembunyikan.
- Anda tetap hanya diminta mengambil **dua**. Sembilan yang ada di `solution/`
  adalah rujukan bentuk, bukan target yang harus dikejar.
- Membandingkan pekerjaan Anda dengan rujukan:

  ```bash
  # dari dalam kelas/hari-3/L3.6-proyek-akhir
  diff -r starter solution --exclude=chroma_db --exclude=*.pkl --exclude=__pycache__
  ```

- Folder mandiri: dokumen & set_uji sudah disertakan di keduanya.
