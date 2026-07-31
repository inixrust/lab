# -*- coding: utf-8 -*-
"""Langkah 1-2 pipeline pengindeksan: memuat dokumen dan memotongnya — versi Hari 1.

Hari 1 memakai SATU strategi pemotongan untuk semua dokumen, dan belum menyentuh
status dokumen atau penyisipan konteks induk. Semua itu ditambahkan di Hari 2
(latihan L2.1), setelah kita melihat sendiri kenapa satu strategi tidak cukup.
"""
import warnings
from pathlib import Path

# langchain-community kini berstatus pemeliharaan; impor PyPDFLoader dapat
# memunculkan peringatan usang. Disenyapkan hanya di baris ini agar layar bersih
# saat demo — kodenya tetap berjalan.
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langchain_community.document_loaders import PyPDFLoader

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

import konfig


def _pemotong() -> RecursiveCharacterTextSplitter:
    """Satu pemotong untuk semua jenis dokumen (Hari 1)."""
    return RecursiveCharacterTextSplitter(
        chunk_size=konfig.UKURAN_POTONGAN,
        chunk_overlap=konfig.TUMPANG_TINDIH,
        separators=konfig.PEMISAH,
    )


def muat_semua(akar: Path = None, diam: bool = False):
    """Baca seluruh dokumen di folder dokumen/, kembalikan daftar potongan."""
    akar = Path(akar or konfig.DOKUMEN)
    if not akar.exists():
        raise FileNotFoundError(
            f"Folder dokumen tidak ditemukan: {akar}\n"
            f"Jalankan skrip ini dari dalam folder latihan (tempat konfig.py berada)."
        )

    pemotong = _pemotong()
    semua = []
    for folder in sorted(p for p in akar.iterdir() if p.is_dir()):
        jenis = folder.name
        for berkas in sorted(folder.rglob("*")):
            if berkas.suffix.lower() == ".pdf":
                dokumen = PyPDFLoader(str(berkas)).load()
                for h in dokumen:
                    h.metadata["source"] = berkas.name
            elif berkas.suffix.lower() == ".md":
                teks = berkas.read_text(encoding="utf-8")
                dokumen = [Document(page_content=teks, metadata={"source": berkas.name})]
            else:
                continue

            potongan = pemotong.split_documents(dokumen)

            for p in potongan:
                p.metadata.setdefault("source", berkas.name)
                p.metadata["jenis"] = jenis
                p.metadata.setdefault("page", None)
            semua += potongan
            if not diam:
                print(f"  {berkas.name:44s} {len(potongan):3d} potongan")

    if not semua:
        raise RuntimeError(f"Tidak ada dokumen terbaca di {akar}.")
    if not diam:
        print(f"  {'TOTAL':44s} {len(semua):3d} potongan")
    return semua


if __name__ == "__main__":
    print("Memuat dan memotong dokumen...")
    potongan = muat_semua()
    print("\nContoh satu potongan:")
    print("-" * 66)
    print(potongan[0].page_content[:400])
    print("-" * 66)
    print("metadata:", potongan[0].metadata)
