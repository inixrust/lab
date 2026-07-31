# -*- coding: utf-8 -*-
"""Pipeline pengambilan: vektor + BM25 -> RRF -> penyusunan ulang.

    singkatan   perluasan kueri termurah yang ada
    penyaring   aturan keras: dokumen dicabut tidak pernah keluar (B3)
    gabung      Reciprocal Rank Fusion
    sumber      indeks + BM25 yang dipakai bersama, dimuat sekali
    pencari     tiga cara mencari, sengaja dipisah agar bisa dibandingkan (B6)

Tiga fungsi utama:

    cari_vektor(t)   pencarian semantik saja        — dasar
    cari_hybrid(t)   vektor + BM25 digabung RRF     — memperbaiki CAKUPAN
    ambil_terbaik(t) hybrid + penyusunan ulang      — memperbaiki KETEPATAN
"""
from __future__ import annotations

from .gabung import rrf
from .pencari import ambil_terbaik, cari_hybrid, cari_vektor
from .penyaring import saring_untuk
from .singkatan import SINGKATAN, perluas
from .sumber import lupakan_sumber

__all__ = [
    "SINGKATAN",
    "ambil_terbaik",
    "cari_hybrid",
    "cari_vektor",
    "lupakan_sumber",
    "perluas",
    "rrf",
    "saring_untuk",
]
