# -*- coding: utf-8 -*-
"""Pencarian: vektor, hybrid, dan penyusunan ulang — ditampilkan berdampingan.

    python cari.py "pertanyaan Anda"
    python cari.py --semua "pertanyaan Anda"    tanpa penyaring status

Isinya ada di rag_lab/pengambilan/; berkas ini hanya titik masuknya.
"""
import sys

from rag_lab.perintah.cari import utama

if __name__ == "__main__":
    sys.exit(utama())
