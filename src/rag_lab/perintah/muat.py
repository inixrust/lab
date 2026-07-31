# -*- coding: utf-8 -*-
"""python muat.py — memuat dan memotong dokumen, lalu tunjukkan satu contoh.

Tidak menyentuh indeks sama sekali. Gunanya melihat HASIL PEMOTONGAN sebelum
menghabiskan waktu membuat embedding — perhatikan awalan
"[sumber > bab > bagian]" pada isi potongan (pelajaran B2).
"""
from __future__ import annotations

import argparse
from typing import Sequence

from ..pengindeksan import muat_semua

PANJANG_CONTOH = 400
LEBAR_GARIS = 66


def utama(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="muat.py", description=__doc__)
    parser.add_argument(
        "--nomor", type=int, default=1,
        help="potongan ke berapa yang ditampilkan sebagai contoh (bawaan: 1)",
    )
    argumen = parser.parse_args(argv)

    print("Memuat dan memotong dokumen...")
    potongan = muat_semua()

    indeks = max(1, min(argumen.nomor, len(potongan))) - 1
    contoh = potongan[indeks]
    print(f"\nContoh potongan ke-{indeks + 1} dari {len(potongan)}:")
    print("-" * LEBAR_GARIS)
    print(contoh.page_content[:PANJANG_CONTOH])
    print("-" * LEBAR_GARIS)
    print("metadata:", contoh.metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
