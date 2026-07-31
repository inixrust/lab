# -*- coding: utf-8 -*-
"""Pipeline pengambilan: vektor + BM25 -> RRF -> penyusunan ulang.

Tiga fungsi utama, sengaja dipisah agar bisa dibandingkan satu sama lain
di modul B6:

    cari_vektor(t)   pencarian semantik saja        — dasar
    cari_hybrid(t)   vektor + BM25 digabung RRF     — memperbaiki CAKUPAN
    ambil_terbaik(t) hybrid + penyusunan ulang      — memperbaiki KETEPATAN

Jalankan langsung untuk mencoba: python cari.py "pertanyaan Anda"
"""
import hashlib
import pickle
import sys
import warnings

from langchain_chroma import Chroma

# BM25Retriever masih berada di langchain-community (status pemeliharaan) dan
# impornya bisa memunculkan peringatan usang. Disenyapkan hanya di baris ini —
# lihat catatan lengkap di muat.py. Kodenya tetap berjalan; periksa dokumentasi
# resmi sebelum mengajar kalau-kalau kelasnya sudah pindah paket.
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langchain_community.retrievers import BM25Retriever

import konfig
import meta
import util
from model import ambil_embedding, ambil_reranker

# --------------------------------------------------------------- singkatan
# Perluasan kueri termurah yang ada, dan paling berdampak untuk korpus
# organisasi Indonesia. Tidak butuh model, tidak butuh pelatihan — hanya
# daftar pasangan istilah. Tambahkan singkatan organisasi Anda di sini.
SINGKATAN = {
    "sppd": "Surat Perintah Perjalanan Dinas",
    "simpeg": "Sistem Informasi Kepegawaian",
    "sop": "Standar Operasional Prosedur",
    "se": "Surat Edaran",
    "sk": "Surat Keputusan",
    "po": "Purchase Order",
    "nib": "Nomor Induk Berusaha",
    "npwp": "Nomor Pokok Wajib Pajak",
}


def perluas(pertanyaan: str) -> str:
    """Tambahkan kepanjangan singkatan yang muncul di pertanyaan."""
    # TODO L2.3-1: Perluas pertanyaan dengan kepanjangan singkatan yang muncul (lihat kamus SINGKATAN). Ini perluasan kueri termurah dan paling berdampak untuk korpus Indonesia.
    return pertanyaan


# --------------------------------------------------------------- pemuatan
def _buka_indeks():
    if not konfig.INDEKS.exists():
        raise FileNotFoundError(
            f"Indeks belum dibangun.\n"
            f"Jalankan lebih dulu:  python indeks.py"
        )
    return Chroma(
        collection_name=konfig.NAMA_KOLEKSI,
        embedding_function=ambil_embedding(),
        persist_directory=str(konfig.INDEKS),
    )


def muat_potongan_tersimpan():
    """Baca potongan yang disimpan indeks.py. Dibutuhkan BM25."""
    if not konfig.POTONGAN_TERSIMPAN.exists():
        raise FileNotFoundError(
            f"Berkas {konfig.POTONGAN_TERSIMPAN.name} tidak ada.\n"
            f"Jalankan lebih dulu:  python indeks.py"
        )
    with open(konfig.POTONGAN_TERSIMPAN, "rb") as f:
        return pickle.load(f)


_basis = None
_bm25 = None


def _siapkan():
    global _basis, _bm25
    if _basis is None:
        # Periksa sidik jari indeks SEBELUM memakainya. Kalau indeks dibangun
        # dengan embedding atau ukuran potongan berbeda, hasilnya akan acak
        # tanpa galat — jadi peringatkan sekali, di sini, dengan jelas.
        cocok, pesan = meta.periksa()
        if not cocok:
            print(pesan)
        _basis = _buka_indeks()
        potongan = muat_potongan_tersimpan()
        _bm25 = BM25Retriever.from_documents(potongan)
        _bm25.k = konfig.JUMLAH_KANDIDAT
    return _basis, _bm25


# --------------------------------------------------------------- pencarian
def _saring_baku(saring):
    """Secara bawaan, dokumen yang dicabut TIDAK PERNAH dikembalikan.

    Ini contoh prinsip modul A4: aturan yang benar-benar tidak boleh dilanggar
    ditegakkan di kode, bukan dititipkan ke instruksi prompt.

    Aturan pemakaian:
        saring=None   -> penyaring bawaan, hanya dokumen berstatus berlaku
        saring={}     -> tanpa penyaring sama sekali (untuk demo di kelas)
        saring={...}  -> penyaring Anda sendiri
    """
    return {"status": konfig.STATUS_BERLAKU} if saring is None else saring


def _untuk_chroma(saring):
    """Chroma menolak penyaring berupa dict kosong dan meminta None.

    Terlihat sepele, tapi ini justru contoh bagus untuk kelas: pustaka sering
    punya aturan tak tertulis yang baru ketahuan saat dijalankan. Karena itu
    kode lab ini diuji, bukan hanya ditulis.
    """
    return saring or None


def _lolos_saring(dokumen, saring):
    """Penyaringan manual untuk BM25, yang tidak mengenal metadata."""
    if not saring:
        return True
    return all(dokumen.metadata.get(k) == v for k, v in saring.items())


def cari_vektor(pertanyaan, k=None, saring=None):
    basis, _ = _siapkan()
    return basis.similarity_search(
        perluas(pertanyaan),
        k=k or konfig.JUMLAH_KANDIDAT,
        filter=_untuk_chroma(_saring_baku(saring)),
    )


def rrf(daftar_daftar, k=60, ambil=None):
    """Reciprocal Rank Fusion — gabungkan beberapa daftar berperingkat.

    Memakai POSISI, bukan skor, karena skor BM25 (0 sampai belasan) dan skor
    kemiripan kosinus (-1 sampai 1) berada pada skala yang tak sebanding.
    """
    # TODO L2.3-2: Reciprocal Rank Fusion: gabungkan beberapa daftar berperingkat memakai POSISI (1/(k+peringkat)), bukan skor, karena skala skor BM25 dan kosinus tak sebanding.
    return daftar_daftar[0][:(ambil or konfig.JUMLAH_KANDIDAT)] if daftar_daftar else []


def cari_hybrid(pertanyaan, saring=None):
    """Vektor + BM25. Memperbaiki CAKUPAN — memunculkan dokumen yang
    sebelumnya tidak pernah terambil, misalnya yang memuat nomor surat."""
    # TODO L2.3-3: Pencarian hybrid: jalankan pencarian vektor DAN BM25 (saring BM25 manual karena ia tak kenal metadata), lalu gabungkan dengan rrf().
    return cari_vektor(pertanyaan, k=konfig.JUMLAH_KANDIDAT, saring=saring)


def ambil_terbaik(pertanyaan, k=None, saring=None):
    """Hybrid + penyusunan ulang. Memperbaiki KETEPATAN — menaikkan potongan
    yang paling relevan ke urutan atas. Bila reranker tidak tersedia, hasil
    hybrid dikembalikan apa adanya."""
    # TODO L2.3-4: Penyusunan ulang (reranking): ambil kandidat hybrid, beri skor ulang dengan cross-encoder, kembalikan k teratas. Bila reranker tak ada, kembalikan hybrid apa adanya.
    return cari_hybrid(pertanyaan, saring=saring)[:(k or konfig.JUMLAH_AKHIR)]


# --------------------------------------------------------------- coba cepat
def tampilkan(potongan, judul=""):
    print(f"\n{judul} — {len(potongan)} potongan")
    print("-" * 74)
    for i, d in enumerate(potongan, 1):
        cuplik = " ".join(d.page_content.split())[:88]
        print(f"[{i}] {d.metadata.get('source', '?')[:34]:36s} "
              f"{util.lokasi(d.metadata):14s} {cuplik}...")


if __name__ == "__main__":
    tanya = " ".join(sys.argv[1:]) or "Berapa lama masa percobaan karyawan baru?"
    print(f"Pertanyaan: {tanya}")
    if perluas(tanya) != tanya:
        print(f"Setelah perluasan singkatan: {perluas(tanya)}")

    tampilkan(cari_vektor(tanya, k=konfig.JUMLAH_AKHIR), "VEKTOR SAJA")
    tampilkan(cari_hybrid(tanya)[:konfig.JUMLAH_AKHIR], "HYBRID")
    tampilkan(ambil_terbaik(tanya), "HYBRID + SUSUN ULANG")
