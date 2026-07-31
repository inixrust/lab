# -*- coding: utf-8 -*-
"""Pipeline pembangkitan — versi Hari 1: susun konteks -> prompt -> jawaban.

    python jawab.py "pertanyaan Anda"

Kebiasaan terpenting Hari 1: LIHAT POTONGAN SEBELUM MELIHAT JAWABAN. Inilah yang
memisahkan orang yang bisa memperbaiki RAG dari yang hanya mengganti-ganti prompt.
Pemeriksaan sitasi otomatis dan penolakan terukur ditambahkan di Hari 2.
"""
import sys

from langchain_core.prompts import ChatPromptTemplate

import konfig
import util
from cari import cari_vektor
from model import ambil_llm

TIDAK_DITEMUKAN = konfig.TIDAK_DITEMUKAN

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
4. Jawab langsung, ringkas, dalam bahasa Indonesia. Jangan menuliskan proses
   berpikir Anda."""

TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SISTEM),
    ("human", "KONTEKS:\n{konteks}\n\nPERTANYAAN:\n{pertanyaan}"),
])


def rakit_konteks(potongan):
    """Beri nomor tiap potongan agar model bisa merujuknya kembali."""
    bagian = []
    for i, d in enumerate(potongan, start=1):
        m = d.metadata
        bagian.append(
            f"[{i}] sumber: {m.get('source', '?')}, {util.lokasi(m)}\n"
            f"{d.page_content}"
        )
    return "\n\n---\n\n".join(bagian)


def susun_jawaban(llm, pertanyaan, potongan):
    """Rakit konteks, kirim ke model, kembalikan teks jawabannya."""
    if not potongan:
        return TIDAK_DITEMUKAN
    prompt = TEMPLATE.invoke({
        "konteks": rakit_konteks(potongan),
        "pertanyaan": pertanyaan,
    })
    return llm.invoke(prompt).content.strip()


_llm = None


def jawab(pertanyaan, k=None, tampilkan_potongan=True):
    """Kembalikan (jawaban, potongan)."""
    global _llm
    if _llm is None:
        _llm = ambil_llm()

    potongan = cari_vektor(pertanyaan, k=k)

    # Kebiasaan F3: LIHAT POTONGAN DULU. Jangan dihapus.
    if tampilkan_potongan:
        print("-" * 74)
        for i, d in enumerate(potongan, 1):
            cuplik = " ".join(d.page_content.split())[:84]
            print(f"[{i}] {d.metadata.get('source', '?')[:32]:34s} "
                  f"{util.lokasi(d.metadata):14s} {cuplik}...")
        print("-" * 74)

    isi = susun_jawaban(_llm, pertanyaan, potongan)
    return isi, potongan


if __name__ == "__main__":
    tanya = " ".join(sys.argv[1:]) or "Berapa lama masa percobaan karyawan baru?"
    print(f"Pertanyaan: {tanya}\n")
    isi, potongan = jawab(tanya)
    print("\nJAWABAN:")
    print(isi)
