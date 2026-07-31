# -*- coding: utf-8 -*-
"""Agent yang SAMA, ditulis ulang sebagai graph — modul A3 (orchestration).

    python graf.py "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
    python graf.py "Berapa panjang minimum kata sandi sistem internal?"
    python graf.py --peran keuangan "Berapa nilai kontrak sewa pusat data?"

Bukalah berkas ini bersebelahan dengan agen.py. Alat, prompt sistem, dan
modelnya PERSIS SAMA — sengaja diimpor dari agen.py, bukan disalin. Yang berubah
hanya cara alurnya dinyatakan:

    agen.py   ->  lingkaran `for` yang KITA tulis sendiri: panggil model, periksa
                  tool_calls, jalankan alatnya, sisipkan ToolMessage, ulangi.
    graf.py   ->  alurnya DIGAMBAR sebagai simpul (node) dan sisi (edge), lalu
                  LangGraph yang menjalankan lingkarannya.

            START -> model -> (ada tool_calls?) -> alat -+
                       ^                                 |
                       +---------------------------------+
                                   |
                              (tidak) -> END

Kenapa repot-repot? Untuk dua alat, lingkaran manual di agen.py justru lebih
pendek dan lebih jelas — itu jawaban jujurnya, dan jangan disembunyikan dari
peserta. Graph baru membayar ketika:
  - ada lebih dari satu agent yang harus bergantian (lihat tim.py),
  - Anda perlu melihat atau merekam tiap langkah (di sini: .stream()),
  - Anda perlu menyisipkan persetujuan manusia di tengah, atau mengulang dari
    satu simpul tanpa menjalankan ulang semuanya.

Pelajarannya bukan "graph lebih baik", melainkan: lingkaran agent itu POLA yang
berulang, dan begitu polanya dikenali, ia bisa dinyatakan sebagai data (simpul
dan sisi) alih-alih sebagai kode.
"""
import sys
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

import izin
import konfig
import util
from agen import ALAT, SISTEM, cari_kebijakan, set_pengguna
from model import ambil_llm


# ============================================================ keadaan (state)
class Keadaan(TypedDict):
    """Data yang mengalir lewat graph.

    `add_messages` adalah sebuah REDUCER: ketika sebuah simpul mengembalikan
    {"pesan": [...]}, isinya DITAMBAHKAN ke daftar yang sudah ada, bukan
    menimpanya. Inilah padanan `pesan.append(...)` di agen.py — bedanya, di sini
    penambahan itu menjadi aturan graph, bukan baris kode yang harus diingat
    di setiap cabang.

    Nama kunci "pesan" dipakai agar seragam dengan berkas lain di lab ini.
    Bawaan LangGraph adalah "messages"; karena itu ToolNode di bawah perlu
    diberi tahu lewat messages_key.
    """
    pesan: Annotated[list, add_messages]


# ============================================================ simpul (node)
_beralat = {}


def _llm_beralat(peran):
    """LLM yang sudah diikat ke daftar alat peran ini. Dibuat sekali per peran.

    PENINGKATAN 5 + 6 — cache-nya dikunci PER PERAN, bukan satu objek untuk
    semua. Satu objek bersama akan membuat peran yang dijalankan lebih dulu
    menentukan daftar alat bagi semua peran sesudahnya dalam proses yang sama:
    kebocoran yang tak akan pernah terlihat pada pengujian satu peran saja.
    """
    if peran not in _beralat:
        alat = izin.saring_alat({"peran": peran}, ALAT)
        _beralat[peran] = ambil_llm().bind_tools(alat)
    return _beralat[peran]


def buat_simpul_model(peran):
    """Buat simpul model untuk satu peran.

    Simpul tetap fungsi biasa: menerima keadaan, mengembalikan perubahannya.
    Yang berubah, peran-nya ditutup (closure) di dalam fungsi ini alih-alih
    dibaca dari keadaan. Sengaja: apa pun yang berada di dalam keadaan bisa
    berubah di tengah jalan oleh simpul lain — dan hak akses bukan sesuatu yang
    boleh berubah di tengah jalan.
    """
    def simpul_model(keadaan: Keadaan) -> dict:
        balasan = _llm_beralat(peran).invoke(
            [SystemMessage(SISTEM)] + keadaan["pesan"])
        return {"pesan": [balasan]}

    return simpul_model


def perlu_alat(keadaan: Keadaan) -> str:
    """Penentu arah: model meminta alat, atau sudah siap menjawab?

    Ini persis baris `if not balasan.tool_calls:` di agen.py, hanya dipindahkan
    keluar menjadi fungsi tersendiri supaya graph bisa memakainya sebagai
    penunjuk jalan. LangGraph menyediakan `tools_condition` yang melakukan hal
    yang sama; di sini ditulis manual agar terlihat isinya tidak ajaib.
    """
    terakhir = keadaan["pesan"][-1]
    return "alat" if getattr(terakhir, "tool_calls", None) else END


def bangun_graf(peran=None):
    """Rakit dan kompilasi graph-nya untuk satu peran."""
    peran = peran or izin.PERAN_BAKU
    alur = StateGraph(Keadaan)

    alur.add_node("model", buat_simpul_model(peran))

    # ToolNode menjalankan SETIAP tool_call pada pesan terakhir dan
    # mengembalikan ToolMessage-nya. Satu baris ini menggantikan seluruh blok
    # `for panggilan in balasan.tool_calls: ...` di agen.py, termasuk
    # penanganan alat yang namanya tidak dikenal.
    #
    # Daftar alatnya disaring peran, sama seperti yang diikat ke model. Dua
    # tempat, satu sumber (izin.saring_alat): mengikat alat yang lebih sedikit
    # daripada yang dijalankan ToolNode akan menyisakan celah persis sebesar
    # selisihnya.
    alur.add_node("alat", ToolNode(izin.saring_alat({"peran": peran}, ALAT),
                                   messages_key="pesan"))

    alur.add_edge(START, "model")
    alur.add_conditional_edges("model", perlu_alat, {"alat": "alat", END: END})

    # Sisi inilah 'lingkaran'-nya: hasil alat selalu kembali ke model.
    # Di agen.py, lingkaran ini adalah `for langkah in range(...)`.
    alur.add_edge("alat", "model")

    return alur.compile()


# ============================================================ menjalankan
def _cetak_langkah(pesan):
    """Cetak satu langkah agar 'jalan pikiran' agent tetap terlihat."""
    if isinstance(pesan, AIMessage):
        for panggilan in pesan.tool_calls:
            print(f"  [model] minta {panggilan['name']}({panggilan['args']})")
    elif isinstance(pesan, ToolMessage):
        cuplik = " ".join(str(pesan.content).split())[:104]
        print(f"  [alat ] {pesan.name} -> {cuplik}")


def jalankan_graf(pertanyaan, pengguna=None, maks_langkah=5,
                  tampilkan_langkah=True):
    """Jalankan graph sampai selesai, kembalikan teks jawaban akhir."""
    llm = ambil_llm()

    # Peran ditetapkan SEBELUM graph dibangun: ia menentukan alat yang diikat
    # ke model, alat yang dijalankan ToolNode, dan penyaring di dalam
    # cari_kebijakan.
    orang = set_pengguna(pengguna)

    # Sama seperti agen.py: tanpa tool-calling, tidak ada yang bisa diputuskan
    # model. Tunjukkan satu panggilan RAG langsung supaya alurnya tetap terlihat.
    if konfig.MODE_TIRUAN or not hasattr(llm, "bind_tools"):
        print("  [Graph agent membutuhkan model dengan tool-calling — mode tiruan "
              "tidak mendukungnya.]")
        print("  [Menampilkan satu panggilan cari_kebijakan langsung sebagai gantinya.]\n")
        return cari_kebijakan.invoke({"pertanyaan": pertanyaan})

    if tampilkan_langkah:
        print(f"  [peran {orang['peran']}] alat: "
              f"{', '.join(sorted(izin.alat_boleh(orang))) or '(tidak ada)'}")

    graf = bangun_graf(orang["peran"])

    # .stream() memberi kita SETIAP keadaan setelah tiap simpul selesai.
    # Di agen.py, keterlihatan ini harus dibuat sendiri dengan print di tempat
    # yang tepat; di graph ia gratis — dan inilah yang dipakai antarmuka
    # sungguhan untuk menampilkan "sedang mencari dokumen ..." selagi berjalan.
    #
    # recursion_limit dihitung dalam SIMPUL, bukan langkah agent. Satu langkah
    # agent = 2 simpul (model + alat), ditambah satu simpul model penutup.
    batas = {"recursion_limit": maks_langkah * 2 + 1}
    akhir = None

    try:
        for potret in graf.stream({"pesan": [HumanMessage(pertanyaan)]}, batas,
                                  stream_mode="values"):
            if not potret["pesan"]:
                continue
            akhir = potret["pesan"][-1]
            if tampilkan_langkah:
                _cetak_langkah(akhir)
    except GraphRecursionError:
        return ("(Batas langkah tercapai tanpa jawaban akhir. Sederhanakan "
                "pertanyaan, atau naikkan maks_langkah.)")

    return (getattr(akhir, "content", "") or "").strip()


if __name__ == "__main__":
    argumen = sys.argv[1:]
    peran = util.ambil_bendera(argumen, "--peran", izin.PERAN_BAKU)
    tanya = " ".join(argumen) or \
        "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"

    orang = izin.bereskan({"peran": peran})
    print(f"Pertanyaan: {tanya}")
    print(f"Peran     : {orang['peran']}\n")
    jawaban = jalankan_graf(tanya, pengguna=orang)
    print("\nJAWABAN GRAPH AGENT:")
    print(jawaban)
