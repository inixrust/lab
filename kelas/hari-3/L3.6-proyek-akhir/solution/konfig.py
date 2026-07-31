# -*- coding: utf-8 -*-
"""Satu tempat untuk semua setelan.

Kalau ada yang perlu diubah selama lab, ubahnya di sini — bukan tersebar di
banyak berkas. Ini juga berlaku di sistem sungguhan: setelan yang berserakan
adalah sumber kegagalan senyap yang dibahas di modul F3.
"""
import os
from pathlib import Path

AKAR = Path(__file__).resolve().parent

# ---------------------------------------------------------------- model
# Sesuaikan dengan RAM mesin Anda. Lihat reference/0002-setup-ollama.html
#   RAM  8 GB  -> "qwen3:4b"
#   RAM 16 GB  -> "qwen3:8b"
#   RAM 64 GB  -> "gpt-oss:20b"
MODEL_CHAT = os.getenv("MODEL_CHAT", "qwen3:8b")

# JANGAN diubah tanpa membangun ulang indeks. Lihat modul F3.
# bge-m3 dipilih karena mendukung bahasa Indonesia; nomic-embed-text tidak.
MODEL_EMBEDDING = os.getenv("MODEL_EMBEDDING", "bge-m3")

# Alamat layanan Ollama. Kosong = bawaan langchain (http://localhost:11434).
# Perlu diisi hanya saat aplikasi berjalan di dalam Docker, karena "localhost"
# di dalam container menunjuk container itu sendiri, bukan Ollama di host.
# Lihat DEPLOY.md. Contoh isi: http://host.docker.internal:11434
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "")

# Reranker berjalan lewat sentence-transformers, bukan Ollama.
# Berat untuk RAM 8 GB — matikan lewat variabel PAKAI_RERANKER=0.
# Cara menyetel per-terminal (PowerShell/cmd/bash) ada di PANDUAN-PESERTA.md.
MODEL_RERANKER = "BAAI/bge-reranker-v2-m3"
PAKAI_RERANKER = os.getenv("PAKAI_RERANKER", "1") == "1"

# ------------------------------------------------------------- pemotongan
# PENINGKATAN 3 — ukuran potongan & pemisah disetel ulang setelah korpus
# bertambah (peningkatan 1). Dua hal berubah dari garis dasar:
#
#   a. ukuran 900 -> 700, tumpang tindih 130 -> 120.
#      Dokumen tambahan berisi tabel, dan tabel yang diekstrak PyPDFLoader
#      menjadi banyak baris pendek. Potongan 900 karakter menelan satu tabel
#      penuh BESERTA pasal di sekitarnya, sehingga satu potongan memuat dua
#      topik dan skor kemiripannya menjadi kabur.
#
#   b. pemisah ditulis sebagai REGEX, bukan teks tetap.
#      "\nPasal " hanya cocok bila ada spasi sesudahnya; penanda ayat "(1) "
#      tidak tertangkap sama sekali. Dengan regex, batas pasal, bab, dan ayat
#      semuanya menjadi titik potong yang sah.
#
# Keduanya WAJIB diukur, bukan diyakini — lihat PENINGKATAN.md untuk angka
# sebelum/sesudah pada set uji yang sama. Nilainya sengaja bisa disetel lewat
# variabel lingkungan supaya penyapuan (sweep) tidak menuntut penyuntingan
# berkas:  UKURAN_POTONGAN=500 python indeks.py --ulang && python nilai.py
UKURAN_POTONGAN = int(os.getenv("UKURAN_POTONGAN", "700"))
TUMPANG_TINDIH = int(os.getenv("TUMPANG_TINDIH", "120"))

# Urutan pemisah menentukan mutu chunking. Penanda pasal diletakkan paling
# atas agar pemotongan mengikuti struktur dokumen, bukan jumlah karakter.
#
# Ditulis sebagai regex (lihat PEMISAH_REGEX di bawah). Perhatikan ". " yang
# harus ditulis "\. " — titik adalah karakter khusus di regex, dan lupa
# melolosinya membuat pemotong memenggal di SEMBARANG karakter.
PEMISAH_PERATURAN = [r"\nPasal \d+", r"\nBAB [IVXLC]+", r"\n\(\d+\) ",
                     r"\n\n", r"\n", r"\. ", " ", ""]
PEMISAH_PROSA = [r"\n\n", r"\n", r"\. ", " ", ""]
PEMISAH_REGEX = True

# Jenis dokumen yang berstruktur pasal, jadi dipotong dengan PEMISAH_PERATURAN.
# Dikumpulkan di sini supaya menambah jenis baru (mis. "kontrak" pada
# peningkatan 5) cukup satu baris, bukan berburu tuple di dalam muat.py.
JENIS_BERPASAL = {"sop", "edaran", "kontrak"}

# ------------------------------------------------------------- pencarian
# Jumlah kandidat yang diambil TIAP pencari sebelum digabung dengan RRF.
#
# Nilai ini HARUS sebanding dengan besar korpus. Korpus lab hanya 29 potongan;
# mengambil 20 kandidat berarti hampir seluruh korpus ikut masuk, dan RRF
# kehilangan daya pilahnya — dokumen yang peringkat tengah di kedua daftar
# justru mengalahkan dokumen yang peringkat satu di salah satu daftar.
#
# Terbukti pada set uji lab: kandidat <= 10 memberi recall 100%,
# kandidat 15-20 turun menjadi 95%. Untuk korpus puluhan ribu potongan,
# 50 sampai 100 baru masuk akal.
#
# Aturan praktis: sekitar sepertiga korpus untuk korpus kecil,
# 50-100 untuk korpus besar.
#
# PENINGKATAN 1 + 3 — DIUKUR, LALU DIKEMBALIKAN. Ini catatan kegagalan, dan
# sengaja ditinggalkan di sini utuh.
#
# Korpus tumbuh dari 29 menjadi 68 potongan (peningkatan 1), jadi menurut
# aturan sepertiga di atas angka ini seharusnya naik ke sekitar 18. Perubahan
# itu dipasang, lalu diukur pada set uji yang sama — dan hasilnya kebalikannya:
#
#     kandidat   recall@4 hybrid   recall@4 hybrid+susun ulang
#         8          100%                    100%
#        10           98%                    100%
#        12           95%                    100%
#        14           93%                    100%
#        18           93%                    100%
#        24           93%                    100%
#
# Menaikkan kandidat justru MEMPERBURUK tahap hybrid, persis seperti yang
# sudah diperingatkan paragraf di atas: pada korpus sekecil ini, mengambil 18
# dari 68 potongan membuat RRF kehilangan daya pilahnya. "Sepertiga korpus"
# ternyata aturan praktis yang salah di sini, dan aturan praktis kalah oleh
# pengukuran.
#
# Nilainya dikembalikan ke 10, bukan diturunkan ke 8: bedanya hanya satu
# pertanyaan dari 41, terlalu tipis untuk dijadikan dasar. Menyetel angka ke
# nilai yang kebetulan sempurna pada satu set uji adalah cara paling halus
# untuk menipu diri sendiri.
JUMLAH_KANDIDAT = int(os.getenv("JUMLAH_KANDIDAT", "10"))
JUMLAH_AKHIR = int(os.getenv("JUMLAH_AKHIR", "4"))   # dikirim ke model setelah disusun ulang

# ------------------------------------------------------------- lokasi
DOKUMEN = AKAR / "dokumen"
INDEKS = AKAR / "chroma_db"
POTONGAN_TERSIMPAN = AKAR / "potongan.pkl"
SET_UJI = AKAR / "set_uji.json"
NAMA_KOLEKSI = "korpus_ncs"

# Sidik jari indeks: mencatat DENGAN APA indeks dibangun (lihat meta.py).
# Dipakai untuk menolak diam-diamnya kegagalan F3 — indeks yang dibangun
# dengan embedding berbeda memberi hasil acak tanpa galat apa pun.
META = AKAR / "indeks_meta.json"

# ------------------------------------------------------------- kalimat baku
# Dipakai di prompt DAN di pengukuran. Karena dicocokkan sebagai teks persis,
# ia harus didefinisikan di SATU tempat saja — kalau tidak, metrik penolakan
# akan selalu melaporkan nol tanpa ada yang menyadari.
TIDAK_DITEMUKAN = "Informasi ini tidak ditemukan dalam dokumen yang tersedia."

# ------------------------------------------------------------- kosakata status
# Status dokumen dipakai lintas berkas (muat, cari, jawab, nilai). Disatukan di
# sini agar mengubahnya tidak menuntut berburu string yang sama di banyak tempat.
STATUS_BERLAKU = "berlaku"
STATUS_DICABUT = "dicabut"

# Ambang cakupan sitasi. Di bawah nilai ini, jawaban ditandai untuk diperiksa
# manual (dipakai di jawab.py dan app.py — satu sumber, bukan dua angka lepas).
AMBANG_CAKUPAN = float(os.getenv("AMBANG_CAKUPAN", "0.7"))

# ------------------------------------------------------------- eskalasi
# PENINGKATAN 9 — kebijakan "kapan manusia dilibatkan", dipisahkan dari ambang
# tampilan di atas.
#
# Sebelumnya keduanya satu angka (AMBANG_CAKUPAN = 0,7) dan dipakai untuk dua
# keputusan yang sangat berbeda: MENAMPILKAN peringatan kuning di layar, dan
# MENGHENTIKAN alur untuk menunggu penyelia. Menyatukannya terdengar rapi,
# tetapi berarti menurunkan kebisingan peringatan otomatis melonggarkan pagar
# eskalasi — dua hal yang seharusnya bisa disetel sendiri-sendiri.
#
# Angka pembuka di bawah ini bukan tebakan yang harus dipercaya; ia titik awal
# yang HARUS diukur ulang di korpus Anda sendiri:
#     python alur.py --set-uji --otomatis setuju
#     python jejak.py
# Bandingkan "rasio eskalasi" sebelum dan sesudah menyetelnya. Angka eskalasi
# yang terlalu tinggi melatih penyelia menekan 'setuju' tanpa membaca — dan
# pagar yang selalu disetujui sama saja dengan tidak ada pagar.
AMBANG_ESKALASI = float(os.getenv("AMBANG_ESKALASI", "0.5"))

# Ambang dukungan sitasi (lihat simpul `dukungan` di alur.py — peningkatan 8).
# Cakupan hanya menghitung ADANYA penanda [n]; dukungan memeriksa apakah
# potongan yang ditunjuk benar-benar memuat kata-kata jawabannya.
AMBANG_DUKUNGAN = float(os.getenv("AMBANG_DUKUNGAN", "0.35"))

# Jenis dokumen yang jawabannya SELALU diperiksa manusia, berapa pun cakupannya.
# Ini kebijakan organisasi, bukan urusan mutu model: nilai kontrak salah kutip
# lebih mahal daripada nomor pasal salah kutip.
ESKALASI_JENIS = {j.strip() for j in os.getenv("ESKALASI_JENIS", "kontrak").split(",")
                  if j.strip()}

# Sitasi hantu (menunjuk potongan yang tidak ada) selalu dieskalasi. Dibiarkan
# sebagai saklar agar bisa dimatikan saat mengukur pengaruh ambang saja.
ESKALASI_SITASI_HANTU = os.getenv("ESKALASI_SITASI_HANTU", "1") == "1"

# Peran yang TIDAK dieskalasi karena jenis dokumen — orangnya sendiri yang
# menjadi penyetuju. Menghentikan alur untuk meminta persetujuan Direktur atas
# jawaban yang ia baca sendiri bukan pengamanan, melainkan gangguan; dan
# gangguan yang berulang adalah cara tercepat membuat orang menyetujui apa pun
# tanpa membaca.
#
# Perhatikan batasnya: yang dilewati HANYA pemicu jenis dokumen. Sitasi hantu,
# cakupan rendah, dan dukungan rendah tetap dieskalasi untuk semua peran —
# itu soal mutu jawaban, dan jabatan tidak memperbaiki mutu jawaban.
PERAN_TANPA_ESKALASI = {p.strip() for p in
                        os.getenv("PERAN_TANPA_ESKALASI", "pimpinan").split(",")
                        if p.strip()}

# ------------------------------------------------------------- pagar masukan
# PENINGKATAN 8 — simpul `saring_masukan` di alur.py. Pertanyaan yang ditolak
# di sini tidak pernah menyentuh indeks maupun model: nol token, nol detik.
PANJANG_MIN_PERTANYAAN = int(os.getenv("PANJANG_MIN_PERTANYAAN", "8"))
PANJANG_MAKS_PERTANYAAN = int(os.getenv("PANJANG_MAKS_PERTANYAAN", "600"))

# ------------------------------------------------------------- singgahan
# Cache jawaban. Dimatikan lewat PAKAI_SINGGAHAN=0 saat mengukur waktu asli —
# kalau lupa, angka latensi Anda hanya mengukur kecepatan dict Python.
PAKAI_SINGGAHAN = os.getenv("PAKAI_SINGGAHAN", "1") == "1"
SINGGAHAN_MAKS = 256          # jumlah jawaban tersimpan sebelum yang tertua dibuang

# SENGAJA TIDAK AMAN — hanya untuk demo L3.4. Bila diisi 1, kunci cache dibuat
# dari pertanyaannya saja, tanpa hak akses, sehingga jawaban milik pimpinan
# bisa terbaca oleh staf. Lihat singgahan.py.
SINGGAHAN_TANPA_IZIN = os.getenv("SINGGAHAN_TANPA_IZIN", "0") == "1"

# ------------------------------------------------------------- jejak
# Satu baris JSON per pertanyaan yang dilayani. Ini bahan bakar observability:
# tanpa catatan per langkah, satu-satunya cara mendiagnosis keluhan "jawabannya
# salah kemarin sore" adalah menebak.
# Berkasnya bisa diarahkan lewat variabel lingkungan. Ini yang membuat
# pengukuran "sebelum" dan "sesudah" pada peningkatan 9 bisa disimpan
# terpisah, lalu dibandingkan — bukan tercampur di satu berkas dan
# menghasilkan rata-rata yang tidak berarti apa-apa:
#     JEJAK=jejak-sebelum.jsonl python alur.py --set-uji
#     JEJAK=jejak-sebelum.jsonl python jejak.py
JEJAK = Path(os.getenv("JEJAK", "")) if os.getenv("JEJAK") else AKAR / "jejak.jsonl"
PAKAI_JEJAK = os.getenv("PAKAI_JEJAK", "1") == "1"

# ------------------------------------------------------------- mode tiruan
# Untuk berjaga-jaga bila Ollama bermasalah di tengah kelas.
# Aktifkan lewat variabel MODE_TIRUAN=1 (cara per-terminal ada di PANDUAN-PESERTA.md).
# Embedding diganti fungsi hash deterministik — mutunya buruk, tapi seluruh
# alur tetap berjalan sehingga peserta bisa mengikuti pelajarannya.
MODE_TIRUAN = os.getenv("MODE_TIRUAN", "0") == "1"


def ringkas():
    """Tampilkan setelan aktif. Berguna saat mendiagnosis masalah peserta."""
    print("  model chat      :", MODEL_CHAT)
    print("  model embedding :", MODEL_EMBEDDING)
    print("  reranker        :", MODEL_RERANKER if PAKAI_RERANKER else "dimatikan")
    print("  potongan        :", f"{UKURAN_POTONGAN} karakter, tumpang tindih {TUMPANG_TINDIH}")
    print("  kandidat -> akhir:", f"{JUMLAH_KANDIDAT} -> {JUMLAH_AKHIR}")
    # Ambang eskalasi ikut dicetak: ia menentukan berapa sering penyelia
    # dipanggil, dan angka itu harus terlihat saat membandingkan hasil ukur.
    print("  ambang cakupan  :", f"{AMBANG_CAKUPAN:.2f} (peringatan tampilan)")
    print("  ambang eskalasi :", f"cakupan < {AMBANG_ESKALASI:.2f}, "
                                 f"dukungan < {AMBANG_DUKUNGAN:.2f}, "
                                 f"jenis {sorted(ESKALASI_JENIS) or '-'}")
    if MODE_TIRUAN:
        print("  MODE TIRUAN AKTIF — hasil tidak mencerminkan mutu sebenarnya")
