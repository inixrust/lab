# -*- coding: utf-8 -*-
"""Pemeriksaan kesiapan. JALANKAN INI PALING PERTAMA.

    python cek.py

Sebagian besar kegagalan lab bukan karena konsepnya sulit, melainkan karena
satu hal kecil di penyiapan: layanan belum hidup, model belum ditarik, paket
belum terpasang. Skrip ini menemukan semuanya dalam beberapa detik, sebelum
peserta menghabiskan dua puluh menit menebak-nebak.
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
        "rank_bm25": "rank_bm25",
    }
    pilihan = {
        "sentence_transformers": "sentence-transformers  (untuk reranker, modul B4)",
        "streamlit": "streamlit             (untuk antarmuka, modul A5)",
    }
    for modul, paket in wajib.items():
        try:
            importlib.import_module(modul)
            print(f"{OK} {paket}")
        except ImportError:
            print(f"{GAGAL} {paket} belum terpasang")
            masalah.append(f"pip install {paket}")
    for modul, ket in pilihan.items():
        try:
            importlib.import_module(modul)
            print(f"{OK} {ket}")
        except ImportError:
            print(f"{INGAT} {ket} belum ada — opsional")


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
        data = json.loads(urllib.request.urlopen(
            dasar + "/api/tags", timeout=6).read())
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
    print("\n3. Dokumen dan set uji")
    import konfig
    if not konfig.DOKUMEN.exists():
        print(f"{GAGAL} folder dokumen tidak ada: {konfig.DOKUMEN}")
        masalah.append("Jalankan skrip dari dalam folder lab/src")
        return
    berkas = [p for p in konfig.DOKUMEN.rglob("*") if p.suffix.lower() in (".pdf", ".md")]
    print(f"{OK} {len(berkas)} dokumen ditemukan")

    # Uji keterbacaan PDF — kebiasaan dari modul F4.
    try:
        from pypdf import PdfReader
        for p in berkas:
            if p.suffix.lower() != ".pdf":
                continue
            r = PdfReader(str(p))
            isi = sum(len((h.extract_text() or "").strip()) for h in r.pages)
            if isi < 50:
                print(f"{GAGAL} {p.name} nyaris tanpa teks — kemungkinan hasil pindaian")
                masalah.append(f"{p.name} perlu OCR atau diganti")
            else:
                print(f"{OK} {p.name} terbaca ({len(r.pages)} hal, {isi} karakter)")
    except ImportError:
        pass

    if konfig.SET_UJI.exists():
        import json
        n = len(json.loads(konfig.SET_UJI.read_text(encoding="utf-8")))
        print(f"{OK} set_uji.json berisi {n} kasus")
    else:
        print(f"{INGAT} set_uji.json belum ada — evaluasi di modul B6 tidak bisa jalan")


def _indeks():
    print("\n4. Indeks")
    import konfig
    import meta
    if konfig.INDEKS.exists() and konfig.POTONGAN_TERSIMPAN.exists():
        cocok, pesan = meta.periksa()
        if cocok:
            print(f"{OK} indeks sudah dibangun — langsung bisa memakai jawab.py")
        else:
            print(f"{GAGAL} {pesan}")
            masalah.append("python indeks.py --ulang  (indeks tidak cocok dengan konfig)")
    else:
        print(f"{INGAT} indeks belum ada. Jalankan:  python indeks.py")


def utama():
    print("=" * 62)
    print("PEMERIKSAAN KESIAPAN LAB")
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
    print("SIAP. Langkah berikutnya:")
    print("  python indeks.py     bangun indeks (sekali saja)")
    print("  python jawab.py      ajukan pertanyaan")
    print("  python nilai.py      ukur mutu retrieval")
    return 0


if __name__ == "__main__":
    sys.exit(utama())
