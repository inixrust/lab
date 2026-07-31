# -*- coding: utf-8 -*-
"""python indeks.py — bangun indeks. `--ulang` untuk membangun dari nol.

Ingat pelajaran F3: mengganti MODEL_EMBEDDING atau ukuran potongan di
konfig.py mengharuskan pengindeksan diulang. Kalau tidak, sistem tetap
berjalan tanpa galat apa pun — hanya hasil pencariannya yang menjadi acak.
"""
from __future__ import annotations

import argparse
from typing import Sequence

from ..pengindeksan import bangun


def utama(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="indeks.py", description=__doc__)
    parser.add_argument(
        "--ulang", action="store_true",
        help="hapus indeks lama lebih dulu, lalu bangun dari nol",
    )
    argumen = parser.parse_args(argv)

    bangun(ulang=argumen.ulang)
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
