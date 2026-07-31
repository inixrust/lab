# -*- coding: utf-8 -*-
"""Evaluasi: mengubah 'rasanya lebih baik' menjadi angka yang bisa dibandingkan.

    python nilai.py              evaluasi retrieval + penyaringan status
    python nilai.py --penolakan  ikut menguji kemampuan menolak (butuh model)

Isinya ada di rag_lab/evaluasi/; berkas ini hanya titik masuknya.
"""
import sys

from rag_lab.perintah.nilai import utama

if __name__ == "__main__":
    sys.exit(utama())
