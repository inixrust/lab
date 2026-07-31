# -*- coding: utf-8 -*-
"""Pemeriksaan kesiapan lab.

Sebagian besar kegagalan lab bukan karena konsepnya sulit, melainkan karena
satu hal kecil di penyiapan: layanan belum hidup, model belum ditarik, paket
belum terpasang. Modul ini menemukan semuanya dalam beberapa detik, sebelum
peserta menghabiskan dua puluh menit menebak-nebak.

Aturan penting modul ini: JANGAN mengimpor langchain, chroma, atau apa pun
dari `rag_lab` yang membutuhkannya di tingkat modul. Pemeriksaan ini harus
tetap berjalan justru di mesin yang paketnya belum lengkap. Yang boleh
diimpor hanya `konfig` dan `sidik_jari`, yang keduanya murni pustaka bawaan.

Setiap fungsi periksa_* mengembalikan daftar langkah perbaikan, bukan
mencetak lalu menyimpannya di variabel global. Dengan begitu urutan dan
bentuk laporannya ditentukan di satu tempat: `jalankan()`.
"""
from __future__ import annotations

import importlib
import json
import sys
import urllib.request

from . import konfig, sidik_jari

OK = "  [ OK ]"
GAGAL = "  [GAGAL]"
INGAT = "  [catat]"

# modul yang diimpor -> nama paket yang dipasang lewat pip
PAKET_WAJIB = {
    "langchain_core": "langchain",
    "langchain_text_splitters": "langchain-text-splitters",
    "langchain_community": "langchain-community",
    "langchain_chroma": "langchain-chroma",
    "langchain_ollama": "langchain-ollama",
    "pypdf": "pypdf",
    "rank_bm25": "rank_bm25",
}

PAKET_PILIHAN = {
    "sentence_transformers": "sentence-transformers  (untuk reranker, modul B4)",
    "streamlit": "streamlit             (untuk antarmuka, modul A5)",
}

SUFIKS_DOKUMEN = (".pdf", ".md")
AMBANG_TEKS = 50
BATAS_WAKTU = 6


def _ada(modul: str) -> bool:
    try:
        importlib.import_module(modul)
        return True
    except ImportError:
        return False


def periksa_paket() -> list[str]:
    """Paket wajib harus ada; paket pilihan cukup dicatat bila belum ada."""
    print("\n1. Paket Python")
    masalah: list[str] = []

    for modul, paket in PAKET_WAJIB.items():
        if _ada(modul):
            print(f"{OK} {paket}")
        else:
            print(f"{GAGAL} {paket} belum terpasang")
            masalah.append(f"pip install {paket}")

    for modul, keterangan in PAKET_PILIHAN.items():
        if _ada(modul):
            print(f"{OK} {keterangan}")
        else:
            print(f"{INGAT} {keterangan} belum ada — opsional")
    return masalah


def _model_tersedia(dasar: str) -> set[str]:
    """Nama model di Ollama, lengkap dan tanpa tag (qwen3:8b dan qwen3)."""
    with urllib.request.urlopen(dasar + "/api/tags", timeout=BATAS_WAKTU) as balasan:
        data = json.loads(balasan.read())
    nama = {m["name"] for m in data.get("models", [])}
    return nama | {n.split(":")[0] for n in nama}


def periksa_ollama() -> list[str]:
    """Layanan hidup, dan kedua model yang dipakai lab sudah ditarik."""
    print("\n2. Layanan Ollama")
    if konfig.MODE_TIRUAN:
        print(f"{INGAT} MODE TIRUAN aktif — Ollama dilewati")
        return []

    masalah: list[str] = []
    dasar = konfig.alamat_ollama()
    tampil = dasar.replace("http://", "")

    try:
        urllib.request.urlopen(dasar, timeout=4).read()
        print(f"{OK} layanan hidup di {tampil}")
    except Exception:
        # Apa pun sebabnya — koneksi ditolak, DNS, proxy — artinya sama saja
        # bagi peserta: layanannya belum siap dipakai.
        print(f"{GAGAL} layanan tidak menjawab di {tampil}")
        return ["Jalankan Ollama (buka aplikasinya, atau: ollama serve)"]

    try:
        tersedia = _model_tersedia(dasar)
    except Exception as e:
        # Daftar model gagal dibaca bukan alasan menyatakan BELUM SIAP:
        # layanannya sudah terbukti hidup di pemeriksaan sebelumnya.
        print(f"{INGAT} tidak bisa membaca daftar model ({type(e).__name__})")
        return masalah

    for nama in (konfig.MODEL_CHAT, konfig.MODEL_EMBEDDING):
        if nama in tersedia or nama.split(":")[0] in tersedia:
            print(f"{OK} model {nama}")
        else:
            print(f"{GAGAL} model {nama} belum ditarik")
            masalah.append(f"ollama pull {nama}")
    return masalah


def _periksa_keterbacaan(berkas) -> list[str]:
    """Uji keterbacaan PDF — kebiasaan dari modul F4."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return []

    masalah: list[str] = []
    for p in berkas:
        if p.suffix.lower() != ".pdf":
            continue
        pembaca = PdfReader(str(p))
        isi = sum(len((h.extract_text() or "").strip()) for h in pembaca.pages)
        if isi < AMBANG_TEKS:
            print(f"{GAGAL} {p.name} nyaris tanpa teks — kemungkinan hasil pindaian")
            masalah.append(f"{p.name} perlu OCR atau diganti")
        else:
            print(f"{OK} {p.name} terbaca ({len(pembaca.pages)} hal, {isi} karakter)")
    return masalah


def periksa_dokumen() -> list[str]:
    """Korpus ada, terbaca, dan set ujinya lengkap."""
    print("\n3. Dokumen dan set uji")
    if not konfig.DOKUMEN.exists():
        print(f"{GAGAL} folder dokumen tidak ada: {konfig.DOKUMEN}")
        return ["Jalankan skrip dari dalam folder lab/src"]

    berkas = [
        p for p in konfig.DOKUMEN.rglob("*") if p.suffix.lower() in SUFIKS_DOKUMEN
    ]
    print(f"{OK} {len(berkas)} dokumen ditemukan")
    masalah = _periksa_keterbacaan(berkas)

    if konfig.SET_UJI.exists():
        jumlah = len(json.loads(konfig.SET_UJI.read_text(encoding="utf-8")))
        print(f"{OK} set_uji.json berisi {jumlah} kasus")
    else:
        print(f"{INGAT} set_uji.json belum ada — evaluasi di modul B6 tidak bisa jalan")
    return masalah


def periksa_indeks() -> list[str]:
    """Indeks ada DAN dibangun dengan setelan yang sama seperti sekarang (F3)."""
    print("\n4. Indeks")
    if not (konfig.INDEKS.exists() and konfig.POTONGAN_TERSIMPAN.exists()):
        print(f"{INGAT} indeks belum ada. Jalankan:  python indeks.py")
        return []

    cocok, pesan = sidik_jari.periksa()
    if cocok:
        print(f"{OK} indeks sudah dibangun — langsung bisa memakai jawab.py")
        return []

    print(f"{GAGAL} {pesan}")
    return ["python indeks.py --ulang  (indeks tidak cocok dengan konfig)"]


def jalankan() -> int:
    """Jalankan seluruh pemeriksaan. Kembalikan 0 bila siap, 1 bila belum."""
    print("=" * 62)
    print("PEMERIKSAAN KESIAPAN LAB")
    print("=" * 62)
    print(f"  Python {sys.version.split()[0]}")

    masalah = periksa_paket()
    try:
        masalah += periksa_ollama() + periksa_dokumen() + periksa_indeks()
    except ImportError:
        print("\n  (pemeriksaan lain dilewati karena ada paket yang belum terpasang)")

    print("\n" + "=" * 62)
    if masalah:
        print("BELUM SIAP. Yang perlu dikerjakan:\n")
        # dict.fromkeys membuang duplikat tanpa mengubah urutan.
        for nomor, langkah in enumerate(dict.fromkeys(masalah), start=1):
            print(f"  {nomor}. {langkah}")
        print("\nSetelah beres, jalankan lagi: python cek.py")
        return 1

    print("SIAP. Langkah berikutnya:")
    print("  python indeks.py     bangun indeks (sekali saja)")
    print("  python jawab.py      ajukan pertanyaan")
    print("  python nilai.py      ukur mutu retrieval")
    return 0
