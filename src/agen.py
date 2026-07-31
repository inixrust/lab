# -*- coding: utf-8 -*-
"""Agent minimal, sepenuhnya on-premise — modul A2 / A6.

    python agen.py "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
    python agen.py "Berapa panjang minimum kata sandi sistem internal?"

Isinya ada di rag_lab/agen/; berkas ini hanya titik masuknya.
"""
import sys

from rag_lab.perintah.agen import utama

if __name__ == "__main__":
    sys.exit(utama())
