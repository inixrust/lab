# -*- coding: utf-8 -*-
"""python jawab.py "pertanyaan" — jawaban ber-sitasi dari dokumen internal.

Potongan yang diambil ditampilkan LEBIH DULU, di atas jawaban. Itu disengaja:
kebiasaan membaca potongan sebelum membaca jawaban adalah yang memisahkan
orang yang bisa memperbaiki sistem RAG dari orang yang hanya bisa
mengganti-ganti prompt (modul F3).
"""
from __future__ import annotations

import argparse
from typing import Sequence

from ..pembangkitan import jawab
from ._argumen import gabung_pertanyaan, tambah_pertanyaan


def utama(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jawab.py", description=__doc__)
    tambah_pertanyaan(parser)
    parser.add_argument(
        "-k", type=int, default=None,
        help="jumlah potongan yang dikirim ke model (bawaan: konfig.JUMLAH_AKHIR)",
    )
    argumen = parser.parse_args(argv)
    tanya = gabung_pertanyaan(argumen.pertanyaan)

    print(f"Pertanyaan: {tanya}\n")
    isi, _, laporan = jawab(tanya, k=argumen.k)
    print("\nJAWABAN:")
    print(isi)
    print(f"\n(cakupan sitasi {laporan.cakupan:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
