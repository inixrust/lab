# -*- coding: utf-8 -*-
"""Metrik lab: recall retrieval, kebocoran dokumen dicabut, kemampuan menolak."""
from __future__ import annotations

from collections import defaultdict
from typing import Callable, Sequence

from langchain_core.documents import Document

from .. import konfig
from ..pengambilan.pencari import ambil_terbaik, cari_hybrid, cari_vektor
from .set_uji import cocok, kasus_penolakan, kasus_retrieval, kasus_versi

# Sebuah pencari: pertanyaan masuk, daftar potongan keluar.
Pencari = Callable[[str], Sequence[Document]]


def metode_baku() -> list[tuple[str, Pencari]]:
    """Ketiga metode pencarian sebagai pasangan (nama, fungsi).

    Berurutan dari yang paling sederhana — itulah urutan yang dibandingkan di
    modul B6. Nama dipakai apa adanya sebagai judul di laporan.
    """
    return [
        ("VEKTOR SAJA", lambda t: cari_vektor(t, k=konfig.JUMLAH_AKHIR)),
        ("HYBRID", cari_hybrid),
        ("HYBRID + SUSUN ULANG", ambil_terbaik),
    ]


def evaluasi_retrieval(
    ambil_fn: Pencari, nama: str, k: int | None = None, rinci: bool = True
) -> float:
    """Recall@k satu metode pencarian, dirinci per jenis pertanyaan."""
    k = k or konfig.JUMLAH_AKHIR
    kasus_semua = kasus_retrieval()

    kena = 0
    per_jenis: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    gagal: list[tuple[str, str]] = []

    for kasus in kasus_semua:
        potongan = ambil_fn(kasus["tanya"])[:k]
        benar = cocok(potongan, kasus)
        kena += benar
        per_jenis[kasus["jenis"]][0] += benar
        per_jenis[kasus["jenis"]][1] += 1
        if not benar:
            gagal.append((kasus["jenis"], kasus["tanya"]))

    recall = kena / len(kasus_semua)
    print(f"\n=== {nama} ===")
    print(f"  recall@{k} keseluruhan : {recall:.0%}  ({kena}/{len(kasus_semua)})")
    for jenis in sorted(per_jenis):
        benar_jenis, total_jenis = per_jenis[jenis]
        print(f"    {jenis:16s} {benar_jenis}/{total_jenis}")
    if gagal and rinci:
        print("  yang terlewat:")
        for jenis, tanya in gagal:
            print(f"    [{jenis}] {tanya}")
    return recall


def bandingkan_metode(k: int | None = None) -> dict[str, float]:
    """Jalankan ketiga metode pada set uji yang sama, lalu ringkas hasilnya.

    Inilah bentuk perbaikan yang bisa dipertanggungjawabkan: angka sebelum dan
    sesudah, pada set uji yang sama.
    """
    k = k or konfig.JUMLAH_AKHIR
    hasil = {nama: evaluasi_retrieval(fn, nama, k=k) for nama, fn in metode_baku()}

    print("\n" + "=" * 52)
    print("RINGKASAN")
    for nama, recall in hasil.items():
        print(f"  {nama:24s} recall@{k} = {recall:.0%}")
    print("=" * 52)
    print("Inilah bentuk perbaikan yang bisa dipertanggungjawabkan:")
    print("angka sebelum dan sesudah, pada set uji yang sama.")
    return hasil


def evaluasi_filter_status() -> tuple[int, int] | None:
    """Ukur manfaat penyaringan metadata status — inti modul B3.

    Jebakan korpus: SOP-03 (DICABUT) dan SOP-05 (BERLAKU) saling bertentangan.
    Recall biasa tidak menangkapnya — kedua dokumen sama-sama 'relevan' menurut
    kesamaan makna. Yang berbahaya adalah dokumen yang sudah dicabut IKUT masuk
    ke konteks, karena model lalu bisa menjawab dari aturan yang tidak berlaku.

    Metrik ini menghitung, untuk pertanyaan bertipe 'versi', berapa kali dokumen
    dicabut bocor ke dalam potongan yang diambil — dengan dan tanpa penyaring.
    Tidak memanggil model: cukup memeriksa metadata potongan.
    """
    kasus = kasus_versi()
    if not kasus:
        print("\n  Tidak ada kasus 'versi' di set uji.")
        return None

    def ada_dicabut(potongan: Sequence[Document]) -> bool:
        return any(d.metadata.get("status") == konfig.STATUS_DICABUT for d in potongan)

    print(f"\n=== PENYARINGAN STATUS — {len(kasus)} kasus versi (B3) ===")
    bocor_tanpa = bocor_dengan = 0
    for x in kasus:
        # saring={} -> tanpa penyaring apa pun; saring=None -> filter bawaan 'berlaku'
        ada_tanpa = ada_dicabut(ambil_terbaik(x["tanya"], saring={}))
        ada_dengan = ada_dicabut(ambil_terbaik(x["tanya"]))
        bocor_tanpa += ada_tanpa
        bocor_dengan += ada_dengan
        print(
            f"  tanpa filter: {'DICABUT bocor' if ada_tanpa else 'aman':13s}"
            f" | dengan filter: {'DICABUT bocor' if ada_dengan else 'aman':13s}"
            f" | {x['tanya']}"
        )

    print("\n  dokumen dicabut masuk konteks:")
    print(f"    tanpa penyaring  : {bocor_tanpa}/{len(kasus)}")
    print(f"    dengan penyaring : {bocor_dengan}/{len(kasus)}")
    print("  Penyaringan status inilah yang mencegah jawaban SALAH SECARA")
    print("  ORGANISASI (mis. '8 karakter' dari SOP yang sudah dicabut) —")
    print("  bukan sekadar kurang tepat. Ditegakkan di kode, bukan di prompt.")
    return bocor_tanpa, bocor_dengan


def evaluasi_penolakan() -> float | None:
    """Menguji apakah sistem BERANI berkata tidak tahu.

    Sistem yang tidak pernah menolak adalah sistem yang selalu mengarang saat
    konteksnya tidak memadai — dan itu jauh lebih berbahaya daripada sistem
    yang sesekali menjawab 'tidak ditemukan'.

    Satu-satunya metrik di modul ini yang memanggil model bahasa, jadi juga
    yang paling lambat.
    """
    from ..pembangkitan.penjawab import jawab

    kasus = kasus_penolakan()
    if not kasus:
        print("\n  Tidak ada kasus penolakan di set uji. Tambahkan.")
        return None

    benar = 0
    print(f"\n=== KEMAMPUAN MENOLAK ({len(kasus)} kasus) ===")
    for x in kasus:
        isi, _, _ = jawab(x["tanya"], tampilkan_potongan=False)
        menolak = konfig.TIDAK_DITEMUKAN in isi
        benar += menolak
        print(f"  {'MENOLAK ' if menolak else 'MENJAWAB'}  {x['tanya']}")
        if not menolak:
            print(f"            -> {isi[:90]}...")
    print(f"  benar menolak: {benar}/{len(kasus)} ({benar / len(kasus):.0%})")
    return benar / len(kasus)
