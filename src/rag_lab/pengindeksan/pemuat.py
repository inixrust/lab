# -*- coding: utf-8 -*-
"""Membaca satu berkas menjadi potongan Document.

Modul ini hanya tahu cara MEMBACA. Ia tidak mencetak apa pun dan tidak
memutuskan berkas mana yang dilewati — berkas yang tak terbaca dilaporkan
lewat galat `DokumenTakTerbaca`, dan pemanggilnya (korpus.py) yang memilih
mau melewati atau berhenti. Pemisahan ini yang membuat modul bisa diuji tanpa
menangkap keluaran layar.
"""
from __future__ import annotations

import warnings
from pathlib import Path

# langchain-community kini berstatus pemeliharaan; mengimpor PyPDFLoader dapat
# memunculkan peringatan usang yang mengotori layar saat demo di depan kelas.
# Kodenya tetap berjalan. Peringatan disenyapkan HANYA di sekitar baris impor
# ini, sehingga peringatan lain yang muncul kemudian tetap terlihat.
# Sebelum mengajar, cek dokumentasi resmi LangChain: bila PyPDFLoader sudah
# pindah ke paket integrasi tersendiri, ganti impor ini dan requirements.txt.
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langchain_community.document_loaders import PyPDFLoader

from langchain_core.documents import Document

from ..galat import DokumenTakTerbaca
from .pemotong import PEMOTONG_MARKDOWN, pemotong_untuk

SUFIKS_DIDUKUNG = frozenset({".pdf", ".md"})

# Di bawah jumlah karakter ini, sebuah PDF dianggap tanpa lapisan teks.
# Kebiasaan dari modul F4: PDF hasil pindaian lolos TANPA GALAT dan
# menghasilkan indeks kosong yang membingungkan.
AMBANG_TEKS = 50


def didukung(berkas: Path) -> bool:
    """Apakah berkas ini jenis yang bisa dibaca lab?"""
    return berkas.is_file() and berkas.suffix.lower() in SUFIKS_DIDUKUNG


def _baca_pdf(berkas: Path, jenis: str) -> list[Document]:
    halaman = PyPDFLoader(str(berkas)).load()

    isi = sum(len((h.page_content or "").strip()) for h in halaman)
    if isi < AMBANG_TEKS:
        raise DokumenTakTerbaca(berkas.name)

    for h in halaman:
        h.metadata["source"] = berkas.name
    return pemotong_untuk(jenis).split_documents(halaman)


def _baca_markdown(berkas: Path) -> list[Document]:
    teks = berkas.read_text(encoding="utf-8")
    # MarkdownHeaderTextSplitter mengembalikan Document tanpa "source".
    return [
        Document(
            page_content=p.page_content,
            metadata={**p.metadata, "source": berkas.name},
        )
        for p in PEMOTONG_MARKDOWN.split_text(teks)
    ]


def baca(berkas: Path, jenis: str) -> list[Document]:
    """Baca satu berkas menjadi potongan, sesuai jenis dan formatnya.

    Melempar `DokumenTakTerbaca` bila PDF-nya nyaris tanpa teks.
    """
    sufiks = berkas.suffix.lower()
    if sufiks == ".pdf":
        return _baca_pdf(berkas, jenis)
    if sufiks == ".md":
        return _baca_markdown(berkas)
    raise ValueError(f"Format tidak didukung: {berkas.name}")
