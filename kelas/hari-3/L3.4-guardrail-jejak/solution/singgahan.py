# -*- coding: utf-8 -*-
"""Cache jawaban yang dikunci per HAK AKSES — modul A4.

    python singgahan.py          # peragaan kebocoran, tanpa perlu Ollama

Cache adalah peningkatan paling menggoda di sistem RAG: jawaban yang sama
diminta berkali-kali, dan tiap jawaban memakan beberapa detik GPU. Menyimpannya
terasa seperti kemenangan gratis.

Di situlah letak jebakannya. Kunci cache yang wajar bagi kebanyakan orang —

    kunci = pertanyaan

— adalah lubang kebocoran hak akses. Alurnya begini:

    1. Seorang pimpinan bertanya "berapa nilai pengadaan penyimpanan tambahan?"
       Sistem mencari di SELURUH korpus (termasuk notulen), menjawab
       "Rp 180.000.000", lalu menyimpannya dengan kunci berupa pertanyaan itu.
    2. Seorang staf mengetik pertanyaan yang persis sama.
    3. Cache kena. Jawabannya dikembalikan langsung — tanpa pernah menyentuh
       penyaring izin di cari.py, karena pencariannya memang tidak dijalankan.

Perhatikan bahwa guardrail di izin.py TIDAK rusak sedikit pun. Ia hanya
dilewati. Ini pola kegagalan yang berulang di sistem sungguhan: kebocoran
jarang datang dari pagar yang jebol, melainkan dari jalan pintas yang dibangun
belakangan dan tidak melewati pagarnya.

Obatnya satu baris: hak akses ikut menjadi bagian kunci.

    kunci = (pertanyaan, sidik hak akses)

Yang disidik adalah HAK AKSESNYA, bukan identitas orangnya — lihat izin.sidik().
Dua staf berbeda melihat korpus yang sama, jadi mereka boleh berbagi baris
cache; kalau kuncinya memakai nama orang, cache-nya nyaris tidak pernah kena.
"""
import hashlib
import sys
from collections import OrderedDict

import izin
import konfig


def _normalkan(pertanyaan):
    """Samakan pertanyaan yang berbeda hanya di spasi dan huruf besar-kecil.

    Sengaja sederhana, dan batasnya harus disebut: "berapa lama masa percobaan"
    dan "masa percobaan berapa lama" dianggap DUA pertanyaan berbeda. Cache
    berbasis teks memang hanya menangkap pengulangan persis. Menyamakan makna
    menuntut embedding pertanyaan — peningkatan yang bagus, tapi bukan di sini.
    """
    return " ".join(str(pertanyaan).lower().split())


class Singgahan:
    """Cache sederhana dengan pembuangan yang tertua (LRU)."""

    def __init__(self, sertakan_izin=True, maks=None):
        # sertakan_izin=False HANYA dipakai untuk memperagakan kebocoran.
        self.sertakan_izin = sertakan_izin
        self.maks = maks or konfig.SINGGAHAN_MAKS
        self._isi = OrderedDict()
        self.kena = 0
        self.meleset = 0

    def kunci(self, pertanyaan, pengguna):
        """Bangun kunci cache.

        Inilah satu-satunya baris yang memisahkan cache yang aman dari cache
        yang membocorkan dokumen.
        """
        bagian = _normalkan(pertanyaan)
        if self.sertakan_izin:
            bagian += "|" + izin.sidik(pengguna)
        # Di-hash supaya kunci pendek dan tidak menyimpan teks pertanyaan
        # pengguna apa adanya di dalam memori proses.
        return hashlib.sha256(bagian.encode("utf-8")).hexdigest()[:32]

    def ambil(self, pertanyaan, pengguna):
        """Kembalikan nilai tersimpan, atau None bila belum ada."""
        k = self.kunci(pertanyaan, pengguna)
        if k in self._isi:
            self._isi.move_to_end(k)
            self.kena += 1
            return self._isi[k]
        self.meleset += 1
        return None

    def simpan(self, pertanyaan, pengguna, nilai):
        k = self.kunci(pertanyaan, pengguna)
        self._isi[k] = nilai
        self._isi.move_to_end(k)
        while len(self._isi) > self.maks:
            self._isi.popitem(last=False)
        return nilai

    def statistik(self):
        total = self.kena + self.meleset
        return {
            "kena": self.kena,
            "meleset": self.meleset,
            "rasio_kena": round(self.kena / total, 2) if total else 0.0,
            "terisi": len(self._isi),
        }


# Satu singgahan bersama untuk seluruh proses.
BERSAMA = Singgahan(sertakan_izin=not konfig.SINGGAHAN_TANPA_IZIN)


# ============================================================ peragaan
def _peragakan():
    """Tunjukkan kebocorannya dengan angka, tanpa memanggil model sama sekali."""
    pimpinan = {"nama": "Bramantyo", "peran": "pimpinan"}
    staf = {"nama": "Gunawan", "peran": "staf"}
    tanya = "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"
    rahasia = "Rp 180.000.000, memerlukan persetujuan Direktur Keuangan [1]."

    print(f"Pertanyaan : {tanya}")
    print(f"Sidik izin pimpinan : {izin.sidik(pimpinan)}")
    print(f"Sidik izin staf     : {izin.sidik(staf)}\n")

    for judul, sertakan in (("TANPA hak akses di kunci (SALAH)", False),
                            ("DENGAN hak akses di kunci (BENAR)", True)):
        c = Singgahan(sertakan_izin=sertakan)
        c.simpan(tanya, pimpinan, rahasia)      # pimpinan bertanya lebih dulu
        hasil = c.ambil(tanya, staf)            # lalu staf bertanya sama persis

        print(f"{judul}")
        print(f"  kunci pimpinan : {c.kunci(tanya, pimpinan)}")
        print(f"  kunci staf     : {c.kunci(tanya, staf)}")
        if hasil is None:
            print("  staf -> MELESET; pencarian dijalankan, penyaring izin "
                  "berlaku. Aman.\n")
        else:
            print(f"  staf -> KENA; menerima: {hasil}")
            print("  BOCOR: staf membaca isi notulen tanpa pernah melewati "
                  "izin.py.\n")

    print("Guardrail-nya tidak rusak — ia hanya dilewati.")
    print("Setiap jalan pintas yang melewatkan pencarian juga melewatkan "
          "penyaringnya.")


if __name__ == "__main__":
    _peragakan()
    sys.exit(0)
