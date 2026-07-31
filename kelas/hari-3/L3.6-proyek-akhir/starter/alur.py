# -*- coding: utf-8 -*-
"""Graf berkeadaan: langkah PASTI + langkah MODEL + persetujuan manusia.

    python alur.py --peran pimpinan "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"
    python alur.py --peran staf     "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"
    python alur.py --otomatis tolak "Apa saja tahapan pengadaan langsung?"

Di L3.3 seluruh simpul adalah panggilan model. Alur ini sengaja dicampur, dan
pembagiannya adalah inti pelajarannya:

    PASTI (deterministik, bisa diaudit, nyaris gratis)
        izin        hitung hak akses          -> izin.py
        singgahan   cari jawaban tersimpan    -> singgahan.py
        cari        ambil potongan            -> cari.py
        periksa     periksa sitasi (regex)    -> jawab.py
        tolak       kalimat penolakan baku    -> konfig.py
        catat       tulis jejak               -> jejak.py

    MODEL (mahal, tidak bisa diulang persis, tidak bisa dijamin)
        jawab       merangkai jawaban

    MANUSIA
        persetujuan alur berhenti dan menunggu orang

Dua akibat yang langsung terasa, dan keduanya bisa Anda lihat di layar:

1. Bila `cari` tidak menemukan apa pun, penolakannya dikeluarkan oleh simpul
   `tolak` TANPA memanggil model sama sekali. Nol detik, nol token, dan
   kalimatnya persis sama setiap kali — sesuatu yang tidak pernah bisa
   dijanjikan model. Banyak "kecerdasan" pada sistem RAG yang baik sebenarnya
   adalah cabang if biasa yang diletakkan di tempat yang tepat.

2. Setiap simpul menuliskan barisnya sendiri ke keadaan (`langkah`). Jadi jejak
   audit BUKAN log yang ditempel di samping, melainkan bagian dari keadaan yang
   ikut mengalir. Ia tidak bisa lupa tercatat, karena ialah yang mengalir.

Manusianya masuk lewat `interrupt()`: alur benar-benar BERHENTI, keadaannya
disimpan checkpointer, dan proses boleh mati. Ketika keputusan datang, alur
dilanjutkan dari titik itu juga — bukan diulang dari awal. Inilah bedanya
"human-in-the-loop" yang sungguhan dengan sekadar input() di tengah fungsi.
"""
import operator
import sys
import uuid
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

import izin
import jejak as modul_jejak
import konfig
import singgahan
from cari import ambil_terbaik
from jawab import periksa_sitasi, susun_jawaban
from model import ambil_llm


# ============================================================ keadaan
class Keadaan(TypedDict):
    """Seluruh yang diketahui alur ini tentang satu pertanyaan.

    `langkah` memakai reducer operator.add, jadi tiap simpul cukup
    mengembalikan satu barisnya sendiri dan daftarnya tersambung otomatis.
    Inilah jejak audit — dan karena ia BAGIAN DARI KEADAAN, ia mustahil
    tertinggal: simpul yang berjalan pasti menuliskan barisnya.
    """
    pertanyaan: str
    pengguna: dict
    saring: dict
    potongan: list
    jawaban: str
    lapor: dict
    ditolak: bool
    disetujui: bool
    alasan: str
    dari_singgahan: bool
    langkah: Annotated[list, operator.add]


def _baris(nama, jenis, **info):
    """Satu baris jejak audit. `jenis` menandai pasti / model / manusia."""
    return {"simpul": nama, "jenis": jenis, **info}


# ============================================================ simpul PASTI
def simpul_izin(keadaan: Keadaan) -> dict:
    """PASTI. Hak akses dihitung sebelum apa pun yang lain."""
    pengguna = izin.bereskan(keadaan["pengguna"])
    saring = izin.saring_untuk(pengguna)
    return {
        "pengguna": pengguna,
        "saring": saring,
        "langkah": [_baris("izin", "pasti", peran=pengguna["peran"],
                           jenis_boleh=sorted(saring["jenis"]))],
    }


def simpul_singgahan(keadaan: Keadaan) -> dict:
    """PASTI. Kuncinya memuat hak akses — lihat singgahan.py."""
    if not konfig.PAKAI_SINGGAHAN:
        return {"langkah": [_baris("singgahan", "pasti", hasil="dimatikan")]}

    tersimpan = singgahan.BERSAMA.ambil(keadaan["pertanyaan"], keadaan["pengguna"])
    if tersimpan is None:
        return {"langkah": [_baris("singgahan", "pasti", hasil="meleset")]}
    return {
        "jawaban": tersimpan["jawaban"],
        "ditolak": tersimpan["ditolak"],
        "lapor": {"cakupan": tersimpan["cakupan"], "hantu": set()},
        "dari_singgahan": True,
        "langkah": [_baris("singgahan", "pasti", hasil="kena")],
    }


def simpul_cari(keadaan: Keadaan) -> dict:
    """PASTI. Tidak ada model di sini — hanya indeks, BM25, dan penyaring."""
    potongan = ambil_terbaik(keadaan["pertanyaan"], saring=keadaan["saring"])
    sebelum = len(potongan)
    potongan = izin.saring_potongan(keadaan["pengguna"], potongan)
    return {
        "potongan": potongan,
        "langkah": [_baris("cari", "pasti", jumlah=len(potongan),
                           dibuang_pagar_akhir=sebelum - len(potongan),
                           sumber=sorted({d.metadata.get("source", "?")
                                          for d in potongan}))],
    }


def simpul_tolak(keadaan: Keadaan) -> dict:
    """PASTI. Penolakan tidak butuh model.

    Kalimatnya diambil dari konfig.TIDAK_DITEMUKAN — satu sumber yang sama
    dengan yang dicocokkan nilai.py. Kalau penolakan dirangkai model, kata-
    katanya akan bergeser sedikit tiap kali, dan metrik penolakan diam-diam
    melaporkan nol.
    """
    alasan = keadaan.get("alasan") or "tidak ada potongan yang relevan"
    return {
        "jawaban": konfig.TIDAK_DITEMUKAN,
        "ditolak": True,
        "langkah": [_baris("tolak", "pasti", alasan=alasan)],
    }


def simpul_periksa(keadaan: Keadaan) -> dict:
    """PASTI. Pemeriksaan sitasi — regex, bukan model.

    Selain melapor, simpul ini merumuskan ALASAN dalam bahasa manusia. Alasan
    dan keputusan eskalasi lahir di satu tempat; kalau dipisah, keduanya akan
    bergeser sendiri-sendiri dan penyelia menerima "tolong periksa" tanpa
    keterangan apa yang harus diperiksa.
    """
    lapor = periksa_sitasi(keadaan["jawaban"], len(keadaan["potongan"]))

    alasan = ""
    if lapor["hantu"]:
        alasan = (f"sitasi menunjuk potongan yang tidak ada: "
                  f"{sorted(lapor['hantu'])}")
    elif lapor["cakupan"] < konfig.AMBANG_CAKUPAN:
        alasan = (f"cakupan sitasi rendah ({lapor['cakupan']:.0%}, "
                  f"ambang {konfig.AMBANG_CAKUPAN:.0%})")

    return {
        "lapor": lapor,
        "alasan": alasan,
        "langkah": [_baris("periksa", "pasti", cakupan=lapor["cakupan"],
                           hantu=sorted(lapor["hantu"]), alasan=alasan or "-")],
    }


def simpul_catat(keadaan: Keadaan) -> dict:
    """PASTI. Tuliskan jejak, dan simpan ke singgahan bila layak."""
    jejak = modul_jejak.Jejak(keadaan["pertanyaan"], keadaan["pengguna"])
    jejak.data["langkah"] = keadaan["langkah"]
    jejak.catat(
        ditolak=keadaan.get("ditolak", False),
        jumlah_potongan=len(keadaan.get("potongan") or []),
        sumber=sorted({d.metadata.get("source", "?")
                       for d in (keadaan.get("potongan") or [])}),
        cakupan=(keadaan.get("lapor") or {}).get("cakupan", 0.0),
        singgahan="kena" if keadaan.get("dari_singgahan") else "meleset",
        disetujui=keadaan.get("disetujui"),
    )
    jejak.tutup()

    # Jawaban yang butuh koreksi manusia TIDAK disimpan ke cache. Menyimpannya
    # berarti menyebarkan satu jawaban meragukan ke semua penanya berikutnya
    # tanpa ada yang memeriksanya lagi.
    layak = (konfig.PAKAI_SINGGAHAN and not keadaan.get("dari_singgahan")
             and keadaan.get("disetujui") is not False)
    if layak:
        singgahan.BERSAMA.simpan(keadaan["pertanyaan"], keadaan["pengguna"], {
            "jawaban": keadaan["jawaban"],
            "ditolak": keadaan.get("ditolak", False),
            "jumlah_potongan": len(keadaan.get("potongan") or []),
            "sumber": sorted({d.metadata.get("source", "?")
                              for d in (keadaan.get("potongan") or [])}),
            "cakupan": (keadaan.get("lapor") or {}).get("cakupan", 0.0),
        })
    return {"langkah": [_baris("catat", "pasti", id_jejak=jejak.data["id"])]}


# ============================================================ simpul MODEL
_llm = None


def simpul_jawab(keadaan: Keadaan) -> dict:
    """MODEL. Satu-satunya simpul yang tidak bisa dijanjikan hasilnya."""
    global _llm
    if _llm is None:
        _llm = ambil_llm()
    isi = susun_jawaban(_llm, keadaan["pertanyaan"], keadaan["potongan"])
    return {
        "jawaban": isi,
        "ditolak": konfig.TIDAK_DITEMUKAN in isi,
        "langkah": [_baris("jawab", "model", panjang=len(isi))],
    }


# ============================================================ simpul MANUSIA
def simpul_persetujuan(keadaan: Keadaan) -> dict:
    """MANUSIA. Alur berhenti di sini sampai ada keputusan.

    interrupt() bukan input(). Ia menyimpan keadaan lewat checkpointer lalu
    keluar; proses boleh mati, mesin boleh dimatikan. Ketika keputusan datang,
    alur dilanjutkan DARI SIMPUL INI — pencarian dan pemanggilan model yang
    tadi sudah berjalan tidak diulang.

    Yang dikirim ke manusia sengaja ringkas dan sudah berisi ALASAN, bukan
    hanya jawabannya. Orang yang diminta menyetujui butuh tahu apa yang
    mencurigakan, kalau tidak ia hanya akan menekan 'setuju' terus-menerus.
    """
    lapor = keadaan.get("lapor") or {}
    keputusan = interrupt({
        "pertanyaan": keadaan["pertanyaan"],
        "jawaban": keadaan["jawaban"],
        "alasan": keadaan.get("alasan", ""),
        "cakupan": lapor.get("cakupan"),
        "sumber": sorted({d.metadata.get("source", "?")
                          for d in (keadaan.get("potongan") or [])}),
    })

    disetujui = bool(keputusan.get("disetujui")) if keputusan else False
    oleh = (keputusan or {}).get("oleh", "?")
    return {
        "disetujui": disetujui,
        # Alasan ditimpa supaya simpul_tolak mencatat sebab yang sebenarnya:
        # bukan lagi "cakupan rendah", melainkan keputusan orangnya.
        "alasan": keadaan.get("alasan", "") if disetujui else f"ditolak oleh {oleh}",
        "langkah": [_baris("persetujuan", "manusia", disetujui=disetujui,
                           oleh=oleh)],
    }


# ============================================================ percabangan
def arah_singgahan(keadaan: Keadaan) -> str:
    """PASTI. Cache kena -> langsung catat; meleset -> cari."""
    return "catat" if keadaan.get("dari_singgahan") else "cari"


def arah_cari(keadaan: Keadaan) -> str:
    """PASTI. Tanpa potongan, tidak ada gunanya memanggil model."""
    return "jawab" if keadaan["potongan"] else "tolak"


def arah_periksa(keadaan: Keadaan) -> str:
    """PASTI. Gerbang yang memutuskan apakah manusia perlu dilibatkan.

    Perhatikan siapa yang memutuskan: sebuah fungsi biasa, bukan model. Aturan
    "kapan manusia dipanggil" adalah kebijakan organisasi — ia harus bisa
    dibaca, diuji, dan diubah tanpa menyentuh prompt.

    Pemicunya sudah dirumuskan simpul_periksa sebagai `alasan`: ada isinya
    berarti ada yang mencurigakan (sitasi hantu, atau cakupan sitasi di bawah
    konfig.AMBANG_CAKUPAN). Membaca satu bidang yang sama membuat alasan yang
    ditampilkan ke penyelia mustahil berbeda dari alasan yang memicunya.

    Penolakan TIDAK dieskalasi. Sistem yang menjawab "tidak ditemukan" sedang
    berperilaku benar, dan membanjiri manusia dengan itu hanya melatih mereka
    menyetujui apa pun tanpa membaca.
    """
    if keadaan.get("ditolak"):
        return "catat"
    return "persetujuan" if keadaan.get("alasan") else "catat"


def arah_persetujuan(keadaan: Keadaan) -> str:
    """PASTI. Ditolak manusia -> jawabannya diganti penolakan baku."""
    return "catat" if keadaan.get("disetujui") else "tolak"


# ============================================================ merakit
def bangun_alur(checkpointer=None):
    """Rakit alur. Checkpointer WAJIB ada bila interrupt() dipakai."""
    alur = StateGraph(Keadaan)

    alur.add_node("izin", simpul_izin)
    alur.add_node("singgahan", simpul_singgahan)
    alur.add_node("cari", simpul_cari)
    alur.add_node("jawab", simpul_jawab)
    alur.add_node("periksa", simpul_periksa)
    alur.add_node("persetujuan", simpul_persetujuan)
    alur.add_node("tolak", simpul_tolak)
    alur.add_node("catat", simpul_catat)

    alur.add_edge(START, "izin")
    alur.add_edge("izin", "singgahan")
    alur.add_conditional_edges("singgahan", arah_singgahan,
                               {"cari": "cari", "catat": "catat"})
    alur.add_conditional_edges("cari", arah_cari,
                               {"jawab": "jawab", "tolak": "tolak"})
    alur.add_edge("jawab", "periksa")
    alur.add_conditional_edges("periksa", arah_periksa,
                               {"persetujuan": "persetujuan", "catat": "catat"})
    alur.add_conditional_edges("persetujuan", arah_persetujuan,
                               {"catat": "catat", "tolak": "tolak"})
    alur.add_edge("tolak", "catat")
    alur.add_edge("catat", END)

    return alur.compile(checkpointer=checkpointer or InMemorySaver())


# ============================================================ menjalankan
def _tanya_manusia(permintaan):
    """Penanya bawaan: tampilkan berkas perkaranya, minta keputusan."""
    print("\n" + "!" * 74)
    print("ALUR BERHENTI — menunggu keputusan manusia")
    print("!" * 74)
    print(f"  pertanyaan : {permintaan['pertanyaan']}")
    print(f"  alasan     : {permintaan['alasan']}")
    print(f"  cakupan    : {permintaan['cakupan']}")
    print(f"  sumber     : {', '.join(permintaan['sumber']) or '-'}")
    print(f"\n  jawaban usulan:\n    {permintaan['jawaban']}\n")
    jwb = input("  Setujui jawaban ini? [y/T] ").strip().lower()
    return {"disetujui": jwb in ("y", "ya"), "oleh": "penyelia-kelas"}


def jalankan(pertanyaan, pengguna, penanya=None, tampilkan=True):
    """Jalankan alur sampai selesai, termasuk berhenti untuk manusia."""
    graf = bangun_alur()
    setelan = {"configurable": {"thread_id": uuid.uuid4().hex[:12]}}
    penanya = penanya or _tanya_manusia

    hasil = graf.invoke({
        "pertanyaan": pertanyaan, "pengguna": pengguna, "saring": {},
        "potongan": [], "jawaban": "", "lapor": {}, "ditolak": False,
        "disetujui": None, "alasan": "", "dari_singgahan": False,
        "langkah": [],
    }, setelan)

    # Selama alur masih menahan diri, layani permintaannya lalu lanjutkan.
    # Bentuk while, bukan if: satu alur boleh berhenti lebih dari sekali.
    while "__interrupt__" in hasil:
        keputusan = penanya(hasil["__interrupt__"][0].value)
        hasil = graf.invoke(Command(resume=keputusan), setelan)

    if tampilkan:
        _tampilkan(hasil)
    return hasil


def _tampilkan(hasil):
    print("\n  jejak audit (jenis tiap langkah):")
    for l in hasil["langkah"]:
        tambahan = {k: v for k, v in l.items() if k not in ("simpul", "jenis")}
        print(f"    {l['jenis']:8s} {l['simpul']:12s} {tambahan}")

    pasti = sum(1 for l in hasil["langkah"] if l["jenis"] == "pasti")
    model = sum(1 for l in hasil["langkah"] if l["jenis"] == "model")
    print(f"\n  {pasti} langkah pasti, {model} langkah model.")
    print(f"\n  JAWABAN: {hasil['jawaban']}")
    if hasil.get("disetujui") is not None:
        print(f"  (keputusan manusia: "
              f"{'disetujui' if hasil['disetujui'] else 'DITOLAK'})")


if __name__ == "__main__":
    argumen = sys.argv[1:]
    peran, otomatis = "pimpinan", None
    for bendera, bawaan in (("--peran", None), ("--otomatis", None)):
        if bendera in argumen:
            i = argumen.index(bendera)
            nilai = argumen[i + 1]
            del argumen[i:i + 2]
            if bendera == "--peran":
                peran = nilai
            else:
                otomatis = nilai

    tanya = " ".join(argumen) or \
        "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"

    # --otomatis setuju|tolak menjawab tanpa menunggu ketikan. Berguna untuk
    # demo di depan kelas dan untuk pengujian.
    penanya = None
    if otomatis:
        def penanya(permintaan, _o=otomatis):
            print(f"\n  [alur berhenti — dijawab otomatis: {_o}]")
            print(f"  alasan: {permintaan['alasan']}")
            return {"disetujui": _o.lower().startswith("s"), "oleh": "otomatis"}

    orang = izin.bereskan({"peran": peran})
    print(f"Pertanyaan: {tanya}")
    print(f"Peran     : {orang['peran']}")
    jalankan(tanya, orang, penanya=penanya)
    print(f"\n  singgahan: {singgahan.BERSAMA.statistik()}")
