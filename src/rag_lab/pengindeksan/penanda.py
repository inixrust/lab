# -*- coding: utf-8 -*-
"""Metadata potongan: status dokumen dan jalur judul.

Dua hal kecil yang menentukan mutu seluruh sistem di hilir — penyaringan
status (B3) dan konteks induk yang ikut di-embed (B2).
"""
from __future__ import annotations

from typing import Iterable

from langchain_core.documents import Document

from .. import konfig

# Urutan bagian jalur judul yang ditempelkan ke isi potongan.
BAGIAN_JALUR = ("source", "bab", "bagian")


def status_dokumen(nama_berkas: str) -> str:
    """Dokumen dengan penanda DICABUT pada namanya ditandai agar bisa disaring.

    Di sistem sungguhan status ini datang dari basis data dokumen, bukan dari
    nama berkas. Untuk lab, cara ini cukup dan mudah dilihat peserta.
    """
    return (
        konfig.STATUS_DICABUT
        if konfig.PENANDA_DICABUT in nama_berkas.upper()
        else konfig.STATUS_BERLAKU
    )


def beri_konteks(
    potongan: Iterable[Document], jenis: str, nama_berkas: str
) -> list[Document]:
    """Sisipkan jalur judul ke ISI potongan, bukan hanya ke metadata.

    Metadata tidak ikut di-embed. Kalau konteks induk hanya ditaruh di sana,
    ia tidak membantu pencarian sama sekali — pelajaran B2.
    """
    hasil: list[Document] = []
    for dokumen in potongan:
        m = dokumen.metadata
        m.setdefault("source", nama_berkas)
        m["jenis"] = jenis
        m["status"] = status_dokumen(nama_berkas)
        # PDF punya "page" dari PyPDFLoader, bernomor mulai 0. Nomor mentah ini
        # sengaja disimpan apa adanya karena evaluasi membandingkannya dengan
        # set_uji.json; tampilan.lokasi yang mengubahnya jadi nomor cetak saat
        # ditampilkan. Sumber non-halaman (mis. Markdown) dibiarkan None —
        # tampilan.lokasi menampilkan nama bagian untuk itu.
        m.setdefault("page", None)

        jalur = [str(m[k]) for k in BAGIAN_JALUR if m.get(k)]
        if jalur:
            dokumen.page_content = "[" + " > ".join(jalur) + "]\n\n" + dokumen.page_content
        hasil.append(dokumen)
    return hasil
