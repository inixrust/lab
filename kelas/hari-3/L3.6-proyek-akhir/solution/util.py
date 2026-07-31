# -*- coding: utf-8 -*-
"""Fungsi tampilan kecil yang dipakai beberapa berkas."""


# ------------------------------------------------------------- baris perintah
# Sesudah peningkatan 5 dan 6, hampir semua skrip menerima "--peran <nama>".
# Menyalin potongan penguraiannya ke lima berkas berarti lima tempat yang bisa
# berbeda sendiri-sendiri; ini versi tunggalnya. Sengaja TIDAK memakai argparse:
# skrip lab dipanggil dengan pertanyaan bebas sebagai sisa argumen, dan argparse
# akan menuntut tanda kutip di tempat yang tidak diduga peserta.
def ambil_bendera(argumen, nama, bawaan=None):
    """Ambil nilai "--nama nilai" dari daftar argumen, sekaligus membuangnya.

    Daftar `argumen` diubah di tempat, jadi sisanya bisa langsung disatukan
    menjadi pertanyaan. Bendera tanpa nilai di belakangnya dianggap tidak ada —
    lebih baik memakai bawaan daripada menjatuhkan program karena salah ketik.
    """
    if nama not in argumen:
        return bawaan
    i = argumen.index(nama)
    if i + 1 >= len(argumen):
        del argumen[i:]
        return bawaan
    nilai = argumen[i + 1]
    del argumen[i:i + 2]
    return nilai


def ambil_saklar(argumen, nama):
    """True bila "--nama" ada; bendera itu sekaligus dibuang dari daftar."""
    if nama in argumen:
        argumen.remove(nama)
        return True
    return False


def lokasi(metadata):
    """Keterangan letak potongan untuk sitasi, dengan nomor halaman manusia.

    PyPDFLoader menomori halaman mulai 0. Nomor mentah itu dipakai apa adanya
    oleh `set_uji.json` dan `nilai.py`, dan memang harus begitu — evaluasi
    membandingkan metadata, bukan teks tampilan.

    Tetapi tidak ada dokumen yang punya "halaman 0". Menampilkannya ke pengguna
    membuat sitasi tidak bisa diverifikasi: orang membuka PDF-nya, mencari
    halaman 0, dan tidak menemukan apa pun. Sitasi yang tidak bisa dicek sama
    saja dengan tidak ada sitasi. Karena itu penyesuaian dilakukan DI SINI, di
    lapisan tampilan, tanpa mengubah metadata yang tersimpan di indeks.

    Urutan yang dipakai:
      1. `page_label` — label cetak asli dari PDF ("1", "ii", "A-3"). Paling
         benar: inilah yang tertulis di halaman itu sendiri.
      2. `page` + 1 — bila PDF tidak membawa label.
      3. nama bagian/bab — untuk sumber tanpa halaman, misalnya Markdown.
    """
    label = metadata.get("page_label")
    if label not in (None, ""):
        return f"hal. {label}"

    halaman = metadata.get("page")
    if isinstance(halaman, int):
        return f"hal. {halaman + 1}"
    if halaman is not None:
        return f"hal. {halaman}"

    bagian = metadata.get("bagian") or metadata.get("bab")
    return f"bagian: {bagian}" if bagian else "sumber"
