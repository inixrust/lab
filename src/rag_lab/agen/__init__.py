# -*- coding: utf-8 -*-
"""Agent minimal, sepenuhnya on-premise — modul A2 / A6.

Inti pelajaran: sebuah agent pada dasarnya hanyalah SEBUAH LINGKARAN.

    1. Model diberi daftar alat (tool) dan sebuah pertanyaan.
    2. Model memutuskan: memanggil sebuah alat, atau menjawab langsung.
    3. Kalau memanggil alat, KITA yang menjalankannya, lalu hasilnya
       dikembalikan ke model.
    4. Ulangi sampai model berhenti memanggil alat dan memberi jawaban akhir.

Bandingkan dengan pembangkitan/: di sana alurnya TETAP (retrieve -> generate).
Di sini MODEL yang memilih langkahnya sendiri, dan bisa menggabungkan beberapa
alat. Itulah yang membuatnya 'agentic'.

Semua tetap lokal: qwen3 lewat Ollama melakukan tool-calling. Tidak ada API
luar, sesuai syarat kelas — semuanya masih jalan tanpa internet.

    aritmetika  kalkulator yang menolak apa pun selain aritmetika (A4)
    alat        dua alat yang boleh dipanggil model
    lingkaran   lingkaran agent-nya sendiri
"""
from __future__ import annotations

from .alat import ALAT, PETA_ALAT, cari_kebijakan, hitung
from .aritmetika import hitung_ekspresi
from .lingkaran import MAKS_LANGKAH, SISTEM, jalankan_agen

__all__ = [
    "ALAT",
    "MAKS_LANGKAH",
    "PETA_ALAT",
    "SISTEM",
    "cari_kebijakan",
    "hitung",
    "hitung_ekspresi",
    "jalankan_agen",
]
