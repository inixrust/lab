# -*- coding: utf-8 -*-
"""Agent minimal, sepenuhnya on-premise — modul A2 / A6.

    python agen.py "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
    python agen.py "Berapa panjang minimum kata sandi sistem internal?"

Inti pelajaran: sebuah agent pada dasarnya hanyalah SEBUAH LINGKARAN.

    1. Model diberi daftar alat (tool) dan sebuah pertanyaan.
    2. Model memutuskan: memanggil sebuah alat, atau menjawab langsung.
    3. Kalau memanggil alat, KITA yang menjalankannya, lalu hasilnya
       dikembalikan ke model.
    4. Ulangi sampai model berhenti memanggil alat dan memberi jawaban akhir.

Bandingkan dengan jawab.py: di sana alurnya TETAP (retrieve -> generate). Di sini
MODEL yang memilih langkahnya sendiri, dan bisa menggabungkan beberapa alat.
Itulah yang membuatnya 'agentic'.

Semua tetap lokal: qwen3 lewat Ollama melakukan tool-calling. Tidak ada API luar,
sesuai syarat kelas — semuanya masih jalan tanpa internet.

Dua alat sengaja dipilih agar satu pertanyaan bisa membutuhkan KEDUANYA:
    cari_kebijakan  -> mengambil fakta dari dokumen (seluruh pipeline RAG)
    hitung          -> aritmetika sederhana yang aman

Pertanyaan "dinas 3 hari golongan Manajer, berapa totalnya?" memaksa agent
mencari besaran harian dulu (cari_kebijakan), lalu mengalikannya (hitung) —
demo dua langkah yang tidak bisa diselesaikan satu alat saja.
"""
import ast
import operator
import sys

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

import konfig
from cari import ambil_terbaik
from jawab import susun_jawaban
from model import ambil_llm


# ============================================================ alat 1: RAG
# LLM tanpa alat, khusus untuk merangkai jawaban di DALAM alat cari_kebijakan.
# Harus terpisah dari LLM agent — kalau alat memanggil LLM ber-alat lagi, ia
# bisa mencoba memanggil alat di dalam alat (rekursi yang membingungkan).
_llm_polos = None


def _polos():
    global _llm_polos
    if _llm_polos is None:
        _llm_polos = ambil_llm()
    return _llm_polos


@tool
def cari_kebijakan(pertanyaan: str) -> str:
    """Cari jawaban dari dokumen internal perusahaan (SOP, surat edaran, notulen).

    Gunakan untuk semua pertanyaan tentang aturan, prosedur, besaran, batas nilai,
    kewenangan, atau ketentuan apa pun. Jangan menebak dari ingatan — selalu
    lewat alat ini. Masukan: pertanyaan dalam bahasa Indonesia. Keluaran: jawaban
    ber-sitasi dari dokumen, atau pernyataan bahwa informasinya tidak ditemukan.
    """
    potongan = ambil_terbaik(pertanyaan)
    if not potongan:
        return konfig.TIDAK_DITEMUKAN
    return susun_jawaban(_polos(), pertanyaan, potongan)


# ============================================================ alat 2: kalkulator
# Sengaja TIDAK memakai eval(). eval() akan menjalankan kode Python apa pun —
# termasuk yang berbahaya bila ekspresinya datang dari sumber tak tepercaya.
# Di sini hanya operator aritmetika yang di-whitelist. Ini contoh nyata prinsip
# guardrail modul A4: batasi kemampuan alat sampai sebatas yang benar diperlukan.
_OPERATOR = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _hitung_aman(simpul):
    if isinstance(simpul, ast.Constant) and isinstance(simpul.value, (int, float)):
        return simpul.value
    if isinstance(simpul, ast.BinOp) and type(simpul.op) in _OPERATOR:
        return _OPERATOR[type(simpul.op)](_hitung_aman(simpul.left),
                                          _hitung_aman(simpul.right))
    if isinstance(simpul, ast.UnaryOp) and type(simpul.op) in _OPERATOR:
        return _OPERATOR[type(simpul.op)](_hitung_aman(simpul.operand))
    raise ValueError("hanya angka dan operator + - * / % ** yang diizinkan")


@tool
def hitung(ekspresi: str) -> str:
    """Hitung ekspresi aritmetika, misalnya '500000 * 3' atau '(2 + 3) * 4'.

    Hanya menerima angka dan operator + - * / % ( ). Tidak menjalankan kode lain.
    Gunakan untuk mengalikan, menjumlahkan, atau menghitung total dari angka yang
    Anda peroleh dari cari_kebijakan.
    """
    try:
        return str(_hitung_aman(ast.parse(ekspresi, mode="eval").body))
    except Exception:
        return f"Ekspresi tidak bisa dihitung: {ekspresi!r}"


ALAT = [cari_kebijakan, hitung]
PETA_ALAT = {a.name: a for a in ALAT}


# ============================================================ lingkaran agent
SISTEM = """Anda asisten internal PT Nusantara Cipta Solusi.

Anda memiliki dua alat:
- cari_kebijakan(pertanyaan): mencari fakta di dokumen internal.
- hitung(ekspresi): menghitung aritmetika.

Aturan:
1. Untuk pertanyaan apa pun tentang aturan, besaran, atau ketentuan, SELALU
   panggil cari_kebijakan lebih dulu. Jangan menjawab dari ingatan.
2. Bila jawaban membutuhkan perhitungan (misalnya total beberapa hari),
   ambil angkanya dari cari_kebijakan lalu panggil hitung.
3. Bila cari_kebijakan menyatakan informasi tidak ditemukan, sampaikan itu apa
   adanya. Jangan mengarang.
4. Jawaban akhir singkat, dalam bahasa Indonesia."""


def jalankan_agen(pertanyaan, maks_langkah=5, tampilkan_langkah=True):
    """Jalankan lingkaran agent sampai model memberi jawaban akhir.

    Kembalikan teks jawaban akhir. Setiap panggilan alat dicetak agar peserta
    melihat 'jalan pikiran' agent — bagian terpenting dari demo ini.
    """
    llm = ambil_llm()

    # Mode tiruan (dan model tanpa tool-calling) tidak bisa menjadi agent.
    # Daripada gagal, tunjukkan satu panggilan RAG langsung supaya alurnya tetap
    # terlihat — sejalan dengan filosofi mode tiruan di seluruh lab.
    if konfig.MODE_TIRUAN or not hasattr(llm, "bind_tools"):
        print("  [Agent membutuhkan model dengan tool-calling — mode tiruan tidak "
              "mendukungnya.]")
        print("  [Menampilkan satu panggilan cari_kebijakan langsung sebagai gantinya.]\n")
        return cari_kebijakan.invoke({"pertanyaan": pertanyaan})

    # TODO L3.1-1: Lingkaran agent: ikat alat ke model (bind_tools), lalu ulangi — minta model, jika ada tool_calls JALANKAN alatnya dan kembalikan hasil sebagai ToolMessage, jika tidak kembalikan jawaban akhir. Batasi maks_langkah.
    return cari_kebijakan.invoke({"pertanyaan": pertanyaan})


if __name__ == "__main__":
    tanya = " ".join(sys.argv[1:]) or \
        "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
    print(f"Pertanyaan: {tanya}\n")
    jawaban = jalankan_agen(tanya)
    print("\nJAWABAN AGEN:")
    print(jawaban)
