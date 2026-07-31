# -*- coding: utf-8 -*-
"""Pipeline pengindeksan: muat -> potong -> embed -> simpan.

    pemuat       membaca berkas menjadi Document (PDF, Markdown)
    pemotong     strategi chunking per jenis dokumen (pelajaran B2)
    penanda      status dokumen + jalur judul yang ikut di-embed
    korpus       orkestrasi langkah 1-2: muat_semua()
    penyimpanan  artefak indeks: chroma_db/ dan potongan.pkl
    pembangun    orkestrasi langkah 3-4: bangun()
"""
from __future__ import annotations

from .korpus import muat_semua
from .pembangun import bangun
from .penyimpanan import (
    buat_indeks,
    buka_indeks,
    hapus_indeks,
    jumlah_vektor,
    muat_potongan,
    simpan_potongan,
)

__all__ = [
    "bangun",
    "buat_indeks",
    "buka_indeks",
    "hapus_indeks",
    "jumlah_vektor",
    "muat_potongan",
    "muat_semua",
    "simpan_potongan",
]
