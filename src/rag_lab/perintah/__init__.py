# -*- coding: utf-8 -*-
"""Titik masuk baris perintah.

Setiap modul di sini punya satu fungsi `utama(argv=None) -> int` yang memuat
seluruh urusan baris perintah: penguraian argumen, pencetakan, dan kode keluar.
Berkas di `src/` hanya memanggilnya, sehingga perintah di PANDUAN-PESERTA.md
tetap sama persis:

    python cek.py            python cari.py "pertanyaan"
    python muat.py           python jawab.py "pertanyaan"
    python indeks.py         python nilai.py
    python agen.py "..."     streamlit run app.py

Bentuk `python -m rag_lab.perintah.cari "pertanyaan"` juga berjalan.
"""
