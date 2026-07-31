# -*- coding: utf-8 -*-
"""Satu tempat untuk semua setelan — versi Hari 1 (pipeline dasar).

Sengaja ringkas: Hari 1 baru membangun pipeline RAG yang UTUH (muat -> potong ->
embed -> simpan -> cari -> jawab), belum yang benar & terukur. Setelan untuk
hybrid, reranker, penyaringan status, dan evaluasi baru ditambahkan di Hari 2.
"""
import os
from pathlib import Path

AKAR = Path(__file__).resolve().parent

# ---------------------------------------------------------------- model
#   RAM  8 GB  -> "qwen3:4b"
#   RAM 16 GB  -> "qwen3:8b"
MODEL_CHAT = os.getenv("MODEL_CHAT", "qwen3:8b")

# bge-m3 mendukung bahasa Indonesia; nomic-embed-text tidak. JANGAN diubah tanpa
# membangun ulang indeks (pelajaran F3 — dibuktikan di latihan L1.4).
MODEL_EMBEDDING = os.getenv("MODEL_EMBEDDING", "bge-m3")

# Kosong = bawaan langchain (http://localhost:11434). Diisi hanya di dalam Docker.
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "")

# ------------------------------------------------------------- pemotongan
UKURAN_POTONGAN = 900
TUMPANG_TINDIH = 130
# Hari 1 memakai SATU strategi pemotongan untuk semua dokumen. Di Hari 2 kita
# lihat kenapa peraturan berpasal butuh pemisah sendiri.
PEMISAH = ["\n\n", "\n", ". ", " ", ""]

# ------------------------------------------------------------- pencarian
JUMLAH_AKHIR = 4          # jumlah potongan yang dikirim ke model

# ------------------------------------------------------------- lokasi
DOKUMEN = AKAR / "dokumen"
INDEKS = AKAR / "chroma_db"
SET_UJI = AKAR / "set_uji.json"
NAMA_KOLEKSI = "korpus_ncs"

# ------------------------------------------------------------- kalimat baku
TIDAK_DITEMUKAN = "Informasi ini tidak ditemukan dalam dokumen yang tersedia."

# ------------------------------------------------------------- mode tiruan
# Bila Ollama bermasalah, MODE_TIRUAN=1 mengganti embedding dengan fungsi hash
# deterministik — mutunya buruk, tapi seluruh alur tetap berjalan. Justru berguna
# di L1.4: bandingkan hasilnya dengan bge-m3 untuk melihat sumbangan embedding.
MODE_TIRUAN = os.getenv("MODE_TIRUAN", "0") == "1"


def ringkas():
    print("  model chat      :", MODEL_CHAT)
    print("  model embedding :", MODEL_EMBEDDING)
    print("  potongan        :", f"{UKURAN_POTONGAN} karakter, tumpang tindih {TUMPANG_TINDIH}")
    print("  diambil         :", f"{JUMLAH_AKHIR} potongan")
    if MODE_TIRUAN:
        print("  MODE TIRUAN AKTIF — hasil tidak mencerminkan mutu sebenarnya")
