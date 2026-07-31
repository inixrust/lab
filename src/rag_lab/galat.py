# -*- coding: utf-8 -*-
"""Kelas galat lab.

Kenapa tidak cukup melempar `RuntimeError` biasa: pemanggil perlu MEMBEDAKAN
"berkasnya belum ada" (peserta tinggal menjalankan satu perintah) dari
"Ollama mati" (masalah lain). app.py memakai pembedaan itu untuk menampilkan
pesan yang bisa ditindaklanjuti, bukan sekadar tumpukan traceback.

Setiap galat mewarisi juga jenis bawaan Python yang paling dekat
(`FileNotFoundError`, `RuntimeError`) supaya kode lama yang menangkap jenis
bawaan tetap bekerja.
"""
from __future__ import annotations


class GalatLab(Exception):
    """Induk semua galat yang sengaja dilempar kode lab."""


class BerkasBelumAda(GalatLab, FileNotFoundError):
    """Ada berkas yang harus dibuat lebih dulu oleh perintah lain."""


class IndeksBelumDibangun(BerkasBelumAda):
    """Indeks vektor atau potongan BM25 belum ada. Jalankan `python indeks.py`."""


class FolderDokumenTakAda(BerkasBelumAda):
    """Folder dokumen/ tidak ditemukan — biasanya karena salah folder kerja."""


class SetUjiTakAda(BerkasBelumAda):
    """set_uji.json tidak ditemukan; evaluasi tidak bisa dijalankan."""


class KorpusKosong(GalatLab, RuntimeError):
    """Folder dokumen ada, tetapi tidak satu pun berkas terbaca."""


class DokumenTakTerbaca(GalatLab, ValueError):
    """PDF nyaris tanpa lapisan teks — hampir selalu hasil pindaian (modul F4)."""

    def __init__(self, nama_berkas: str) -> None:
        self.nama_berkas = nama_berkas
        super().__init__(
            f"{nama_berkas}: nyaris tanpa teks. "
            f"Kemungkinan PDF hasil pindaian, perlu OCR."
        )


class EkspresiTidakAman(GalatLab, ValueError):
    """Ekspresi di luar aritmetika sederhana ditolak kalkulator agent (modul A4)."""
