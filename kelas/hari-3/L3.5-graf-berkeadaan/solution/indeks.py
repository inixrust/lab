# -*- coding: utf-8 -*-
"""Langkah 3-4 pipeline pengindeksan: embedding dan penyimpanan.

Jalankan sekali:      python indeks.py
Bangun ulang total:   python indeks.py --ulang

Ingat pelajaran F3: mengganti MODEL_EMBEDDING atau ukuran potongan di konfig.py
mengharuskan pengindeksan diulang. Kalau tidak, sistem tetap berjalan tanpa
galat apa pun — hanya hasil pencariannya yang menjadi acak.
"""
import pickle
import shutil
import sys

from langchain_chroma import Chroma

import konfig
import meta
from model import ambil_embedding
from muat import muat_semua


def bangun(ulang: bool = False):
    if ulang and konfig.INDEKS.exists():
        print(f"Menghapus indeks lama di {konfig.INDEKS.name}/ ...")
        shutil.rmtree(konfig.INDEKS)

    print("\nSetelan aktif:")
    konfig.ringkas()

    print("\n1-2. Memuat dan memotong dokumen")
    potongan = muat_semua()

    print("\n3-4. Membuat embedding dan menyimpan ke indeks")
    print("     (bagian paling lambat — di laptop tanpa GPU bisa beberapa menit)")
    basis = Chroma.from_documents(
        documents=potongan,
        embedding=ambil_embedding(),
        collection_name=konfig.NAMA_KOLEKSI,
        persist_directory=str(konfig.INDEKS),
    )

    # BM25 bekerja di memori dan tidak membaca dari vector store, jadi
    # potongannya disimpan terpisah. Tanpa ini, pencarian hybrid di cari.py
    # harus memuat ulang seluruh PDF setiap kali dijalankan.
    with open(konfig.POTONGAN_TERSIMPAN, "wb") as f:
        pickle.dump(potongan, f)

    # Catat sidik jari: dengan embedding & ukuran potongan apa indeks ini dibuat.
    # cari.py dan cek.py membacanya untuk menolak ketidakcocokan secara dini.
    meta.tulis()

    jumlah = basis._collection.count()
    print(f"\nSelesai. {jumlah} vektor tersimpan di {konfig.INDEKS.name}/")
    print(f"Potongan untuk BM25 tersimpan di {konfig.POTONGAN_TERSIMPAN.name}")
    print("\nCatat di catatan proyek Anda:")
    print(f"  model embedding = {konfig.MODEL_EMBEDDING}")
    print(f"  ukuran potongan = {konfig.UKURAN_POTONGAN}")
    print("Mengubah salah satunya berarti indeks harus dibangun ulang.")
    return basis


if __name__ == "__main__":
    bangun(ulang="--ulang" in sys.argv)
