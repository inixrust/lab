# -*- coding: utf-8 -*-
"""Pembuat objek model, dengan jalur cadangan bila Ollama bermasalah — versi Hari 1.

Seluruh berkas lain cukup memanggil `ambil_embedding()` dan `ambil_llm()` tanpa
peduli apakah yang berjalan Ollama sungguhan atau mode tiruan. Reranker baru
diperkenalkan di Hari 2, jadi belum ada di sini.
"""
import hashlib

import konfig


# ============================================================ mode tiruan
class EmbeddingTiruan:
    """Embedding palsu berbasis hash. HANYA untuk berjaga-jaga.

    Mutunya buruk — tidak memahami makna, hanya mengubah kata menjadi angka
    secara deterministik. Tapi seluruh alur pipeline tetap berjalan.
    """
    DIMENSI = 256

    def _vektor(self, teks: str):
        v = [0.0] * self.DIMENSI
        kata = "".join(c.lower() if c.isalnum() else " " for c in teks).split()
        for k in kata:
            h = int(hashlib.md5(k.encode()).hexdigest(), 16)
            v[h % self.DIMENSI] += 1.0
        panjang = sum(x * x for x in v) ** 0.5 or 1.0
        return [x / panjang for x in v]

    def embed_documents(self, daftar):
        return [self._vektor(t) for t in daftar]

    def embed_query(self, teks):
        return self._vektor(teks)


class LLMTiruan:
    """Model chat palsu. Mengembalikan penanda saja."""
    class _Balasan:
        def __init__(self, isi):
            self.content = isi

    def invoke(self, masukan):
        teks = str(masukan)
        if "KONTEKS:" in teks and len(teks) > 200:
            return self._Balasan(
                "[MODE TIRUAN] Model bahasa tidak aktif, jadi jawaban tidak "
                "dirangkai. Potongan yang berhasil diambil sudah ditampilkan "
                "di atas — itulah yang penting untuk pelajaran ini. [1]"
            )
        return self._Balasan("[MODE TIRUAN]")


# ============================================================ pembuat objek
def ambil_embedding():
    if konfig.MODE_TIRUAN:
        return EmbeddingTiruan()
    from langchain_ollama import OllamaEmbeddings
    ekstra = {"base_url": konfig.OLLAMA_URL} if konfig.OLLAMA_URL else {}
    return OllamaEmbeddings(model=konfig.MODEL_EMBEDDING, **ekstra)


def ambil_llm():
    if konfig.MODE_TIRUAN:
        return LLMTiruan()
    from langchain_ollama import ChatOllama
    ekstra = {"base_url": konfig.OLLAMA_URL} if konfig.OLLAMA_URL else {}
    return ChatOllama(model=konfig.MODEL_CHAT, temperature=0, **ekstra)
