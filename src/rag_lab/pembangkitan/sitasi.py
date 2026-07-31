# -*- coding: utf-8 -*-
"""Pemeriksaan sitasi: murah, otomatis, dan sadar diri akan batasnya.

Yang diperiksa di sini hanya STRUKTUR — apakah penanda sumbernya ada dan
menunjuk potongan yang benar-benar dikirim. Pemeriksaan ini TIDAK menangkap
sitasi yang menunjuk potongan nyata namun isinya tak mendukung klaim; lihat
pembahasan halusinasi bersitasi di modul B5.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .. import konfig

# Pola satu penanda sitasi. Menerima bentuk gabungan seperti [1, 2] atau [1;2],
# bukan hanya [1] — kalau tidak, kalimat ber-sitasi ganda dianggap tak bersumber
# dan cakupan terhitung rendah keliru. Wajib memuat setidaknya satu digit.
POLA_SITASI = r"\[\s*\d[\d,;\s]*\]"

# Akhir kalimat: titik, tanda tanya, atau tanda seru yang diikuti spasi.
POLA_KALIMAT = r"(?<=[.!?])\s+"


@dataclass(frozen=True)
class LaporanSitasi:
    """Hasil pemeriksaan struktural satu jawaban.

    hantu   nomor sitasi yang menunjuk potongan tak ada (terurut)
    cakupan bagian kalimat yang membawa sitasi, 0.0 sampai 1.0
    """

    hantu: tuple[int, ...]
    cakupan: float

    @property
    def cakupan_rendah(self) -> bool:
        return self.cakupan < konfig.AMBANG_CAKUPAN


def periksa_sitasi(jawaban: str, jumlah_potongan: int) -> LaporanSitasi:
    """Hitung sitasi hantu dan cakupan sitasi sebuah jawaban."""
    dirujuk: set[int] = set()
    for grup in re.findall(POLA_SITASI, jawaban):
        dirujuk.update(int(n) for n in re.findall(r"\d+", grup))
    hantu = tuple(sorted(n for n in dirujuk if not 1 <= n <= jumlah_potongan))

    kalimat = [k for k in re.split(POLA_KALIMAT, jawaban) if k.strip()]
    bersitasi = [k for k in kalimat if re.search(POLA_SITASI, k)]
    cakupan = len(bersitasi) / len(kalimat) if kalimat else 0.0

    return LaporanSitasi(hantu=hantu, cakupan=round(cakupan, 2))


def peringatan(laporan: LaporanSitasi, jawaban: str) -> list[str]:
    """Kalimat peringatan yang layak ditampilkan, atau daftar kosong.

    Dipisah dari pencetakan supaya baris peringatan yang sama bisa dipakai di
    baris perintah maupun di antarmuka Streamlit.
    """
    pesan: list[str] = []
    if laporan.hantu:
        pesan.append(
            f"PERINGATAN: sitasi menunjuk potongan yang tidak ada: "
            f"{list(laporan.hantu)}"
        )
    # Penolakan memang tidak perlu sitasi — jangan diperingatkan.
    if konfig.TIDAK_DITEMUKAN not in jawaban and laporan.cakupan_rendah:
        pesan.append(f"PERINGATAN: cakupan sitasi rendah ({laporan.cakupan:.0%})")
    return pesan
