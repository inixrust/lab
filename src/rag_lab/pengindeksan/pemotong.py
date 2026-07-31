# -*- coding: utf-8 -*-
"""Strategi pemotongan — inti pelajaran B2.

Satu strategi per jenis dokumen. Peraturan berpasal dan notulen rapat butuh
perlakuan berbeda, karena struktur bawaannya memuat makna yang berbeda pula.
"""
from __future__ import annotations

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from .. import konfig


def pemotong_untuk(jenis: str) -> RecursiveCharacterTextSplitter:
    """Peraturan dan surat edaran dipotong di batas pasal; sisanya di paragraf.

    `jenis` diambil dari nama subfolder di dokumen/ (sop, edaran, notulen).
    """
    pemisah = (
        konfig.PEMISAH_PERATURAN
        if jenis in konfig.JENIS_BERPASAL
        else konfig.PEMISAH_PROSA
    )
    return RecursiveCharacterTextSplitter(
        chunk_size=konfig.UKURAN_POTONGAN,
        chunk_overlap=konfig.TUMPANG_TINDIH,
        separators=pemisah,
    )


# Markdown dipotong menurut headingnya, bukan jumlah karakter: heading adalah
# batas makna yang sudah ditulis penulisnya sendiri.
# strip_headers=False -> heading ikut di teks, dan itu penting untuk embedding.
PEMOTONG_MARKDOWN = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "bab"), ("##", "bagian")],
    strip_headers=False,
)
