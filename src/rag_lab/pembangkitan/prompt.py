# -*- coding: utf-8 -*-
"""Kalimat sistem dan perakitan konteks.

Dipisah dari logika penjawab supaya prompt bisa dibaca, dibandingkan, dan
diubah sebagai teks — tanpa menggeser kode di sekitarnya. Di kelas, prompt
memang bagian yang paling sering diutak-atik peserta.
"""
from __future__ import annotations

from typing import Sequence

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from .. import konfig, tampilan

SISTEM = f"""Anda asisten dokumen internal PT Nusantara Cipta Solusi.
Anda menjawab HANYA berdasarkan KONTEKS yang diberikan.

ATURAN — tidak boleh dilanggar:
1. Gunakan hanya informasi dari KONTEKS. Jangan menambahkan pengetahuan dari
   luar, meskipun Anda mengetahuinya.
2. Setiap klaim faktual wajib diikuti penanda sumber berupa ANGKA di dalam
   kurung siku, sesuai nomor potongan pada KONTEKS — contohnya [1] atau [2].
   Gunakan angkanya, jangan menulis huruf di dalam kurung (bukan [n]).
3. Bila KONTEKS tidak memuat jawabannya, jawab persis kalimat berikut dan
   tidak menambahkan apa pun:
   {konfig.TIDAK_DITEMUKAN}
4. Bila potongan saling bertentangan, sebutkan pertentangannya beserta
   sumber masing-masing. Jangan memilih salah satu diam-diam.
5. Jawab langsung, ringkas, dalam bahasa Indonesia. Jangan menuliskan proses
   berpikir Anda."""

TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", SISTEM),
        ("human", "KONTEKS:\n{konteks}\n\nPERTANYAAN:\n{pertanyaan}"),
    ]
)

PEMISAH_POTONGAN = "\n\n---\n\n"


def rakit_konteks(potongan: Sequence[Document]) -> str:
    """Beri nomor tiap potongan agar model bisa merujuknya kembali.

    Nomor inilah yang muncul sebagai [1], [2] di jawaban — dan yang diperiksa
    ulang oleh sitasi.periksa_sitasi.
    """
    bagian = [
        f"[{nomor}] sumber: {tampilan.sumber(d)}, {tampilan.lokasi(d.metadata)}\n"
        f"{d.page_content}"
        for nomor, d in enumerate(potongan, start=1)
    ]
    return PEMISAH_POTONGAN.join(bagian)
