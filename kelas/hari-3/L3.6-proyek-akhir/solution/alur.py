# -*- coding: utf-8 -*-
"""Graf berkeadaan: langkah PASTI + langkah MODEL + persetujuan manusia.

    python alur.py --peran pimpinan "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"
    python alur.py --peran staf     "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"
    python alur.py --otomatis tolak "Apa saja tahapan pengadaan langsung?"
    python alur.py --set-uji --otomatis setuju      # ukur rasio eskalasi (nomor 9)
    python alur.py --set-uji --batas 5              # cobanya sebagian dulu

Di L3.3 seluruh simpul adalah panggilan model. Alur ini sengaja dicampur, dan
pembagiannya adalah inti pelajarannya:

    PASTI (deterministik, bisa diaudit, nyaris gratis)
        saring      pagar masukan (regex)     -> peningkatan 8
        izin        hitung hak akses          -> izin.py
        singgahan   cari jawaban tersimpan    -> singgahan.py
        cari        ambil potongan            -> cari.py
        periksa     periksa sitasi (regex)    -> jawab.py
        dukungan    sitasi vs isi potongan    -> peningkatan 8
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
import json
import operator
import re
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
import util
from cari import ambil_terbaik
from jawab import POLA_SITASI, periksa_sitasi, susun_jawaban
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
    # Ditambahkan pada peningkatan 8 dan 9:
    diblokir: bool        # ditolak pagar masukan, sebelum indeks disentuh
    dukungan: float       # seberapa jauh sitasi didukung isi potongannya
    dieskalasi: bool      # apakah alur berhenti untuk manusia
    langkah: Annotated[list, operator.add]


def _baris(nama, jenis, **info):
    """Satu baris jejak audit. `jenis` menandai pasti / model / manusia."""
    return {"simpul": nama, "jenis": jenis, **info}


# ============================================================ simpul PASTI
# PENINGKATAN 8 — simpul pasti baru nomor satu: pagar masukan.
#
# Letaknya paling depan, sebelum izin dan sebelum pencarian. Pertanyaan yang
# ditolak di sini tidak menyentuh indeks, tidak memanggil model, dan tidak
# menghasilkan token satu pun — dan penolakannya berbunyi persis sama setiap
# kali, sesuatu yang tidak pernah bisa dijanjikan model.
#
# BATASNYA HARUS DIKATAKAN TERUS TERANG: daftar pola di bawah bukan pengamanan
# terhadap prompt injection. Ia menangkap percobaan yang ditulis apa adanya,
# dan akan dilewati dengan mudah oleh kalimat yang sedikit diputar. Yang
# benar-benar menahan penyalahgunaan tetap dua hal lain: alat agent yang
# sempit (izin.ALAT_PER_PERAN) dan penyaring dokumen di hulu (izin.saring_untuk).
# Pagar ini menghemat ongkos dan menyeragamkan penolakan — bukan menggantikan
# keduanya. Guardrail yang dikira lebih kuat daripada sebenarnya lebih
# berbahaya daripada tidak ada guardrail.
POLA_TERLARANG = [
    (re.compile(r"abaikan\s+(semua\s+)?(instruksi|aturan|perintah)", re.I),
     "meminta mengabaikan instruksi sistem"),
    (re.compile(r"(tampilkan|cetak|ulangi|sebutkan)\s+(isi\s+)?(prompt|instruksi)\s*"
                r"(sistem|awal)?", re.I),
     "meminta isi prompt sistem"),
    (re.compile(r"(lupakan|hapus|buang)\s+(semua\s+)?(aturan|batasan|pagar)", re.I),
     "meminta membuang batasan"),
    (re.compile(r"\b(kamu|anda)\s+(sekarang\s+)?adalah\s+\w+", re.I),
     "mencoba mengganti peran sistem"),
    (re.compile(r"(jawab|jawablah)\s+(tanpa|tanpa\s+memakai)\s+dokumen", re.I),
     "meminta jawaban tanpa dasar dokumen"),
]


def periksa_masukan(pertanyaan):
    """Kembalikan alasan penolakan, atau "" bila pertanyaannya layak diproses."""
    teks = (pertanyaan or "").strip()
    if len(teks) < konfig.PANJANG_MIN_PERTANYAAN:
        return (f"pertanyaan terlalu pendek ({len(teks)} karakter, "
                f"minimum {konfig.PANJANG_MIN_PERTANYAAN})")
    if len(teks) > konfig.PANJANG_MAKS_PERTANYAAN:
        return (f"pertanyaan terlalu panjang ({len(teks)} karakter, "
                f"maksimum {konfig.PANJANG_MAKS_PERTANYAAN})")
    for pola, sebab in POLA_TERLARANG:
        if pola.search(teks):
            return sebab
    return ""


def simpul_saring_masukan(keadaan: Keadaan) -> dict:
    """PASTI. Pagar masukan — nol token, nol detik, kalimat selalu sama."""
    sebab = periksa_masukan(keadaan["pertanyaan"])
    return {
        "diblokir": bool(sebab),
        "alasan": sebab,
        "langkah": [_baris("saring", "pasti", diblokir=bool(sebab),
                           sebab=sebab or "-")],
    }


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

    Simpul ini hanya MELAPOR: berapa cakupan sitasinya dan adakah sitasi hantu.
    Keputusan "apakah manusia perlu dipanggil" sengaja TIDAK diambil di sini,
    melainkan di simpul_dukungan (peningkatan 9), setelah seluruh bahannya
    lengkap. Satu tempat mengambil keputusan, beberapa tempat mengumpulkan
    bahan — bukan sebaliknya.
    """
    lapor = periksa_sitasi(keadaan["jawaban"], len(keadaan["potongan"]))
    return {
        "lapor": lapor,
        "langkah": [_baris("periksa", "pasti", cakupan=lapor["cakupan"],
                           hantu=sorted(lapor["hantu"]))],
    }


# ---------------------------------------------------------------- dukungan
# PENINGKATAN 8 — simpul pasti baru nomor dua.
#
# periksa_sitasi() hanya menghitung ADANYA penanda [n]. Kalimat "Masa percobaan
# adalah 6 bulan [1]" lolos sempurna meski potongan [1] menulis 3 bulan: ia
# ber-sitasi, nomornya sah, cakupannya 100%. Inilah halusinasi bersitasi yang
# dicatat modul B5 — dan justru bentuk kesalahan yang paling meyakinkan bagi
# pembaca, karena tampak sudah diverifikasi.
#
# Yang dikerjakan di sini murah dan pasti: untuk tiap kalimat ber-sitasi,
# hitung berapa banyak kata isinya yang benar-benar muncul di potongan yang
# dirujuk. Tanpa model, tanpa embedding, bisa diulang persis.
#
# Batasnya juga jelas dan harus disebut: ini pencocokan KATA, bukan makna.
# Parafrasa yang benar akan tampak lemah, dan kalimat salah yang kebetulan
# memakai kata-kata potongannya akan tampak kuat. Karena itu hasilnya dipakai
# untuk MEMANGGIL MANUSIA, bukan untuk menolak jawaban secara otomatis.
KATA_UMUM = {
    "yang", "untuk", "pada", "dari", "dengan", "adalah", "tidak", "dalam",
    "atau", "oleh", "akan", "dapat", "harus", "telah", "sebagai", "sesuai",
    "berdasarkan", "tersebut", "ini", "itu", "juga", "serta", "bila", "apabila",
    "menurut", "dokumen", "sumber", "potongan",
}


def _kata_isi(teks):
    """Kata bermakna dari sepotong teks: kata panjang dan seluruh angka."""
    kata = re.findall(r"[a-z0-9]+", (teks or "").lower())
    return {k for k in kata
            if (len(k) > 3 or k.isdigit()) and k not in KATA_UMUM}


def ukur_dukungan(jawaban, potongan):
    """Kembalikan (dukungan, daftar kalimat yang lemah dukungannya).

    dukungan = rata-rata bagian kata isi tiap kalimat ber-sitasi yang benar
    ditemukan di potongan yang dirujuk kalimat itu. Jawaban tanpa satu pun
    kalimat ber-sitasi bernilai 0,0 — bukan 1,0. Tidak adanya bukti bukan
    bukti tidak adanya masalah.
    """
    kalimat = [k for k in re.split(r"(?<=[.!?])\s+", jawaban or "") if k.strip()]
    nilai, lemah = [], []

    for k in kalimat:
        nomor = {int(n) for grup in re.findall(POLA_SITASI, k)
                 for n in re.findall(r"\d+", grup)}
        nomor = {n for n in nomor if 1 <= n <= len(potongan)}
        if not nomor:
            continue

        # Penanda sitasi dibuang sebelum kalimatnya diurai, supaya angka
        # di dalam "[1, 2]" tidak ikut terhitung sebagai kata isi.
        kata = _kata_isi(re.sub(POLA_SITASI, " ", k))
        if not kata:
            continue

        rujukan = set()
        for n in nomor:
            rujukan |= _kata_isi(potongan[n - 1].page_content)

        cocok = len(kata & rujukan) / len(kata)
        nilai.append(cocok)
        if cocok < 0.5:
            lemah.append(" ".join(k.split())[:70])

    return (round(sum(nilai) / len(nilai), 2) if nilai else 0.0), lemah


# ---------------------------------------------------------------- eskalasi
def perlu_manusia(keadaan: Keadaan):
    """PENINGKATAN 9 — kebijakan eskalasi, satu fungsi, tanpa model.

    Kembalikan daftar alasan; daftar kosong berarti tidak perlu manusia.

    Perhatikan bahwa semua ambangnya datang dari konfig.py, dan tidak satu pun
    dihitung model. "Kapan manusia dipanggil" adalah kebijakan organisasi: ia
    harus bisa dibaca oleh orang yang tidak menulis kodenya, diuji dengan
    angka, dan diubah tanpa menyentuh satu pun prompt.

    Empat pemicunya sengaja berbeda jenis:
      1. sitasi hantu     — jawaban menunjuk sumber yang tidak ada;
      2. cakupan rendah   — sebagian kalimat tidak membawa sumber;
      3. dukungan rendah  — sumbernya ada, isinya tidak mendukung;
      4. jenis dokumen    — bukan soal mutu sama sekali, melainkan taruhan.
         Salah kutip nilai kontrak lebih mahal daripada salah kutip nomor
         pasal, dan itu keputusan yang tidak bisa dibaca dari angka mana pun.
    """
    alasan = []
    lapor = keadaan.get("lapor") or {}

    if konfig.ESKALASI_SITASI_HANTU and lapor.get("hantu"):
        alasan.append(f"sitasi menunjuk potongan yang tidak ada: "
                      f"{sorted(lapor['hantu'])}")

    cakupan = lapor.get("cakupan", 0.0)
    if cakupan < konfig.AMBANG_ESKALASI:
        alasan.append(f"cakupan sitasi rendah ({cakupan:.0%}, "
                      f"ambang {konfig.AMBANG_ESKALASI:.0%})")

    dukungan = keadaan.get("dukungan", 0.0)
    if dukungan < konfig.AMBANG_DUKUNGAN:
        alasan.append(f"dukungan sitasi rendah ({dukungan:.0%}, "
                      f"ambang {konfig.AMBANG_DUKUNGAN:.0%})")

    peran = (keadaan.get("pengguna") or {}).get("peran", "")
    jenis = {d.metadata.get("jenis") for d in (keadaan.get("potongan") or [])}
    peka = sorted(jenis & konfig.ESKALASI_JENIS)
    if peka and peran not in konfig.PERAN_TANPA_ESKALASI:
        alasan.append(f"jawaban menyentuh dokumen berjenis {peka}")

    return alasan


def simpul_dukungan(keadaan: Keadaan) -> dict:
    """PASTI. Ukur dukungan sitasi, lalu putuskan perlu-tidaknya manusia."""
    dukungan, lemah = ukur_dukungan(keadaan["jawaban"], keadaan["potongan"])

    # Keputusan dan alasannya lahir di satu tempat. Kalau keduanya dipisah,
    # penyelia menerima "tolong periksa" tanpa keterangan apa yang harus
    # diperiksa — dan penyelia yang tidak tahu apa yang diperiksa akan
    # menyetujui semuanya.
    alasan = perlu_manusia({**keadaan, "dukungan": dukungan})
    return {
        "dukungan": dukungan,
        "alasan": "; ".join(alasan),
        "dieskalasi": bool(alasan),
        "langkah": [_baris("dukungan", "pasti", dukungan=dukungan,
                           kalimat_lemah=len(lemah),
                           eskalasi=bool(alasan), alasan="; ".join(alasan) or "-")],
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
        # PENINGKATAN 8 + 9 — tiga bidang baru. Tanpa ketiganya, menyetel
        # ambang eskalasi hanya bisa dilakukan dengan perasaan: jejak.py tidak
        # punya apa pun untuk dihitung, dan pertanyaan "berapa banyak yang
        # dieskalasi minggu lalu?" tidak terjawab.
        dukungan=keadaan.get("dukungan", 0.0),
        dieskalasi=bool(keadaan.get("dieskalasi")),
        diblokir=bool(keadaan.get("diblokir")),
        alasan=keadaan.get("alasan", ""),
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
def arah_saring(keadaan: Keadaan) -> str:
    """PASTI. Pertanyaan yang diblokir tidak perlu izin maupun pencarian."""
    return "tolak" if keadaan.get("diblokir") else "izin"


def arah_singgahan(keadaan: Keadaan) -> str:
    """PASTI. Cache kena -> langsung catat; meleset -> cari."""
    return "catat" if keadaan.get("dari_singgahan") else "cari"


def arah_cari(keadaan: Keadaan) -> str:
    """PASTI. Tanpa potongan, tidak ada gunanya memanggil model."""
    return "jawab" if keadaan["potongan"] else "tolak"


def arah_dukungan(keadaan: Keadaan) -> str:
    """PASTI. Gerbang yang memutuskan apakah manusia perlu dilibatkan.

    Perhatikan siapa yang memutuskan: sebuah fungsi biasa, bukan model.

    Pemicunya sudah dirumuskan simpul_dukungan sebagai `alasan` lewat
    perlu_manusia(). Gerbang ini hanya membaca bidang yang sama, sehingga
    alasan yang ditampilkan ke penyelia mustahil berbeda dari alasan yang
    memicunya.

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

    alur.add_node("saring", simpul_saring_masukan)
    alur.add_node("izin", simpul_izin)
    alur.add_node("singgahan", simpul_singgahan)
    alur.add_node("cari", simpul_cari)
    alur.add_node("jawab", simpul_jawab)
    alur.add_node("periksa", simpul_periksa)
    alur.add_node("dukungan", simpul_dukungan)
    alur.add_node("persetujuan", simpul_persetujuan)
    alur.add_node("tolak", simpul_tolak)
    alur.add_node("catat", simpul_catat)

    # PENINGKATAN 8 — pagar masukan menjadi simpul PERTAMA. Urutan ini yang
    # membuatnya berguna: diletakkan sesudah `cari`, ia tetap menolak hal yang
    # sama tetapi indeksnya sudah terlanjur dibaca dan modelnya sudah terlanjur
    # dipanggil. Menolak lebih awal adalah separuh dari nilai sebuah pagar.
    alur.add_edge(START, "saring")
    alur.add_conditional_edges("saring", arah_saring,
                               {"izin": "izin", "tolak": "tolak"})
    alur.add_edge("izin", "singgahan")
    alur.add_conditional_edges("singgahan", arah_singgahan,
                               {"cari": "cari", "catat": "catat"})
    alur.add_conditional_edges("cari", arah_cari,
                               {"jawab": "jawab", "tolak": "tolak"})
    alur.add_edge("jawab", "periksa")
    alur.add_edge("periksa", "dukungan")
    alur.add_conditional_edges("dukungan", arah_dukungan,
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
        "diblokir": False, "dukungan": 0.0, "dieskalasi": False,
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


# ============================================================ pengukuran
def jalankan_set_uji(peran="staf", otomatis="setuju", batas=None):
    """PENINGKATAN 9 — jalankan seluruh set uji, hitung berapa yang dieskalasi.

    Inilah alat ukur untuk peningkatan nomor 9, dan bentuk laporannya persis
    yang diminta README: "sebelum 6 dari 20, sesudah 2 dari 20, set uji sama".

    Dua hal yang membuat angka ini bisa dipercaya:

      - SINGGAHAN DIMATIKAN selama pengukuran. Kalau tidak, pertanyaan yang
        berulang akan kena cache, melompati simpul dukungan sama sekali, dan
        rasio eskalasi terlihat turun karena alasan yang tidak ada
        hubungannya dengan ambang yang sedang Anda setel;
      - keputusan manusianya dijawab OTOMATIS, karena yang sedang diukur
        adalah berapa sering manusia DIPANGGIL, bukan apa jawabannya.

    Perhatikan ongkosnya sebelum menjalankan: satu pertanyaan = satu panggilan
    model. Set uji 30 kasus di laptop tanpa GPU bisa belasan menit. Pakai
    --batas untuk mencoba sebagian dulu.
    """
    kasus = json.loads(konfig.SET_UJI.read_text(encoding="utf-8"))
    if batas:
        kasus = kasus[:batas]
    orang = izin.bereskan({"peran": peran})

    def penanya(permintaan, _o=otomatis):
        return {"disetujui": _o.lower().startswith("s"), "oleh": "otomatis"}

    # Cache dimatikan dengan mengganti singgahan bersama, bukan dengan variabel
    # lingkungan — supaya pengukuran ini tidak menuntut peserta menyetel apa pun
    # dan tidak ikut mengotori cache proses lain.
    singgahan_lama = singgahan.BERSAMA
    singgahan.BERSAMA = singgahan.Singgahan(maks=1)

    print(f"Menjalankan {len(kasus)} pertanyaan sebagai peran '{orang['peran']}'")
    print("Setelan eskalasi aktif:")
    print(f"  cakupan  < {konfig.AMBANG_ESKALASI:.2f}")
    print(f"  dukungan < {konfig.AMBANG_DUKUNGAN:.2f}")
    print(f"  jenis    : {sorted(konfig.ESKALASI_JENIS) or '-'}")
    print(f"  sitasi hantu selalu dieskalasi: "
          f"{'ya' if konfig.ESKALASI_SITASI_HANTU else 'tidak'}\n")

    dieskalasi, ditolak, sebab = 0, 0, {}
    try:
        for i, x in enumerate(kasus, 1):
            hasil = jalankan(x["tanya"], orang, penanya=penanya, tampilkan=False)
            naik = bool(hasil.get("dieskalasi")) and not hasil.get("ditolak")
            dieskalasi += naik
            ditolak += bool(hasil.get("ditolak"))
            if naik:
                for a in hasil.get("alasan", "").split("; "):
                    kunci = a.split("(")[0].strip()
                    sebab[kunci] = sebab.get(kunci, 0) + 1
            print(f"  [{i:2d}/{len(kasus)}] "
                  f"{'ESKALASI' if naik else 'lewat   '}  "
                  f"cakupan={(hasil.get('lapor') or {}).get('cakupan', 0):.0%} "
                  f"dukungan={hasil.get('dukungan', 0):.0%}  "
                  f"{x['tanya'][:52]}")
    finally:
        singgahan.BERSAMA = singgahan_lama

    print("\n" + "=" * 74)
    print(f"  dieskalasi ke manusia : {dieskalasi} dari {len(kasus)} "
          f"({dieskalasi / len(kasus):.0%})")
    print(f"  ditolak (tidak dieskalasi): {ditolak}")
    for a, n in sorted(sebab.items(), key=lambda x: -x[1]):
        print(f"      {n:3d}x {a}")
    print("=" * 74)
    print("Catat angka ini SEBELUM menyetel ambang di konfig.py, lalu ulangi")
    print("dengan set uji yang sama. Itulah bukti untuk peningkatan nomor 9.")
    return dieskalasi, len(kasus)


if __name__ == "__main__":
    argumen = sys.argv[1:]
    peran = util.ambil_bendera(argumen, "--peran", "pimpinan")
    otomatis = util.ambil_bendera(argumen, "--otomatis")
    batas = util.ambil_bendera(argumen, "--batas")
    set_uji = util.ambil_saklar(argumen, "--set-uji")

    if set_uji:
        jalankan_set_uji(peran=peran, otomatis=otomatis or "setuju",
                         batas=int(batas) if batas else None)
        sys.exit(0)

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
