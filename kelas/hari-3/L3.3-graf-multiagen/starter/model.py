# -*- coding: utf-8 -*-
"""Pembuat objek model, dengan jalur cadangan bila Ollama bermasalah.

Kenapa dipisah ke berkas sendiri: seluruh berkas lain cukup memanggil
`ambil_embedding()` dan `ambil_llm()` tanpa peduli apakah yang berjalan Ollama
sungguhan atau mode tiruan. Ini juga contoh praktik yang baik — lapisan model
diisolasi sehingga bisa diganti tanpa menyentuh logika RAG.
"""
import hashlib

import konfig


# ============================================================ mode tiruan
class EmbeddingTiruan:
    """Embedding palsu berbasis hash. HANYA untuk berjaga-jaga.

    Mutunya buruk — ia tidak memahami makna sama sekali, hanya mengubah kata
    menjadi angka secara deterministik. Tapi seluruh alur pipeline tetap
    berjalan, sehingga peserta yang Ollama-nya bermasalah masih bisa mengikuti
    pelajaran tentang chunking, metadata, dan evaluasi.

    Justru berguna sebagai bahan ajar: bandingkan angka recall-nya dengan
    bge-m3, dan peserta melihat sendiri berapa besar sumbangan embedding yang
    benar-benar memahami bahasa.
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
    """Model chat palsu. Mengembalikan potongan konteks apa adanya."""
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


# Reranker sengaja dimuat MALAS (baru saat dipakai pertama kali).
# Kalau dimuat saat import, berkas modelnya sekitar 2 GB akan diunduh diam-diam
# dan peserta mengira programnya menggantung. Ini jebakan lab yang nyata.
_penyusun = None


def ambil_reranker():
    """Kembalikan objek reranker, atau None bila tidak tersedia.

    Sengaja tidak melempar galat: di laptop 8 GB reranker memang sebaiknya
    dimatikan, dan lab harus tetap jalan tanpanya.
    """
    global _penyusun
    if not konfig.PAKAI_RERANKER or konfig.MODE_TIRUAN:
        return None
    if _penyusun is None:
        try:
            from sentence_transformers import CrossEncoder
            print(f"  Memuat reranker {konfig.MODEL_RERANKER} ...")
            print("  (unduhan pertama sekitar 2 GB — biarkan sampai selesai)")
            _penyusun = CrossEncoder(konfig.MODEL_RERANKER, max_length=512)
        except Exception as e:
            print(f"  Reranker tidak tersedia ({type(e).__name__}). "
                  f"Lab dilanjutkan tanpa penyusunan ulang.")
            _penyusun = False
    return _penyusun or None
