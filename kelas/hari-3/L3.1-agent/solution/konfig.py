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
UKURAN_POTONGAN = 900
TUMPANG_TINDIH = 130

# Urutan pemisah menentukan mutu chunking. Penanda pasal diletakkan paling
# atas agar pemotongan mengikuti struktur dokumen, bukan jumlah karakter.
PEMISAH_PERATURAN = ["\nPasal ", "\nBAB ", "\n\n", "\n", ". ", " ", ""]
PEMISAH_PROSA = ["\n\n", "\n", ". ", " ", ""]

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
JUMLAH_KANDIDAT = 10
JUMLAH_AKHIR = 4         # dikirim ke model setelah disusun ulang

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
AMBANG_CAKUPAN = 0.7

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
    if MODE_TIRUAN:
        print("  MODE TIRUAN AKTIF — hasil tidak mencerminkan mutu sebenarnya")
