# Panduan Lab — TX-AI11

Panduan langkah demi langkah untuk peserta. Ikuti berurutan; setiap langkah
punya cara memastikan bahwa ia berhasil sebelum lanjut.

> Kalau ada yang macet, jangan menebak. Jalankan `python cek.py` — skrip itu
> memberi tahu persis apa yang belum beres dan apa yang harus dikerjakan.

---

## Langkah 0 — Sebelum kelas dimulai

Lakukan di rumah atau kantor, **jangan** di ruang kelas. Unduhan model
sekitar 6 GB; kalau dua puluh orang mengunduh bersamaan, wifi ruangan akan
lumpuh dan waktu pelajaran habis.

```bash
# 1. Pasang Ollama — unduh dari https://ollama.com/download

# 2. Tarik model. Sesuaikan dengan RAM laptop Anda:
ollama pull bge-m3          # WAJIB, untuk semua orang (~1,2 GB)

ollama pull qwen3:4b        # kalau RAM 8 GB
ollama pull qwen3:8b        # kalau RAM 16 GB atau lebih

# 3. Pastikan keduanya muncul
ollama list
```

**Penting:** model `bge-m3` harus sama untuk semua peserta. Model chat boleh
berbeda menyesuaikan RAM, tetapi model embedding tidak — kalau berbeda,
indeks tidak bisa saling dipertukarkan dan angka evaluasi tidak bisa
dibandingkan antar-peserta.

---

## Langkah 1 — Siapkan lingkungan Python

```bash
cd lab

python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

**Memastikan berhasil:**

```bash
cd src
python cek.py
```

Keluarannya harus berakhir dengan `SIAP`. Kalau belum, skrip itu menuliskan
daftar hal yang perlu dikerjakan — kerjakan dari nomor satu.

---

## Langkah 2 — Kenali dokumennya

Korpus lab berisi dokumen fiktif PT Nusantara Cipta Solusi. Luangkan dua
menit membukanya, karena seluruh lab akan berputar di sekitar isinya.

| Berkas | Isi |
|---|---|
| `SOP-01-Kepegawaian.pdf` | Masa percobaan, cuti, lembur, tunjangan |
| `SOP-02-Pengadaan.pdf` | Batas nilai, kewenangan, alur pengadaan |
| `SE-12-2026-Perjalanan-Dinas.pdf` | SPPD, uang harian, penginapan |
| `SOP-05-Keamanan-Informasi.pdf` | Kata sandi, perangkat, insiden — **berlaku** |
| `SOP-03-Keamanan-Informasi-DICABUT.pdf` | Versi lama — **sudah dicabut** |
| `NR-04-2026-Rapat-Koordinasi-TI.md` | Notulen rapat |

Perhatikan dua berkas terakhir tentang keamanan informasi. Keduanya
**bertentangan** — dan itu disengaja. Kita akan memakainya untuk membuktikan
sesuatu yang penting di modul B3.

---

## Langkah 3 — Bangun indeks

```bash
python indeks.py
```

Ini menjalankan empat langkah pipeline pengindeksan dari modul F3: memuat,
memotong, membuat embedding, dan menyimpan. Bagian embedding adalah yang
paling lambat — di laptop tanpa GPU bisa satu sampai tiga menit.

**Memastikan berhasil:** keluaran berakhir dengan jumlah vektor tersimpan
(sekitar 29 untuk korpus lab), dan muncul folder `chroma_db/` beserta berkas
`potongan.pkl`.

> Jalankan ini **sekali saja**. Skrip berikutnya membaca indeks yang sudah
> jadi, tidak membangunnya ulang.

---

## Langkah 4 — Ajukan pertanyaan

```bash
python jawab.py "Berapa lama masa percobaan karyawan baru?"
```

Perhatikan bahwa potongan yang diambil dicetak **sebelum** jawabannya. Itu
disengaja, dan merupakan kebiasaan paling penting yang dibawa pulang dari
kelas ini: saat jawaban salah, lihat dulu bahannya sebelum menyalahkan model.

Coba beberapa pertanyaan lain:

```bash
python jawab.py "Bagaimana ketentuan pengajuan SPPD?"
python jawab.py "Berapa panjang minimum kata sandi sistem internal?"
python jawab.py "Berapa besaran tunjangan transportasi?"
```

Pertanyaan terakhir jawabannya **tidak ada** di dokumen. Sistem seharusnya
menolak, bukan mengarang.

---

## Langkah 5 — Bandingkan tiga cara mencari

```bash
python cari.py "Apa isi SE-12/2026?"
```

Skrip ini menampilkan hasil dari tiga konfigurasi berdampingan: vektor saja,
hybrid, dan hybrid dengan penyusunan ulang. Amati perbedaannya, terutama
untuk pertanyaan yang memuat nomor surat atau singkatan.

---

## Langkah 6 — Ukur, jangan menebak

```bash
python nilai.py
```

Inilah bagian yang mengubah "rasanya lebih baik" menjadi angka. Skrip ini
menjalankan 20 pertanyaan uji pada tiga konfigurasi dan melaporkan recall
masing-masing, dipecah menurut jenis pertanyaan.

Untuk ikut menguji kemampuan menolak (memakai model bahasa, lebih lambat):

```bash
python nilai.py --penolakan
```

---

## Langkah 7 — Rusak, lalu ukur lagi

Ini latihan paling berkesan di seluruh kelas. Ubah satu hal di `konfig.py`,
lalu jalankan `python nilai.py` dan lihat apa yang terjadi pada angkanya.

| Coba ubah | Yang akan Anda lihat |
|---|---|
| `MODEL_EMBEDDING` jadi `nomic-embed-text` **tanpa** membangun ulang indeks | Sistem tetap jalan, **tanpa galat** — tapi recall jatuh |
| `PAKAI_RERANKER = 0` | Presisi turun, cakupan tetap |
| `JUMLAH_KANDIDAT` jadi `2` | Hybrid kehilangan manfaatnya |
| `UKURAN_POTONGAN` jadi `300`, lalu `python indeks.py --ulang` | Syarat pengecualian terpisah dari ketentuannya |

Yang paling penting adalah baris pertama. Sistem **tidak memberi tanda apa
pun** bahwa ada yang salah — hanya angkanya yang jatuh. Itulah alasan modul
evaluasi ada.

Kembalikan setelan seperti semula setelah selesai:

```bash
python indeks.py --ulang
```

---

## Langkah 8 — Bungkus jadi antarmuka

```bash
streamlit run app.py
```

Buka `http://localhost:8501`. Inilah bentuk yang bisa Anda tunjukkan ke
atasan saat kembali ke kantor.

---

## Langkah 9 — Biarkan model memilih langkahnya (agent) · Hari 3

Sampai di sini alurnya selalu tetap: ambil potongan, lalu jawab. Agent
membalik itu — **model yang memutuskan** alat mana dipakai dan berapa kali.

```bash
python agen.py "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
```

Perhatikan keluarannya: agent memanggil `cari_kebijakan` untuk menemukan
besaran harian, lalu `hitung` untuk mengalikannya dengan tiga. Satu pertanyaan,
dua alat, dipilih sendiri oleh model. Coba juga pertanyaan satu langkah:

```bash
python agen.py "Berapa panjang minimum kata sandi sistem internal?"
```

> Agent membutuhkan model yang mendukung *tool-calling* (qwen3 mendukung).
> Di mode tiruan, `agen.py` jatuh ke satu panggilan pencarian langsung — alurnya
> tetap terlihat meski tanpa kemampuan memilih alat.

---

## Kalau ada yang macet

| Gejala | Penyebab &amp; perbaikan |
|---|---|
| `ConnectionError` ke port 11434 | Layanan Ollama belum berjalan. Buka aplikasinya atau jalankan `ollama serve` |
| `model "bge-m3" not found` | Belum ditarik: `ollama pull bge-m3` |
| `Indeks belum dibangun` | Jalankan `python indeks.py` lebih dulu |
| Sangat lambat | Wajar di CPU. Turunkan ke model lebih kecil, atau matikan reranker (`PAKAI_RERANKER=0`, lihat cara di bawah) |
| Reranker mengunduh lama | Berkasnya sekitar 2 GB dan diunduh dari Hugging Face, bukan Ollama. Biarkan sampai selesai, atau matikan |
| Jawaban acak setelah mengganti model embedding | Indeks belum dibangun ulang: `python indeks.py --ulang` |
| Semua terasa terlalu berat di laptop | Berpasangan dengan peserta lain, atau aktifkan mode tiruan (`MODE_TIRUAN=1`, lihat cara di bawah) |

### Menyetel lewat variabel lingkungan

Beberapa setelan (`PAKAI_RERANKER`, `MODE_TIRUAN`, `MODEL_CHAT`, `MODEL_EMBEDDING`)
bisa diatur tanpa mengubah `konfig.py`. **Caranya berbeda tiap terminal** — pakai
yang sesuai, kalau tidak variabelnya diam-diam tidak terpasang:

```powershell
# PowerShell (default Windows 11)
$env:PAKAI_RERANKER = "0"
python nilai.py
```

```bat
:: Command Prompt (cmd.exe)
set PAKAI_RERANKER=0
python nilai.py
```

```bash
# macOS / Linux (bash, zsh)
PAKAI_RERANKER=0 python nilai.py
```

Contoh lain: mengaktifkan **mode tiruan** — ganti `PAKAI_RERANKER=0` di atas
dengan `MODE_TIRUAN=1`.

**Mode tiruan** mengganti model dengan fungsi sederhana. Mutu jawabannya
buruk, tetapi seluruh alur tetap berjalan — sehingga Anda tetap bisa
mengikuti pelajaran tentang chunking, metadata, dan evaluasi meski Ollama
sedang bermasalah.

---

## Susunan berkas

```
lab/
├── PANDUAN-PESERTA.md      panduan ini
├── requirements.txt        daftar paket
├── set_uji.json            24 kasus uji untuk evaluasi
├── dokumen/                korpus fiktif
└── src/
    ├── cek.py              pemeriksaan kesiapan — JALANKAN PERTAMA
    ├── konfig.py           semua setelan ada di sini
    ├── model.py            pembuat objek model + mode tiruan
    ├── meta.py             sidik jari indeks — jaga embedding tetap cocok (F3)
    ├── muat.py             memuat dan memotong dokumen
    ├── indeks.py           membangun indeks
    ├── cari.py             pencarian: vektor, hybrid, penyusunan ulang
    ├── jawab.py            menyusun jawaban ber-sitasi
    ├── nilai.py            evaluasi
    ├── agen.py             agent: model memilih & memanggil alat sendiri (A2/A6)
    ├── app.py              antarmuka Streamlit
    └── buat_dokumen.py     pembangkit ulang dokumen contoh
```

Semua setelan yang mungkin perlu diubah ada di `konfig.py`. Kalau Anda ingin
mengubah sesuatu, mulailah dari sana.
