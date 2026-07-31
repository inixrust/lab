# -*- coding: utf-8 -*-
"""Membuka dokumen ASLI di balik sebuah sitasi.

Ini kelanjutan langsung dari alasan yang sudah ditulis panjang di
`tampilan.lokasi()`:

    "Sitasi yang tidak bisa dicek sama saja dengan tidak ada sitasi."

Menampilkan "SOP-01-Kepegawaian.pdf — hal. 3" sudah lebih baik daripada tidak
ada apa-apa, tetapi pengguna masih harus percaya. Untuk benar-benar memeriksa,
ia perlu melihat halaman 3 yang SUNGGUHAN — bukan potongan yang kebetulan
tersimpan di indeks. Kalau potongannya sendiri keliru (salah halaman, terpotong
di tempat yang salah), cuplikan dari indeks akan ikut keliru dan kekeliruannya
tidak akan pernah ketahuan.

Karena itu modul ini membaca ulang dokumen aslinya dari `konfig.DOKUMEN`, bukan
dari indeks. Yang ditampilkan adalah halaman asli, dengan bagian yang dibaca
model disorot di dalamnya — jadi terlihat sekaligus apa yang dipakai model dan
apa yang ada di sekitarnya.

BACA SAJA. Modul ini sengaja hanya mengembalikan TEKS, tidak pernah byte
berkasnya. Memeriksa sitasi dan mengunduh dokumen adalah dua kebutuhan berbeda,
dan hanya yang pertama yang dijanjikan sistem ini: satu halaman cukup untuk
memastikan jawaban benar, sedangkan berkas utuh berarti menyebarkan salinan
dokumen internal yang tak bisa ditarik kembali. Batas itu ditegakkan dengan
tidak pernah menyediakan isinya — bukan dengan menyembunyikan tombol.

Tidak ada paket baru: pypdf memang sudah dipakai lapisan pengindeksan.
"""
from __future__ import annotations

import html
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from . import konfig

# Awalan "[berkas > bab > bagian]" yang ditempelkan lapisan pengindeksan ke ISI
# potongan. Ia sengaja ada di sana agar ikut ter-embed, tapi ia BUKAN bagian
# dari dokumen asli — jadi harus dibuang sebelum dicocokkan ke halaman.
POLA_AWALAN = re.compile(r"^\[[^\]\n]*\]\n\n")

# <mark> bawaan peramban memaksa hitam-di-atas-kuning, yang bertabrakan dengan
# tema gelap. Sorotan tembus pandang dengan warna huruf DIWARISI terbaca pada
# tema terang maupun gelap.
GAYA_SOROT = (
    "background:rgba(255,209,0,0.30); color:inherit; "
    "border-radius:0.15rem; padding:0.05rem 0.1rem;"
)
GAYA_KOTAK = (
    "white-space:pre-wrap; font-size:0.86rem; line-height:1.55; "
    "max-height:22rem; overflow-y:auto; padding:0.7rem; "
    "border:1px solid rgba(128,128,128,0.3); border-radius:0.4rem;"
)


def isi_asli(dokumen: Any) -> str:
    """Isi potongan tanpa awalan konteks yang ditempelkan saat pengindeksan."""
    return POLA_AWALAN.sub("", dokumen.page_content, count=1)


def _rapikan(teks: str | None) -> str:
    """Rapikan spasi tanpa menghapus struktur baris.

    Spasi ganda hasil ekstraksi PDF diratakan, tapi pergantian baris
    dipertahankan — teks berpasal tak terbaca kalau dijadikan satu paragraf.
    """
    teks = re.sub(r"[ \t]+", " ", teks or "")
    return re.sub(r"\n{3,}", "\n\n", teks).strip()


# --------------------------------------------------------------- berkas asli
@lru_cache(maxsize=64)
def _cari_berkas(nama_berkas: str) -> Path | None:
    """Cari berkas asli di dalam folder dokumen. None bila tak ada.

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
def _halaman_pdf(jalur: Path, nomor: int, cap_waktu: float) -> str | None:
    """Teks satu halaman PDF.

    cap_waktu ikut menjadi kunci cache supaya berkas yang diperbarui tidak
    terus terbaca dari cache lama.
    """
    from pypdf import PdfReader

    halaman = PdfReader(str(jalur)).pages
    if not 0 <= nomor < len(halaman):
        return None
    return _rapikan(halaman[nomor].extract_text() or "")


@lru_cache(maxsize=64)
def _isi_teks(jalur: Path, cap_waktu: float) -> str:
    return _rapikan(Path(jalur).read_text(encoding="utf-8"))


def _bagian_markdown(teks: str, metadata: Mapping[str, Any]) -> str:
    """Ambil satu bagian Markdown berdasarkan judulnya.

    Notulen dipotong per heading, jadi metadatanya menyimpan nama bab/bagian —
    bukan nomor halaman. Judul itu dicari kembali di berkas asli, lalu dipotong
    sampai judul setingkat berikutnya.
    """
    judul = metadata.get("bagian") or metadata.get("bab")
    if not judul:
        return teks

    for tingkat in ("## ", "# "):
        awal = teks.find(f"{tingkat}{judul}")
        if awal == -1:
            continue
        lanjut = teks.find(f"\n{tingkat}", awal + 1)
        return teks[awal : lanjut if lanjut != -1 else len(teks)].strip()
    return teks


def halaman_asli(metadata: Mapping[str, Any]) -> tuple[str | None, str]:
    """Kembalikan (teks, keterangan) halaman/bagian asli dari sebuah sitasi.

    teks None berarti berkasnya tidak bisa dibaca — pemanggil harus
    mengatakannya apa adanya, bukan menampilkan halaman kosong seolah-olah
    dokumennya memang kosong.
    """
    jalur = _cari_berkas(metadata.get("source", ""))
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
        return (
            _bagian_markdown(_isi_teks(jalur, cap), metadata),
            f"Bagian asli dari {jalur.name}",
        )
    except Exception as e:  # noqa: BLE001 - pemanggil hanya perlu tahu gagalnya
        return None, f"Gagal membaca berkas asli: {type(e).__name__}"


# ---------------------------------------------------------------- penyorotan
def belah(teks_halaman: str, kutipan: str) -> tuple[str, str, str]:
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
        return (
            teks_halaman[:posisi],
            kutipan,
            teks_halaman[posisi + len(kutipan) :],
        )

    # Cadangan: cocokkan tanpa memedulikan pergantian baris. Pemotong kadang
    # memangkas spasi di tepi potongan sehingga pencocokan mentah meleset.
    datar_halaman = re.sub(r"\s+", " ", teks_halaman)
    datar_kutipan = re.sub(r"\s+", " ", kutipan)
    posisi = datar_halaman.find(datar_kutipan)
    if posisi == -1:
        return teks_halaman, "", ""

    def _asli(indeks_datar: int) -> int:
        """Petakan posisi pada teks datar kembali ke teks asli."""
        lewat = i = 0
        while i < len(teks_halaman) and lewat < indeks_datar:
            if not (
                teks_halaman[i].isspace()
                and i + 1 < len(teks_halaman)
                and teks_halaman[i + 1].isspace()
            ):
                lewat += 1
            i += 1
        return i

    awal = _asli(posisi)
    akhir = _asli(posisi + len(datar_kutipan))
    return teks_halaman[:awal], teks_halaman[awal:akhir], teks_halaman[akhir:]


def sorot_html(teks_halaman: str, kutipan: str) -> str:
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


# --------------------------------------------------------------- pemeriksaan
def periksa_korpus(potongan) -> tuple[int, int]:
    """Pastikan tiap potongan benar-benar bisa ditemukan kembali di aslinya.

    Uji murah yang sangat berharga: bila sebuah potongan tidak ditemukan di
    dokumen asalnya, berarti yang ditampilkan ke pengguna sebagai 'sumber'
    tidak bisa dipertanggungjawabkan.
    """
    potongan = list(potongan)
    ketemu = 0
    for d in potongan:
        teks, _ = halaman_asli(d.metadata)
        if teks is None:
            continue
        if belah(teks, isi_asli(d))[1]:
            ketemu += 1
    return ketemu, len(potongan)
