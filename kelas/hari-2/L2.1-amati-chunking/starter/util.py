# -*- coding: utf-8 -*-
"""Fungsi tampilan kecil yang dipakai beberapa berkas."""


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
