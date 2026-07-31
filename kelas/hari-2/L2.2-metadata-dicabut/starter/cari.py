# -*- coding: utf-8 -*-
"""Pengambilan potongan — Hari 2 / L2.2: pencarian vektor + PENYARINGAN STATUS.

    python cari.py "pertanyaan Anda"          hanya dokumen berlaku (bawaan)
    python cari.py --semua "pertanyaan Anda"   tanpa penyaring (lihat kebocoran)

Inti L2.2: dokumen yang sudah DICABUT tidak boleh masuk ke konteks. Aturan sekeras
ini ditegakkan di KODE (lapisan retrieval), bukan dititipkan ke instruksi prompt —
prompt hanyalah harapan. Pencarian leksikal (BM25) dan penyusunan ulang baru
ditambahkan di L2.3.
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


def _saring_baku(saring):
    """Secara bawaan, dokumen yang dicabut TIDAK PERNAH dikembalikan.

    Aturan pemakaian:
        saring=None   -> penyaring bawaan, hanya dokumen berstatus berlaku
        saring={}     -> tanpa penyaring sama sekali (untuk demo kebocoran)
        saring={...}  -> penyaring Anda sendiri
    """
    # TODO L2.2-1: Bila saring None, kembalikan penyaring bawaan {"status": konfig.STATUS_BERLAKU} agar hanya dokumen berlaku yang lolos; selain itu kembalikan saring apa adanya.
    return {"status": konfig.STATUS_BERLAKU} if saring is None else saring


def _untuk_chroma(saring):
    """Chroma meminta None, bukan dict kosong, untuk 'tanpa penyaring'."""
    return saring or None


_basis = None


def cari_vektor(pertanyaan, k=None, saring=None):
    global _basis
    if _basis is None:
        _basis = _buka_indeks()
    return _basis.similarity_search(
        pertanyaan,
        k=k or konfig.JUMLAH_AKHIR,
        filter=_untuk_chroma(_saring_baku(saring)),
    )


def tampilkan(potongan, judul=""):
    print(f"\n{judul} — {len(potongan)} potongan")
    print("-" * 74)
    for i, d in enumerate(potongan, 1):
        cuplik = " ".join(d.page_content.split())[:80]
        print(f"[{i}] {d.metadata.get('source', '?')[:32]:34s} "
              f"status={d.metadata.get('status', '?'):8s} {cuplik}...")


if __name__ == "__main__":
    args = sys.argv[1:]
    semua = "--semua" in args
    tanya = " ".join(a for a in args if a != "--semua") \
        or "Berapa panjang minimum kata sandi sistem internal?"
    print(f"Pertanyaan: {tanya}")
    if semua:
        tampilkan(cari_vektor(tanya, saring={}), "TANPA PENYARING (dokumen dicabut bisa bocor)")
    else:
        tampilkan(cari_vektor(tanya), "HANYA BERLAKU (bawaan)")
