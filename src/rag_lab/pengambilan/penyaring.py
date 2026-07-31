# -*- coding: utf-8 -*-
"""Penyaringan metadata — aturan keras modul A4 dan B3.

Aturan yang benar-benar tidak boleh dilanggar ditegakkan di KODE, bukan
dititipkan ke instruksi prompt. Prompt hanyalah harapan; penyaring adalah
jaminan.
"""
from __future__ import annotations

from typing import Any, Mapping

from langchain_core.documents import Document

from .. import konfig

Saring = dict[str, Any]


def saring_baku(saring: Saring | None) -> Saring:
    """Secara bawaan, dokumen yang dicabut TIDAK PERNAH dikembalikan.

    Aturan pemakaian:
        saring=None   -> penyaring bawaan, hanya dokumen berstatus berlaku
        saring={}     -> tanpa penyaring sama sekali (untuk demo di kelas)
        saring={...}  -> penyaring Anda sendiri
    """
    return {"status": konfig.STATUS_BERLAKU} if saring is None else saring


def saring_untuk(pengguna: Mapping[str, Any] | None = None) -> Saring:
    """Penyaring untuk seorang pengguna.

    Sekarang hasilnya sama untuk semua orang: hanya dokumen yang berlaku.
    Di sinilah penyaringan per unit kerja ditambahkan (modul A4), misalnya:

        saring = {"status": konfig.STATUS_BERLAKU}
        if pengguna and pengguna.get("peran") != "pimpinan":
            saring["unit"] = pengguna["unit"]
        return saring

    Perhatikan bahwa kewenangan disaring DI SINI, di lapisan pengambilan —
    bukan dengan meminta model "jangan menjawab bila pengguna bukan pimpinan".
    """
    return {"status": konfig.STATUS_BERLAKU}


def untuk_chroma(saring: Saring) -> Saring | None:
    """Chroma menolak penyaring berupa dict kosong dan meminta None.

    Terlihat sepele, tapi ini justru contoh bagus untuk kelas: pustaka sering
    punya aturan tak tertulis yang baru ketahuan saat dijalankan. Karena itu
    kode lab ini diuji, bukan hanya ditulis.
    """
    return saring or None


def lolos_saring(dokumen: Document, saring: Saring) -> bool:
    """Penyaringan manual untuk BM25, yang tidak mengenal metadata."""
    if not saring:
        return True
    return all(dokumen.metadata.get(k) == v for k, v in saring.items())
