# Protokol Pengujian Lab TX-AI11

Langkah-langkah yang dipakai untuk memverifikasi seluruh kode lab, di **host**
maupun di **Docker**. Dokumen ini bukan catatan sejarah — ia dirancang untuk
**dijalankan ulang**: sebelum mengajar, setelah mengubah kode, atau saat
menyiapkan laptop baru.

Setiap langkah menyebut perintahnya, **apa yang harus terlihat**, dan kenapa
langkah itu ada. Kalau sebuah langkah gagal, jangan lanjut — perbaiki dulu.

> **Terminal.** Perintah di bawah memakai PowerShell (bawaan Windows 11).
> Untuk cmd.exe atau bash, cara menyetel variabel lingkungan berbeda — lihat
> bagian "Menyetel lewat variabel lingkungan" di `PANDUAN-PESERTA.md`.

Hasil acuan pada dokumen ini diperoleh 26 Juli 2026 di Windows 11,
Python 3.13.1, Ollama 0.32.4, Docker 29.6.2.

---

# Bagian A — Prasyarat

## A1. Ollama hidup dan model tersedia

```powershell
ollama --version
ollama list
```

**Harus terlihat:** `bge-m3` (wajib), dan minimal satu model chat
(`qwen3:8b` untuk RAM 16 GB, `qwen3:4b` untuk 8 GB).

**Kenapa:** `bge-m3` adalah satu-satunya model embedding yang dipakai seluruh
materi. Model chat boleh berbeda antar-mesin; embedding **tidak boleh**.

## A2. Lingkungan Python

```powershell
cd lab
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Perkiraan waktu:** 3–6 menit. Paling lama pada `sentence-transformers`
(menarik torch, ratusan MB).

---

# Bagian B — Pengujian di Host

Semua perintah dijalankan dari dalam `lab/src`:

```powershell
cd lab\src
```

Ganti `python` di bawah dengan `..\.venv\Scripts\python.exe`, atau aktifkan
venv lebih dulu (`..\.venv\Scripts\Activate.ps1`).

## B1. Pemeriksaan kesiapan

```powershell
python cek.py
```

**Harus berakhir:** `SIAP.`

**Harus terlihat:** semua paket wajib `[ OK ]`, layanan Ollama hidup, model
chat & `bge-m3` terdeteksi, 6 dokumen terbaca dengan jumlah karakter wajar
(966–6021), `set_uji.json` berisi 24 kasus.

**Kenapa:** menangkap masalah penyiapan dalam hitungan detik, sebelum peserta
menghabiskan dua puluh menit menebak.

## B2. Bangun indeks

```powershell
python indeks.py
```

**Harus terlihat:** rincian per berkas yang berjumlah **29 potongan**, lalu
`Selesai. 29 vektor tersimpan di chroma_db/`.

**Perkiraan waktu:** 1–3 menit di CPU (tahap embedding).

Perhatikan `SOP-03-Keamanan-Informasi-DICABUT.pdf` harus bertanda `(dicabut)`,
sisanya `(berlaku)`. Kalau tidak, penyaringan status di B6 tidak akan bermakna.

## B3. Sidik jari indeks tertulis

```powershell
Get-Content ..\indeks_meta.json
```

**Harus berisi:** `"model_embedding": "bge-m3"`, `"ukuran_potongan": 900`,
`"mode_tiruan": false`.

**Kenapa:** berkas ini yang membuat kegagalan senyap F3 bisa dideteksi
(lihat B10).

## B4. Jawaban dasar dan mutu sitasi

```powershell
python jawab.py "Berapa lama masa percobaan karyawan baru?"
```

**Harus terlihat:**
- Potongan dicetak **sebelum** jawaban (kebiasaan inti kelas).
- Jawaban menyebut **3 (tiga) bulan**.
- Penanda sitasi berupa **angka**, misalnya `[1]` — **bukan** `[n]`, `[n1]`,
  atau huruf lain.
- Keterangan letak berupa **nomor cetak**, dimulai dari `hal. 1` —
  **bukan** `hal. 0`.
- `(cakupan sitasi 100%)`.

> **Regresi yang pernah terjadi.** Sitasi sempat tampil sebagai `hal. 0`.
> PyPDFLoader menomori halaman mulai 0, dan nomor mentah itu dulu dicetak apa
> adanya. Akibatnya sitasi **tidak bisa diverifikasi**: peserta membuka PDF-nya,
> mencari halaman 0, dan tidak menemukan apa pun. Sitasi yang tak bisa dicek
> sama nilainya dengan tidak ada sitasi. `util.lokasi` sekarang mengubahnya
> menjadi nomor cetak saat ditampilkan.
>
> **`set_uji.json` tetap memakai indeks mulai 0** dan memang harus begitu —
> `nilai.py` membandingkan metadata, bukan teks di layar. Jadi kasus yang di
> `set_uji.json` tertulis `"halaman": [0]` akan tampil sebagai `hal. 1`.
> Keduanya menunjuk halaman yang sama. **Jangan "memperbaiki" `set_uji.json`
> agar cocok dengan layar** — itu justru merusak angka recall.

> **Regresi yang pernah terjadi.** qwen3 sempat menuliskan `[n1]` karena
> menafsirkan contoh `[n]` di prompt secara harfiah. Akibatnya cakupan
> dilaporkan **0% padahal model mengutip** — metrik gagal senyap. Aturan 2 di
> `jawab.py` sudah diperjelas. **Kalau penanda kembali bukan angka, itu
> regresi prompt, bukan sekadar gaya bahasa model.**

## B5. Jebakan dokumen dicabut

```powershell
python jawab.py "Berapa panjang minimum kata sandi sistem internal?"
```

**Harus dijawab:** **14 karakter** (dari SOP-05 yang berlaku).

**Gagal bila dijawab:** 8 karakter — artinya sistem membaca SOP-03 yang sudah
**dicabut**, dan penyaringan metadata tidak bekerja. Ini kesalahan yang
**salah secara organisasi**, bukan sekadar kurang tepat.

## B6. Keberanian menolak

```powershell
python jawab.py "Berapa besaran tunjangan transportasi bulanan?"
```

**Harus dijawab persis:**
`Informasi ini tidak ditemukan dalam dokumen yang tersedia.`

**Kenapa persis:** kalimat itu dicocokkan sebagai teks **persis** oleh
`nilai.py`. Beda satu kata membuat metrik penolakan selalu melaporkan 0%.

## B7. Tiga cara mencari berdampingan

```powershell
python cari.py "Apa isi SE-12/2026?"
```

**Harus terlihat:** tiga blok — `VEKTOR SAJA`, `HYBRID`,
`HYBRID + SUSUN ULANG`.

Perhatikan dua bentuk keterangan letak yang berdampingan di sini:

- Potongan PDF tampil sebagai **`hal. 1`**, `hal. 2`, dan seterusnya — nomor
  cetak, sama dengan yang dilihat peserta saat membuka berkasnya. **Tidak
  pernah `hal. 0`.**
- Potongan dari notulen (`.md`) tampil sebagai **`bagian: Agenda 3 - ...`**.
  Sumber Markdown memang tidak punya nomor halaman, jadi yang dipakai nama
  bagian — bukan nomor halaman karangan.

**Kenapa:** sitasi ada untuk diverifikasi. Keterangan letak yang tidak menunjuk
ke tempat yang benar-benar bisa dibuka membuat seluruh mekanisme sitasi
kehilangan gunanya.

## B8. Evaluasi terukur

```powershell
python nilai.py
```

**Hasil acuan:** `recall@4 = 100%` (20/20) pada ketiga konfigurasi, merata di
semua kategori (mudah, parafrasa, singkatan, nomor_dokumen, sulit,
pengecualian, versi).

**Dan pada bagian PENYARINGAN STATUS:**

```
dokumen dicabut masuk konteks:
  tanpa penyaring  : 3/3
  dengan penyaring : 0/3
```

**Kenapa penting:** inilah bukti terukur bahwa penyaringan status bekerja.
Tanpa metrik ini, jebakan SOP-03 hanya jadi demo manual yang tak terpantau.

Untuk ikut menguji penolakan (memakai model, lebih lambat):

```powershell
python nilai.py --penolakan
```

## B9. Agent memanggil alat

```powershell
$env:MODEL_CHAT = "qwen3:4b"
python agen.py "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
Remove-Item Env:\MODEL_CHAT
```

**Harus terlihat:** jejak langkah `[langkah 1] memanggil cari_kebijakan(...)`,
dan jawaban akhir yang benar secara aritmetika — uang harian Manajer
Dalam Provinsi Rp 350.000 × 3 hari = **Rp 1.050.000**.

> **Jangan menuntut jalur yang sama persis.** Terbukti pada pengujian ini:
> di host, model memanggil `cari_kebijakan` lalu `hitung`. Di container, pada
> satu kali jalan model hanya memanggil `cari_kebijakan` lalu menghitung sendiri
> ketiga skenario; pada kali lain — **container yang sama, pertanyaan yang
> sama** — ia memakai kedua alat. Ketiganya benar. `temperature=0` **tidak**
> menjamin pemilihan alat yang sama, bahkan pada lingkungan yang identik.
> Yang diuji adalah **kebenaran jawaban**, bukan urutan alat.

## B10. Mode tiruan dan penjaga sidik jari

Dua hal diuji sekaligus di sini: jaring pengaman saat Ollama bermasalah, dan
penjaga yang mencegah kegagalan senyap F3.

```powershell
$env:MODE_TIRUAN = "1"
python indeks.py --ulang
python jawab.py "Berapa lama masa percobaan karyawan baru?"
python agen.py "Berapa panjang minimum kata sandi?"
Remove-Item Env:\MODE_TIRUAN
```

**Harus terlihat:** seluruh alur tetap berjalan; jawaban diawali
`[MODE TIRUAN]`. Untuk `agen.py`, muncul keterangan bahwa mode tiruan tidak
mendukung tool-calling dan sistem jatuh ke satu panggilan pencarian langsung.

Sekarang indeks berisi embedding tiruan, sementara setelan aktif kembali
normal. Penjaga harus menangkapnya:

```powershell
python cek.py
```

**Harus terlihat:**

```
[GAGAL] PERINGATAN: indeks dibangun dengan setelan berbeda dari konfig aktif:
    - mode tiruan: indeks ya vs sekarang tidak
  Pencarian akan ACAK tanpa memunculkan galat apa pun (pelajaran F3).
```

dan laporan berakhir `BELUM SIAP.`

**Kenapa ini uji paling penting di bagian ini:** tanpa penjaga, sistem tetap
berjalan **tanpa galat apa pun** dengan indeks yang salah — hanya hasilnya
yang acak. Persis kegagalan yang paling sulit didiagnosis.

**Pulihkan indeks sungguhan sebelum lanjut:**

```powershell
python indeks.py --ulang
Get-Content ..\indeks_meta.json    # pastikan "mode_tiruan": false
```

## B11. Antarmuka Streamlit

```powershell
python -m streamlit run app.py --server.headless true --server.port 8501 --server.address 127.0.0.1
```

Di jendela lain:

```powershell
curl.exe -s http://127.0.0.1:8501/_stcore/health
```

**Harus menjawab:** `ok`

> **`--server.address 127.0.0.1` bukan hiasan.** Tanpa itu Streamlit terikat ke
> semua antarmuka (`::` / `0.0.0.0`), dan aplikasi berisi SOP internal dapat
> dibuka siapa pun di jaringan yang sama, tanpa kata sandi — sama persis dengan
> bahaya yang dicegah `127.0.0.1:` pada pemetaan port Docker di C5. Terbukti
> pada pengujian ini: `streamlit run app.py` polos meninggalkan proses yang
> mendengarkan di `::`.

**Hentikan dengan `Ctrl+C` di jendela pertama, lalu pastikan benar-benar mati:**

```powershell
Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
```

**Harus tidak menghasilkan apa-apa.** Kalau masih ada, hentikan prosesnya:

```powershell
Get-NetTCPConnection -LocalPort 8501 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

**Kenapa langkah ini wajib:** Streamlit host yang tertinggal di 8501 membuat
**C7 lulus palsu** — lihat catatan di sana.

## B12. Reranker (B4)

```powershell
python cari.py "Apa isi SE-12/2026?"
```

**Unduhan pertama sekitar 2 GB** dari Hugging Face — biarkan sampai selesai.
Peringatan `HF_TOKEN` dan symlink Windows tidak berbahaya.

**Harus terlihat perbedaan nyata:** pada blok `HYBRID`, SE-12 bisa berada di
peringkat bawah; setelah `HYBRID + SUSUN ULANG`, **SE-12 naik ke peringkat 1
dan 2**. Inilah sumbangan reranker terhadap ketepatan.

---

# Bagian C — Pengujian di Docker

Dijalankan dari folder `lab`:

```powershell
cd ..    # dari lab\src kembali ke lab
```

## C1. Docker tersedia

```powershell
docker --version
docker info --format "{{.ServerVersion}}"
```

Keduanya harus menjawab tanpa galat.

## C2. Bangun image

```powershell
docker build -t tanya-sop .
```

**Perkiraan waktu:** 3–6 menit pada build pertama.

**Harus berakhir:** `naming to docker.io/library/tanya-sop:latest done`.

## C3. Ukuran image masuk akal

```powershell
docker images tanya-sop
```

**Harus sekitar 1,4 GB.**

**Kalau mendekati 9,5 GB**, artinya `Dockerfile` memasang `requirements.txt`
penuh, bukan `requirements-docker.txt`. `sentence-transformers` menarik torch
+ CUDA sebesar **3,9 GB yang tidak pernah dipakai**, karena container menyetel
`PAKAI_RERANKER=0`. Periksa baris `COPY`/`RUN pip install` di `Dockerfile`.

## C4. Build context tidak membawa sampah

```powershell
docker build -t tanya-sop . --no-cache --progress=plain 2>&1 | Select-String "transferring context"
```

Atau lebih sederhana — pastikan `.dockerignore` memuat `chroma_db/`,
`potongan.pkl`, `.venv/`.

**Kenapa:** `.venv` bisa mencapai 1,7 GB. Lebih penting lagi, **indeks host
tidak boleh ikut ke image** — indeks terikat pada model embedding yang
membangunnya, dan menyalinnya adalah cara termudah menciptakan kegagalan
senyap F3 di lingkungan lain.

## C5. Jalankan container

```powershell
docker run -d --name tanya-sop-uji -p 127.0.0.1:8501:8501 tanya-sop
```

> **Perhatikan `127.0.0.1:` di depan pemetaan port.** Tanpa itu Docker
> mengikat ke `0.0.0.0`, dan aplikasi berisi SOP internal dapat dibuka siapa
> pun di jaringan yang sama, tanpa kata sandi. Terbukti pada pengujian ini:
> log Streamlit menampilkan `External URL` berisi alamat publik mesin.

## C6. Indeks terbangun di dalam container

```powershell
docker logs tanya-sop-uji
```

**Harus terlihat:** `Selesai. 29 vektor tersimpan di chroma_db/`

**Kenapa ini uji paling kritis di bagian Docker:** container tidak menjalankan
Ollama sendiri. Berhasilnya pembangunan indeks membuktikan container dapat
menjangkau Ollama di **host** lewat `host.docker.internal:11434`. Kalau macet
di sini, periksa `OLLAMA_BASE_URL`; di Linux tambahkan
`--add-host=host.docker.internal:host-gateway`.

**Perkiraan waktu:** 1–3 menit sebelum Streamlit siap.

## C7. Antarmuka hidup

**Pastikan dulu 8501 hanya dipegang container.** Kalau Streamlit dari B11 masih
hidup di host, langkah ini akan menjawab `ok` tanpa peduli container-nya jalan
atau tidak:

```powershell
Get-NetTCPConnection -LocalPort 8501 -State Listen |
  ForEach-Object { (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.OwningProcess)").CommandLine }
```

**Harus kosong, atau hanya menyebut proses Docker** — bukan `streamlit.exe run
app.py`. Bila muncul Streamlit host, hentikan lebih dulu (lihat B11).

```powershell
curl.exe -s http://127.0.0.1:8501/_stcore/health
```

**Harus menjawab:** `ok`

> **Uji ini mengukur "ada yang mendengarkan di 8501", bukan "container hidup".**
> Terbukti pada pengujian ini: setelah `docker rm -f tanya-sop-uji`, health
> check **tetap** menjawab `ok` — yang menjawab ternyata Streamlit host yang
> tertinggal dari B11. Health check hijau dengan **nol container berjalan**
> adalah lulus palsu yang sangat mudah terlewat. Kalau ragu, buktikan sumbernya:
> `docker logs tanya-sop-uji` harus menunjukkan Streamlit yang siap.

## C8. Binding jaringan benar-benar terbatas

```powershell
docker port tanya-sop-uji
Get-NetTCPConnection -LocalPort 8501 -State Listen | Select-Object LocalAddress,LocalPort
```

**Harus terlihat:** `8501/tcp -> 127.0.0.1:8501`, dan `LocalAddress` **hanya**
`127.0.0.1`.

**Gagal bila muncul** `0.0.0.0` atau `::` — berarti aplikasi terekspos ke
jaringan. Perhatikan: pesan `External URL` di log Streamlit **bukan** bukti
terekspos; Streamlit di dalam container tidak mengetahui pemetaan port Docker.
Yang menentukan adalah keluaran perintah di atas.

## C9. Fungsi RAG di dalam container

```powershell
docker exec tanya-sop-uji python jawab.py "Berapa panjang minimum kata sandi sistem internal?"
docker exec tanya-sop-uji python jawab.py "Berapa besaran tunjangan transportasi bulanan?"
```

**Harus:** yang pertama menjawab **14 karakter** dengan cakupan sitasi 100%;
yang kedua menolak dengan kalimat baku.

## C10. Agent di dalam container

```powershell
docker exec -e MODEL_CHAT=qwen3:4b tanya-sop-uji python agen.py "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
```

**Harus:** jejak pemanggilan alat terlihat, dan angkanya benar
(Rp 350.000 × 3 = Rp 1.050.000). Sekali lagi — jalurnya boleh berbeda dari
host, lihat catatan di B9.

## C11. Reranker absen ditangani dengan baik

```powershell
docker exec -e PAKAI_RERANKER=1 tanya-sop-uji python cari.py "Apa isi SE-12/2026?"
```

**Harus terlihat:**
`Reranker tidak tersedia (ModuleNotFoundError). Lab dilanjutkan tanpa penyusunan ulang.`
dan pencarian **tetap memberi hasil**.

**Kenapa:** image ramping sengaja tidak memuat `sentence-transformers`.
Menyetel `PAKAI_RERANKER=1` di sini tidak mengaktifkannya — yang diuji adalah
bahwa ketiadaan paket **tidak merusak apa pun**.

## C12. Pembersihan

```powershell
docker rm -f tanya-sop-uji
```

Bila ingin menghapus image juga:

```powershell
docker rmi tanya-sop
```

---

# Bagian D — Ringkasan hasil acuan

Diperoleh 26 Juli 2026. Pakai sebagai pembanding, bukan sebagai target yang
harus dipaksakan sama.

| Pengujian | Hasil acuan |
|---|---|
| `cek.py` | SIAP |
| `indeks.py` | 29 potongan, 29 vektor |
| `jawab.py` masa percobaan | "3 bulan", sitasi `[1]`, cakupan 100% |
| Keterangan letak sitasi | PDF `hal. 1` dst; Markdown `bagian: ...` |
| `jawab.py` kata sandi | **14 karakter** (SOP-05) |
| `jawab.py` tunjangan transportasi | menolak, kalimat baku |
| `nilai.py` recall@4 | 100% (20/20) di tiga konfigurasi |
| `nilai.py` penyaringan status | dicabut bocor 3/3 → 0/3 |
| `cari.py` + reranker | SE-12 naik ke peringkat 1–2 |
| `agen.py` | Rp 1.050.000 (jalur alat boleh bervariasi) |
| `cek.py` setelah mode tiruan | BELUM SIAP, menyebut ketidakcocokan |
| Streamlit host & container | health `ok` |
| Ukuran image Docker | 1,38 GB |
| Binding container | hanya `127.0.0.1` |

> **Catatan tentang angka recall.** 100% diperoleh pada korpus lab 29 potongan
> dengan `bge-m3`. Angka ini sah dikutip sebagai hasil lab, tetapi **bukan**
> klaim mutu umum — korpus kecil, dan pertanyaan ujinya disusun bersama
> dokumennya. Jangan memakainya sebagai janji kinerja pada korpus peserta.

---

# Bagian E — Kalau ada yang gagal

| Gejala | Langkah | Penyebab yang paling mungkin |
|---|---|---|
| `cek.py` gagal pada Ollama | B1 | Layanan mati — `ollama serve` |
| Recall jauh di bawah acuan | B8 | Indeks dibangun dengan embedding lain; `python indeks.py --ulang` |
| Cakupan sitasi 0% padahal ada rujukan | B4 | Model menulis `[n]`/`[n1]` — regresi prompt di `jawab.py` |
| Sitasi menampilkan `hal. 0` | B4, B7 | `util.lokasi` mencetak indeks mentah PyPDFLoader; nomor cetak = indeks + 1. **Jangan** ubah `set_uji.json` |
| Perbaikan kode tidak terlihat di container | C2 | Kode ikut ke dalam image — bangun ulang `docker build -t tanya-sop .` |
| Jawaban "8 karakter" | B5 | Penyaringan status tidak jalan; periksa metadata `status` di `muat.py` |
| Metrik penolakan selalu 0% | B8 | Kalimat penolakan tidak lagi persis sama dengan `konfig.TIDAK_DITEMUKAN` |
| Container macet saat bangun indeks | C6 | Tidak bisa menjangkau Ollama host; periksa `OLLAMA_BASE_URL` |
| Image mendekati 9,5 GB | C3 | `Dockerfile` memakai `requirements.txt`, bukan `requirements-docker.txt` |
| `Get-NetTCPConnection` menampilkan `0.0.0.0` | C8 | Pemetaan port tanpa awalan `127.0.0.1:` |
| C7 menjawab `ok` padahal container mati | C7, B11 | Streamlit host dari B11 masih memegang 8501 — lulus palsu. Hentikan, lalu ulangi |
| Streamlit host terikat `::` | B11 | Dijalankan tanpa `--server.address 127.0.0.1` — aplikasi terekspos ke jaringan |
