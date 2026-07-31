# -*- coding: utf-8 -*-
"""python nilai.py — evaluasi retrieval + penyaringan status.

    python nilai.py              evaluasi retrieval + penyaringan status
    python nilai.py --penolakan  ikut menguji kemampuan menolak (butuh model)

Evaluasi retrieval sengaja TIDAK memanggil model bahasa: cepat, murah,
objektif, dan bisa dijalankan setiap kali ada perubahan setelan.
"""
from __future__ import annotations

import argparse
from typing import Sequence

from .. import konfig
from ..evaluasi import bandingkan_metode, evaluasi_filter_status, evaluasi_penolakan


def utama(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nilai.py", description=__doc__)
    parser.add_argument(
        "--penolakan", action="store_true",
        help="ikut menguji kemampuan menolak — memanggil model, jadi lebih lambat",
    )
    argumen = parser.parse_args(argv)

    print("Setelan aktif:")
    konfig.ringkas()

    bandingkan_metode()

    # Cepat dan tanpa model — selalu dijalankan karena inilah bukti terukur B3.
    evaluasi_filter_status()

    if argumen.penolakan:
        evaluasi_penolakan()
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
