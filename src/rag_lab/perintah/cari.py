# -*- coding: utf-8 -*-
"""python cari.py "pertanyaan" — bandingkan tiga cara mencari.

    python cari.py "pertanyaan Anda"           bawaan: hanya dokumen berlaku
    python cari.py --semua "pertanyaan Anda"   tanpa penyaring status (B3)

Ketiga blok hasil ditampilkan berurutan supaya perbedaannya terlihat langsung:
vektor saja, hybrid, lalu hybrid dengan penyusunan ulang.
"""
from __future__ import annotations

import argparse
from typing import Sequence

from .. import konfig, tampilan
from ..pengambilan import ambil_terbaik, cari_hybrid, cari_vektor, perluas
from ._argumen import gabung_pertanyaan, tambah_pertanyaan


def utama(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cari.py", description=__doc__)
    tambah_pertanyaan(parser)
    parser.add_argument(
        "--semua", action="store_true",
        help="matikan penyaring status — dokumen yang sudah dicabut ikut muncul",
    )
    argumen = parser.parse_args(argv)
    tanya = gabung_pertanyaan(argumen.pertanyaan)

    # saring={} berarti tanpa penyaring; None berarti penyaring bawaan.
    saring = {} if argumen.semua else None

    print(f"Pertanyaan: {tanya}")
    if perluas(tanya) != tanya:
        print(f"Setelah perluasan singkatan: {perluas(tanya)}")
    if argumen.semua:
        print("Penyaring status DIMATIKAN — dokumen dicabut boleh muncul.")

    tampilan.cetak_potongan(
        cari_vektor(tanya, k=konfig.JUMLAH_AKHIR, saring=saring), "VEKTOR SAJA"
    )
    tampilan.cetak_potongan(
        cari_hybrid(tanya, saring=saring)[: konfig.JUMLAH_AKHIR], "HYBRID"
    )
    tampilan.cetak_potongan(
        ambil_terbaik(tanya, saring=saring), "HYBRID + SUSUN ULANG"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
