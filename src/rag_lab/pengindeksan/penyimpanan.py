# -*- coding: utf-8 -*-
"""Artefak indeks: basis vektor Chroma dan potongan tersimpan untuk BM25.

Semua sentuhan ke berkas indeks dikumpulkan di sini. Modul pengambilan cukup
meminta "buka indeks" tanpa tahu di folder mana, dengan nama koleksi apa, atau
bahwa BM25 memerlukan berkas pickle terpisah.
"""
from __future__ import annotations

import pickle
import shutil
from typing import Sequence

from langchain_chroma import Chroma
from langchain_core.documents import Document

from .. import konfig
from ..galat import IndeksBelumDibangun
from ..model import ambil_embedding


def hapus_indeks() -> bool:
    """Hapus folder indeks. Kembalikan True bila memang ada yang dihapus."""
    if not konfig.INDEKS.exists():
        return False
    shutil.rmtree(konfig.INDEKS)
    return True


def buat_indeks(potongan: Sequence[Document]) -> Chroma:
    """Buat embedding seluruh potongan dan simpan ke basis vektor."""
    return Chroma.from_documents(
        documents=list(potongan),
        embedding=ambil_embedding(),
        collection_name=konfig.NAMA_KOLEKSI,
        persist_directory=str(konfig.INDEKS),
    )


def buka_indeks() -> Chroma:
    """Buka indeks yang sudah dibangun."""
    if not konfig.INDEKS.exists():
        raise IndeksBelumDibangun(
            "Indeks belum dibangun.\nJalankan lebih dulu:  python indeks.py"
        )
    return Chroma(
        collection_name=konfig.NAMA_KOLEKSI,
        embedding_function=ambil_embedding(),
        persist_directory=str(konfig.INDEKS),
    )


def jumlah_vektor(basis: Chroma) -> int:
    """Banyaknya vektor tersimpan.

    Memakai atribut privat `_collection` — satu-satunya cara menghitungnya di
    versi langchain-chroma saat ini. Dikurung di satu fungsi supaya kalau API
    itu berubah, hanya baris ini yang perlu diperbaiki.
    """
    return basis._collection.count()


def simpan_potongan(potongan: Sequence[Document]) -> None:
    """Simpan potongan untuk BM25.

    BM25 bekerja di memori dan tidak membaca dari vector store, jadi
    potongannya disimpan terpisah. Tanpa ini, pencarian hybrid harus memuat
    ulang seluruh PDF setiap kali dijalankan.
    """
    with open(konfig.POTONGAN_TERSIMPAN, "wb") as f:
        pickle.dump(list(potongan), f)


def muat_potongan() -> list[Document]:
    """Baca potongan yang disimpan saat indeks dibangun. Dibutuhkan BM25."""
    if not konfig.POTONGAN_TERSIMPAN.exists():
        raise IndeksBelumDibangun(
            f"Berkas {konfig.POTONGAN_TERSIMPAN.name} tidak ada.\n"
            f"Jalankan lebih dulu:  python indeks.py"
        )
    with open(konfig.POTONGAN_TERSIMPAN, "rb") as f:
        return pickle.load(f)
