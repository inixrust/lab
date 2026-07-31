# -*- coding: utf-8 -*-
"""Lingkaran agent: panggil model, jalankan alat yang dimintanya, ulangi."""
from __future__ import annotations

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from .. import konfig
from ..model import ambil_llm
from .alat import ALAT, PETA_ALAT, cari_kebijakan

SISTEM = """Anda asisten internal PT Nusantara Cipta Solusi.

Anda memiliki dua alat:
- cari_kebijakan(pertanyaan): mencari fakta di dokumen internal.
- hitung(ekspresi): menghitung aritmetika.

Aturan:
1. Untuk pertanyaan apa pun tentang aturan, besaran, atau ketentuan, SELALU
   panggil cari_kebijakan lebih dulu. Jangan menjawab dari ingatan.
2. Bila jawaban membutuhkan perhitungan (misalnya total beberapa hari),
   ambil angkanya dari cari_kebijakan lalu panggil hitung.
3. Bila cari_kebijakan menyatakan informasi tidak ditemukan, sampaikan itu apa
   adanya. Jangan mengarang.
4. Jawaban akhir singkat, dalam bahasa Indonesia."""

MAKS_LANGKAH = 5
LEBAR_CUPLIKAN_HASIL = 110

PESAN_BATAS = (
    "(Batas langkah tercapai tanpa jawaban akhir. Sederhanakan pertanyaan, "
    "atau naikkan maks_langkah.)"
)


def _bisa_beragent(llm: object) -> bool:
    """Mode tiruan dan model tanpa tool-calling tidak bisa menjadi agent."""
    return not konfig.MODE_TIRUAN and hasattr(llm, "bind_tools")


def _jalankan_alat(nama: str, argumen: dict) -> str:
    alat = PETA_ALAT.get(nama)
    if alat is None:
        return f"Alat '{nama}' tidak ada."
    return str(alat.invoke(argumen))


def jalankan_agen(
    pertanyaan: str,
    maks_langkah: int = MAKS_LANGKAH,
    tampilkan_langkah: bool = True,
) -> str:
    """Jalankan lingkaran agent sampai model memberi jawaban akhir.

    Kembalikan teks jawaban akhir. Setiap panggilan alat dicetak agar peserta
    melihat 'jalan pikiran' agent — bagian terpenting dari demo ini.
    """
    llm = ambil_llm()

    # Daripada gagal, tunjukkan satu panggilan RAG langsung supaya alurnya
    # tetap terlihat — sejalan dengan filosofi mode tiruan di seluruh lab.
    if not _bisa_beragent(llm):
        print(
            "  [Agent membutuhkan model dengan tool-calling — mode tiruan tidak "
            "mendukungnya.]"
        )
        print("  [Menampilkan satu panggilan cari_kebijakan langsung sebagai gantinya.]\n")
        return cari_kebijakan.invoke({"pertanyaan": pertanyaan})

    llm_beralat = llm.bind_tools(ALAT)
    pesan: list = [SystemMessage(SISTEM), HumanMessage(pertanyaan)]

    for langkah in range(1, maks_langkah + 1):
        balasan: AIMessage = llm_beralat.invoke(pesan)
        pesan.append(balasan)

        # Tidak ada panggilan alat -> model sudah siap menjawab.
        if not balasan.tool_calls:
            return (balasan.content or "").strip()

        for panggilan in balasan.tool_calls:
            nama, argumen = panggilan["name"], panggilan["args"]
            if tampilkan_langkah:
                print(f"  [langkah {langkah}] memanggil {nama}({argumen})")

            hasil = _jalankan_alat(nama, argumen)

            if tampilkan_langkah:
                cuplik = " ".join(hasil.split())[:LEBAR_CUPLIKAN_HASIL]
                print(f"             -> {cuplik}")

            pesan.append(ToolMessage(content=hasil, tool_call_id=panggilan["id"]))

    return PESAN_BATAS
