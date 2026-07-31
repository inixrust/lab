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
JENIS_PER_PERAN = {
    "staf": {"edaran", "sop"},
    "pimpinan": {"edaran", "notulen", "sop"},
}

# Alat yang boleh dipanggil agent, per peran. Agent hanya boleh seampuh peran
# penggunanya — daftar alat yang diberikan ke bind_tools() pun harus disaring.
ALAT_PER_PERAN = {
    "staf": {"cari_kebijakan", "hitung"},
    "pimpinan": {"cari_kebijakan", "hitung"},
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
    # TODO L3.4-1a: sertakan hak akses, bukan hanya status. Kembalikan:
    #     {"status": konfig.STATUS_BERLAKU,
    #      "jenis": set(jenis_boleh(pengguna))}
    #
    # Sebelum dikerjakan, yang disaring hanya status — artinya staf ikut
    # membaca notulen. Jalankan dulu apa adanya:
    #     python tanya.py --bandingkan "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"
    # Kedua peran akan sama-sama menerima Rp 180.000.000. Itulah keadaan yang
    # sedang Anda perbaiki.
    return {"status": konfig.STATUS_BERLAKU}


def boleh_lihat(pengguna, metadata):
    """Periksa satu potongan. Ini PAGAR TERAKHIR, sesudah pencarian.

    Kenapa diperiksa dua kali, padahal penyaringnya sudah dipasang di hulu?
    Karena jalur pengambilan lebih dari satu (vektor, BM25, dan nanti cache),
    dan cukup SATU jalur yang lupa disaring untuk membocorkan semuanya —
    persis kegagalan senyap yang sudah dicatat di cari.py soal BM25.

    Pemeriksaan ini murah dan tidak memanggil model. Jangan dihapus dengan
    alasan mubazir; justru mubazirnya yang menjadi jaminan.
    """
    # TODO L3.4-1b: kembalikan True HANYA bila keduanya terpenuhi:
    #     metadata.get("jenis")  ada di dalam jenis_boleh(pengguna), DAN
    #     metadata.get("status") sama dengan konfig.STATUS_BERLAKU
    #
    # Sesudah TODO L3.4-1a selesai, pagar ini memang tidak akan pernah membuang
    # apa pun. Itu bukan alasan melewatkannya — lihat penjelasan di atas.
    return True


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


if __name__ == "__main__":
    print("Peta hak akses\n")
    for peran in sorted(JENIS_PER_PERAN):
        orang = {"peran": peran}
        print(f"  {peran:10s} jenis : {sorted(jenis_boleh(orang))}")
        print(f"  {'':10s} alat  : {sorted(alat_boleh(orang))}")
        print(f"  {'':10s} sidik : {sidik(orang)}")
        print(f"  {'':10s} saring: {saring_untuk(orang)}\n")

    print("Peran tak dikenal diturunkan ke peran paling sempit:")
    for coba in ("direktur", "", None, "PIMPINAN"):
        print(f"  {str(coba)!r:12s} -> {bereskan({'peran': coba})['peran']}")
    sys.exit(0)
