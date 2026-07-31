# Cara Menambah Dokumen ke Sistem

Panduan singkat: apa yang harus dilakukan agar sistem bisa menjawab berdasarkan
dokumen baru. Berlaku untuk menambah **maupun** mengganti dokumen.

> **Inti yang wajib diingat:** indeks bersifat *persisten*. Menaruh file di folder
> **tidak** membuat sistem langsung mengenalnya — Anda harus **membangun ulang
> indeks**. Kalau langkah ini terlewat, sistem tetap berjalan tanpa galat, hanya
> saja jawabannya mengabaikan dokumen baru itu (pelajaran F3).

Semua perintah dijalankan dari folder **`src/`**.

---

## Langkah wajib

**1. Taruh file di subfolder yang tepat di `dokumen/`.**
Tidak perlu mengubah kode — `muat.py` menemukan semua file secara otomatis. Nama
subfolder menentukan cara dokumen diperlakukan:

| Taruh di | Untuk | Cara dipotong | `jenis` |
|---|---|---|---|
| `dokumen/sop/` | SOP, peraturan berpasal | mengikuti batas **Pasal / BAB** | `sop` |
| `dokumen/edaran/` | surat edaran (SE) | mengikuti batas **Pasal / BAB** | `edaran` |
| `dokumen/notulen/` | notulen `.md` | mengikuti **heading** Markdown | `notulen` |
| folder lain | dokumen prosa umum | per **paragraf** | nama folder |

Status dokumen ditetapkan dari nama berkas: default **berlaku**; menjadi
**dicabut** hanya bila nama memuat kata `DICABUT`
(mis. `SOP-03-Keamanan-Informasi-DICABUT.pdf`).

**2. Pastikan PDF-nya benar-benar berisi teks** (bukan hasil pindaian/scan):

```bash
python cek.py
```

Bila sebuah PDF ditandai *"kemungkinan hasil pindaian"* (teks < 50 karakter),
ia harus di-OCR dulu — tanpa lapisan teks, dokumen itu masuk ke indeks dalam
keadaan kosong tanpa memunculkan galat apa pun.

**3. Bangun ulang indeks** — langkah kunci:

```bash
python indeks.py --ulang
```

> **Kenapa harus `--ulang`, bukan sekadar `python indeks.py`?**
> `indeks.py` memuat **seluruh** dokumen lalu memanggil `Chroma.from_documents`.
> Tanpa `--ulang`, semua dokumen ditambahkan lagi ke koleksi yang sudah ada →
> **duplikat**. `--ulang` menghapus indeks lama lebih dulu, lalu membangun bersih —
> sekaligus memperbarui BM25 (`potongan.pkl`) dan sidik jari (`indeks_meta.json`).
>
> ⚠️ **Jangan** mengganti `MODEL_EMBEDDING` di `konfig.py` saat menambah dokumen.
> Cukup `--ulang` dengan embedding yang sama. Mengganti embedding tanpa indeks
> ulang membuat hasil pencarian **acak tanpa galat**.

**4. Lihat potongan yang terambil** (kebiasaan F3: baca potongan sebelum jawaban):

```bash
python cari.py "pertanyaan tentang dokumen baru Anda"
```

Pastikan potongan dari dokumen baru benar-benar muncul di hasil.

**5. Ajukan pertanyaan.**

```bash
python jawab.py "pertanyaan tentang dokumen baru Anda"
```

Atau lewat antarmuka: `streamlit run app.py`. Jawaban akan ber-sitasi angka
(`[1]`, `[2]`) yang menunjuk potongan sumbernya.

---

## Langkah dianjurkan (kualitas & bukti)

**6. Singkatan baru → tambahkan ke kamus.** Bila dokumen memakai singkatan
organisasi (mis. `THR`, `SKB`), tambahkan pasangannya ke `SINGKATAN` di `cari.py`.
Ini perluasan kueri termurah dan paling berdampak untuk pencarian kata-persis.

**7. Mengganti dokumen lama → tandai yang lama `DICABUT`.** Bila dokumen baru
menggantikan versi lama, ubah nama berkas lama agar memuat `DICABUT`. Dengan
begitu ia otomatis tersaring dari jawaban, dan jawaban tidak lagi mencampur
aturan yang sudah tidak berlaku.

**8. Tambahkan kasus uji, lalu ukur.** Tambahkan 2–3 pertanyaan tentang topik baru
ke `set_uji.json`, lalu:

```bash
python nilai.py
```

Ini mengubah "rasanya sudah jalan" menjadi angka recall yang bisa
dipertanggungjawabkan (modul B6).

---

## Jika ada masalah

| Gejala | Kemungkinan sebab | Tindakan |
|---|---|---|
| Dokumen baru tidak pernah muncul di hasil | belum `indeks.py --ulang` | jalankan langkah 3 |
| Hasil pencarian tiba-tiba acak | `MODEL_EMBEDDING` diubah tanpa indeks ulang | kembalikan embedding, lalu `indeks.py --ulang` |
| PDF masuk tapi isinya "kosong" | PDF hasil pindaian tanpa teks | OCR dulu, baru indeks ulang |
| Dokumen yang sudah dicabut masih terjawab | nama berkas belum memuat `DICABUT` | ganti nama, lalu `indeks.py --ulang` |
| Nomor surat / singkatan tak ketemu | belum ada di kamus perluasan | tambahkan ke `SINGKATAN` di `cari.py` |

---

*Ringkas: **taruh file di folder yang benar → `python indeks.py --ulang`**. Dua
langkah itu yang wajib; sisanya menyempurnakan mutu dan bukti.*
