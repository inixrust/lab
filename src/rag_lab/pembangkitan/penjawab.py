# -*- coding: utf-8 -*-
"""Menyatukan pengambilan, prompt, dan pemeriksaan sitasi menjadi satu jawaban."""
from __future__ import annotations

from typing import Any, Mapping, NamedTuple, Sequence

from langchain_core.documents import Document

from .. import konfig, tampilan
from ..model import ambil_llm
from ..pengambilan.pencari import ambil_terbaik
from ..pengambilan.penyaring import saring_untuk
from .prompt import TEMPLATE, rakit_konteks
from .sitasi import LaporanSitasi, periksa_sitasi, peringatan


class HasilJawaban(NamedTuple):
    """Bisa dibongkar seperti tuple: `isi, potongan, laporan = jawab(...)`."""

    isi: str
    potongan: list[Document]
    laporan: LaporanSitasi


def susun_jawaban(llm: Any, pertanyaan: str, potongan: Sequence[Document]) -> str:
    """Rakit konteks, kirim ke model, kembalikan teks jawabannya.

    Dipisah sebagai fungsi tersendiri karena dipakai ulang oleh pola agentic
    di modul A2 dan A3 — di situ potongannya sudah disaring lebih dulu.
    """
    if not potongan:
        return konfig.TIDAK_DITEMUKAN
    prompt = TEMPLATE.invoke(
        {"konteks": rakit_konteks(potongan), "pertanyaan": pertanyaan}
    )
    return llm.invoke(prompt).content.strip()


def jawab(
    pertanyaan: str,
    pengguna: Mapping[str, Any] | None = None,
    k: int | None = None,
    tampilkan_potongan: bool = True,
) -> HasilJawaban:
    """Ambil potongan, susun jawaban, lalu periksa sitasinya."""
    potongan = ambil_terbaik(pertanyaan, k=k, saring=saring_untuk(pengguna))

    if tampilkan_potongan:
        tampilan.cetak_potongan(potongan, lebar_cuplikan=84)

    isi = susun_jawaban(ambil_llm(), pertanyaan, potongan)
    laporan = periksa_sitasi(isi, len(potongan))

    for pesan in peringatan(laporan, isi):
        print(f"  {pesan}")

    return HasilJawaban(isi, potongan, laporan)
