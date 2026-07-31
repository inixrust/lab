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
    kata = {k.strip(".,?!").lower() for k in pertanyaan.split()}
    tambahan = [v for k, v in SINGKATAN.items() if k in kata]
    return pertanyaan + (" " + " ".join(tambahan) if tambahan else "")


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
    """Terjemahkan penyaring lab menjadi sintaks where milik Chroma.

    Penyaring di lab ini ditulis sebagai dict biasa, dan nilainya boleh berupa
    satu nilai (harus sama persis) atau himpunan/daftar (harus salah satu):

        {"status": "berlaku", "jenis": {"sop", "edaran"}}

    Chroma punya dua aturan tak tertulis yang baru ketahuan saat dijalankan,
    dan keduanya pernah menjatuhkan lab ini:

      1. dict kosong ditolak — ia meminta None;
      2. dua kunci sekaligus ditolak dengan
         "Expected where to have exactly one operator" — gabungan harus
         dinyatakan eksplisit sebagai $and.

    Karena itu penerjemahan dikumpulkan di SATU fungsi. Selama izin.py hanya
    menghasilkan dict biasa, tidak ada berkas lain yang perlu tahu sintaks
    Chroma — dan mengganti basis vektor cukup menyentuh fungsi ini.
    """
    if not saring:
        return None

    syarat = []
    for kunci, nilai in sorted(saring.items()):
        if isinstance(nilai, (set, frozenset, list, tuple)):
            # $in menuntut daftar; set diurutkan agar penyaringnya stabil
            # (berguna saat penyaring ikut masuk ke kunci cache dan ke jejak).
            syarat.append({kunci: {"$in": sorted(nilai)}})
        else:
            syarat.append({kunci: nilai})

    return syarat[0] if len(syarat) == 1 else {"$and": syarat}


def _lolos_saring(dokumen, saring):
    """Penyaringan manual untuk BM25, yang tidak mengenal metadata.

    Harus memahami bentuk himpunan juga. Kalau fungsi ini tertinggal saat
    penyaring bertambah, jalur leksikal akan meloloskan dokumen yang sudah
    ditutup di jalur vektor — kebocoran senyap yang tidak memunculkan galat
    apa pun.
    """
    if not saring:
        return True
    for kunci, nilai in saring.items():
        punya = dokumen.metadata.get(kunci)
        if isinstance(nilai, (set, frozenset, list, tuple)):
            if punya not in nilai:
                return False
        elif punya != nilai:
            return False
    return True


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
    skor, simpan = {}, {}
    for daftar in daftar_daftar:
        for peringkat, d in enumerate(daftar, start=1):
            # Kunci identitas potongan memakai hash ISI PENUH, bukan 60 karakter
            # pertama. Karena _beri_konteks menempelkan awalan "[sumber > bab >
            # bagian]" ke setiap potongan, dua potongan berbeda dari bagian yang
            # sama bisa berbagi awalan itu — kalau kunci hanya potongan awal,
            # keduanya bertabrakan dan salah satunya hilang diam-diam dari hasil.
            kunci = (d.metadata.get("source"), d.metadata.get("page"),
                     hashlib.md5(d.page_content.encode("utf-8")).hexdigest())
            skor[kunci] = skor.get(kunci, 0.0) + 1.0 / (k + peringkat)
            simpan[kunci] = d
    urut = sorted(skor, key=skor.get, reverse=True)
    return [simpan[x] for x in urut[:(ambil or konfig.JUMLAH_KANDIDAT)]]


def cari_hybrid(pertanyaan, saring=None):
    """Vektor + BM25. Memperbaiki CAKUPAN — memunculkan dokumen yang
    sebelumnya tidak pernah terambil, misalnya yang memuat nomor surat."""
    basis, bm25 = _siapkan()
    q = perluas(pertanyaan)
    penyaring = _saring_baku(saring)

    hasil_vektor = basis.similarity_search(
        q, k=konfig.JUMLAH_KANDIDAT, filter=_untuk_chroma(penyaring))

    # BM25 tidak mengenal penyaring metadata, jadi disaring manual di sini.
    # Kalau langkah ini terlupa, dokumen yang dicabut akan bocor lewat jalur
    # leksikal meski jalur vektor sudah disaring — kegagalan senyap yang khas.
    hasil_bm25 = [d for d in bm25.invoke(q) if _lolos_saring(d, penyaring)]

    return rrf([hasil_vektor, hasil_bm25])


def ambil_terbaik(pertanyaan, k=None, saring=None):
    """Hybrid + penyusunan ulang. Memperbaiki KETEPATAN — menaikkan potongan
    yang paling relevan ke urutan atas. Bila reranker tidak tersedia, hasil
    hybrid dikembalikan apa adanya."""
    k = k or konfig.JUMLAH_AKHIR
    kandidat = cari_hybrid(pertanyaan, saring=saring)
    if not kandidat:
        return []

    penyusun = ambil_reranker()
    if penyusun is None:
        return kandidat[:k]

    nilai = penyusun.predict([(pertanyaan, d.page_content) for d in kandidat])
    urut = sorted(zip(kandidat, nilai), key=lambda x: x[1], reverse=True)
    return [d for d, _ in urut[:k]]


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
