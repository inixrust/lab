# -*- coding: utf-8 -*-
"""python agen.py "pertanyaan" — agent yang memilih & memanggil alat sendiri.

    python agen.py "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
    python agen.py "Berapa panjang minimum kata sandi sistem internal?"

Pertanyaan pertama membutuhkan DUA alat: cari besaran hariannya lebih dulu,
lalu kalikan. Perhatikan baris [langkah n] — itulah 'jalan pikiran' agent.
"""
from __future__ import annotations

import argparse
from typing import Sequence

from ..agen import MAKS_LANGKAH, jalankan_agen
from ._argumen import tambah_pertanyaan

PERTANYAAN_AGEN = "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"


def utama(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agen.py", description=__doc__)
    tambah_pertanyaan(parser)
    parser.add_argument(
        "--maks-langkah", type=int, default=MAKS_LANGKAH,
        help=f"batas putaran lingkaran agent (bawaan: {MAKS_LANGKAH})",
    )
    argumen = parser.parse_args(argv)
    tanya = " ".join(argumen.pertanyaan).strip() or PERTANYAAN_AGEN

    print(f"Pertanyaan: {tanya}\n")
    jawaban = jalankan_agen(tanya, maks_langkah=argumen.maks_langkah)
    print("\nJAWABAN AGEN:")
    print(jawaban)
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
