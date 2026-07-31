# -*- coding: utf-8 -*-
"""Kalkulator yang aman dipanggil model — contoh guardrail modul A4.

Sengaja TIDAK memakai eval(). eval() akan menjalankan kode Python apa pun —
termasuk yang berbahaya bila ekspresinya datang dari sumber tak tepercaya, dan
teks yang ditulis model ADALAH sumber tak tepercaya. Di sini hanya operator
aritmetika yang di-whitelist: batasi kemampuan alat sampai sebatas yang
benar-benar diperlukan.
"""
from __future__ import annotations

import ast
import operator
from typing import Callable

from ..galat import EkspresiTidakAman

OPERATOR: dict[type[ast.AST], Callable] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

PESAN_DITOLAK = "hanya angka dan operator + - * / % ** yang diizinkan"


def _nilai(simpul: ast.AST) -> float:
    if isinstance(simpul, ast.Constant) and isinstance(simpul.value, (int, float)):
        return simpul.value
    if isinstance(simpul, ast.BinOp) and type(simpul.op) in OPERATOR:
        return OPERATOR[type(simpul.op)](_nilai(simpul.left), _nilai(simpul.right))
    if isinstance(simpul, ast.UnaryOp) and type(simpul.op) in OPERATOR:
        return OPERATOR[type(simpul.op)](_nilai(simpul.operand))
    raise EkspresiTidakAman(PESAN_DITOLAK)


def hitung_ekspresi(ekspresi: str) -> float:
    """Hitung ekspresi aritmetika sederhana.

    Melempar `EkspresiTidakAman` untuk apa pun di luar angka dan operator
    yang diizinkan — termasuk nama variabel, pemanggilan fungsi, dan atribut.
    """
    try:
        pohon = ast.parse(ekspresi, mode="eval")
    except SyntaxError as e:
        raise EkspresiTidakAman(f"bukan ekspresi yang sah: {ekspresi!r}") from e
    return _nilai(pohon.body)
