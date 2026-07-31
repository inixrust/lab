# -*- coding: utf-8 -*-
"""Langkah 1-2 pipeline pengindeksan: memuat seluruh dokumen dan memotongnya.

Nama subfolder di dokumen/ menjadi `jenis` potongan (sop, edaran, notulen) —
dan jenis itulah yang menentukan strategi pemotongan serta ikut tersimpan di
metadata untuk penyaringan di kemudian hari.
"""
from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document

from .. import konfig
from ..galat import DokumenTakTerbaca, FolderDokumenTakAda, KorpusKosong
from . import pemuat, penanda

LEBAR_NAMA = 44


def muat_semua(akar: Path | str | None = None, diam: bool = False) -> list[Document]:
    """Baca seluruh dokumen di folder dokumen/, kembalikan daftar potongan.

    `diam=True` mematikan laporan per berkas — dipakai bila keluarannya tidak
    perlu dilihat, misalnya di dalam pengujian.
    """
    akar = Path(akar or konfig.DOKUMEN)
    if not akar.exists():
        raise FolderDokumenTakAda(
            f"Folder dokumen tidak ditemukan: {akar}\n"
            f"Jalankan skrip ini dari dalam folder lab/src."
        )

    semua: list[Document] = []
    for folder in sorted(p for p in akar.iterdir() if p.is_dir()):
        jenis = folder.name

        for berkas in sorted(folder.rglob("*")):
            if not pemuat.didukung(berkas):
                continue

            try:
                potongan = pemuat.baca(berkas, jenis)
            except DokumenTakTerbaca as e:
                # Bukan alasan menghentikan seluruh pembangunan indeks: satu
                # berkas hasil pindaian dilewati, sisanya tetap diproses.
                print(f"  LEWATI {e}")
                continue

            potongan = penanda.beri_konteks(potongan, jenis, berkas.name)
            semua += potongan
            if not diam:
                print(
                    f"  {berkas.name:{LEBAR_NAMA}s} {len(potongan):3d} potongan "
                    f"({penanda.status_dokumen(berkas.name)})"
                )

    if not semua:
        raise KorpusKosong(
            f"Tidak ada dokumen terbaca di {akar}.\n"
            f"Pastikan ada berkas .pdf atau .md di dalam subfolder."
        )
    if not diam:
        print(f"  {'TOTAL':{LEBAR_NAMA}s} {len(semua):3d} potongan")
    return semua
