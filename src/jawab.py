# -*- coding: utf-8 -*-
"""Menyusun jawaban ber-sitasi dari dokumen internal.

    python jawab.py "pertanyaan Anda"

Isinya ada di rag_lab/pembangkitan/; berkas ini hanya titik masuknya.
"""
import sys

from rag_lab.perintah.jawab import utama

if __name__ == "__main__":
    sys.exit(utama())
