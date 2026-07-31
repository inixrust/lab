# -*- coding: utf-8 -*-
"""Memuat dan memotong dokumen (langkah 1-2), lalu tunjukkan satu contoh.

    python muat.py

Isinya ada di rag_lab/pengindeksan/; berkas ini hanya titik masuknya.
"""
import sys

from rag_lab.perintah.muat import utama

if __name__ == "__main__":
    sys.exit(utama())
