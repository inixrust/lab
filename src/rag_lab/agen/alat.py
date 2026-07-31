# -*- coding: utf-8 -*-
"""Alat yang boleh dipanggil agent.

Dua alat sengaja dipilih agar satu pertanyaan bisa membutuhkan KEDUANYA:

    cari_kebijakan  -> mengambil fakta dari dokumen (seluruh pipeline RAG)
    hitung          -> aritmetika sederhana yang aman

Pertanyaan "dinas 3 hari golongan Manajer, berapa totalnya?" memaksa agent
mencari besaran harian dulu (cari_kebijakan), lalu mengalikannya (hitung) —
demo dua langkah yang tidak bisa diselesaikan satu alat saja.

Docstring setiap alat BUKAN hiasan: itulah keterangan yang dibaca model untuk
memutuskan kapan alat dipakai. Menulisnya asal-asalan sama dengan memberi
petunjuk yang kabur kepada rekan kerja baru.
"""
from __future__ import annotations

from langchain_core.tools import tool

from .. import konfig
from ..model import ambil_llm
from ..pembangkitan.penjawab import susun_jawaban
from ..pengambilan.pencari import ambil_terbaik
from .aritmetika import hitung_ekspresi


@tool
def cari_kebijakan(pertanyaan: str) -> str:
    """Cari jawaban dari dokumen internal perusahaan (SOP, surat edaran, notulen).

    Gunakan untuk semua pertanyaan tentang aturan, prosedur, besaran, batas nilai,
    kewenangan, atau ketentuan apa pun. Jangan menebak dari ingatan — selalu
    lewat alat ini. Masukan: pertanyaan dalam bahasa Indonesia. Keluaran: jawaban
    ber-sitasi dari dokumen, atau pernyataan bahwa informasinya tidak ditemukan.
    """
    potongan = ambil_terbaik(pertanyaan)
    if not potongan:
        return konfig.TIDAK_DITEMUKAN
    # Perhatikan: yang dipakai di sini model TANPA alat. Kalau alat memanggil
    # LLM ber-alat lagi, ia bisa mencoba memanggil alat di dalam alat — rekursi
    # yang membingungkan. `bind_tools` di lingkaran.py menghasilkan objek baru,
    # jadi model dasar ini tetap polos.
    return susun_jawaban(ambil_llm(), pertanyaan, potongan)


@tool
def hitung(ekspresi: str) -> str:
    """Hitung ekspresi aritmetika, misalnya '500000 * 3' atau '(2 + 3) * 4'.

    Hanya menerima angka dan operator + - * / % ( ). Tidak menjalankan kode lain.
    Gunakan untuk mengalikan, menjumlahkan, atau menghitung total dari angka yang
    Anda peroleh dari cari_kebijakan.
    """
    try:
        return str(hitung_ekspresi(ekspresi))
    except Exception:
        # Alat tidak boleh melempar galat ke lingkaran agent: model justru
        # perlu MEMBACA kegagalannya supaya bisa mencoba ekspresi lain.
        return f"Ekspresi tidak bisa dihitung: {ekspresi!r}"


ALAT = [cari_kebijakan, hitung]
PETA_ALAT = {a.name: a for a in ALAT}
