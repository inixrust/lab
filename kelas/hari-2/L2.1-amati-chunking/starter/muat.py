# -*- coding: utf-8 -*-
"""Langkah 1-2 pipeline pengindeksan: memuat dokumen dan memotongnya.

Inti pelajaran B2: satu strategi pemotongan per jenis dokumen. Peraturan
berpasal dan notulen rapat butuh perlakuan berbeda, karena struktur bawaannya
memuat makna yang berbeda pula.
"""
import warnings
from pathlib import Path

# langchain-community kini berstatus pemeliharaan; mengimpor PyPDFLoader dapat
# memunculkan peringatan usang yang mengotori layar saat demo di depan kelas.
# Kodenya tetap berjalan. Peringatan disenyapkan HANYA di sekitar baris impor
# ini, sehingga peringatan lain yang muncul kemudian tetap terlihat.
# Sebelum mengajar, cek dokumentasi resmi LangChain: bila PyPDFLoader sudah
# pindah ke paket integrasi tersendiri, ganti impor ini dan requirements.txt.
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langchain_community.document_loaders import PyPDFLoader

from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)

import konfig


def _pemotong(jenis: str) -> RecursiveCharacterTextSplitter:
    """Peraturan dan surat edaran dipotong di batas pasal; sisanya di paragraf."""
    # TODO L2.1-1: Pilih pemisah menurut jenis dokumen: peraturan/edaran pakai konfig.PEMISAH_PERATURAN (memotong di batas Pasal), selain itu konfig.PEMISAH_PROSA.
    pemisah = konfig.PEMISAH_PROSA
    return RecursiveCharacterTextSplitter(
        chunk_size=konfig.UKURAN_POTONGAN,
        chunk_overlap=konfig.TUMPANG_TINDIH,
        separators=pemisah,
    )


_MARKDOWN = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "bab"), ("##", "bagian")],
    strip_headers=False,          # heading ikut di teks — penting untuk embedding
)


def _status_dokumen(nama_berkas: str) -> str:
    """Dokumen dengan penanda DICABUT pada namanya ditandai agar bisa disaring.

    Di sistem sungguhan status ini datang dari basis data dokumen, bukan dari
    nama berkas. Untuk lab, cara ini cukup dan mudah dilihat peserta.
    """
    return (konfig.STATUS_DICABUT if "DICABUT" in nama_berkas.upper()
            else konfig.STATUS_BERLAKU)


def _beri_konteks(potongan, jenis: str, nama_berkas: str):
    """Sisipkan jalur judul ke ISI potongan, bukan hanya ke metadata.

    Metadata tidak ikut di-embed. Kalau konteks induk hanya ditaruh di sana,
    ia tidak membantu pencarian sama sekali — pelajaran B2.
    """
    hasil = []
    for d in potongan:
        m = d.metadata
        m.setdefault("source", nama_berkas)
        m["jenis"] = jenis
        m["status"] = _status_dokumen(nama_berkas)
        # PDF punya "page" dari PyPDFLoader, bernomor mulai 0. Nomor mentah ini
        # sengaja disimpan apa adanya karena nilai.py membandingkannya dengan
        # set_uji.json; util.lokasi yang mengubahnya jadi nomor cetak saat
        # ditampilkan. Sumber non-halaman (mis. Markdown) dibiarkan None —
        # util.lokasi menampilkan nama bagian untuk itu.
        m.setdefault("page", None)

        # TODO L2.1-2: Sisipkan jalur judul ke ISI potongan (bukan cuma metadata): rangkai [sumber > bab > bagian] lalu tempelkan ke depan page_content. Metadata tidak ikut di-embed.
        pass
        hasil.append(d)
    return hasil


def muat_semua(akar: Path = None, diam: bool = False):
    """Baca seluruh dokumen di folder dokumen/, kembalikan daftar potongan."""
    akar = Path(akar or konfig.DOKUMEN)
    if not akar.exists():
        raise FileNotFoundError(
            f"Folder dokumen tidak ditemukan: {akar}\n"
            f"Jalankan skrip ini dari dalam folder lab/src."
        )

    semua = []
    for folder in sorted(p for p in akar.iterdir() if p.is_dir()):
        jenis = folder.name

        for berkas in sorted(folder.rglob("*")):
            if berkas.suffix.lower() == ".pdf":
                halaman = PyPDFLoader(str(berkas)).load()

                # Uji keterbacaan — kebiasaan dari modul F4.
                # PDF hasil pindaian tidak punya lapisan teks dan akan lolos
                # tanpa galat, menghasilkan indeks kosong yang membingungkan.
                isi = sum(len((h.page_content or "").strip()) for h in halaman)
                if isi < 50:
                    print(f"  LEWATI {berkas.name}: nyaris tanpa teks. "
                          f"Kemungkinan PDF hasil pindaian, perlu OCR.")
                    continue

                for h in halaman:
                    h.metadata["source"] = berkas.name
                potongan = _pemotong(jenis).split_documents(halaman)

            elif berkas.suffix.lower() == ".md":
                teks = berkas.read_text(encoding="utf-8")
                potongan = _MARKDOWN.split_text(teks)
                # MarkdownHeaderTextSplitter mengembalikan Document tanpa source
                potongan = [Document(page_content=p.page_content,
                                     metadata={**p.metadata, "source": berkas.name})
                            for p in potongan]
            else:
                continue

            potongan = _beri_konteks(potongan, jenis, berkas.name)
            semua += potongan
            if not diam:
                print(f"  {berkas.name:44s} {len(potongan):3d} potongan "
                      f"({_status_dokumen(berkas.name)})")

    if not semua:
        raise RuntimeError(
            f"Tidak ada dokumen terbaca di {akar}.\n"
            f"Pastikan ada berkas .pdf atau .md di dalam subfolder."
        )
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
