# -*- coding: utf-8 -*-
"""Evaluasi: mengubah 'rasanya lebih baik' menjadi angka yang bisa dibandingkan.

    set_uji  membaca dan menyaring kasus uji
    metrik   recall retrieval, kebocoran dokumen dicabut, kemampuan menolak

Evaluasi retrieval sengaja TIDAK memanggil model bahasa: cepat, murah,
objektif, dan bisa dijalankan setiap kali ada perubahan setelan.
"""
from __future__ import annotations

from .metrik import (
    evaluasi_filter_status,
    evaluasi_penolakan,
    evaluasi_retrieval,
    bandingkan_metode,
)
from .set_uji import KasusUji, kasus_penolakan, kasus_retrieval, kasus_versi, muat_set_uji

__all__ = [
    "KasusUji",
    "bandingkan_metode",
    "evaluasi_filter_status",
    "evaluasi_penolakan",
    "evaluasi_retrieval",
    "kasus_penolakan",
    "kasus_retrieval",
    "kasus_versi",
    "muat_set_uji",
]
