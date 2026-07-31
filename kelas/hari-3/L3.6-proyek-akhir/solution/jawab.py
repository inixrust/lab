# -*- coding: utf-8 -*-
"""Pipeline pembangkitan: susun konteks -> prompt -> jawaban ber-sitasi.

Jalankan langsung untuk mencoba: python jawab.py "pertanyaan Anda"
"""
import re
import sys

from langchain_core.prompts import ChatPromptTemplate

import izin
import konfig
import util
from cari import ambil_terbaik
from model import ambil_llm

# Pola satu penanda sitasi. Menerima bentuk gabungan seperti [1, 2] atau [1;2],
# bukan hanya [1] — kalau tidak, kalimat ber-sitasi ganda dianggap tak bersumber
# dan cakupan terhitung rendah keliru. Wajib memuat setidaknya satu digit.
POLA_SITASI = r"\[\s*\d[\d,;\s]*\]"

# Kalimat penolakan diambil dari konfig.py, bukan ditulis ulang di sini.
# Ia dicocokkan sebagai teks persis oleh nilai.py — kalau ada dua versi yang
# sedikit berbeda, metrik penolakan akan melaporkan nol tanpa ada yang sadar.
TIDAK_DITEMUKAN = konfig.TIDAK_DITEMUKAN

SISTEM = f"""Anda asisten dokumen internal PT Nusantara Cipta Solusi.
Anda menjawab HANYA berdasarkan KONTEKS yang diberikan.

ATURAN — tidak boleh dilanggar:
1. Gunakan hanya informasi dari KONTEKS. Jangan menambahkan pengetahuan dari
   luar, meskipun Anda mengetahuinya.
2. Setiap klaim faktual wajib diikuti penanda sumber berupa ANGKA di dalam
   kurung siku, sesuai nomor potongan pada KONTEKS — contohnya [1] atau [2].
   Gunakan angkanya, jangan menulis huruf di dalam kurung (bukan [n]).
3. Bila KONTEKS tidak memuat jawabannya, jawab persis kalimat berikut dan
   tidak menambahkan apa pun:
   {konfig.TIDAK_DITEMUKAN}
4. Bila potongan saling bertentangan, sebutkan pertentangannya beserta
   sumber masing-masing. Jangan memilih salah satu diam-diam.
5. Jawab langsung, ringkas, dalam bahasa Indonesia. Jangan menuliskan proses
   berpikir Anda."""

TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SISTEM),
    ("human", "KONTEKS:\n{konteks}\n\nPERTANYAAN:\n{pertanyaan}"),
])


def rakit_konteks(potongan):
    """Beri nomor tiap potongan agar model bisa merujuknya kembali."""
    bagian = []
    for i, d in enumerate(potongan, start=1):
        m = d.metadata
        bagian.append(
            f"[{i}] sumber: {m.get('source', '?')}, {util.lokasi(m)}\n"
            f"{d.page_content}"
        )
    return "\n\n---\n\n".join(bagian)


def susun_jawaban(llm, pertanyaan, potongan):
    """Rakit konteks, kirim ke model, kembalikan teks jawabannya.

    Dipisah sebagai fungsi tersendiri karena dipakai ulang oleh pola agentic
    di modul A2 dan A3 — di situ potongannya sudah disaring lebih dulu.
    """
    if not potongan:
        return TIDAK_DITEMUKAN
    prompt = TEMPLATE.invoke({
        "konteks": rakit_konteks(potongan),
        "pertanyaan": pertanyaan,
    })
    return llm.invoke(prompt).content.strip()


def periksa_sitasi(jawaban, jumlah_potongan):
    """Pemeriksaan struktural. Murah dan otomatis, tapi TIDAK menangkap
    sitasi yang menunjuk potongan nyata namun isinya tak mendukung klaim —
    lihat pembahasan halusinasi bersitasi di modul B5."""
    dirujuk = set()
    for grup in re.findall(POLA_SITASI, jawaban):
        dirujuk.update(int(n) for n in re.findall(r"\d+", grup))
    hantu = {n for n in dirujuk if not 1 <= n <= jumlah_potongan}

    kalimat = [k for k in re.split(r"(?<=[.!?])\s+", jawaban) if k.strip()]
    bersitasi = [k for k in kalimat if re.search(POLA_SITASI, k)]
    cakupan = len(bersitasi) / len(kalimat) if kalimat else 0.0

    return {"hantu": hantu, "cakupan": round(cakupan, 2)}


_llm = None


def jawab(pertanyaan, pengguna=None, k=None, tampilkan_potongan=True):
    """Kembalikan (jawaban, potongan, laporan_pemeriksaan)."""
    global _llm
    if _llm is None:
        _llm = ambil_llm()

    # PENINGKATAN 5 — sebelumnya di sini hanya ada `pass` berisi catatan
    # "tempat menambahkan penyaring unit kerja", dan akibatnya nyata: pilihan
    # peran di sidebar app.py TIDAK BERPENGARUH APA PUN. Antarmuka yang
    # menampilkan pilihan peran padahal peran tidak dipakai lebih buruk
    # daripada antarmuka tanpa pilihan itu — ia membuat orang percaya ada pagar
    # yang sebenarnya tidak ada.
    #
    # pengguna=None sengaja tetap dibiarkan memakai penyaring status saja:
    # nilai.py mengukur mutu pengambilan atas SELURUH korpus, dan mencampurkan
    # hak akses ke situ membuat angka recall turun karena alasan yang sama
    # sekali berbeda.
    saring = (izin.saring_untuk(pengguna) if pengguna
              else {"status": konfig.STATUS_BERLAKU})

    potongan = ambil_terbaik(pertanyaan, k=k, saring=saring)

    # Pagar terakhir, sama seperti di tanya.py. Seharusnya tidak membuang apa
    # pun; kalau ia pernah membuang sesuatu, ada jalur pengambilan yang lolos
    # dari penyaring di hulu dan Anda ingin tahu hari itu juga.
    if pengguna:
        potongan = izin.saring_potongan(pengguna, potongan)

    # Kebiasaan dari modul F3: LIHAT POTONGAN SEBELUM MELIHAT JAWABAN.
    # Ini yang memisahkan orang yang bisa memperbaiki sistem RAG dari orang
    # yang hanya bisa mengganti-ganti prompt. Jangan dihapus.
    if tampilkan_potongan:
        print("-" * 74)
        for i, d in enumerate(potongan, 1):
            cuplik = " ".join(d.page_content.split())[:84]
            print(f"[{i}] {d.metadata.get('source', '?')[:32]:34s} "
                  f"{util.lokasi(d.metadata):14s} {cuplik}...")
        print("-" * 74)

    isi = susun_jawaban(_llm, pertanyaan, potongan)
    lapor = periksa_sitasi(isi, len(potongan))

    if lapor["hantu"]:
        print(f"  PERINGATAN: sitasi menunjuk potongan yang tidak ada: {lapor['hantu']}")
    if TIDAK_DITEMUKAN not in isi and lapor["cakupan"] < konfig.AMBANG_CAKUPAN:
        print(f"  PERINGATAN: cakupan sitasi rendah ({lapor['cakupan']:.0%})")

    return isi, potongan, lapor


if __name__ == "__main__":
    tanya = " ".join(sys.argv[1:]) or "Berapa lama masa percobaan karyawan baru?"
    print(f"Pertanyaan: {tanya}\n")
    isi, potongan, lapor = jawab(tanya)
    print("\nJAWABAN:")
    print(isi)
    print(f"\n(cakupan sitasi {lapor['cakupan']:.0%})")
