# -*- coding: utf-8 -*-
"""Langkah 3-4 pipeline pengindeksan: embedding dan penyimpanan.

Ingat pelajaran F3: mengganti MODEL_EMBEDDING atau ukuran potongan di konfig.py
mengharuskan pengindeksan diulang. Kalau tidak, sistem tetap berjalan tanpa
galat apa pun — hanya hasil pencariannya yang menjadi acak.
"""
from __future__ import annotations

from langchain_chroma import Chroma

from .. import konfig, sidik_jari
from .korpus import muat_semua
from .penyimpanan import buat_indeks, hapus_indeks, jumlah_vektor, simpan_potongan


def bangun(ulang: bool = False, diam: bool = False) -> Chroma:
    """Bangun indeks dari nol atau tambahkan ke yang sudah ada.

    `ulang=True` menghapus indeks lama lebih dulu — inilah yang wajib
    dilakukan setiap kali setelan embedding atau pemotongan berubah.
    """
    if ulang and konfig.INDEKS.exists():
        print(f"Menghapus indeks lama di {konfig.INDEKS.name}/ ...")
        hapus_indeks()

    print("\nSetelan aktif:")
    konfig.ringkas()

    print("\n1-2. Memuat dan memotong dokumen")
    potongan = muat_semua(diam=diam)

    print("\n3-4. Membuat embedding dan menyimpan ke indeks")
    print("     (bagian paling lambat — di laptop tanpa GPU bisa beberapa menit)")
    basis = buat_indeks(potongan)
    simpan_potongan(potongan)

    # Catat sidik jari: dengan embedding & ukuran potongan apa indeks ini dibuat.
    # Pengambilan dan cek.py membacanya untuk menolak ketidakcocokan secara dini.
    sidik_jari.tulis()

    # Indeks baru berarti handle pencarian yang tersimpan di memori sudah basi.
    # Diimpor di dalam fungsi supaya pengindeksan tidak bergantung pada
    # pengambilan saat impor (keduanya akan saling menunggu).
    from ..pengambilan.sumber import lupakan_sumber

    lupakan_sumber()

    print(f"\nSelesai. {jumlah_vektor(basis)} vektor tersimpan di {konfig.INDEKS.name}/")
    print(f"Potongan untuk BM25 tersimpan di {konfig.POTONGAN_TERSIMPAN.name}")
    print("\nCatat di catatan proyek Anda:")
    print(f"  model embedding = {konfig.MODEL_EMBEDDING}")
    print(f"  ukuran potongan = {konfig.UKURAN_POTONGAN}")
    print("Mengubah salah satunya berarti indeks harus dibangun ulang.")
    return basis
