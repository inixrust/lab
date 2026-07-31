# -*- coding: utf-8 -*-
"""Hak akses yang ditegakkan di KODE — modul A4 (guardrail).

    python izin.py

Ini kelanjutan langsung dari satu kalimat di cari.py:

    "aturan yang benar-benar tidak boleh dilanggar ditegakkan di kode,
     bukan dititipkan ke instruksi prompt."

Di sana yang ditegakkan baru satu hal: dokumen berstatus 'dicabut' tidak pernah
dikembalikan. Di sini prinsip yang sama dipakai untuk HAK AKSES per peran.

Kenapa tidak lewat prompt saja ("jangan sebutkan isi notulen kepada staf")?
Karena prompt adalah IMBAUAN, bukan pagar:
  - potongan rahasianya sudah terlanjur masuk ke konteks model, jadi kebocoran
    tinggal menunggu satu kalimat bujukan yang tepat;
  - ia juga sudah terlanjur tercatat di log, di cache, dan di jejak;
  - dan tidak ada yang bisa Anda tunjukkan ke auditor selain "modelnya kami
    minta baik-baik".

Penyaring di kode memutus semuanya di hulu: potongan yang tidak boleh dilihat
TIDAK PERNAH terambil, jadi tidak ada yang bisa bocor.

Pembagiannya sengaja dibuat sesederhana mungkin agar terlihat di kelas: peran
dipetakan ke JENIS dokumen, dan jenis sudah tersedia sebagai metadata sejak
muat.py (nama subfolder di dokumen/).
"""
import sys

import konfig

# ------------------------------------------------------------------ peran
# Notulen rapat memuat hal yang tidak untuk semua orang — pada korpus lab ini
# misalnya nilai pengadaan Rp 180.000.000 dan angka kepatuhan 2FA. SOP dan
# surat edaran memang diedarkan ke seluruh karyawan.
#
# Di sistem sungguhan peta ini datang dari direktori pengguna (LDAP/SSO),
# bukan ditulis di berkas. Yang TIDAK berubah: keputusannya tetap diambil di
# kode, sebelum pencarian dijalankan.
#
# PENINGKATAN 5 — dua hal ditambahkan sekaligus, dan keduanya memang sepasang:
#
#   a. KLASIFIKASI DOKUMEN BARU: 'kontrak'. Perjanjian dengan pihak ketiga
#      memuat nilai, denda, dan klausul pengakhiran. Sebelumnya satu-satunya
#      pilihan adalah menaruhnya di 'notulen' (salah secara arti) atau di
#      'sop' (terbuka untuk semua karyawan — salah secara akibat).
#
#   b. DUA PERAN BARU di antara staf dan pimpinan. Dengan hanya dua peran,
#      setiap kebutuhan membaca notulen memaksa orang dinaikkan menjadi
#      'pimpinan', dan hak akses meluber. Inilah cara peta hak akses membusuk
#      di sistem sungguhan: bukan karena dirancang salah, melainkan karena
#      tidak punya tingkat menengah saat dibutuhkan.
#
# Perhatikan bentuknya: setiap peran menyebutkan jenisnya SENDIRI, tidak
# mewarisi dari peran di bawahnya. Pewarisan terlihat rapi, tetapi membuat
# jawaban atas "siapa saja yang bisa membaca kontrak?" harus ditelusuri
# berantai. Untuk hak akses, daftar yang eksplisit lebih baik daripada daftar
# yang pintar.
JENIS_PER_PERAN = {
    "staf": {"edaran", "sop"},
    "sdm": {"edaran", "sop", "notulen"},
    "keuangan": {"edaran", "sop", "notulen", "kontrak"},
    "pimpinan": {"edaran", "notulen", "sop", "kontrak"},
}

# Urutan dari yang paling sempit ke yang paling luas. Dipakai tanya.py
# --bandingkan supaya perbedaan hak akses terlihat sebagai DERET, bukan sebagai
# dua kutub. Menuliskannya di sini juga membuat urutannya bisa diuji: himpunan
# jenis tiap peran harus mencakup peran sebelumnya (lihat pemeriksaan di bawah).
PERAN_TERURUT = ["staf", "sdm", "keuangan", "pimpinan"]

# Alat yang boleh dipanggil agent, per peran. Agent hanya boleh seampuh peran
# penggunanya — daftar alat yang diberikan ke bind_tools() pun harus disaring.
#
# hitung_tanggal (peningkatan 6) hanya berhitung hari kerja dan tidak menyentuh
# dokumen, jadi ia aman untuk semua peran. Tetap dituliskan satu per satu:
# begitu ada alat yang BERAKIBAT ke luar (mengirim surel, membuat tiket,
# menyetujui pengajuan), daftar inilah tempat membatasinya — dan daftar yang
# sudah terbiasa ditulis lengkap tidak akan tiba-tiba dilewati.
ALAT_PER_PERAN = {
    "staf": {"cari_kebijakan", "hitung", "hitung_tanggal"},
    "sdm": {"cari_kebijakan", "hitung", "hitung_tanggal"},
    "keuangan": {"cari_kebijakan", "hitung", "hitung_tanggal"},
    "pimpinan": {"cari_kebijakan", "hitung", "hitung_tanggal"},
}

PERAN_BAKU = "staf"


def bereskan(pengguna):
    """Kembalikan pengguna yang sudah dinormalkan.

    Peran yang tidak dikenal TIDAK dianggap galat, melainkan diturunkan ke
    peran paling sempit. Ini pilihan sadar: sistem izin harus gagal ke arah
    AMAN. Kalau peran salah ketik lalu diperlakukan sebagai 'pimpinan', tidak
    akan ada yang menyadarinya sampai terlambat.
    """
    pengguna = pengguna or {}
    peran = str(pengguna.get("peran", PERAN_BAKU)).strip().lower()
    if peran not in JENIS_PER_PERAN:
        peran = PERAN_BAKU
    return {"nama": pengguna.get("nama", "anonim"), "peran": peran}


def jenis_boleh(pengguna):
    """Himpunan jenis dokumen yang boleh dilihat pengguna ini."""
    return JENIS_PER_PERAN[bereskan(pengguna)["peran"]]


def alat_boleh(pengguna):
    """Himpunan nama alat yang boleh dipanggil agent untuk pengguna ini."""
    return ALAT_PER_PERAN.get(bereskan(pengguna)["peran"], set())


def saring_alat(pengguna, daftar_alat):
    """Saring daftar alat SEBELUM diikat ke model (bind_tools).

    Alat yang tidak diberikan tidak bisa dipanggil sama sekali — jauh lebih
    kuat daripada menuliskan 'jangan panggil alat X' di prompt sistem.
    """
    boleh = alat_boleh(pengguna)
    return [a for a in daftar_alat if a.name in boleh]


# ------------------------------------------------------------- penyaring
def saring_untuk(pengguna):
    """Penyaring metadata untuk pengguna ini — dipakai SEBELUM pencarian.

    Bentuknya dict biasa; nilainya boleh berupa satu nilai (harus sama persis)
    atau himpunan (harus salah satu). cari.py yang menerjemahkannya ke sintaks
    Chroma maupun ke penyaringan manual BM25.

    Penyaring status ikut disertakan di sini supaya pemanggil tidak perlu
    mengingat untuk menggabungkannya sendiri — satu fungsi, satu kebenaran.
    """
    return {
        "status": konfig.STATUS_BERLAKU,
        "jenis": set(jenis_boleh(pengguna)),
    }


def boleh_lihat(pengguna, metadata):
    """Periksa satu potongan. Ini PAGAR TERAKHIR, sesudah pencarian.

    Kenapa diperiksa dua kali, padahal penyaringnya sudah dipasang di hulu?
    Karena jalur pengambilan lebih dari satu (vektor, BM25, dan nanti cache),
    dan cukup SATU jalur yang lupa disaring untuk membocorkan semuanya —
    persis kegagalan senyap yang sudah dicatat di cari.py soal BM25.

    Pemeriksaan ini murah dan tidak memanggil model. Jangan dihapus dengan
    alasan mubazir; justru mubazirnya yang menjadi jaminan.
    """
    return (metadata.get("jenis") in jenis_boleh(pengguna)
            and metadata.get("status") == konfig.STATUS_BERLAKU)


def saring_potongan(pengguna, potongan):
    """Terapkan boleh_lihat() ke sekumpulan potongan."""
    return [d for d in potongan if boleh_lihat(pengguna, d.metadata)]


# ------------------------------------------------------------------ sidik
def sidik(pengguna):
    """Sidik jari hak akses — penanda 'sudut pandang' pengguna ini.

    Dipakai singgahan.py sebagai bagian kunci cache. Yang disidik adalah HAK
    AKSESNYA, bukan nama orangnya: dua staf yang berbeda melihat korpus yang
    sama persis, jadi jawaban untuk yang satu aman dipakai ulang untuk yang
    lain. Menyidik nama akan membuat cache nyaris tidak pernah kena.
    """
    return "jenis=" + ",".join(sorted(jenis_boleh(pengguna)))


def periksa_peta():
    """Uji mandiri peta hak akses. Kembalikan daftar keganjilan yang ditemukan.

    PENINGKATAN 5 — begitu perannya lebih dari dua, peta hak akses berhenti
    bisa diperiksa dengan membacanya sekilas. Tiga hal yang diperiksa di sini
    semuanya pernah terjadi di sistem sungguhan:

      1. peran di PERAN_TERURUT yang tidak punya entri jenis (salah ketik saat
         menambah peran — akibatnya semua yang memakainya diam-diam turun ke
         peran baku);
      2. peran yang punya jenis tetapi tidak punya daftar alat (agent-nya jadi
         tidak bisa memanggil apa pun, dan gejalanya muncul jauh dari sebabnya);
      3. urutan yang tidak bersarang — peran yang lebih tinggi kehilangan jenis
         yang boleh dilihat peran di bawahnya. Ini yang paling berbahaya:
         tidak ada galat, hanya jawaban yang lebih miskin bagi orang yang
         seharusnya melihat lebih banyak.
    """
    keluhan = []
    for peran in PERAN_TERURUT:
        if peran not in JENIS_PER_PERAN:
            keluhan.append(f"peran '{peran}' ada di PERAN_TERURUT tapi tidak "
                           f"punya entri di JENIS_PER_PERAN")
        elif peran not in ALAT_PER_PERAN:
            keluhan.append(f"peran '{peran}' tidak punya entri di ALAT_PER_PERAN")

    lengkap = [p for p in PERAN_TERURUT if p in JENIS_PER_PERAN]
    for sempit, luas in zip(lengkap, lengkap[1:]):
        hilang = JENIS_PER_PERAN[sempit] - JENIS_PER_PERAN[luas]
        if hilang:
            keluhan.append(f"peran '{luas}' seharusnya mencakup '{sempit}', "
                           f"tetapi kehilangan {sorted(hilang)}")

    for peran in JENIS_PER_PERAN:
        if peran not in PERAN_TERURUT:
            keluhan.append(f"peran '{peran}' tidak tercantum di PERAN_TERURUT, "
                           f"jadi ia tidak akan pernah ikut dibandingkan")
    return keluhan


if __name__ == "__main__":
    print("Peta hak akses\n")
    for peran in PERAN_TERURUT:
        orang = {"peran": peran}
        print(f"  {peran:10s} jenis : {sorted(jenis_boleh(orang))}")
        print(f"  {'':10s} alat  : {sorted(alat_boleh(orang))}")
        print(f"  {'':10s} sidik : {sidik(orang)}")
        print(f"  {'':10s} saring: {saring_untuk(orang)}\n")

    print("Peran tak dikenal diturunkan ke peran paling sempit:")
    for coba in ("direktur", "", None, "PIMPINAN", "keuangan"):
        print(f"  {str(coba)!r:12s} -> {bereskan({'peran': coba})['peran']}")

    print("\nPemeriksaan peta:")
    masalah = periksa_peta()
    for m in masalah:
        print(f"  MASALAH: {m}")
    if not masalah:
        print("  peta konsisten — setiap peran bersarang di peran berikutnya.")
    sys.exit(1 if masalah else 0)
