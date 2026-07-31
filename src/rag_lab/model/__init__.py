# -*- coding: utf-8 -*-
"""Lapisan model: satu-satunya tempat yang tahu model itu datang dari mana.

Seluruh modul lain cukup memanggil `ambil_embedding()`, `ambil_llm()`, dan
`ambil_reranker()` tanpa peduli apakah yang berjalan Ollama sungguhan atau
mode tiruan. Lapisan model yang terisolasi seperti ini bisa diganti tanpa
menyentuh logika RAG sama sekali.
"""
from __future__ import annotations

from .penyedia import (
    ambil_embedding,
    ambil_llm,
    ambil_reranker,
    lupakan_model,
)

__all__ = [
    "ambil_embedding",
    "ambil_llm",
    "ambil_reranker",
    "lupakan_model",
]
