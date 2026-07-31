# -*- coding: utf-8 -*-
"""Evaluasi: mengubah 'rasanya lebih baik' menjadi angka yang bisa dibandingkan.

    python nilai.py              evaluasi retrieval + penyaringan status
    python nilai.py --penolakan  ikut menguji kemampuan menolak (butuh model)

Evaluasi retrieval sengaja TIDAK memanggil model bahasa: cepat, murah,
objektif, dan bisa dijalankan setiap kali ada perubahan setelan.
"""
import json
import sys
from collections import defaultdict

import konfig
from cari import cari_vektor, cari_hybrid, ambil_terbaik


def muat_set_uji():
    if not konfig.SET_UJI.exists():
        raise FileNotFoundError(f"Set uji tidak ditemukan: {konfig.SET_UJI}")
    return json.loads(konfig.SET_UJI.read_text(encoding="utf-8"))


def _cocok(potongan, kasus):
    """Apakah salah satu potongan berasal dari sumber dan halaman yang benar?

    Nomor halaman di set_uji.json memakai indeks mulai 0, mengikuti
    PyPDFLoader. Halaman pertama bernomor 0 di sini.

    Jangan bingung bila sitasi di layar menyebut "hal. 1" untuk kasus yang di
    set_uji.json tertulis halaman 0: keduanya menunjuk halaman yang sama.
    Evaluasi memakai indeks mentah, tampilan memakai nomor cetak — lihat
    util.lokasi.
    """
    # TODO L2.4-2: Definisikan apa yang dihitung sebagai 'kena': salah satu potongan berasal dari sumber DAN halaman yang benar menurut kasus uji. Ini inti pengukuran recall.
    return False


def evaluasi_retrieval(ambil_fn, nama, k=None, rinci=True):
    k = k or konfig.JUMLAH_AKHIR
    kasus_semua = [x for x in muat_set_uji() if not x.get("harus_menolak")]

    kena = 0
    per_jenis = defaultdict(lambda: [0, 0])
    gagal = []

    for kasus in kasus_semua:
        potongan = ambil_fn(kasus["tanya"])[:k]
        benar = _cocok(potongan, kasus)
        kena += benar
        per_jenis[kasus["jenis"]][0] += benar
        per_jenis[kasus["jenis"]][1] += 1
        if not benar:
            gagal.append((kasus["jenis"], kasus["tanya"]))

    recall = kena / len(kasus_semua)
    print(f"\n=== {nama} ===")
    print(f"  recall@{k} keseluruhan : {recall:.0%}  ({kena}/{len(kasus_semua)})")
    for jenis in sorted(per_jenis):
        b, t = per_jenis[jenis]
        print(f"    {jenis:16s} {b}/{t}")
    if gagal and rinci:
        print("  yang terlewat:")
        for jenis, tanya in gagal:
            print(f"    [{jenis}] {tanya}")
    return recall


def evaluasi_filter_status():
    """Ukur manfaat penyaringan metadata status — inti modul B3.

    Jebakan korpus: SOP-03 (DICABUT) dan SOP-05 (BERLAKU) saling bertentangan.
    Recall biasa tidak menangkapnya — kedua dokumen sama-sama 'relevan' menurut
    kesamaan makna. Yang berbahaya adalah dokumen yang sudah dicabut IKUT masuk
    ke konteks, karena model lalu bisa menjawab dari aturan yang tidak berlaku.

    Metrik ini menghitung, untuk pertanyaan bertipe 'versi', berapa kali dokumen
    dicabut bocor ke dalam potongan yang diambil — dengan dan tanpa penyaring.
    Tidak memanggil model: cukup memeriksa metadata potongan.
    """
    kasus = [x for x in muat_set_uji() if x.get("jenis") == "versi"]
    if not kasus:
        print("\n  Tidak ada kasus 'versi' di set uji.")
        return None

    print(f"\n=== PENYARINGAN STATUS — {len(kasus)} kasus versi (B3) ===")
    bocor_tanpa = bocor_dengan = 0
    for x in kasus:
        # saring={} -> tanpa penyaring apa pun; saring=None -> filter bawaan 'berlaku'
        tanpa = ambil_terbaik(x["tanya"], saring={})
        dengan = ambil_terbaik(x["tanya"])
        ada_tanpa = any(d.metadata.get("status") == konfig.STATUS_DICABUT for d in tanpa)
        ada_dengan = any(d.metadata.get("status") == konfig.STATUS_DICABUT for d in dengan)
        bocor_tanpa += ada_tanpa
        bocor_dengan += ada_dengan
        print(f"  tanpa filter: {'DICABUT bocor' if ada_tanpa else 'aman':13s}"
              f" | dengan filter: {'DICABUT bocor' if ada_dengan else 'aman':13s}"
              f" | {x['tanya']}")

    print(f"\n  dokumen dicabut masuk konteks:")
    print(f"    tanpa penyaring  : {bocor_tanpa}/{len(kasus)}")
    print(f"    dengan penyaring : {bocor_dengan}/{len(kasus)}")
    print("  Penyaringan status inilah yang mencegah jawaban SALAH SECARA")
    print("  ORGANISASI (mis. '8 karakter' dari SOP yang sudah dicabut) —")
    print("  bukan sekadar kurang tepat. Ditegakkan di kode, bukan di prompt.")
    return bocor_tanpa, bocor_dengan


def evaluasi_penolakan():
    """Menguji apakah sistem BERANI berkata tidak tahu.

    Sistem yang tidak pernah menolak adalah sistem yang selalu mengarang saat
    konteksnya tidak memadai — dan itu jauh lebih berbahaya daripada sistem
    yang sesekali menjawab 'tidak ditemukan'.
    """
    from jawab import jawab, TIDAK_DITEMUKAN

    kasus = [x for x in muat_set_uji() if x.get("harus_menolak")]
    if not kasus:
        print("\n  Tidak ada kasus penolakan di set uji. Tambahkan.")
        return None

    benar = 0
    print(f"\n=== KEMAMPUAN MENOLAK ({len(kasus)} kasus) ===")
    for x in kasus:
        isi, _, _ = jawab(x["tanya"], tampilkan_potongan=False)
        menolak = TIDAK_DITEMUKAN in isi
        benar += menolak
        print(f"  {'MENOLAK ' if menolak else 'MENJAWAB'}  {x['tanya']}")
        if not menolak:
            print(f"            -> {isi[:90]}...")
    print(f"  benar menolak: {benar}/{len(kasus)} ({benar/len(kasus):.0%})")
    return benar / len(kasus)


if __name__ == "__main__":
    print("Setelan aktif:")
    konfig.ringkas()

    hasil = {}
    for nama, fn in [
        ("VEKTOR SAJA", lambda t: cari_vektor(t, k=konfig.JUMLAH_AKHIR)),
        ("HYBRID", cari_hybrid),
        ("HYBRID + SUSUN ULANG", ambil_terbaik),
    ]:
        hasil[nama] = evaluasi_retrieval(fn, nama)

    print("\n" + "=" * 52)
    print("RINGKASAN")
    for nama, r in hasil.items():
        print(f"  {nama:24s} recall@{konfig.JUMLAH_AKHIR} = {r:.0%}")
    print("=" * 52)
    print("Inilah bentuk perbaikan yang bisa dipertanggungjawabkan:")
    print("angka sebelum dan sesudah, pada set uji yang sama.")

    # Cepat dan tanpa model — selalu dijalankan karena inilah bukti terukur B3.
    evaluasi_filter_status()

    if "--penolakan" in sys.argv:
        evaluasi_penolakan()
