# -*- coding: utf-8 -*-
"""Sumber pencarian: basis vektor + BM25, dimuat sekali lalu dipakai ulang.

Memuat ulang keduanya di setiap pertanyaan berarti membaca kembali potongan
dari cakram dan membangun ulang indeks BM25 — mahal, dan sangat terasa saat
evaluasi memanggil pencarian puluhan kali berturut-turut.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from functools import lru_cache

from langchain_chroma import Chroma

# BM25Retriever masih berada di langchain-community (status pemeliharaan) dan
# impornya bisa memunculkan peringatan usang. Disenyapkan hanya di baris ini —
# lihat catatan lengkap di pengindeksan/pemuat.py. Kodenya tetap berjalan;
# periksa dokumentasi resmi sebelum mengajar kalau-kalau kelasnya sudah pindah.
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langchain_community.retrievers import BM25Retriever

from .. import konfig, sidik_jari
from ..pengindeksan.penyimpanan import buka_indeks, muat_potongan


@dataclass(frozen=True)
class SumberPencarian:
    """Dua pencari yang bekerja berdampingan atas korpus yang sama."""

    basis: Chroma
    bm25: BM25Retriever


@lru_cache(maxsize=1)
def sumber() -> SumberPencarian:
    """Siapkan (sekali) indeks vektor dan indeks leksikal."""
    # Periksa sidik jari indeks SEBELUM memakainya. Kalau indeks dibangun
    # dengan embedding atau ukuran potongan berbeda, hasilnya akan acak
    # tanpa galat — jadi peringatkan sekali, di sini, dengan jelas.
    cocok, pesan = sidik_jari.periksa()
    if not cocok:
        print(pesan)

    basis = buka_indeks()
    bm25 = BM25Retriever.from_documents(muat_potongan())
    bm25.k = konfig.JUMLAH_KANDIDAT
    return SumberPencarian(basis, bm25)


def lupakan_sumber() -> None:
    """Buang sumber yang tersimpan — wajib setelah indeks dibangun ulang."""
    sumber.cache_clear()
