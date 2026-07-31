# -*- coding: utf-8 -*-
"""Lapisan tampilan: mengubah potongan menjadi baris yang enak dibaca.

Dikumpulkan di satu modul karena tiga tempat mencetak daftar potongan dengan
bentuk yang sama (cari.py, jawab.py, dan antarmuka). Sebelumnya ketiganya
menyalin potongan kode yang nyaris identik dengan lebar kolom yang berbeda —
persis jenis duplikasi yang membuat perbaikan kecil harus dikerjakan tiga kali.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

LEBAR_GARIS = 74
LEBAR_CUPLIKAN = 88


def lokasi(metadata: Mapping[str, Any]) -> str:
    """Keterangan letak potongan untuk sitasi, dengan nomor halaman manusia.

    PyPDFLoader menomori halaman mulai 0. Nomor mentah itu dipakai apa adanya
    oleh `set_uji.json` dan modul evaluasi, dan memang harus begitu — evaluasi
    membandingkan metadata, bukan teks tampilan.

    Tetapi tidak ada dokumen yang punya "halaman 0". Menampilkannya ke pengguna
    membuat sitasi tidak bisa diverifikasi: orang membuka PDF-nya, mencari
    halaman 0, dan tidak menemukan apa pun. Sitasi yang tidak bisa dicek sama
    saja dengan tidak ada sitasi. Karena itu penyesuaian dilakukan DI SINI, di
    lapisan tampilan, tanpa mengubah metadata yang tersimpan di indeks.

    Urutan yang dipakai:
      1. `page_label` — label cetak asli dari PDF ("1", "ii", "A-3"). Paling
         benar: inilah yang tertulis di halaman itu sendiri.
      2. `page` + 1 — bila PDF tidak membawa label.
      3. nama bagian/bab — untuk sumber tanpa halaman, misalnya Markdown.
    """
    label = metadata.get("page_label")
    if label not in (None, ""):
        return f"hal. {label}"

    halaman = metadata.get("page")
    if isinstance(halaman, int):
        return f"hal. {halaman + 1}"
    if halaman is not None:
        return f"hal. {halaman}"

    bagian = metadata.get("bagian") or metadata.get("bab")
    return f"bagian: {bagian}" if bagian else "sumber"


def cuplikan(dokumen: Any, lebar: int = LEBAR_CUPLIKAN) -> str:
    """Awal isi potongan dalam satu baris — spasi berlebih dirapikan."""
    return " ".join(dokumen.page_content.split())[:lebar]


def sumber(dokumen: Any) -> str:
    """Nama berkas asal potongan, atau '?' bila metadata tidak membawanya."""
    return dokumen.metadata.get("source", "?")


def baris_potongan(nomor: int, dokumen: Any, lebar_cuplikan: int = LEBAR_CUPLIKAN) -> str:
    """Satu baris ringkas: nomor, berkas, letak, cuplikan isi."""
    return (
        f"[{nomor}] {sumber(dokumen)[:34]:36s} "
        f"{lokasi(dokumen.metadata):14s} {cuplikan(dokumen, lebar_cuplikan)}..."
    )


def cetak_potongan(
    potongan: Iterable[Any],
    judul: str | None = None,
    lebar_cuplikan: int = LEBAR_CUPLIKAN,
) -> None:
    """Cetak daftar potongan yang diambil.

    Kebiasaan dari modul F3: LIHAT POTONGAN SEBELUM MELIHAT JAWABAN. Ini yang
    memisahkan orang yang bisa memperbaiki sistem RAG dari orang yang hanya
    bisa mengganti-ganti prompt. Jangan dihapus.
    """
    potongan = list(potongan)
    if judul:
        print(f"\n{judul} — {len(potongan)} potongan")
    print("-" * LEBAR_GARIS)
    for nomor, dokumen in enumerate(potongan, start=1):
        print(baris_potongan(nomor, dokumen, lebar_cuplikan))
    print("-" * LEBAR_GARIS)
