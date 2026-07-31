# -*- coding: utf-8 -*-
"""Satu tempat untuk semua setelan.

Kalau ada yang perlu diubah selama lab, ubahnya di sini — bukan tersebar di
banyak berkas. Ini juga berlaku di sistem sungguhan: setelan yang berserakan
adalah sumber kegagalan senyap yang dibahas di modul F3.

Modul ini sengaja hanya memakai pustaka bawaan Python. `cek.py` membacanya
sebelum memastikan paket lain terpasang — kalau di sini ada `import langchain`,
pemeriksaan kesiapan justru gagal pada mesin yang paling membutuhkannya.
"""
from __future__ import annotations

import os
from pathlib import Path

# Letak berkas ini: lab/src/rag_lab/konfig.py
#   parents[0] = rag_lab   parents[1] = src   parents[2] = lab
# AKAR harus menunjuk folder lab/, karena dokumen, indeks, dan set uji ada di
# sana — bukan di dalam src/. Sesuaikan angkanya bila berkas ini dipindahkan.
AKAR: Path = Path(__file__).resolve().parents[2]


def _bendera(nama: str, bawaan: str = "0") -> bool:
    """Baca variabel lingkungan sebagai ya/tidak.

    Cara menyetelnya per-terminal (PowerShell/cmd/bash) ada di
    PANDUAN-PESERTA.md. Nilai yang dianggap "ya": 1, true, ya, y.
    """
    return os.getenv(nama, bawaan).strip().lower() in {"1", "true", "ya", "y"}


# ---------------------------------------------------------------- model
# Sesuaikan dengan RAM mesin Anda. Lihat reference/0002-setup-ollama.html
#   RAM  8 GB  -> "qwen3:4b"
#   RAM 16 GB  -> "qwen3:8b"
#   RAM 64 GB  -> "gpt-oss:20b"
MODEL_CHAT: str = os.getenv("MODEL_CHAT", "qwen3:8b")

# JANGAN diubah tanpa membangun ulang indeks. Lihat modul F3.
# bge-m3 dipilih karena mendukung bahasa Indonesia; nomic-embed-text tidak.
MODEL_EMBEDDING: str = os.getenv("MODEL_EMBEDDING", "bge-m3")

# Alamat layanan Ollama. Kosong = bawaan langchain (http://localhost:11434).
# Perlu diisi hanya saat aplikasi berjalan di dalam Docker, karena "localhost"
# di dalam container menunjuk container itu sendiri, bukan Ollama di host.
# Lihat DEPLOY.md. Contoh isi: http://host.docker.internal:11434
OLLAMA_URL: str = os.getenv("OLLAMA_BASE_URL", "")
OLLAMA_URL_BAWAAN: str = "http://localhost:11434"

# Reranker berjalan lewat sentence-transformers, bukan Ollama.
# Berat untuk RAM 8 GB — matikan lewat variabel PAKAI_RERANKER=0.
MODEL_RERANKER: str = "BAAI/bge-reranker-v2-m3"
PAKAI_RERANKER: bool = _bendera("PAKAI_RERANKER", "1")

# ------------------------------------------------------------- pemotongan
UKURAN_POTONGAN: int = 900
TUMPANG_TINDIH: int = 130

# Urutan pemisah menentukan mutu chunking. Penanda pasal diletakkan paling
# atas agar pemotongan mengikuti struktur dokumen, bukan jumlah karakter.
PEMISAH_PERATURAN: list[str] = ["\nPasal ", "\nBAB ", "\n\n", "\n", ". ", " ", ""]
PEMISAH_PROSA: list[str] = ["\n\n", "\n", ". ", " ", ""]

# Jenis dokumen (= nama subfolder di dokumen/) yang dipotong di batas pasal.
JENIS_BERPASAL: frozenset[str] = frozenset({"sop", "edaran"})

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
JUMLAH_KANDIDAT: int = 10
JUMLAH_AKHIR: int = 4         # dikirim ke model setelah disusun ulang

# ------------------------------------------------------------- lokasi
DOKUMEN: Path = AKAR / "dokumen"
INDEKS: Path = AKAR / "chroma_db"
POTONGAN_TERSIMPAN: Path = AKAR / "potongan.pkl"
SET_UJI: Path = AKAR / "set_uji.json"
NAMA_KOLEKSI: str = "korpus_ncs"

# Sidik jari indeks: mencatat DENGAN APA indeks dibangun (lihat sidik_jari.py).
# Dipakai untuk menolak diam-diamnya kegagalan F3 — indeks yang dibangun
# dengan embedding berbeda memberi hasil acak tanpa galat apa pun.
META: Path = AKAR / "indeks_meta.json"

# ------------------------------------------------------------- kalimat baku
# Dipakai di prompt DAN di pengukuran. Karena dicocokkan sebagai teks persis,
# ia harus didefinisikan di SATU tempat saja — kalau tidak, metrik penolakan
# akan selalu melaporkan nol tanpa ada yang menyadari.
TIDAK_DITEMUKAN: str = "Informasi ini tidak ditemukan dalam dokumen yang tersedia."

# ------------------------------------------------------------- kosakata status
# Status dokumen dipakai lintas modul (pengindeksan, pengambilan, evaluasi).
# Disatukan di sini agar mengubahnya tidak menuntut berburu string yang sama.
STATUS_BERLAKU: str = "berlaku"
STATUS_DICABUT: str = "dicabut"

# Penanda pada NAMA BERKAS yang menyatakan dokumen sudah dicabut. Di sistem
# sungguhan status ini datang dari basis data dokumen, bukan dari nama berkas.
PENANDA_DICABUT: str = "DICABUT"

# Ambang cakupan sitasi. Di bawah nilai ini, jawaban ditandai untuk diperiksa
# manual (dipakai di pembangkitan dan antarmuka — satu sumber, bukan dua angka).
AMBANG_CAKUPAN: float = 0.7

# ------------------------------------------------------------- mode tiruan
# Untuk berjaga-jaga bila Ollama bermasalah di tengah kelas.
# Aktifkan lewat variabel MODE_TIRUAN=1 (cara per-terminal ada di PANDUAN-PESERTA.md).
# Embedding diganti fungsi hash deterministik — mutunya buruk, tapi seluruh
# alur tetap berjalan sehingga peserta bisa mengikuti pelajarannya.
MODE_TIRUAN: bool = _bendera("MODE_TIRUAN")


def alamat_ollama() -> str:
    """Alamat Ollama yang benar-benar dipakai — untuk ditampilkan ke peserta."""
    return OLLAMA_URL or OLLAMA_URL_BAWAAN


def ringkas() -> None:
    """Tampilkan setelan aktif. Berguna saat mendiagnosis masalah peserta."""
    print("  model chat      :", MODEL_CHAT)
    print("  model embedding :", MODEL_EMBEDDING)
    print("  reranker        :", MODEL_RERANKER if PAKAI_RERANKER else "dimatikan")
    print("  potongan        :", f"{UKURAN_POTONGAN} karakter, tumpang tindih {TUMPANG_TINDIH}")
    print("  kandidat -> akhir:", f"{JUMLAH_KANDIDAT} -> {JUMLAH_AKHIR}")
    if MODE_TIRUAN:
        print("  MODE TIRUAN AKTIF — hasil tidak mencerminkan mutu sebenarnya")
