# -*- coding: utf-8 -*-
"""Pembacaan set uji dan penyaringan kasus menurut apa yang diujinya.

Nomor halaman di set_uji.json memakai indeks mulai 0, mengikuti PyPDFLoader.
Halaman pertama bernomor 0 di sini. Jangan bingung bila sitasi di layar
menyebut "hal. 1" untuk kasus yang di set_uji.json tertulis halaman 0:
keduanya menunjuk halaman yang sama. Evaluasi memakai indeks mentah, tampilan
memakai nomor cetak — lihat tampilan.lokasi.
"""
from __future__ import annotations

import json
from typing import Any, Sequence

from .. import konfig
from ..galat import SetUjiTakAda

# Satu kasus uji apa adanya dari JSON: tanya, sumber, halaman, jenis, dan
# (opsional) harus_menolak. Dibiarkan sebagai dict supaya berkasnya tetap
# menjadi satu-satunya sumber kebenaran — menambah kolom di JSON tidak
# menuntut perubahan kode di sini.
KasusUji = dict[str, Any]

JENIS_VERSI = "versi"


def muat_set_uji() -> list[KasusUji]:
    """Baca seluruh kasus uji dari set_uji.json."""
    if not konfig.SET_UJI.exists():
        raise SetUjiTakAda(f"Set uji tidak ditemukan: {konfig.SET_UJI}")
    return json.loads(konfig.SET_UJI.read_text(encoding="utf-8"))


def kasus_retrieval(semua: Sequence[KasusUji] | None = None) -> list[KasusUji]:
    """Kasus yang punya jawaban benar di dokumen (bukan kasus penolakan)."""
    return [k for k in (semua or muat_set_uji()) if not k.get("harus_menolak")]


def kasus_penolakan(semua: Sequence[KasusUji] | None = None) -> list[KasusUji]:
    """Kasus yang jawabannya memang TIDAK ada di korpus."""
    return [k for k in (semua or muat_set_uji()) if k.get("harus_menolak")]


def kasus_versi(semua: Sequence[KasusUji] | None = None) -> list[KasusUji]:
    """Kasus bertipe 'versi' — menguji penyaringan status dokumen (B3)."""
    return [k for k in (semua or muat_set_uji()) if k.get("jenis") == JENIS_VERSI]


def cocok(potongan: Sequence[Any], kasus: KasusUji) -> bool:
    """Apakah salah satu potongan berasal dari sumber dan halaman yang benar?"""
    return any(
        d.metadata.get("source") == kasus["sumber"]
        and d.metadata.get("page") in kasus["halaman"]
        for d in potongan
    )
