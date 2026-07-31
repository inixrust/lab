# -*- coding: utf-8 -*-
"""Agent yang SAMA, ditulis ulang sebagai graph — modul A3 (orchestration).

    python graf.py "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
    python graf.py "Berapa panjang minimum kata sandi sistem internal?"

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

import konfig
from agen import ALAT, SISTEM, cari_kebijakan
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
_beralat = None


def _llm_beralat():
    """LLM yang sudah diikat ke daftar alat. Dibuat sekali, dipakai berulang."""
    global _beralat
    if _beralat is None:
        _beralat = ambil_llm().bind_tools(ALAT)
    return _beralat


def simpul_model(keadaan: Keadaan) -> dict:
    """Satu panggilan model. Padanan `llm_beralat.invoke(pesan)` di agen.py.

    Sebuah simpul hanyalah fungsi biasa: menerima keadaan, mengembalikan
    perubahannya. Tidak ada kelas khusus yang perlu diwarisi.
    """
    balasan = _llm_beralat().invoke([SystemMessage(SISTEM)] + keadaan["pesan"])
    return {"pesan": [balasan]}


def perlu_alat(keadaan: Keadaan) -> str:
    """Penentu arah: model meminta alat, atau sudah siap menjawab?

    Ini persis baris `if not balasan.tool_calls:` di agen.py, hanya dipindahkan
    keluar menjadi fungsi tersendiri supaya graph bisa memakainya sebagai
    penunjuk jalan. LangGraph menyediakan `tools_condition` yang melakukan hal
    yang sama; di sini ditulis manual agar terlihat isinya tidak ajaib.
    """
    terakhir = keadaan["pesan"][-1]
    return "alat" if getattr(terakhir, "tool_calls", None) else END


def bangun_graf():
    """Rakit dan kompilasi graph-nya."""
    alur = StateGraph(Keadaan)

    # TODO L3.3-1: Rakit graph-nya, lalu kembalikan alur.compile().
    #   1. alur.add_node("model", simpul_model)
    #   2. alur.add_node("alat", ToolNode(ALAT, messages_key="pesan"))
    #      -> ToolNode menjalankan semua tool_call dan mengembalikan
    #         ToolMessage-nya; ia menggantikan seluruh blok
    #         `for panggilan in balasan.tool_calls: ...` di agen.py.
    #      -> messages_key perlu disebut karena bawaan LangGraph adalah
    #         "messages", sedangkan Keadaan di atas memakai nama "pesan".
    #   3. alur.add_edge(START, "model")
    #   4. alur.add_conditional_edges("model", perlu_alat, {...})
    #      -> petakan "alat" ke simpul "alat", dan END ke END.
    #   5. alur.add_edge("alat", "model")
    #      -> SISI INILAH 'lingkaran'-nya. Di agen.py ia berwujud
    #         `for langkah in range(...)`. Coba hapus sisi ini setelah jadi:
    #         agent akan berhenti sesudah satu alat, dan pertanyaan dua langkah
    #         gagal dijawab. Itu memperlihatkan apa yang sebenarnya dikerjakan
    #         lingkaran tersebut.
    return None


# ============================================================ menjalankan
def _cetak_langkah(pesan):
    """Cetak satu langkah agar 'jalan pikiran' agent tetap terlihat."""
    if isinstance(pesan, AIMessage):
        for panggilan in pesan.tool_calls:
            print(f"  [model] minta {panggilan['name']}({panggilan['args']})")
    elif isinstance(pesan, ToolMessage):
        cuplik = " ".join(str(pesan.content).split())[:104]
        print(f"  [alat ] {pesan.name} -> {cuplik}")


def jalankan_graf(pertanyaan, maks_langkah=5, tampilkan_langkah=True):
    """Jalankan graph sampai selesai, kembalikan teks jawaban akhir."""
    llm = ambil_llm()

    # Sama seperti agen.py: tanpa tool-calling, tidak ada yang bisa diputuskan
    # model. Tunjukkan satu panggilan RAG langsung supaya alurnya tetap terlihat.
    if konfig.MODE_TIRUAN or not hasattr(llm, "bind_tools"):
        print("  [Graph agent membutuhkan model dengan tool-calling — mode tiruan "
              "tidak mendukungnya.]")
        print("  [Menampilkan satu panggilan cari_kebijakan langsung sebagai gantinya.]\n")
        return cari_kebijakan.invoke({"pertanyaan": pertanyaan})

    graf = bangun_graf()

    # Selama TODO L3.3-1 belum dikerjakan, graph-nya belum ada. Jangan gagal
    # dengan galat yang membingungkan — katakan apa yang kurang.
    if graf is None:
        print("  [Graph belum dirakit — kerjakan TODO L3.3-1 di bangun_graf().]")
        print("  [Sementara ini satu panggilan cari_kebijakan ditampilkan.]\n")
        return cari_kebijakan.invoke({"pertanyaan": pertanyaan})

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
    tanya = " ".join(sys.argv[1:]) or \
        "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
    print(f"Pertanyaan: {tanya}\n")
    jawaban = jalankan_graf(tanya)
    print("\nJAWABAN GRAPH AGENT:")
    print(jawaban)
