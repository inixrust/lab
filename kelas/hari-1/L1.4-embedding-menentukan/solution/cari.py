# -*- coding: utf-8 -*-
"""Pengambilan potongan — versi Hari 1: PENCARIAN VEKTOR saja.

    python cari.py "pertanyaan Anda"

Ini pencarian semantik dasar: pertanyaan di-embed, lalu Chroma mengembalikan
potongan yang vektornya paling dekat. Di Hari 2 (L2.3) kita tambahkan pencarian
leksikal (BM25) + penggabungan (RRF) + penyusunan ulang, dan mengukur bahwa
gabungannya memang lebih baik — bukan sekadar terasa lebih baik.
"""
import sys

from langchain_chroma import Chroma

import konfig
import util
from model import ambil_embedding


def _buka_indeks():
    if not konfig.INDEKS.exists():
        raise FileNotFoundError(
            "Indeks belum dibangun.\nJalankan lebih dulu:  python indeks.py"
        )
    return Chroma(
        collection_name=konfig.NAMA_KOLEKSI,
        embedding_function=ambil_embedding(),
        persist_directory=str(konfig.INDEKS),
    )


_basis = None


def cari_vektor(pertanyaan, k=None):
    """Kembalikan k potongan yang paling dekat maknanya dengan pertanyaan."""
    global _basis
    if _basis is None:
        _basis = _buka_indeks()
    return _basis.similarity_search(pertanyaan, k=k or konfig.JUMLAH_AKHIR)


def tampilkan(potongan, judul=""):
    print(f"\n{judul} — {len(potongan)} potongan")
    print("-" * 74)
    for i, d in enumerate(potongan, 1):
        cuplik = " ".join(d.page_content.split())[:88]
        print(f"[{i}] {d.metadata.get('source', '?')[:34]:36s} "
              f"{util.lokasi(d.metadata):14s} {cuplik}...")


if __name__ == "__main__":
    tanya = " ".join(sys.argv[1:]) or "Berapa lama masa percobaan karyawan baru?"
    print(f"Pertanyaan: {tanya}")
    tampilkan(cari_vektor(tanya), "VEKTOR SAJA")
