# -*- coding: utf-8 -*-
"""Penggabungan hasil beberapa pencari: Reciprocal Rank Fusion."""
from __future__ import annotations

import hashlib
from typing import Iterable, Sequence

from langchain_core.documents import Document

from .. import konfig

# Konstanta peredam RRF. Nilai 60 adalah bawaan dari makalah aslinya: cukup
# besar untuk membuat selisih peringkat teratas tidak terlalu tajam.
PEREDAM = 60


def _kunci(dokumen: Document) -> tuple[object, object, str]:
    """Identitas satu potongan.

    Memakai hash ISI PENUH, bukan 60 karakter pertama. Karena jalur judul
    ditempelkan ke setiap potongan ("[sumber > bab > bagian]"), dua potongan
    berbeda dari bagian yang sama bisa berbagi awalan itu — kalau kunci hanya
    potongan awal, keduanya bertabrakan dan salah satunya hilang diam-diam
    dari hasil.
    """
    return (
        dokumen.metadata.get("source"),
        dokumen.metadata.get("page"),
        hashlib.md5(dokumen.page_content.encode("utf-8")).hexdigest(),
    )


def rrf(
    daftar_daftar: Iterable[Sequence[Document]],
    k: int = PEREDAM,
    ambil: int | None = None,
) -> list[Document]:
    """Gabungkan beberapa daftar berperingkat menjadi satu.

    Memakai POSISI, bukan skor, karena skor BM25 (0 sampai belasan) dan skor
    kemiripan kosinus (-1 sampai 1) berada pada skala yang tak sebanding.
    """
    skor: dict[tuple, float] = {}
    simpan: dict[tuple, Document] = {}

    for daftar in daftar_daftar:
        for peringkat, dokumen in enumerate(daftar, start=1):
            kunci = _kunci(dokumen)
            skor[kunci] = skor.get(kunci, 0.0) + 1.0 / (k + peringkat)
            simpan[kunci] = dokumen

    urut = sorted(skor, key=skor.__getitem__, reverse=True)
    return [simpan[kunci] for kunci in urut[: (ambil or konfig.JUMLAH_KANDIDAT)]]
