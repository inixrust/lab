# -*- coding: utf-8 -*-
"""Melayani satu pertanyaan: izin -> singgahan -> cari -> jawab -> periksa.

    python tanya.py --peran staf     "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"
    python tanya.py --peran pimpinan "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"
    python tanya.py --bandingkan     "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"

Inilah jawab.py dari hari sebelumnya, tetapi dengan tiga hal yang selalu
dituntut sistem sungguhan dan tidak pernah ada di demo:

    izin.py       siapa boleh melihat apa      (guardrail di kode)
    singgahan.py  jawaban dipakai ulang        (dikunci per hak akses)
    jejak.py      apa yang terjadi tadi        (observability)

Urutannya bukan selera. IZIN DIHITUNG LEBIH DULU, karena hasilnya ikut
menentukan kunci cache. Membalik dua langkah ini persis menghasilkan kebocoran
yang diperagakan singgahan.py.
"""
import sys

import izin
import jejak as modul_jejak
import konfig
import singgahan
import util
from cari import ambil_terbaik
from jawab import periksa_sitasi, susun_jawaban
from model import ambil_llm

_llm = None


def _model():
    global _llm
    if _llm is None:
        _llm = ambil_llm()
    return _llm


def layani(pertanyaan, pengguna, pakai_singgahan=None):
    """Layani satu pertanyaan. Kembalikan dict berisi jawaban dan catatannya."""
    pengguna = izin.bereskan(pengguna)
    if pakai_singgahan is None:
        pakai_singgahan = konfig.PAKAI_SINGGAHAN

    jejak = modul_jejak.Jejak(pertanyaan, pengguna)

    # --- 1. izin: dihitung SEBELUM apa pun yang lain
    with jejak.langkah("izin") as langkah:
        saring = izin.saring_untuk(pengguna)
        langkah["jenis"] = sorted(saring["jenis"])
        langkah["sidik"] = izin.sidik(pengguna)

    # --- 2. singgahan: kuncinya memuat hak akses di atas
    with jejak.langkah("singgahan") as langkah:
        tersimpan = (singgahan.BERSAMA.ambil(pertanyaan, pengguna)
                     if pakai_singgahan else None)
        langkah["hasil"] = "kena" if tersimpan else "meleset"

    if tersimpan is not None:
        jejak.catat(singgahan="kena", ditolak=tersimpan["ditolak"],
                    jumlah_potongan=tersimpan["jumlah_potongan"],
                    sumber=tersimpan["sumber"], cakupan=tersimpan["cakupan"])
        jejak.tutup()
        return {**tersimpan, "potongan": [], "dari_singgahan": True,
                "jejak": jejak}

    # --- 3. cari, dengan penyaring izin terpasang di hulu
    with jejak.langkah("cari") as langkah:
        potongan = ambil_terbaik(pertanyaan, saring=saring)
        sebelum = len(potongan)

        # Pagar terakhir. Seharusnya tidak membuang apa pun — dan justru itu
        # gunanya: kalau angka ini pernah bukan nol, ada jalur pengambilan yang
        # lolos dari penyaring di hulu, dan Anda ingin tahu HARI ITU juga.
        potongan = izin.saring_potongan(pengguna, potongan)
        langkah["jumlah"] = len(potongan)
        langkah["dibuang_pagar_akhir"] = sebelum - len(potongan)

    if sebelum - len(potongan):
        print(f"  PERINGATAN: {sebelum - len(potongan)} potongan lolos penyaring "
              f"hulu dan baru tertahan di pagar terakhir. Periksa cari.py.")

    # --- 4. jawab
    with jejak.langkah("jawab"):
        isi = susun_jawaban(_model(), pertanyaan, potongan)

    # --- 5. periksa sitasi
    with jejak.langkah("periksa") as langkah:
        lapor = periksa_sitasi(isi, len(potongan))
        langkah["cakupan"] = lapor["cakupan"]
        langkah["hantu"] = sorted(lapor["hantu"])

    hasil = {
        "jawaban": isi,
        "ditolak": konfig.TIDAK_DITEMUKAN in isi,
        "jumlah_potongan": len(potongan),
        "sumber": sorted({d.metadata.get("source", "?") for d in potongan}),
        "cakupan": lapor["cakupan"],
    }

    jejak.catat(singgahan="meleset", **{k: hasil[k] for k in
                ("ditolak", "jumlah_potongan", "sumber", "cakupan")})
    jejak.tutup()

    if pakai_singgahan:
        singgahan.BERSAMA.simpan(pertanyaan, pengguna, hasil)

    return {**hasil, "potongan": potongan, "dari_singgahan": False,
            "jejak": jejak}


# ============================================================ tampilan
def _tampilkan(hasil, pengguna):
    print(f"\n--- peran: {pengguna['peran']} "
          f"{'(dari singgahan)' if hasil['dari_singgahan'] else ''}")
    for i, d in enumerate(hasil.get("potongan") or [], 1):
        cuplik = " ".join(d.page_content.split())[:70]
        print(f"  [{i}] {d.metadata.get('source', '?')[:30]:32s} "
              f"{util.lokasi(d.metadata):12s} {cuplik}...")
    print(f"\n  JAWABAN: {hasil['jawaban']}")
    print(f"  ditolak={hasil['ditolak']}  potongan={hasil['jumlah_potongan']}  "
          f"cakupan={hasil['cakupan']:.0%}")
    print(hasil["jejak"].ringkas_baris())


def _bandingkan(pertanyaan):
    """Pertanyaan yang sama, SEMUA peran. Bedanya harus terlihat, bukan diyakini.

    PENINGKATAN 5 — dulu fungsi ini membandingkan dua peran yang ditulis
    tetap ("staf", "pimpinan"). Begitu peran bertambah, perbandingan seperti
    itu diam-diam berhenti menguji peran yang baru: peran 'keuangan' bisa saja
    salah dipetakan berbulan-bulan tanpa satu pun pengujian menyentuhnya.
    Sekarang daftarnya dibaca dari izin.PERAN_TERURUT — satu sumber yang sama
    dengan peta hak aksesnya sendiri.
    """
    print(f"Pertanyaan: {pertanyaan}")
    hasil = {}
    for peran in izin.PERAN_TERURUT:
        pengguna = izin.bereskan({"peran": peran})
        hasil[peran] = layani(pertanyaan, pengguna)
        _tampilkan(hasil[peran], pengguna)

    print("\n" + "=" * 74)
    print("RINGKASAN PER PERAN")
    for peran in izin.PERAN_TERURUT:
        h = hasil[peran]
        print(f"  {peran:10s} {'DITOLAK ' if h['ditolak'] else 'dijawab '} "
              f"potongan={h['jumlah_potongan']:2d}  "
              f"sumber={', '.join(h['sumber']) or '-'}")

    # YANG DIPERIKSA DI SINI SENGAJA BUKAN "peran yang lebih luas melihat lebih
    # banyak sumber". Godaan itu besar, dan salah:
    #
    # pengambilan mengembalikan k potongan TERBAIK. Begitu dokumen yang lebih
    # cocok terbuka bagi peran yang lebih luas, dokumen yang tadi terambil untuk
    # peran sempit akan TERGESER keluar dari k — bukan karena hak aksesnya
    # berkurang, melainkan karena ada yang lebih relevan. Daftar sumbernya
    # memang tidak bersarang, dan memang tidak seharusnya bersarang.
    #
    # Yang benar-benar harus dijamin adalah KEBOCORAN: tidak boleh ada satu pun
    # potongan berjenis di luar hak akses perannya. Itu sifat yang bisa salah,
    # dan itulah yang diperiksa.
    print()
    bocor = []
    for peran in izin.PERAN_TERURUT:
        boleh = izin.jenis_boleh({"peran": peran})
        for d in hasil[peran].get("potongan") or []:
            if d.metadata.get("jenis") not in boleh:
                bocor.append((peran, d.metadata.get("source"),
                              d.metadata.get("jenis")))

    if bocor:
        print("BOCOR — potongan di luar hak akses ikut terambil:")
        for peran, sumber_bocor, jenis in bocor:
            print(f"  {peran}: {sumber_bocor} (jenis {jenis})")
        print("Periksa izin.saring_untuk dan penyaringan manual BM25 di cari.py.")
    else:
        print("Tidak ada kebocoran jenis dokumen: setiap peran hanya menerima")
        print("potongan yang memang boleh dilihatnya.")

    jawaban_beda = len({h["jawaban"] for h in hasil.values()}) > 1
    if jawaban_beda:
        print("Jawabannya BERBEDA antarperan — periksa kolom sumber di atas untuk")
        print("melihat dokumen mana yang tersedia bagi siapa.")
    else:
        print("Semua peran menerima jawaban yang sama. Wajar bila jawabannya")
        print("bersumber dari SOP/edaran yang boleh dibaca semua orang; coba")
        print("pertanyaan yang jawabannya hanya ada di notulen (mis. nilai")
        print("pengadaan) atau di kontrak (mis. nilai sewa pusat data).")

    # Dua peran dengan hak akses yang sama persis akan BERBAGI baris singgahan,
    # karena yang disidik adalah hak aksesnya, bukan orangnya (izin.sidik).
    # Ini bukan kebocoran — justru itulah rancangannya. Disebut di sini supaya
    # 'dari singgahan' di atas tidak dikira kesalahan.
    sidik = {}
    for peran in izin.PERAN_TERURUT:
        sidik.setdefault(izin.sidik({"peran": peran}), []).append(peran)
    kembar = [p for p in sidik.values() if len(p) > 1]
    if kembar:
        print("\nPeran dengan sidik izin identik (berbagi singgahan, memang begitu):")
        for kelompok in kembar:
            print(f"  {', '.join(kelompok)}")

    print(f"\nsinggahan: {singgahan.BERSAMA.statistik()}")


if __name__ == "__main__":
    argumen = sys.argv[1:]
    peran = "staf"
    if "--peran" in argumen:
        i = argumen.index("--peran")
        peran = argumen[i + 1]
        del argumen[i:i + 2]
    bandingkan = "--bandingkan" in argumen
    if bandingkan:
        argumen.remove("--bandingkan")

    tanya = " ".join(argumen) or \
        "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"

    if bandingkan:
        _bandingkan(tanya)
    else:
        orang = izin.bereskan({"peran": peran})
        print(f"Pertanyaan: {tanya}")
        _tampilkan(layani(tanya, orang), orang)
