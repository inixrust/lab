# -*- coding: utf-8 -*-
"""Tiga cara mencari, sengaja dipisah agar bisa dibandingkan satu sama lain
di modul B6:

    cari_vektor(t)   pencarian semantik saja        — dasar
    cari_hybrid(t)   vektor + BM25 digabung RRF     — memperbaiki CAKUPAN
    ambil_terbaik(t) hybrid + penyusunan ulang      — memperbaiki KETEPATAN

Ketiganya menerima `saring` dengan aturan yang sama (lihat penyaring.py):
None berarti penyaring bawaan, `{}` berarti tanpa penyaring sama sekali.
"""
from __future__ import annotations

from langchain_core.documents import Document

from .. import konfig
from ..model import ambil_reranker
from .gabung import rrf
from .penyaring import Saring, lolos_saring, saring_baku, untuk_chroma
from .singkatan import perluas
from .sumber import sumber


def cari_vektor(
    pertanyaan: str, k: int | None = None, saring: Saring | None = None
) -> list[Document]:
    """Pencarian semantik murni — dasar pembanding untuk dua cara lainnya."""
    return sumber().basis.similarity_search(
        perluas(pertanyaan),
        k=k or konfig.JUMLAH_KANDIDAT,
        filter=untuk_chroma(saring_baku(saring)),
    )


def cari_hybrid(pertanyaan: str, saring: Saring | None = None) -> list[Document]:
    """Vektor + BM25. Memperbaiki CAKUPAN — memunculkan dokumen yang
    sebelumnya tidak pernah terambil, misalnya yang memuat nomor surat."""
    pencari = sumber()
    kueri = perluas(pertanyaan)
    penyaring = saring_baku(saring)

    hasil_vektor = pencari.basis.similarity_search(
        kueri, k=konfig.JUMLAH_KANDIDAT, filter=untuk_chroma(penyaring)
    )

    # BM25 tidak mengenal penyaring metadata, jadi disaring manual di sini.
    # Kalau langkah ini terlupa, dokumen yang dicabut akan bocor lewat jalur
    # leksikal meski jalur vektor sudah disaring — kegagalan senyap yang khas.
    hasil_bm25 = [d for d in pencari.bm25.invoke(kueri) if lolos_saring(d, penyaring)]

    return rrf([hasil_vektor, hasil_bm25])


def ambil_terbaik(
    pertanyaan: str, k: int | None = None, saring: Saring | None = None
) -> list[Document]:
    """Hybrid + penyusunan ulang. Memperbaiki KETEPATAN — menaikkan potongan
    yang paling relevan ke urutan atas. Bila reranker tidak tersedia, hasil
    hybrid dikembalikan apa adanya."""
    k = k or konfig.JUMLAH_AKHIR
    kandidat = cari_hybrid(pertanyaan, saring=saring)
    if not kandidat:
        return []

    penyusun = ambil_reranker()
    if penyusun is None:
        return kandidat[:k]

    nilai = penyusun.predict([(pertanyaan, d.page_content) for d in kandidat])
    urut = sorted(zip(kandidat, nilai), key=lambda pasangan: pasangan[1], reverse=True)
    return [dokumen for dokumen, _ in urut[:k]]
