# -*- coding: utf-8 -*-
"""python cek.py — pemeriksaan kesiapan. JALANKAN INI PALING PERTAMA."""
from __future__ import annotations

import argparse
from typing import Sequence

from ..diagnosa import jalankan


def utama(argv: Sequence[str] | None = None) -> int:
    argparse.ArgumentParser(
        prog="cek.py", description=__doc__
    ).parse_args(argv)
    return jalankan()


if __name__ == "__main__":
    raise SystemExit(utama())
