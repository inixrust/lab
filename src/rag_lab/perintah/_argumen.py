# -*- coding: utf-8 -*-
"""Pembantu kecil yang dipakai beberapa perintah."""
from __future__ import annotations

import argparse
from typing import Sequence

# Pertanyaan bawaan bila peserta menjalankan perintah tanpa argumen. Sengaja
# satu pertanyaan yang jawabannya jelas ada di korpus, supaya percobaan
# pertama selalu memperlihatkan sistem yang bekerja.
PERTANYAAN_BAWAAN = "Berapa lama masa percobaan karyawan baru?"


def tambah_pertanyaan(parser: argparse.ArgumentParser) -> None:
    """Daftarkan argumen pertanyaan bebas-spasi (boleh tanpa tanda kutip)."""
    parser.add_argument(
        "pertanyaan",
        nargs="*",
        help=f'pertanyaan Anda (bawaan: "{PERTANYAAN_BAWAAN}")',
    )


def gabung_pertanyaan(bagian: Sequence[str]) -> str:
    """Satukan potongan argumen menjadi satu pertanyaan."""
    return " ".join(bagian).strip() or PERTANYAAN_BAWAAN
