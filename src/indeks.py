# -*- coding: utf-8 -*-
"""Membangun indeks (langkah 3-4: embedding dan penyimpanan).

    python indeks.py            bangun indeks
    python indeks.py --ulang    hapus indeks lama lebih dulu

Isinya ada di rag_lab/pengindeksan/; berkas ini hanya titik masuknya.
"""
import sys

from rag_lab.perintah.indeks import utama

if __name__ == "__main__":
    sys.exit(utama())
