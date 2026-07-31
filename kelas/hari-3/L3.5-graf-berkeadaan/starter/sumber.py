# -*- coding: utf-8 -*-
"""Membuka dokumen ASLI di balik sebuah sitasi — modul A5.

    python sumber.py            # periksa semua potongan bisa ditemukan kembali

Ini kelanjutan langsung dari alasan yang sudah ditulis di util.lokasi():

    "Sitasi yang tidak bisa dicek sama saja dengan tidak ada sitasi."

Menampilkan "SOP-01-Kepegawaian.pdf — hal. 3" memang sudah lebih baik daripada
tidak ada apa-apa, tetapi pengguna masih harus percaya. Untuk benar-benar
memeriksa, ia perlu melihat halaman 3 yang SUNGGUHAN — bukan potongan yang
kebetulan disimpan sistem, karena kalau potongannya salah, cuplikan yang
ditampilkan pun ikut salah dan kekeliruannya tak akan pernah ketahuan.

Karena itu berkas ini membaca ulang dokumen aslinya dari folder dokumen/,
bukan dari indeks. Yang ditampilkan ke pengguna adalah halaman asli, dengan
bagian yang dibaca model DISOROT di dalamnya — jadi terlihat sekaligus:
apa yang dipakai model, dan apa yang ada di sekitarnya.

Tidak ada paket baru. pypdf memang sudah dipakai muat.py untuk mengindeks.
"""
import html
import re
import sys
from functools import lru_cache
from pathlib import Path

import konfig

# Awalan "[berkas > bab > bagian]" yang ditempelkan muat._beri_konteks ke ISI
# potongan. Ia sengaja ada di sana agar ikut ter-embed, tapi ia BUKAN bagian
# dari dokumen asli — jadi harus dibuang sebelum dicocokkan ke halaman.
POLA_AWALAN = re.compile(r"^\[[^\]\n]*\]\n\n")


def isi_asli(potongan):
    """Isi potongan tanpa awalan konteks buatan muat.py."""
    return POLA_AWALAN.sub("", potongan.page_content, count=1)


def _rapikan(teks):
    """Rapikan spasi tanpa menghapus struktur baris.

    Spasi ganda hasil ekstraksi PDF diratakan, tapi pergantian baris
    dipertahankan — teks berpasal jadi tak terbaca kalau dijadikan satu paragraf.
    """
    teks = re.sub(r"[ \t]+", " ", teks or "")
    teks = re.sub(r"\n{3,}", "\n\n", teks)
    return teks.strip()


# ------------------------------------------------------------- berkas asli
@lru_cache(maxsize=64)
def berkas_asli(nama_berkas):
    """Cari berkas asli di dalam folder dokumen/. None bila tak ada.

    Dicari berdasarkan nama, bukan jalur tersimpan, karena indeks bisa saja
    dibangun di mesin lain dengan jalur berbeda.
    """
    if not nama_berkas:
        return None
    for jalur in Path(konfig.DOKUMEN).rglob("*"):
        if jalur.is_file() and jalur.name == nama_berkas:
            return jalur
    return None


@lru_cache(maxsize=256)
def _halaman_pdf(jalur, nomor, cap_waktu):
    """Teks satu halaman PDF. cap_waktu ikut jadi kunci cache agar berkas yang
    diperbarui tidak terus terbaca dari cache lama."""
    from pypdf import PdfReader
    halaman = PdfReader(str(jalur)).pages
    if not 0 <= nomor < len(halaman):
        return None
    return _rapikan(halaman[nomor].extract_text() or "")


@lru_cache(maxsize=64)
def _isi_teks(jalur, cap_waktu):
    return _rapikan(Path(jalur).read_text(encoding="utf-8"))


def _bagian_markdown(teks, metadata):
    """Ambil satu bagian Markdown berdasarkan judulnya.

    Notulen dipotong MarkdownHeaderTextSplitter, jadi metadatanya menyimpan
    nama bab/bagian — bukan nomor halaman. Judul itu dicari kembali di berkas
    asli, lalu dipotong sampai judul setingkat berikutnya.
    """
    judul = metadata.get("bagian") or metadata.get("bab")
    if not judul:
        return teks

    for tingkat in ("## ", "# "):
        awal = teks.find(f"{tingkat}{judul}")
        if awal == -1:
            continue
        lanjut = teks.find(f"\n{tingkat}", awal + 1)
        return teks[awal:lanjut if lanjut != -1 else len(teks)].strip()
    return teks


def halaman_asli(metadata):
    """Kembalikan (teks, keterangan) halaman/bagian asli dari sebuah sitasi.

    teks None berarti berkasnya tidak bisa dibaca — pemanggil harus
    mengatakannya apa adanya, bukan menampilkan halaman kosong seolah-olah
    dokumennya memang kosong.
    """
    jalur = berkas_asli(metadata.get("source"))
    if jalur is None:
        return None, f"Berkas asli tidak ditemukan di {konfig.DOKUMEN.name}/"

    cap = jalur.stat().st_mtime
    try:
        if jalur.suffix.lower() == ".pdf":
            nomor = metadata.get("page")
            if not isinstance(nomor, int):
                return None, "Sitasi ini tidak membawa nomor halaman."
            teks = _halaman_pdf(jalur, nomor, cap)
            if teks is None:
                return None, f"Halaman {nomor + 1} tidak ada di berkas ini."
            return teks, f"Halaman asli dari {jalur.name}"
        return (_bagian_markdown(_isi_teks(jalur, cap), metadata),
                f"Bagian asli dari {jalur.name}")
    except Exception as e:
        return None, f"Gagal membaca berkas asli: {type(e).__name__}"


# ------------------------------------------------------------- penyorotan
def belah(teks_halaman, kutipan):
    """Belah halaman menjadi (sebelum, kutipan, sesudah).

    Bila kutipan tidak ketemu, kembalikan (halaman, "", "") — halaman tetap
    ditampilkan, hanya tanpa sorotan. Ini bisa terjadi bila indeks dibangun
    dari versi dokumen yang berbeda, dan justru pantas terlihat.
    """
    if not teks_halaman or not kutipan:
        return teks_halaman or "", "", ""

    kutipan = _rapikan(kutipan)
    posisi = teks_halaman.find(kutipan)
    if posisi != -1:
        return (teks_halaman[:posisi], kutipan,
                teks_halaman[posisi + len(kutipan):])

    # Cadangan: cocokkan tanpa memedulikan pergantian baris. Pemotong kadang
    # memangkas spasi di tepi potongan sehingga pencocokan mentah meleset.
    datar_halaman = re.sub(r"\s+", " ", teks_halaman)
    datar_kutipan = re.sub(r"\s+", " ", kutipan)
    posisi = datar_halaman.find(datar_kutipan)
    if posisi == -1:
        return teks_halaman, "", ""

    # Petakan posisi pada teks datar kembali ke teks asli, dengan menghitung
    # berapa karakter bukan-spasi yang dilewati.
    def _asli(indeks_datar):
        lewat, i = 0, 0
        while i < len(teks_halaman) and lewat < indeks_datar:
            if not (teks_halaman[i].isspace()
                    and i + 1 < len(teks_halaman)
                    and teks_halaman[i + 1].isspace()):
                lewat += 1
            i += 1
        return i

    awal = _asli(posisi)
    akhir = _asli(posisi + len(datar_kutipan))
    return teks_halaman[:awal], teks_halaman[awal:akhir], teks_halaman[akhir:]


# <mark> bawaan peramban memaksa hitam-di-atas-kuning, yang bertabrakan dengan
# tema gelap Streamlit. Sorotan tembus pandang dengan warna huruf DIWARISI
# terbaca pada tema terang maupun gelap.
GAYA_SOROT = ("background:rgba(255,209,0,0.30); color:inherit; "
              "border-radius:0.15rem; padding:0.05rem 0.1rem;")

GAYA_KOTAK = ("white-space:pre-wrap; font-size:0.86rem; line-height:1.55; "
              "max-height:22rem; overflow-y:auto; padding:0.7rem; "
              "border:1px solid rgba(128,128,128,0.3); border-radius:0.4rem;")


def sorot_html(teks_halaman, kutipan):
    """Halaman asli sebagai HTML, dengan bagian yang dibaca model disorot.

    Seluruh teks dokumen dilewatkan html.escape() lebih dulu. Isi dokumen
    adalah data, bukan markup — dan berkas yang memuat "<script>" tidak boleh
    berubah menjadi skrip hanya karena kita menampilkannya.
    """
    sebelum, cocok, sesudah = belah(teks_halaman, kutipan)
    bagian = html.escape(sebelum)
    if cocok:
        bagian += f"<mark style='{GAYA_SOROT}'>{html.escape(cocok)}</mark>"
    bagian += html.escape(sesudah)
    return f"<div style='{GAYA_KOTAK}'>{bagian}</div>"


# ------------------------------------------------------------- pemeriksaan
def _periksa_korpus():
    """Pastikan tiap potongan benar-benar bisa ditemukan kembali di aslinya.

    Ini uji yang murah dan sangat berharga: bila sebuah potongan tidak
    ditemukan di dokumen asalnya, berarti yang ditampilkan ke pengguna sebagai
    'sumber' tidak bisa dipertanggungjawabkan.
    """
    from muat import muat_semua

    potongan = muat_semua(diam=True)
    ketemu = kosong = 0
    for d in potongan:
        teks, _ = halaman_asli(d.metadata)
        if teks is None:
            kosong += 1
            print(f"  TIDAK TERBACA {d.metadata.get('source')} "
                  f"{d.metadata.get('page')}")
            continue
        _, cocok, _ = belah(teks, isi_asli(d))
        if cocok:
            ketemu += 1
        else:
            print(f"  TIDAK COCOK  {d.metadata.get('source')} "
                  f"hal={d.metadata.get('page')} "
                  f"awal={_rapikan(isi_asli(d))[:60]!r}")

    print(f"\n  {ketemu}/{len(potongan)} potongan tersorot di halaman aslinya"
          f"{f', {kosong} berkas tak terbaca' if kosong else ''}.")
    return ketemu, len(potongan)


if __name__ == "__main__":
    print(f"Memeriksa keterlacakan potongan ke {konfig.DOKUMEN}\n")
    ketemu, total = _periksa_korpus()
    sys.exit(0 if ketemu == total else 1)
