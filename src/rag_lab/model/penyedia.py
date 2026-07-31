# -*- coding: utf-8 -*-
"""Pembuat objek model, dengan jalur cadangan bila Ollama bermasalah.

Ketiga fungsi di sini di-cache: satu objek dipakai ulang selama proses hidup.
Tanpa itu, evaluasi yang memanggil pencarian puluhan kali akan membuat koneksi
baru setiap kali. `lupakan_model()` disediakan untuk pengujian.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from .. import konfig
from .tiruan import EmbeddingTiruan, LLMTiruan


def _argumen_ollama() -> dict[str, str]:
    """base_url hanya dikirim bila memang disetel — selebihnya biar bawaan."""
    return {"base_url": konfig.OLLAMA_URL} if konfig.OLLAMA_URL else {}


@lru_cache(maxsize=1)
def ambil_embedding() -> Any:
    """Model embedding. HARUS sama dengan yang dipakai membangun indeks (F3)."""
    if konfig.MODE_TIRUAN:
        return EmbeddingTiruan()

    from langchain_ollama import OllamaEmbeddings

    return OllamaEmbeddings(model=konfig.MODEL_EMBEDDING, **_argumen_ollama())


@lru_cache(maxsize=1)
def ambil_llm() -> Any:
    """Model chat. temperature=0 agar jawaban bisa diulang dan dibandingkan."""
    if konfig.MODE_TIRUAN:
        return LLMTiruan()

    from langchain_ollama import ChatOllama

    return ChatOllama(model=konfig.MODEL_CHAT, temperature=0, **_argumen_ollama())


# Reranker sengaja dimuat MALAS (baru saat dipakai pertama kali).
# Kalau dimuat saat import, berkas modelnya sekitar 2 GB akan diunduh diam-diam
# dan peserta mengira programnya menggantung. Ini jebakan lab yang nyata.
@lru_cache(maxsize=1)
def ambil_reranker() -> Any | None:
    """Kembalikan objek reranker, atau None bila tidak tersedia.

    Sengaja tidak melempar galat: di laptop 8 GB reranker memang sebaiknya
    dimatikan, dan lab harus tetap jalan tanpanya. Hasil None ikut di-cache,
    sehingga percobaan pemuatan yang gagal tidak diulang di setiap pertanyaan.
    """
    if not konfig.PAKAI_RERANKER or konfig.MODE_TIRUAN:
        return None

    try:
        from sentence_transformers import CrossEncoder

        print(f"  Memuat reranker {konfig.MODEL_RERANKER} ...")
        print("  (unduhan pertama sekitar 2 GB — biarkan sampai selesai)")
        return CrossEncoder(konfig.MODEL_RERANKER, max_length=512)
    except Exception as e:
        # Sengaja menangkap apa pun: paket belum ada, unduhan gagal, RAM habis.
        # Ketiganya berakhir sama — lab dilanjutkan tanpa penyusunan ulang.
        print(
            f"  Reranker tidak tersedia ({type(e).__name__}). "
            f"Lab dilanjutkan tanpa penyusunan ulang."
        )
        return None


def lupakan_model() -> None:
    """Buang objek model yang tersimpan — dipakai pengujian dan demo setelan."""
    ambil_embedding.cache_clear()
    ambil_llm.cache_clear()
    ambil_reranker.cache_clear()
