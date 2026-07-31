# -*- coding: utf-8 -*-
"""Pipeline pembangkitan: susun konteks -> prompt -> jawaban ber-sitasi.

    prompt    kalimat sistem dan perakitan konteks bernomor
    sitasi    pemeriksaan struktural terhadap penanda sumber
    penjawab  menyatukan pengambilan, prompt, dan pemeriksaan
"""
from __future__ import annotations

from .penjawab import HasilJawaban, jawab, susun_jawaban
from .prompt import SISTEM, TEMPLATE, rakit_konteks
from .sitasi import LaporanSitasi, periksa_sitasi

# Kalimat penolakan diambil dari konfig, bukan ditulis ulang di sini.
# Ia dicocokkan sebagai teks persis oleh modul evaluasi — kalau ada dua versi
# yang sedikit berbeda, metrik penolakan akan melaporkan nol tanpa ada yang sadar.
from ..konfig import TIDAK_DITEMUKAN

__all__ = [
    "HasilJawaban",
    "LaporanSitasi",
    "SISTEM",
    "TEMPLATE",
    "TIDAK_DITEMUKAN",
    "jawab",
    "periksa_sitasi",
    "rakit_konteks",
    "susun_jawaban",
]
