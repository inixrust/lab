# -*- coding: utf-8 -*-
"""Pustaka lab RAG PT Nusantara Cipta Solusi (TX-AI11).

Susunan paket mengikuti tahapan pipeline, bukan ukuran berkas:

    konfig        semua setelan — satu-satunya tempat mengubah perilaku
    galat         kelas galat lab, agar penanganan galat bisa spesifik
    sidik_jari    catatan DENGAN APA indeks dibangun (pelajaran F3)
    tampilan      pencetak potongan & keterangan letak untuk sitasi
    model/        pembuat objek embedding, LLM, reranker (+ mode tiruan)
    pengindeksan/ muat -> potong -> embed -> simpan
    pengambilan/  vektor + BM25 -> RRF -> susun ulang
    pembangkitan/ konteks -> prompt -> jawaban ber-sitasi
    agen/         alat + lingkaran agent (modul A2/A6)
    evaluasi/     set uji dan metrik
    diagnosa      pemeriksaan kesiapan (dipakai cek.py)
    antarmuka     aplikasi Streamlit (modul A5)
    perintah/     titik masuk baris perintah; berkas di src/ hanya pembungkus

Berkas di `src/` (cek.py, indeks.py, cari.py, ...) sengaja dibiarkan tipis:
semua perintah di PANDUAN-PESERTA.md tetap berjalan apa adanya, sementara
logikanya bisa diimpor dan diuji tanpa menjalankan skrip.

Modul ini sengaja TIDAK mengimpor apa pun secara langsung. `cek.py` harus
tetap bisa berjalan di mesin yang paketnya belum lengkap — dan itu mustahil
bila mengimpor `rag_lab` ikut menarik langchain.
"""

__version__ = "1.0.0"
