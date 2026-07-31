# -*- coding: utf-8 -*-
"""Pemeriksaan kesiapan — versi Hari 1. JALANKAN INI PALING PERTAMA (latihan L1.1).

    python cek.py

Sebagian besar kegagalan lab bukan karena konsepnya sulit, melainkan satu hal
kecil di penyiapan: layanan belum hidup, model belum ditarik, paket belum
terpasang. Skrip ini menemukan semuanya dalam beberapa detik.
"""
import importlib
import sys

OK, GAGAL, INGAT = "  [ OK ]", "  [GAGAL]", "  [catat]"
masalah = []


def _paket():
    print("\n1. Paket Python")
    wajib = {
        "langchain_core": "langchain",
        "langchain_text_splitters": "langchain-text-splitters",
        "langchain_community": "langchain-community",
        "langchain_chroma": "langchain-chroma",
        "langchain_ollama": "langchain-ollama",
        "pypdf": "pypdf",
    }
    for modul, paket in wajib.items():
        try:
            importlib.import_module(modul)
            print(f"{OK} {paket}")
        except ImportError:
            print(f"{GAGAL} {paket} belum terpasang")
            masalah.append(f"pip install {paket}")


def _ollama():
    print("\n2. Layanan Ollama")
    import konfig
    if konfig.MODE_TIRUAN:
        print(f"{INGAT} MODE TIRUAN aktif — Ollama dilewati")
        return
    dasar = konfig.OLLAMA_URL or "http://localhost:11434"
    tampil = dasar.replace("http://", "")
    try:
        import urllib.request
        urllib.request.urlopen(dasar, timeout=4).read()
        print(f"{OK} layanan hidup di {tampil}")
    except Exception:
        print(f"{GAGAL} layanan tidak menjawab di {tampil}")
        masalah.append("Jalankan Ollama (buka aplikasinya, atau: ollama serve)")
        return

    try:
        import json, urllib.request
        data = json.loads(urllib.request.urlopen(dasar + "/api/tags", timeout=6).read())
        ada = {m["name"].split(":")[0] for m in data.get("models", [])}
        ada |= {m["name"] for m in data.get("models", [])}
        for nama in (konfig.MODEL_CHAT, konfig.MODEL_EMBEDDING):
            pendek = nama.split(":")[0]
            if nama in ada or pendek in ada:
                print(f"{OK} model {nama}")
            else:
                print(f"{GAGAL} model {nama} belum ditarik")
                masalah.append(f"ollama pull {nama}")
    except Exception as e:
        print(f"{INGAT} tidak bisa membaca daftar model ({type(e).__name__})")


def _dokumen():
    print("\n3. Dokumen")
    import konfig
    if not konfig.DOKUMEN.exists():
        print(f"{GAGAL} folder dokumen tidak ada: {konfig.DOKUMEN}")
        masalah.append("Jalankan skrip dari dalam folder latihan (tempat konfig.py berada)")
        return
    berkas = [p for p in konfig.DOKUMEN.rglob("*") if p.suffix.lower() in (".pdf", ".md")]
    print(f"{OK} {len(berkas)} dokumen ditemukan")


def _indeks():
    print("\n4. Indeks")
    import konfig
    if konfig.INDEKS.exists():
        print(f"{OK} indeks sudah dibangun — langsung bisa memakai cari.py / jawab.py")
    else:
        print(f"{INGAT} indeks belum ada. Jalankan:  python indeks.py")


def utama():
    print("=" * 62)
    print("PEMERIKSAAN KESIAPAN LAB — HARI 1")
    print("=" * 62)
    print(f"  Python {sys.version.split()[0]}")

    _paket()
    try:
        _ollama(); _dokumen(); _indeks()
    except ImportError:
        print("\n  (pemeriksaan lain dilewati karena ada paket yang belum terpasang)")

    print("\n" + "=" * 62)
    if masalah:
        print("BELUM SIAP. Yang perlu dikerjakan:\n")
        for i, m in enumerate(dict.fromkeys(masalah), 1):
            print(f"  {i}. {m}")
        print("\nSetelah beres, jalankan lagi: python cek.py")
        return 1
    print("SIAP. Langkah berikutnya (latihan L1.2):")
    print("  python indeks.py     bangun indeks (sekali saja)")
    print("  python cari.py       lihat potongan yang terambil (L1.3)")
    print("  python jawab.py      ajukan pertanyaan (L1.3)")
    return 0


if __name__ == "__main__":
    sys.exit(utama())
