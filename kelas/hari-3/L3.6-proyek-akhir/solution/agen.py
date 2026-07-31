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

Tiga alat sengaja dipilih agar satu pertanyaan bisa membutuhkan LEBIH DARI SATU:
    cari_kebijakan  -> mengambil fakta dari dokumen (seluruh pipeline RAG)
    hitung          -> aritmetika sederhana yang aman
    hitung_tanggal  -> aritmetika hari kerja (peningkatan 6)

Pertanyaan "dinas 3 hari golongan Manajer, berapa totalnya?" memaksa agent
mencari besaran harian dulu (cari_kebijakan), lalu mengalikannya (hitung) —
demo dua langkah yang tidak bisa diselesaikan satu alat saja.

Pertanyaan "saya cuti 1 Juli 2026, paling lambat kapan mengajukannya?" memaksa
jalur yang berbeda: cari_kebijakan menemukan aturannya (7 hari kerja sebelum
pelaksanaan), lalu hitung_tanggal menerjemahkan aturan itu menjadi tanggal.

    python agen.py --peran pimpinan "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"
    python agen.py --peran staf     "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"
"""
import ast
import operator
import re
import sys
from datetime import date, timedelta

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

import izin
import konfig
import util
from cari import ambil_terbaik
from jawab import susun_jawaban
from model import ambil_llm


# ============================================================ pengguna aktif
# PENINGKATAN 5 + 6 — alat agent kini tunduk pada hak akses.
#
# Sebelumnya cari_kebijakan memanggil ambil_terbaik() tanpa penyaring izin sama
# sekali. Akibatnya: seluruh kerja izin.py bisa dilewati hanya dengan bertanya
# lewat agent alih-alih lewat tanya.py — persis pola "jalan pintas yang tidak
# melewati pagar" yang sudah diperagakan singgahan.py untuk cache.
#
# Peran disimpan di tingkat modul, bukan dititipkan sebagai argumen alat.
# Alasannya penting: apa pun yang menjadi ARGUMEN alat adalah sesuatu yang
# MODEL yang mengisinya — dan model tidak boleh bisa menaikkan hak aksesnya
# sendiri dengan menulis peran="pimpinan" di dalam panggilan alat.
_pengguna_aktif = izin.bereskan(None)


def set_pengguna(pengguna):
    """Tetapkan peran yang berlaku untuk seluruh panggilan alat berikutnya."""
    global _pengguna_aktif
    _pengguna_aktif = izin.bereskan(pengguna)
    return _pengguna_aktif


def pengguna_aktif():
    return _pengguna_aktif


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
    orang = pengguna_aktif()
    potongan = ambil_terbaik(pertanyaan, saring=izin.saring_untuk(orang))
    potongan = izin.saring_potongan(orang, potongan)   # pagar terakhir
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


# ============================================================ alat 3: tanggal
# PENINGKATAN 6 — alat baru.
#
# Kenapa alat, bukan prompt? Karena korpus penuh aturan berbentuk "paling
# lambat N hari kerja sebelum pelaksanaan", dan pertanyaan orang berbentuk
# "saya cuti tanggal sekian, paling lambat kapan mengajukannya?". Jarak antara
# keduanya adalah aritmetika kalender — hal yang dikerjakan model bahasa dengan
# buruk dan tidak konsisten, tetapi dikerjakan enam baris Python dengan benar
# setiap kali.
#
# Ini juga alasan umum menambah alat: bukan karena model tidak bisa mencoba,
# melainkan karena hasilnya harus BISA DIULANG. Jawaban tanggal yang berubah
# tiap kali pertanyaan yang sama diajukan tidak bisa dipakai siapa pun.
_BULAN = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11,
    "desember": 12,
}
_NAMA_HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

# Hari libur nasional sengaja DIBIARKAN KOSONG, dan ini keputusan sadar.
# Mengarang daftar tanggal merah akan membuat alat ini terlihat lebih pintar
# sambil diam-diam menjadi salah. Di sistem sungguhan daftar ini datang dari
# kalender resmi organisasi; di lab, alat hanya melewati Sabtu dan Minggu dan
# MENGATAKANNYA pada setiap keluaran.
HARI_LIBUR = set()


def _baca_tanggal(teks: str) -> date:
    """Terima '2026-07-01', '1 Juli 2026', atau '01/07/2026'."""
    teks = (teks or "").strip().lower()

    cocok = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", teks)
    if cocok:
        return date(*(int(x) for x in cocok.groups()))

    cocok = re.fullmatch(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", teks)
    if cocok and cocok.group(2) in _BULAN:
        return date(int(cocok.group(3)), _BULAN[cocok.group(2)], int(cocok.group(1)))

    cocok = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", teks)
    if cocok:
        return date(int(cocok.group(3)), int(cocok.group(2)), int(cocok.group(1)))

    raise ValueError(f"format tanggal tidak dikenali: {teks!r}")


def _geser_hari_kerja(mulai: date, jumlah: int) -> date:
    """Geser sejumlah HARI KERJA, melewati akhir pekan dan HARI_LIBUR."""
    arah = 1 if jumlah >= 0 else -1
    sisa, kini = abs(jumlah), mulai
    while sisa:
        kini += timedelta(days=arah)
        if kini.weekday() < 5 and kini not in HARI_LIBUR:
            sisa -= 1
    return kini


@tool
def hitung_tanggal(tanggal: str, jumlah_hari: int, jenis_hari: str = "kerja") -> str:
    """Hitung tanggal sekian hari sebelum atau sesudah suatu tanggal.

    Pakai untuk menerjemahkan aturan seperti 'paling lambat 7 hari kerja sebelum
    pelaksanaan' menjadi tanggal yang sebenarnya. Masukan: tanggal ('2026-07-01'
    atau '1 Juli 2026'), jumlah_hari (negatif untuk SEBELUM, positif untuk
    SESUDAH), dan jenis_hari ('kerja' untuk hari kerja, 'kalender' untuk hari
    biasa). Keluaran: tanggal hasil beserta nama harinya.
    """
    try:
        mulai = _baca_tanggal(tanggal)
    except ValueError as e:
        return f"Tanggal tidak bisa dibaca: {e}. Contoh yang benar: 2026-07-01."

    jenis = (jenis_hari or "kerja").strip().lower()
    if jenis.startswith("kal"):
        hasil = mulai + timedelta(days=int(jumlah_hari))
        keterangan = "hari kalender"
    else:
        hasil = _geser_hari_kerja(mulai, int(jumlah_hari))
        keterangan = "hari kerja (Sabtu, Minggu dilewati; hari libur nasional " \
                     "TIDAK diperhitungkan)"

    arah = "sesudah" if int(jumlah_hari) >= 0 else "sebelum"
    return (f"{hasil.isoformat()} ({_NAMA_HARI[hasil.weekday()]}), "
            f"yaitu {abs(int(jumlah_hari))} {keterangan} {arah} "
            f"{mulai.isoformat()}")


ALAT = [cari_kebijakan, hitung, hitung_tanggal]
PETA_ALAT = {a.name: a for a in ALAT}


# ============================================================ lingkaran agent
SISTEM = """Anda asisten internal PT Nusantara Cipta Solusi.

Anda memiliki tiga alat:
- cari_kebijakan(pertanyaan): mencari fakta di dokumen internal.
- hitung(ekspresi): menghitung aritmetika.
- hitung_tanggal(tanggal, jumlah_hari, jenis_hari): menghitung tanggal batas,
  misalnya 7 hari kerja sebelum sebuah tanggal (jumlah_hari = -7).

Aturan:
1. Untuk pertanyaan apa pun tentang aturan, besaran, atau ketentuan, SELALU
   panggil cari_kebijakan lebih dulu. Jangan menjawab dari ingatan.
2. Bila jawaban membutuhkan perhitungan (misalnya total beberapa hari),
   ambil angkanya dari cari_kebijakan lalu panggil hitung.
3. Bila jawaban membutuhkan tanggal (misalnya batas akhir pengajuan), ambil
   aturan jumlah harinya dari cari_kebijakan lalu panggil hitung_tanggal.
   Jangan menghitung tanggal di kepala Anda sendiri.
4. Bila cari_kebijakan menyatakan informasi tidak ditemukan, sampaikan itu apa
   adanya. Jangan mengarang.
5. Jawaban akhir singkat, dalam bahasa Indonesia."""


def jalankan_agen(pertanyaan, pengguna=None, maks_langkah=5,
                  tampilkan_langkah=True):
    """Jalankan lingkaran agent sampai model memberi jawaban akhir.

    Kembalikan teks jawaban akhir. Setiap panggilan alat dicetak agar peserta
    melihat 'jalan pikiran' agent — bagian terpenting dari demo ini.
    """
    llm = ambil_llm()
    orang = set_pengguna(pengguna)

    # PENINGKATAN 5 + 6 — alat disaring SEBELUM diikat ke model. Alat yang
    # tidak diberikan tidak muncul di daftar yang dilihat model, jadi ia tidak
    # bisa dipanggil sama sekali; bandingkan dengan menuliskan "jangan panggil
    # alat X" di prompt, yang hanya sebuah imbauan.
    alat_boleh = izin.saring_alat(orang, ALAT)
    if tampilkan_langkah:
        print(f"  [peran {orang['peran']}] alat: "
              f"{', '.join(a.name for a in alat_boleh) or '(tidak ada)'}")

    # Mode tiruan (dan model tanpa tool-calling) tidak bisa menjadi agent.
    # Daripada gagal, tunjukkan satu panggilan RAG langsung supaya alurnya tetap
    # terlihat — sejalan dengan filosofi mode tiruan di seluruh lab.
    if konfig.MODE_TIRUAN or not hasattr(llm, "bind_tools"):
        print("  [Agent membutuhkan model dengan tool-calling — mode tiruan tidak "
              "mendukungnya.]")
        print("  [Menampilkan satu panggilan cari_kebijakan langsung sebagai gantinya.]\n")
        return cari_kebijakan.invoke({"pertanyaan": pertanyaan})

    if not alat_boleh:
        return ("Peran ini tidak memiliki alat apa pun, jadi tidak ada yang bisa "
                "dikerjakan agent. Periksa ALAT_PER_PERAN di izin.py.")

    llm_beralat = llm.bind_tools(alat_boleh)
    pesan = [SystemMessage(SISTEM), HumanMessage(pertanyaan)]

    for langkah in range(1, maks_langkah + 1):
        balasan: AIMessage = llm_beralat.invoke(pesan)
        pesan.append(balasan)

        # Tidak ada panggilan alat -> model sudah siap menjawab.
        if not balasan.tool_calls:
            return (balasan.content or "").strip()

        for panggilan in balasan.tool_calls:
            nama = panggilan["name"]
            argumen = panggilan["args"]
            if tampilkan_langkah:
                print(f"  [langkah {langkah}] memanggil {nama}({argumen})")

            # Pagar kedua, di sisi PEMANGGIL. Alat yang tidak diikat memang
            # tidak terlihat model — tetapi nama alat bisa saja muncul dari
            # percakapan sebelumnya atau dari model yang berhalusinasi. Yang
            # menjalankan alat adalah kode kita, jadi di sinilah keputusannya
            # dipastikan sekali lagi.
            alat = PETA_ALAT.get(nama)
            if nama not in izin.alat_boleh(orang):
                hasil = f"Alat '{nama}' tidak tersedia untuk peran {orang['peran']}."
            elif alat is None:
                hasil = f"Alat '{nama}' tidak ada."
            else:
                hasil = str(alat.invoke(argumen))

            if tampilkan_langkah:
                cuplik = " ".join(hasil.split())[:110]
                print(f"             -> {cuplik}")

            pesan.append(ToolMessage(content=hasil, tool_call_id=panggilan["id"]))

    return ("(Batas langkah tercapai tanpa jawaban akhir. Sederhanakan pertanyaan, "
            "atau naikkan maks_langkah.)")


if __name__ == "__main__":
    argumen = sys.argv[1:]
    peran = util.ambil_bendera(argumen, "--peran", izin.PERAN_BAKU)
    tanya = " ".join(argumen) or \
        "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"

    orang = izin.bereskan({"peran": peran})
    print(f"Pertanyaan: {tanya}")
    print(f"Peran     : {orang['peran']}\n")
    jawaban = jalankan_agen(tanya, pengguna=orang)
    print("\nJAWABAN AGEN:")
    print(jawaban)
