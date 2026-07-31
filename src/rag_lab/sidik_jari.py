# -*- coding: utf-8 -*-
"""Sidik jari indeks: mencatat DENGAN APA indeks dibangun, lalu memastikan
setelan aktif masih cocok sebelum indeks itu dipakai.

Kenapa modul ini ada — inti pelajaran F3:
mengganti model embedding, ukuran potongan, atau berpindah ke/dari mode tiruan
mengharuskan indeks dibangun ulang. Kalau tidak, sistem tetap berjalan TANPA
GALAT tetapi hasil pencariannya menjadi acak. Ini kegagalan senyap yang paling
sulit didiagnosis. Di sini pelajaran itu ditegakkan oleh kode — bukan sekadar
diingatkan lewat komentar yang mudah terlewat.

Letaknya di akar paket, bukan di dalam `pengindeksan/`, karena tiga lapisan
memakainya: pembangunan indeks (menulis), pengambilan (memeriksa sebelum
mencari), dan diagnosa (memeriksa saat `python cek.py`). Modul ini juga hanya
memakai pustaka bawaan Python, sehingga aman diimpor cek.py.
"""
from __future__ import annotations

import json
import time
from typing import NamedTuple

from . import konfig


class HasilPeriksa(NamedTuple):
    """Bisa dibongkar seperti tuple: `cocok, pesan = periksa()`."""

    cocok: bool
    pesan: str | None


def tulis() -> None:
    """Rekam setelan pembangun indeks. Dipanggil setelah indeks dibangun."""
    konfig.META.write_text(
        json.dumps(
            {
                "model_embedding": konfig.MODEL_EMBEDDING,
                "ukuran_potongan": konfig.UKURAN_POTONGAN,
                "mode_tiruan": konfig.MODE_TIRUAN,
                "dibuat": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _beda(tercatat: dict) -> list[str]:
    """Daftar setelan yang berbeda antara indeks dan konfig aktif."""
    beda: list[str] = []
    if tercatat.get("model_embedding") != konfig.MODEL_EMBEDDING:
        beda.append(
            f"embedding: indeks '{tercatat.get('model_embedding')}' "
            f"vs konfig '{konfig.MODEL_EMBEDDING}'"
        )
    if tercatat.get("ukuran_potongan") != konfig.UKURAN_POTONGAN:
        beda.append(
            f"ukuran potongan: indeks {tercatat.get('ukuran_potongan')} "
            f"vs konfig {konfig.UKURAN_POTONGAN}"
        )
    if bool(tercatat.get("mode_tiruan")) != bool(konfig.MODE_TIRUAN):
        beda.append(
            f"mode tiruan: indeks {'ya' if tercatat.get('mode_tiruan') else 'tidak'} "
            f"vs sekarang {'ya' if konfig.MODE_TIRUAN else 'tidak'}"
        )
    return beda


def periksa() -> HasilPeriksa:
    """Bandingkan sidik jari indeks dengan setelan aktif.

    Indeks lama tanpa berkas meta dianggap cocok agar tidak menghalangi —
    hanya ketidakcocokan yang benar-benar terdeteksi yang diperingatkan.
    """
    if not konfig.META.exists():
        return HasilPeriksa(True, None)

    try:
        tercatat = json.loads(konfig.META.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return HasilPeriksa(True, None)

    beda = _beda(tercatat)
    if not beda:
        return HasilPeriksa(True, None)

    pesan = (
        "PERINGATAN: indeks dibangun dengan setelan berbeda dari konfig aktif:\n"
        + "".join(f"    - {b}\n" for b in beda)
        + "  Pencarian akan ACAK tanpa memunculkan galat apa pun (pelajaran F3).\n"
        + "  Bangun ulang lebih dulu:  python indeks.py --ulang"
    )
    return HasilPeriksa(False, pesan)
