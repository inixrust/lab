# -*- coding: utf-8 -*-
"""Jalur cadangan bila Ollama bermasalah di tengah kelas.

Mutunya buruk dengan sengaja. Yang dijaga di sini bukan mutu jawaban,
melainkan agar SELURUH ALUR tetap berjalan: peserta yang Ollama-nya bermasalah
masih bisa mengikuti pelajaran tentang chunking, metadata, dan evaluasi.
"""
from __future__ import annotations

import hashlib
from typing import Any, Sequence

from .. import konfig


class EmbeddingTiruan:
    """Embedding palsu berbasis hash. HANYA untuk berjaga-jaga.

    Ia tidak memahami makna sama sekali, hanya mengubah kata menjadi angka
    secara deterministik.

    Justru berguna sebagai bahan ajar: bandingkan angka recall-nya dengan
    bge-m3, dan peserta melihat sendiri berapa besar sumbangan embedding yang
    benar-benar memahami bahasa.
    """

    DIMENSI = 256

    def _vektor(self, teks: str) -> list[float]:
        vektor = [0.0] * self.DIMENSI
        kata = "".join(c.lower() if c.isalnum() else " " for c in teks).split()
        for k in kata:
            sidik = int(hashlib.md5(k.encode()).hexdigest(), 16)
            vektor[sidik % self.DIMENSI] += 1.0
        panjang = sum(x * x for x in vektor) ** 0.5 or 1.0
        return [x / panjang for x in vektor]

    def embed_documents(self, daftar: Sequence[str]) -> list[list[float]]:
        return [self._vektor(t) for t in daftar]

    def embed_query(self, teks: str) -> list[float]:
        return self._vektor(teks)


class BalasanTiruan:
    """Meniru bentuk balasan LangChain secukupnya: hanya `.content`."""

    def __init__(self, isi: str) -> None:
        self.content = isi


class LLMTiruan:
    """Model chat palsu. Tidak merangkai jawaban, hanya mengakui keadaannya.

    Sengaja TIDAK punya `bind_tools`: agent memang tidak bisa berjalan tanpa
    model sungguhan, dan lingkaran agent memeriksa hal itu untuk memberi pesan
    yang jelas alih-alih gagal di tengah jalan.
    """

    def invoke(self, masukan: Any) -> BalasanTiruan:
        teks = str(masukan)
        if "KONTEKS:" in teks and len(teks) > 200:
            return BalasanTiruan(
                "[MODE TIRUAN] Model bahasa tidak aktif, jadi jawaban tidak "
                "dirangkai. Potongan yang berhasil diambil sudah ditampilkan "
                "di atas — itulah yang penting untuk pelajaran ini. [1]"
            )
        return BalasanTiruan("[MODE TIRUAN]")


def aktif() -> bool:
    """Apakah lab sedang berjalan dengan model tiruan?"""
    return konfig.MODE_TIRUAN
