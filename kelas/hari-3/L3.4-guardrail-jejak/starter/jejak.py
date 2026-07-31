# -*- coding: utf-8 -*-
"""Jejak per pertanyaan — observability yang bisa dijawab saat ditanya.

    python tanya.py --peran staf "..."     # menghasilkan jejak
    python jejak.py                        # ringkasan seluruh jejak
    python jejak.py --akhir 5              # lima jejak terakhir, per langkah

Pertanyaan yang PASTI datang setelah sistem dipakai orang:

    "Kemarin sore jawabannya salah. Kenapa?"

Tanpa catatan, satu-satunya jawaban jujur adalah menebak. Yang dibutuhkan bukan
sekadar 'log', melainkan catatan berstruktur per LANGKAH: berapa lama tiap
bagian berjalan, berapa potongan yang terambil, dari dokumen mana, apakah
jawabannya berupa penolakan, dan apakah cache ikut campur.

Bentuknya satu baris JSON per pertanyaan (JSONL). Sengaja bukan teks bebas:
teks bebas enak dibaca satu-satu, tapi tidak bisa dihitung. Begitu ada 500
baris, yang Anda perlukan adalah persentil dan rasio — dan itu menuntut bidang
yang tetap.

CATATAN PRIVASI — sengaja dibuat sebagai keputusan sadar, bukan kelalaian:
isi potongan dan teks jawaban TIDAK ikut dicatat, hanya nama sumber, halaman,
dan angka-angkanya. Jejak biasanya berumur jauh lebih panjang daripada
jawabannya dan sering dikirim ke sistem pemantauan yang aturan aksesnya
berbeda. Mencatat isi dokumen di situ akan membatalkan seluruh kerja izin.py —
persis kebocoran lewat jalan pintas yang diperagakan singgahan.py.
"""
import json
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime

import konfig


class Jejak:
    """Kumpulkan catatan satu pertanyaan, lalu tulis satu baris JSON."""

    def __init__(self, pertanyaan, pengguna=None):
        pengguna = pengguna or {}
        self.data = {
            "id": uuid.uuid4().hex[:12],
            "waktu": datetime.now().isoformat(timespec="seconds"),
            "peran": pengguna.get("peran", "?"),
            "pertanyaan": pertanyaan,
            "langkah": [],
            "ms_total": 0,
        }
        self._mulai = time.perf_counter()

    @contextmanager
    def langkah(self, nama, **info):
        """Ukur satu langkah. Dipakai sebagai `with jejak.langkah("cari"):`.

        Dibuat sebagai context manager supaya durasinya tercatat MESKIPUN
        langkahnya melempar galat — justru langkah yang gagal itulah yang
        paling ingin Anda lihat kemudian.
        """
        # TODO L3.4-3: ukur dan catat langkah ini.
        #   1. mulai = time.perf_counter()
        #   2. catatan = {"nama": nama, **info}
        #      lalu masukkan catatan itu ke self.data["langkah"]
        #   3. bungkus `yield catatan` dengan try/except/finally:
        #        except Exception as e -> catatan["galat"] = f"{type(e).__name__}: {e}"
        #                                 lalu `raise` lagi (jangan ditelan)
        #        finally              -> catatan["ms"] = round(
        #                                    (time.perf_counter() - mulai) * 1000)
        #
        # Kenapa harus finally, bukan sekadar mengukur setelah yield? Karena
        # langkah yang MELEMPAR GALAT justru yang paling ingin Anda lihat
        # nanti. Bila durasinya hanya dicatat pada jalur mulus, jejak Anda akan
        # rapi persis pada kejadian yang sedang Anda selidiki.
        #
        # Sebelum dikerjakan, `python jejak.py` tidak akan menampilkan satu
        # langkah pun — hanya total per pertanyaan.
        yield {"nama": nama, **info}

    def catat(self, **info):
        """Tambahkan keterangan tingkat pertanyaan (bukan per langkah)."""
        self.data.update(info)
        return self

    def tutup(self):
        """Tutup jejak dan tuliskan satu baris JSON."""
        self.data["ms_total"] = round((time.perf_counter() - self._mulai) * 1000)
        if konfig.PAKAI_JEJAK:
            with open(konfig.JEJAK, "a", encoding="utf-8") as f:
                f.write(json.dumps(self.data, ensure_ascii=False) + "\n")
        return self.data

    def ringkas_baris(self):
        """Satu baris untuk layar, agar peserta melihatnya saat itu juga."""
        langkah = "  ".join(f"{l['nama']}={l.get('ms', 0)}ms"
                            for l in self.data["langkah"])
        return (f"  [jejak {self.data['id']}] peran={self.data['peran']} "
                f"total={self.data['ms_total']}ms  {langkah}")


# ============================================================ pembacaan
def baca(berkas=None):
    """Baca seluruh jejak. Baris rusak dilewati, bukan menjatuhkan program."""
    berkas = berkas or konfig.JEJAK
    if not berkas.exists():
        return []
    catatan = []
    for baris in berkas.read_text(encoding="utf-8").splitlines():
        baris = baris.strip()
        if not baris:
            continue
        try:
            catatan.append(json.loads(baris))
        except json.JSONDecodeError:
            continue
    return catatan


def _persentil(angka, p):
    """Persentil sederhana (nearest-rank). Tanpa numpy, cukup untuk lab."""
    if not angka:
        return 0
    urut = sorted(angka)
    posisi = max(0, min(len(urut) - 1, round(p / 100 * len(urut) + 0.5) - 1))
    return urut[posisi]


def ringkasan(catatan):
    """Hitung angka yang benar-benar ditanyakan orang saat sistem dipakai."""
    if not catatan:
        return None

    ms = [c.get("ms_total", 0) for c in catatan]
    kena = sum(1 for c in catatan if c.get("singgahan") == "kena")
    tolak = sum(1 for c in catatan if c.get("ditolak"))
    galat = sum(1 for c in catatan if c.get("galat"))

    per_peran = {}
    for c in catatan:
        per_peran[c.get("peran", "?")] = per_peran.get(c.get("peran", "?"), 0) + 1

    # Rata-rata per nama langkah — memperlihatkan bagian mana yang mahal.
    total_langkah, jumlah_langkah = {}, {}
    for c in catatan:
        for l in c.get("langkah", []):
            total_langkah[l["nama"]] = total_langkah.get(l["nama"], 0) + l.get("ms", 0)
            jumlah_langkah[l["nama"]] = jumlah_langkah.get(l["nama"], 0) + 1

    return {
        "jumlah": len(catatan),
        "ms_p50": _persentil(ms, 50),
        "ms_p95": _persentil(ms, 95),
        "rasio_singgahan": round(kena / len(catatan), 2),
        "rasio_penolakan": round(tolak / len(catatan), 2),
        "galat": galat,
        "per_peran": per_peran,
        "rata_langkah": {n: round(total_langkah[n] / jumlah_langkah[n])
                         for n in sorted(total_langkah)},
    }


def _cetak_ringkasan(r):
    print(f"  pertanyaan dilayani : {r['jumlah']}")
    print(f"  latensi p50 / p95   : {r['ms_p50']} ms / {r['ms_p95']} ms")
    print(f"  rasio cache kena    : {r['rasio_singgahan']:.0%}")
    print(f"  rasio penolakan     : {r['rasio_penolakan']:.0%}")
    print(f"  jejak dengan galat  : {r['galat']}")
    print(f"  per peran           : {r['per_peran']}")
    print("  rata-rata per langkah:")
    for nama, rata in sorted(r["rata_langkah"].items(), key=lambda x: -x[1]):
        print(f"      {nama:16s} {rata:6d} ms")
    print("\n  Angka penolakan yang MELONJAK biasanya bukan model yang memburuk,")
    print("  melainkan korpus atau penyaring yang berubah. Itulah gunanya diukur.")


def _cetak_terakhir(catatan, n):
    for c in catatan[-n:]:
        print(f"\n  {c['waktu']}  id={c['id']}  peran={c.get('peran')}")
        print(f"  tanya   : {c.get('pertanyaan', '')[:70]}")
        print(f"  hasil   : {c.get('jumlah_potongan', '?')} potongan  "
              f"singgahan={c.get('singgahan', '-')}  "
              f"ditolak={c.get('ditolak', '-')}  "
              f"cakupan={c.get('cakupan', '-')}")
        if c.get("sumber"):
            print(f"  sumber  : {', '.join(c['sumber'])}")
        for l in c.get("langkah", []):
            tanda = f"  GALAT: {l['galat']}" if l.get("galat") else ""
            print(f"      {l['nama']:16s} {l.get('ms', 0):6d} ms{tanda}")


if __name__ == "__main__":
    catatan = baca()
    if not catatan:
        print(f"Belum ada jejak di {konfig.JEJAK.name}.")
        print("Jalankan dulu:  python tanya.py --peran staf \"pertanyaan Anda\"")
        sys.exit(0)

    if "--akhir" in sys.argv:
        n = int(sys.argv[sys.argv.index("--akhir") + 1])
        print(f"{n} jejak terakhir dari {konfig.JEJAK.name}")
        _cetak_terakhir(catatan, n)
    else:
        print(f"Ringkasan {konfig.JEJAK.name}\n")
        _cetak_ringkasan(ringkasan(catatan))
