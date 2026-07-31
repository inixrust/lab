# -*- coding: utf-8 -*-
"""Beberapa agent yang bekerja sebagai TIM — modul A3 (multi-agent).

    python tim.py "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
    python tim.py "Berapa panjang minimum kata sandi sistem internal?"

Di agen.py dan graf.py ada SATU agent yang memegang dua alat sekaligus. Di sini
pekerjaan yang sama dibagi kepada dua agent SPESIALIS, dengan seorang PENYELIA
(supervisor) yang memutuskan giliran siapa:

                       START
                         |
                         v
                  +-------------+
              +-->|  penyelia   |----------------+
              |   +------+------+                |
              |      |       |                   |
              |  pencari   penghitung            v
              |      |       |              perangkum -> END
              +------+-------+

    pencari     -> HANYA memegang alat cari_kebijakan (membaca dokumen)
    penghitung  -> HANYA memegang alat hitung (aritmetika)
    penyelia    -> tidak memegang alat sama sekali; ia hanya memilih giliran
    perangkum   -> menyusun jawaban akhir dari seluruh percakapan

Kenapa dipecah? Bukan karena lebih cepat — untuk soal sekecil ini justru lebih
lambat dan lebih boros token daripada agen.py. Alasan yang sebenarnya:

  - tiap agent punya prompt dan daftar alat yang sempit, jadi lebih sulit
    tersesat; prompt pencari tidak perlu menjelaskan aturan aritmetika;
  - alat berisiko bisa dikurung pada satu anggota yang punya aturannya sendiri
    (prinsip guardrail modul A4) — bayangkan anggota ketiga 'pengirim-email';
  - tim bisa ditambah anggota tanpa menyentuh prompt anggota yang sudah ada.

Kelemahannya nyata dan jangan disembunyikan: satu putaran penyelia = satu
panggilan LLM tambahan, dan penyelia bisa salah menunjuk sehingga tim berputar
tanpa kemajuan (karena itu ada MAKS_PUTARAN di bawah). Multi-agent adalah cara
mengelola KERUMITAN, bukan cara mempercepat. Bila satu agent dengan tiga alat
masih terbaca jelas, pakai satu agent.
"""
import operator
import re
import sys
from typing import Annotated, TypedDict

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

import konfig
from agen import cari_kebijakan, hitung
from model import ambil_llm

# Sesudah sekian putaran penyelia, tim dipaksa merangkum. Tanpa batas ini,
# penyelia yang bingung bisa memanggil anggota yang sama berulang kali.
MAKS_PUTARAN = 4


# ============================================================ keadaan (state)
class Keadaan(TypedDict):
    """Selain daftar pesan, tim perlu mencatat giliran siapa berikutnya.

    Inilah bedanya dengan graf.py: di sana arah ditentukan dengan MEMBACA pesan
    terakhir; di sini penyelia menuliskan keputusannya ke dalam keadaan, dan
    sisi bersyarat tinggal membacanya. Untuk alur yang lebih rumit, keputusan
    yang tersimpan seperti ini jauh lebih mudah ditelusuri saat ada yang salah.
    """
    pesan: Annotated[list, add_messages]
    berikutnya: str
    putaran: int
    # Anggota yang sudah melapor. Reducer operator.add menyambung daftar,
    # jadi tiap anggota cukup mengembalikan namanya sendiri.
    sudah: Annotated[list, operator.add]


# ============================================================ anggota tim
PROMPT_PENCARI = """Anda anggota tim yang bertugas MEMBACA DOKUMEN INTERNAL
PT Nusantara Cipta Solusi.

Gunakan alat cari_kebijakan untuk menemukan fakta yang diminta. Jangan menjawab
dari ingatan. Laporkan temuan Anda apa adanya beserta angkanya bila ada, lengkap
dengan penanda sumber. Bila informasinya tidak ada, katakan demikian.

Anda TIDAK bertugas menghitung. Cukup laporkan angka yang Anda temukan; anggota
lain yang akan mengalikannya."""

PROMPT_PENGHITUNG = """Anda anggota tim yang bertugas MENGHITUNG.

Ambil angka yang sudah disebutkan di percakapan, lalu gunakan alat hitung untuk
menjumlahkan atau mengalikannya. Anda TIDAK bisa membaca dokumen — bila angka
yang diperlukan belum ada di percakapan, katakan bahwa angkanya belum tersedia.

Laporkan hasil hitungannya secara singkat."""

_anggota = {}


def _ambil_anggota(nama):
    """Buat (sekali) satu agent spesialis lengkap dengan lingkaran alatnya.

    create_agent() dari LangChain menghasilkan graph ReAct yang sudah jadi —
    isinya persis pola model->alat->model yang kita rakit tangan di graf.py.
    Sekarang kita memakai yang siap pakai, karena yang sedang dipelajari adalah
    lapisan di ATASNYA: bagaimana beberapa agent dikoordinasikan.
    """
    if nama not in _anggota:
        alat, prompt = {
            "pencari": ([cari_kebijakan], PROMPT_PENCARI),
            "penghitung": ([hitung], PROMPT_PENGHITUNG),
        }[nama]
        _anggota[nama] = create_agent(ambil_llm(), alat, system_prompt=prompt)
    return _anggota[nama]


def _jalankan_anggota(nama, keadaan: Keadaan) -> dict:
    """Jalankan satu anggota, kembalikan laporannya sebagai satu pesan.

    Seluruh percakapan diteruskan supaya penghitung bisa melihat angka yang
    ditemukan pencari. Yang dikembalikan ke tim HANYA pesan terakhir anggota
    itu — langkah internalnya (panggilan alat, hasil mentah) tidak ikut
    mengotori percakapan tim. Pemisahan ini yang membuat multi-agent tetap
    terbaca saat anggotanya bertambah.
    """
    hasil = _ambil_anggota(nama).invoke({"messages": keadaan["pesan"]})
    isi = (hasil["messages"][-1].content or "").strip()
    return {"pesan": [AIMessage(content=isi, name=nama)], "sudah": [nama]}


def simpul_pencari(keadaan: Keadaan) -> dict:
    return _jalankan_anggota("pencari", keadaan)


def simpul_penghitung(keadaan: Keadaan) -> dict:
    return _jalankan_anggota("penghitung", keadaan)


# ============================================================ penyelia
PROMPT_PENYELIA = """Anda penyelia sebuah tim kecil di PT Nusantara Cipta Solusi.

Anggota tim Anda:
- PENCARI    : satu-satunya yang boleh membaca dokumen internal (SOP, surat
               edaran, notulen). Panggil dia untuk semua fakta, aturan, besaran,
               dan ketentuan.
- PENGHITUNG : hanya menghitung dari angka yang SUDAH ada di percakapan. Dia
               tidak bisa membaca dokumen.

Tugas Anda HANYA memilih giliran berikutnya — bukan menjawab pertanyaannya.

Aturan:
1. Bila fakta yang dibutuhkan belum ada di percakapan, pilih PENCARI.
2. Bila angkanya sudah ada tetapi masih perlu dikalikan atau dijumlahkan,
   pilih PENGHITUNG.
3. Bila pertanyaan sudah bisa dijawab dari percakapan, pilih SELESAI.
4. Jangan memanggil anggota yang pekerjaannya sudah selesai.

Jawab dengan SATU KATA saja: PENCARI, PENGHITUNG, atau SELESAI."""

# Urutan tidak menentukan prioritas — yang dipakai adalah kata yang muncul
# PALING AKHIR pada balasan penyelia (lihat _baca_arah).
KATA_ARAH = (("PENCARI", "pencari"), ("PENGHITUNG", "penghitung"),
             ("SELESAI", "selesai"))


def _baca_arah(teks):
    """Terjemahkan balasan penyelia menjadi nama giliran.

    Dua kenyataan lapangan yang ditangani di sini, dan keduanya akan Anda temui
    lagi di sistem sungguhan:

    1. qwen3 kerap menuliskan penalarannya di dalam blok <think>...</think>.
       Blok itu dibuang lebih dulu — kalau tidak, kata 'PENCARI' yang muncul
       saat model sedang menimbang-nimbang bisa terbaca sebagai keputusan.
    2. Model sering menambah kalimat pengantar meski diminta satu kata. Karena
       keputusan sebenarnya hampir selalu di akhir, yang diambil adalah kata
       yang muncul paling belakang.

    Bila tidak ada kata yang dikenali, tim dihentikan — lebih baik merangkum
    apa adanya daripada menebak giliran dan berputar tanpa arah.
    """
    bersih = re.sub(r"<think>.*?</think>", " ", teks or "", flags=re.S | re.I).upper()
    terpilih, posisi_terjauh = "selesai", -1
    for kata, arah in KATA_ARAH:
        posisi = bersih.rfind(kata)
        if posisi > posisi_terjauh:
            terpilih, posisi_terjauh = arah, posisi
    return terpilih


_llm = None


def _model():
    global _llm
    if _llm is None:
        _llm = ambil_llm()
    return _llm


def simpul_penyelia(keadaan: Keadaan) -> dict:
    """Pilih giliran berikutnya dan simpan keputusannya ke dalam keadaan."""
    putaran = keadaan.get("putaran", 0) + 1
    sudah = keadaan.get("sudah", [])

    # Sabuk pengaman: hentikan tim yang berputar tanpa kemajuan.
    if putaran > MAKS_PUTARAN:
        return {"berikutnya": "selesai", "putaran": putaran}

    # TODO L3.3-2: Buat penyelia benar-benar memutuskan.
    #   1. Panggil _model().invoke([...]) dengan, berurutan:
    #        SystemMessage(PROMPT_PENYELIA), lalu seluruh keadaan["pesan"],
    #        lalu HumanMessage(f"Anggota yang sudah melapor: "
    #                          f"{', '.join(sudah) or 'belum ada'}. "
    #                          f"Giliran siapa berikutnya? Jawab satu kata.")
    #      Perhatikan: penyelia TIDAK diberi alat apa pun — tugasnya hanya
    #      memilih. Inilah bedanya dengan agen.py yang satu model memegang
    #      semuanya.
    #   2. Terjemahkan balasannya dengan _baca_arah(balasan.content).
    #   3. KOREKSI PASTI: bila pilihannya sudah ada di `sudah`, ganti jadi
    #      "selesai". Model kecil kerap menunjuk ulang anggota yang baru saja
    #      melapor — dan tim lalu berputar sampai MAKS_PUTARAN dengan jawaban
    #      kosong. Aturan ini ditegakkan di KODE, bukan dititipkan ke prompt
    #      (bandingkan penyaring status di cari.py). Coba hilangkan langkah ini
    #      setelah jadi, lalu jalankan beberapa kali: Anda akan melihat sendiri
    #      berapa sering model mengulang.
    #   4. Kembalikan {"berikutnya": <hasilnya>, "putaran": putaran}.
    #
    # Sebelum dikerjakan, penyelia selalu menjawab "selesai": tim langsung
    # loncat ke perangkum tanpa ada anggota yang bekerja, dan jawabannya keluar
    # tanpa sumber — atau salah sama sekali. Jalankan dulu apa adanya supaya
    # Anda melihat sendiri apa yang hilang ketika tidak ada yang mengatur
    # giliran.
    return {"berikutnya": "selesai", "putaran": putaran}


def arah_penyelia(keadaan: Keadaan) -> str:
    """Sisi bersyarat: cukup membaca keputusan yang sudah ditulis penyelia."""
    return keadaan["berikutnya"]


# ============================================================ perangkum
PROMPT_PERANGKUM = """Anda menyusun jawaban akhir untuk pengguna, berdasarkan
laporan anggota tim dalam percakapan ini.

Aturan:
1. Pakai HANYA yang dilaporkan anggota tim. Jangan menambah pengetahuan luar.
2. Pertahankan penanda sumber berupa angka dalam kurung siku, misalnya [1].
3. Bila laporan menyatakan informasinya tidak ditemukan, sampaikan itu apa
   adanya. Jangan mengarang.
4. Singkat, dalam bahasa Indonesia. Jangan menuliskan proses berpikir Anda."""


def simpul_perangkum(keadaan: Keadaan) -> dict:
    """Satukan laporan anggota menjadi satu jawaban untuk pengguna.

    Susunan pesannya sama seperti di penyelia: sistem di depan, percakapan di
    tengah, perintah di belakang. Model chat dilatih dengan pesan sistem di
    awal — menaruhnya di akhir membuat sebagian model mengabaikannya.
    """
    balasan = _model().invoke(
        [SystemMessage(PROMPT_PERANGKUM)] + keadaan["pesan"]
        + [HumanMessage("Susun jawaban akhirnya sekarang.")]
    )
    return {"pesan": [AIMessage(content=(balasan.content or "").strip(),
                                name="perangkum")]}


# ============================================================ merakit tim
def bangun_tim():
    """Rakit graph tim dan kompilasi."""
    alur = StateGraph(Keadaan)

    alur.add_node("penyelia", simpul_penyelia)
    alur.add_node("pencari", simpul_pencari)
    alur.add_node("penghitung", simpul_penghitung)
    alur.add_node("perangkum", simpul_perangkum)

    alur.add_edge(START, "penyelia")

    # Satu-satunya percabangan ada di penyelia. Anggota tim tidak pernah saling
    # memanggil langsung — semuanya kembali ke penyelia. Pola bintang seperti
    # ini yang membuat alurnya masih bisa dibaca saat anggotanya jadi lima.
    alur.add_conditional_edges("penyelia", arah_penyelia, {
        "pencari": "pencari",
        "penghitung": "penghitung",
        "selesai": "perangkum",
    })

    alur.add_edge("pencari", "penyelia")
    alur.add_edge("penghitung", "penyelia")
    alur.add_edge("perangkum", END)

    return alur.compile()


# ============================================================ menjalankan
def _cetak_langkah(nama, perubahan):
    """Cetak apa yang barusan dikerjakan satu simpul."""
    if nama == "penyelia":
        print(f"  [penyelia] giliran -> {perubahan['berikutnya']}")
    elif nama != "perangkum":
        cuplik = " ".join(perubahan["pesan"][-1].content.split())[:104]
        print(f"  [{nama}] {cuplik}")


def jalankan_tim(pertanyaan, tampilkan_langkah=True):
    """Jalankan tim sampai perangkum selesai, kembalikan jawaban akhirnya."""
    llm = ambil_llm()

    if konfig.MODE_TIRUAN or not hasattr(llm, "bind_tools"):
        print("  [Tim agent membutuhkan model dengan tool-calling — mode tiruan "
              "tidak mendukungnya.]")
        print("  [Menampilkan satu panggilan cari_kebijakan langsung sebagai gantinya.]\n")
        return cari_kebijakan.invoke({"pertanyaan": pertanyaan})

    tim = bangun_tim()
    awal = {"pesan": [HumanMessage(pertanyaan)], "berikutnya": "",
            "putaran": 0, "sudah": []}

    # stream_mode="updates" memberi kita {nama_simpul: perubahannya} — pas untuk
    # multi-agent, karena yang ingin dilihat justru SIAPA yang barusan bekerja.
    # (graf.py memakai "values" karena di sana yang menarik adalah isi pesannya.)
    akhir = ""
    for langkah in tim.stream(awal, {"recursion_limit": 2 * MAKS_PUTARAN + 4},
                              stream_mode="updates"):
        for nama, perubahan in langkah.items():
            if tampilkan_langkah:
                _cetak_langkah(nama, perubahan)
            if nama == "perangkum":
                akhir = perubahan["pesan"][-1].content

    return akhir.strip()


if __name__ == "__main__":
    tanya = " ".join(sys.argv[1:]) or \
        "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
    print(f"Pertanyaan: {tanya}\n")
    jawaban = jalankan_tim(tanya)
    print("\nJAWABAN TIM:")
    print(jawaban)
