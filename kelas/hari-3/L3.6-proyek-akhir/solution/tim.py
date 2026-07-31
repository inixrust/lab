# -*- coding: utf-8 -*-
"""Beberapa agent yang bekerja sebagai TIM — modul A3 (multi-agent).

    python tim.py "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
    python tim.py "Berapa panjang minimum kata sandi sistem internal?"
    python tim.py "Cuti saya mulai 1 Juli 2026, paling lambat kapan diajukan?"

Di agen.py dan graf.py ada SATU agent yang memegang dua alat sekaligus. Di sini
pekerjaan yang sama dibagi kepada dua agent SPESIALIS, dengan seorang PENYELIA
(supervisor) yang memutuskan giliran siapa:

                       START
                         |
                         v
                  +-------------+
              +-->|  penyelia   |----------------+
              |   +------+------+                |
              |      |    |    |                 |
              |  pencari  |  penghitung          v
              |        penanggal            perangkum -> END
              +------+----+----+-+

    pencari     -> HANYA memegang alat cari_kebijakan (membaca dokumen)
    penghitung  -> HANYA memegang alat hitung (aritmetika)
    penanggal   -> HANYA memegang alat hitung_tanggal (peningkatan 7)
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

import izin
import konfig
import util
from agen import cari_kebijakan, hitung, hitung_tanggal, set_pengguna
from model import ambil_llm

# Sesudah sekian putaran penyelia, tim dipaksa merangkum. Tanpa batas ini,
# penyelia yang bingung bisa memanggil anggota yang sama berulang kali.
#
# PENINGKATAN 7 — batas dinaikkan dari 4 ke 5 seiring bertambahnya anggota.
# Angkanya bukan selera: dengan aturan "sekali per anggota" di simpul_penyelia,
# tim bertiga membutuhkan sekurang-kurangnya 3 putaran untuk memanggil semua
# anggota ditambah 1 putaran untuk memutuskan SELESAI. Batas yang tertinggal di
# angka lama akan memotong tim tepat sebelum anggota ketiga sempat bekerja —
# kegagalan yang gejalanya (jawaban kurang lengkap) sama sekali tidak menunjuk
# ke sebabnya.
MAKS_PUTARAN = 5


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

Anda TIDAK menghitung tanggal. Bila yang diminta adalah tanggal batas, katakan
bahwa itu tugas anggota lain.

Laporkan hasil hitungannya secara singkat."""

# PENINGKATAN 7 — anggota ketiga.
#
# Kenapa anggota baru, bukan alat baru pada anggota yang sudah ada? Bandingkan
# dua pilihan itu jujur-jujuran:
#
#   - memberi hitung_tanggal kepada `penghitung` lebih murah satu putaran
#     penyelia, dan untuk tim sekecil ini memang lebih cepat;
#   - anggota tersendiri membuat prompt masing-masing tetap pendek. Prompt
#     penghitung tidak perlu menjelaskan format tanggal dan arah hari
#     (negatif = sebelum), dan prompt penanggal tidak perlu menjelaskan
#     aritmetika rupiah.
#
# Yang menentukan bukan jumlah alatnya, melainkan apakah ATURAN memakai alat
# itu saling mengganggu bila ditulis dalam satu prompt. Di sini iya: arah
# negatif pada hitung_tanggal berarti 'sebelum', sedangkan bilangan negatif
# pada hitung berarti pengurangan biasa. Dua arti untuk satu tanda minus di
# satu prompt yang sama adalah cara terpendek membuat model bingung.
PROMPT_PENANGGAL = """Anda anggota tim yang bertugas MENGHITUNG TANGGAL.

Gunakan alat hitung_tanggal untuk mengubah aturan seperti "paling lambat 7 hari
kerja sebelum pelaksanaan" menjadi tanggal yang sebenarnya.

Aturan:
1. jumlah_hari NEGATIF berarti sebelum, POSITIF berarti sesudah.
2. Pakai jenis_hari "kerja" bila dokumen menyebut "hari kerja", dan "kalender"
   bila dokumen menyebut "hari" saja atau "hari kalender".
3. Anda TIDAK bisa membaca dokumen. Bila jumlah harinya belum disebutkan di
   percakapan, katakan bahwa aturannya belum tersedia.
4. Laporkan tanggal hasilnya beserta nama harinya, singkat."""

_anggota = {}

# Satu tempat yang menghubungkan nama anggota dengan alat dan prompt-nya.
# Menambah anggota keempat berarti menambah satu baris di sini dan satu baris
# di KATA_ARAH — bukan menyunting empat fungsi yang tersebar.
BEKAL_ANGGOTA = {
    "pencari": ([cari_kebijakan], PROMPT_PENCARI),
    "penghitung": ([hitung], PROMPT_PENGHITUNG),
    "penanggal": ([hitung_tanggal], PROMPT_PENANGGAL),
}


def _ambil_anggota(nama):
    """Buat (sekali) satu agent spesialis lengkap dengan lingkaran alatnya.

    create_agent() dari LangChain menghasilkan graph ReAct yang sudah jadi —
    isinya persis pola model->alat->model yang kita rakit tangan di graf.py.
    Sekarang kita memakai yang siap pakai, karena yang sedang dipelajari adalah
    lapisan di ATASNYA: bagaimana beberapa agent dikoordinasikan.
    """
    if nama not in _anggota:
        alat, prompt = BEKAL_ANGGOTA[nama]
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


def simpul_penanggal(keadaan: Keadaan) -> dict:
    return _jalankan_anggota("penanggal", keadaan)


# ============================================================ penyelia
PROMPT_PENYELIA = """Anda penyelia sebuah tim kecil di PT Nusantara Cipta Solusi.

Anggota tim Anda:
- PENCARI    : satu-satunya yang boleh membaca dokumen internal (SOP, surat
               edaran, notulen). Panggil dia untuk semua fakta, aturan, besaran,
               dan ketentuan.
- PENGHITUNG : hanya menghitung angka yang SUDAH ada di percakapan (menjumlah,
               mengalikan). Dia tidak bisa membaca dokumen.
- PENANGGAL  : hanya menghitung TANGGAL dari aturan yang SUDAH ada di
               percakapan, misalnya "7 hari kerja sebelum 1 Juli 2026". Dia
               tidak bisa membaca dokumen dan tidak menghitung uang.

Tugas Anda HANYA memilih giliran berikutnya — bukan menjawab pertanyaannya.

Aturan:
1. Bila fakta yang dibutuhkan belum ada di percakapan, pilih PENCARI.
2. Bila angkanya sudah ada tetapi masih perlu dikalikan atau dijumlahkan,
   pilih PENGHITUNG.
3. Bila yang masih kurang adalah tanggal batas, dan aturan jumlah harinya sudah
   ada di percakapan, pilih PENANGGAL.
4. Bila pertanyaan sudah bisa dijawab dari percakapan, pilih SELESAI.
5. Jangan memanggil anggota yang pekerjaannya sudah selesai.

Jawab dengan SATU KATA saja: PENCARI, PENGHITUNG, PENANGGAL, atau SELESAI."""

# Urutan tidak menentukan prioritas — yang dipakai adalah kata yang muncul
# PALING AKHIR pada balasan penyelia (lihat _baca_arah).
#
# PENINGKATAN 7 — satu jebakan yang baru muncul begitu anggotanya bertambah:
# kata kunci tidak boleh menjadi bagian dari kata kunci lain. "PENCARI" dan
# "PENANGGAL" aman karena tidak saling memuat; seandainya anggota baru diberi
# nama "PENGHITUNG TANGGAL", rfind("PENGHITUNG") akan menemukannya dan tim
# memanggil anggota yang salah tanpa satu pun galat muncul.
KATA_ARAH = (("PENCARI", "pencari"), ("PENGHITUNG", "penghitung"),
             ("PENANGGAL", "penanggal"), ("SELESAI", "selesai"))


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

    balasan = _model().invoke(
        [SystemMessage(PROMPT_PENYELIA)] + keadaan["pesan"]
        + [HumanMessage(
            f"Anggota yang sudah melapor: {', '.join(sudah) or 'belum ada'}. "
            f"Giliran siapa berikutnya? Jawab satu kata.")]
    )
    pilihan = _baca_arah(balasan.content)

    # KOREKSI PASTI di atas keputusan model. Diamati sungguhan di kelas: model
    # kecil kerap menunjuk ulang anggota yang baru saja melapor, lalu tim
    # berputar sampai MAKS_PUTARAN dan jawabannya jadi kosong. Aturan "sekali
    # per anggota" ditegakkan di KODE, bukan dititipkan ke prompt — persis
    # prinsip yang sama dengan penyaring status di cari.py.
    #
    # Batasnya jujur saja: untuk tugas yang memang menuntut satu anggota
    # bekerja dua kali (misalnya dua pencarian berbeda), aturan ini terlalu
    # ketat dan harus diganti — misalnya dengan membandingkan APA yang diminta,
    # bukan sekadar siapa yang dipanggil.
    if pilihan in sudah:
        pilihan = "selesai"

    return {"berikutnya": pilihan, "putaran": putaran}


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
    alur.add_node("penanggal", simpul_penanggal)
    alur.add_node("perangkum", simpul_perangkum)

    alur.add_edge(START, "penyelia")

    # Satu-satunya percabangan ada di penyelia. Anggota tim tidak pernah saling
    # memanggil langsung — semuanya kembali ke penyelia. Pola bintang seperti
    # ini yang membuat alurnya masih bisa dibaca saat anggotanya jadi lima.
    #
    # PENINGKATAN 7 — peta tujuan dibangun dari BEKAL_ANGGOTA, bukan ditulis
    # ulang. Peta yang ditulis tangan adalah tempat anggota baru paling sering
    # terlupakan: KATA_ARAH sudah mengenal namanya, penyelia sudah memilihnya,
    # lalu graph menolak dengan galat tujuan tak dikenal — di tengah demo.
    tujuan = {nama: nama for nama in BEKAL_ANGGOTA}
    tujuan["selesai"] = "perangkum"
    alur.add_conditional_edges("penyelia", arah_penyelia, tujuan)

    for nama in BEKAL_ANGGOTA:
        alur.add_edge(nama, "penyelia")
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


def jalankan_tim(pertanyaan, pengguna=None, tampilkan_langkah=True):
    """Jalankan tim sampai perangkum selesai, kembalikan jawaban akhirnya.

    Kembalikan (jawaban, jejak_langkah). Jejaknya adalah daftar nama simpul
    sesuai urutan jalannya — inilah bukti yang diminta untuk peningkatan 7:
    anggota baru dipanggil atau tidak, dan berapa mahal ongkos tambahannya.
    """
    llm = ambil_llm()
    set_pengguna(pengguna)      # pencari membaca dokumen sebatas hak akses ini

    if konfig.MODE_TIRUAN or not hasattr(llm, "bind_tools"):
        print("  [Tim agent membutuhkan model dengan tool-calling — mode tiruan "
              "tidak mendukungnya.]")
        print("  [Menampilkan satu panggilan cari_kebijakan langsung sebagai gantinya.]\n")
        return cari_kebijakan.invoke({"pertanyaan": pertanyaan}), []

    tim = bangun_tim()
    awal = {"pesan": [HumanMessage(pertanyaan)], "berikutnya": "",
            "putaran": 0, "sudah": []}

    # stream_mode="updates" memberi kita {nama_simpul: perubahannya} — pas untuk
    # multi-agent, karena yang ingin dilihat justru SIAPA yang barusan bekerja.
    # (graf.py memakai "values" karena di sana yang menarik adalah isi pesannya.)
    akhir, jejak_langkah = "", []
    for langkah in tim.stream(awal, {"recursion_limit": 2 * MAKS_PUTARAN + 4},
                              stream_mode="updates"):
        for nama, perubahan in langkah.items():
            jejak_langkah.append(nama)
            if tampilkan_langkah:
                _cetak_langkah(nama, perubahan)
            if nama == "perangkum":
                akhir = perubahan["pesan"][-1].content

    return akhir.strip(), jejak_langkah


def _ringkas_jejak(jejak_langkah):
    """Ringkasan ongkos satu jalannya tim — bahan bukti peningkatan 7.

    Setiap simpul di sini berarti sekurang-kurangnya satu panggilan LLM
    (anggota spesialis bisa lebih, karena ia menjalankan lingkaran alatnya
    sendiri). Angka inilah yang harus dibandingkan sebelum dan sesudah anggota
    baru ditambahkan — multi-agent membeli kejelasan dengan ongkos, dan
    ongkosnya harus terlihat, bukan disembunyikan.
    """
    dipakai = [n for n in jejak_langkah if n in BEKAL_ANGGOTA]
    print("\n  jejak langkah tim:")
    print("    " + " -> ".join(jejak_langkah))
    print(f"    {len(jejak_langkah)} simpul dijalankan, "
          f"{sum(1 for n in jejak_langkah if n == 'penyelia')} putaran penyelia")
    print(f"    anggota yang bekerja : {', '.join(dipakai) or '(tidak ada)'}")
    belum = [n for n in BEKAL_ANGGOTA if n not in dipakai]
    if belum:
        print(f"    anggota yang menganggur: {', '.join(belum)}")


if __name__ == "__main__":
    argumen = sys.argv[1:]
    peran = util.ambil_bendera(argumen, "--peran", izin.PERAN_BAKU)
    tanya = " ".join(argumen) or \
        "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"

    orang = izin.bereskan({"peran": peran})
    print(f"Pertanyaan: {tanya}")
    print(f"Peran     : {orang['peran']}\n")
    jawaban, langkah_tim = jalankan_tim(tanya, pengguna=orang)
    print("\nJAWABAN TIM:")
    print(jawaban)
    if langkah_tim:
        _ringkas_jejak(langkah_tim)
