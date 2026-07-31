# -*- coding: utf-8 -*-
"""Sidik jari indeks: mencatat DENGAN APA indeks dibangun, lalu memastikan
setelan aktif masih cocok sebelum indeks itu dipakai.

Kenapa modul ini ada — inti pelajaran F3:
mengganti model embedding, ukuran potongan, atau berpindah ke/dari mode tiruan
mengharuskan indeks dibangun ulang. Kalau tidak, sistem tetap berjalan TANPA
GALAT tetapi hasil pencariannya menjadi acak. Ini kegagalan senyap yang paling
sulit didiagnosis. Di sini pelajaran itu ditegakkan oleh kode — bukan sekadar
diingatkan lewat komentar yang mudah terlewat.
"""
import json
import time

import konfig


def tulis():
    """Rekam setelan pembangun indeks. Dipanggil indeks.py setelah membangun."""
    konfig.META.write_text(
        json.dumps({
            "model_embedding": konfig.MODEL_EMBEDDING,
            "ukuran_potongan": konfig.UKURAN_POTONGAN,
            "mode_tiruan": konfig.MODE_TIRUAN,
            "dibuat": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def periksa():
    """Bandingkan sidik jari indeks dengan setelan aktif.

    Kembalikan (cocok: bool, pesan: str | None).
    Indeks lama tanpa berkas meta dianggap cocok agar tidak menghalangi —
    hanya ketidakcocokan yang benar-benar terdeteksi yang diperingatkan.
    """
    if not konfig.META.exists():
        return True, None

    try:
        m = json.loads(konfig.META.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return True, None

    beda = []
    if m.get("model_embedding") != konfig.MODEL_EMBEDDING:
        beda.append(f"embedding: indeks '{m.get('model_embedding')}' "
                    f"vs konfig '{konfig.MODEL_EMBEDDING}'")
    if m.get("ukuran_potongan") != konfig.UKURAN_POTONGAN:
        beda.append(f"ukuran potongan: indeks {m.get('ukuran_potongan')} "
                    f"vs konfig {konfig.UKURAN_POTONGAN}")
    if bool(m.get("mode_tiruan")) != bool(konfig.MODE_TIRUAN):
        beda.append(f"mode tiruan: indeks {'ya' if m.get('mode_tiruan') else 'tidak'} "
                    f"vs sekarang {'ya' if konfig.MODE_TIRUAN else 'tidak'}")

    if beda:
        pesan = ("PERINGATAN: indeks dibangun dengan setelan berbeda dari konfig aktif:\n"
                 + "".join(f"    - {b}\n" for b in beda)
                 + "  Pencarian akan ACAK tanpa memunculkan galat apa pun (pelajaran F3).\n"
                 + "  Bangun ulang lebih dulu:  python indeks.py --ulang")
        return False, pesan
    return True, None
