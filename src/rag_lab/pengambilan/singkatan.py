# -*- coding: utf-8 -*-
"""Perluasan kueri lewat daftar singkatan.

Cara perluasan kueri termurah yang ada, dan paling berdampak untuk korpus
organisasi Indonesia. Tidak butuh model, tidak butuh pelatihan — hanya daftar
pasangan istilah. Tambahkan singkatan organisasi Anda di sini.
"""
from __future__ import annotations

SINGKATAN: dict[str, str] = {
    "sppd": "Surat Perintah Perjalanan Dinas",
    "simpeg": "Sistem Informasi Kepegawaian",
    "sop": "Standar Operasional Prosedur",
    "se": "Surat Edaran",
    "sk": "Surat Keputusan",
    "po": "Purchase Order",
    "nib": "Nomor Induk Berusaha",
    "npwp": "Nomor Pokok Wajib Pajak",
}

# Tanda baca yang dilepas dari ujung kata sebelum dicocokkan.
TANDA_BACA = ".,?!"


def perluas(pertanyaan: str) -> str:
    """Tambahkan kepanjangan singkatan yang muncul di pertanyaan."""
    kata = {k.strip(TANDA_BACA).lower() for k in pertanyaan.split()}
    tambahan = [panjang for pendek, panjang in SINGKATAN.items() if pendek in kata]
    return pertanyaan + (" " + " ".join(tambahan) if tambahan else "")
