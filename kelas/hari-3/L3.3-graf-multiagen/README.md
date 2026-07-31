# L3.3-graf-multiagen  -  Dari Lingkaran Tulisan Tangan ke Graph & Tim Agent

**Hari 3 - AI Agents, Orchestration, dan Deployment**

> Lingkaran agent di L3.1 adalah sebuah POLA. Begitu polanya dikenali, ia bisa
> dinyatakan sebagai graph — dan graph itulah yang memungkinkan beberapa agent
> bekerja sebagai tim.

Agent di L3.1 sudah berjalan dan antarmukanya sudah jadi di L3.2. Di sini kita
tidak menambah kemampuan baru, melainkan mengganti **cara alurnya dinyatakan** —
lalu memakai cara baru itu untuk hal yang sulit dilakukan dengan lingkaran
biasa: beberapa agent yang bergantian.

## Cara menjalankan

```bash
# 1. (sekali) buat & aktifkan venv, lalu:
pip install -r requirements.txt
python indeks.py            # bila chroma_db/ belum ada di folder ini

# 2. tiga cara menjawab pertanyaan yang SAMA - jalankan berurutan
python agen.py "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
python graf.py "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
python tim.py  "Saya dinas 3 hari golongan Manajer, berapa total uang hariannya?"
```

Jalankan ketiganya pada pertanyaan yang sama. Itu inti latihan ini: hasilnya
mirip, yang berbeda adalah bagaimana alurnya disusun dan apa yang bisa Anda
lihat saat berjalan.

## Yang harus terlihat

- `agen.py` dan `graf.py` memberi jawaban yang setara — alat, prompt, dan
  modelnya memang sama persis (`graf.py` mengimpornya dari `agen.py`).
- `graf.py` mencetak tiap simpul yang selesai (`[model]` lalu `[alat ]`) tanpa
  satu pun `print` di dalam lingkaran — keterlihatan itu datang dari `.stream()`.
- `tim.py` mencetak keputusan penyelia tiap putaran:
  `[penyelia] giliran -> pencari`, lalu `-> penghitung`, lalu `-> selesai`.
- `tim.py` lebih lambat dan memakai lebih banyak panggilan LLM daripada
  `agen.py` untuk pertanyaan yang sama. **Itu bukan bug** — lihat catatan.
- Sesekali penyelia menunjuk ulang anggota yang baru saja melapor. Yang
  menghentikannya bukan prompt, melainkan **koreksi pasti di kode**
  (`if pilihan in sudah: pilihan = "selesai"`). Ini teramati sungguhan saat
  lab ini diuji dengan qwen3:4b: tanpa koreksi itu, tim berputar sampai
  `MAKS_PUTARAN` lalu mengembalikan jawaban kosong.

## Catatan

Isi dua TODO:

- **TODO L3.3-1** (`graf.py`) — rakit graph-nya: `add_node`, `add_edge`,
  `add_conditional_edges`. Sisi `alat -> model` adalah lingkaran yang di
  `agen.py` berwujud `for langkah in range(...)`. Setelah jadi, **coba hapus
  sisi itu**: agent berhenti sesudah satu alat dan pertanyaan dua langkah gagal.
  Itu memperlihatkan apa yang sebenarnya dikerjakan lingkaran tersebut.
- **TODO L3.3-2** (`tim.py`) — buat penyelia benar-benar memilih giliran.
  Sebelum dikerjakan, penyelia selalu menjawab "selesai": tim melompat ke
  perangkum tanpa ada anggota yang bekerja, dan jawabannya keluar tanpa sumber.
  Jalankan dulu apa adanya untuk melihat apa yang hilang tanpa pengatur giliran.

### Kenapa repot memakai graph?

Jawaban jujurnya: **untuk dua alat, lingkaran manual di `agen.py` lebih pendek
dan lebih jelas.** Jangan pakai graph hanya karena namanya modern. Graph mulai
membayar ketika:

| Kebutuhan | Lingkaran manual | Graph |
|---|---|---|
| 2 alat, satu agent | lebih ringkas — **pakai ini** | berlebihan |
| Melihat tiap langkah berjalan | `print` disisipkan sendiri | `.stream()` |
| Beberapa agent bergantian | cepat kusut | satu percabangan |
| Persetujuan manusia di tengah | sulit | `interrupt_before` |
| Ulang dari satu simpul saja | jalankan ulang semua | checkpointer |

### Kenapa memecah jadi beberapa agent?

Juga bukan demi kecepatan — `tim.py` justru **lebih lambat dan lebih boros
token** daripada `agen.py` untuk soal yang sama, karena tiap putaran penyelia
menambah satu panggilan LLM. Alasan yang sebenarnya:

- tiap anggota punya prompt dan daftar alat yang sempit, jadi lebih sulit
  tersesat — prompt `pencari` tidak perlu menjelaskan aturan aritmetika;
- alat berisiko bisa dikurung di satu anggota yang punya aturannya sendiri
  (guardrail modul A4) — bayangkan anggota ketiga `pengirim-email`;
- anggota baru bisa ditambah tanpa menyentuh prompt anggota lama.

Kelemahannya nyata: penyelia bisa salah menunjuk dan tim berputar tanpa
kemajuan. Karena itu ada `MAKS_PUTARAN` di `tim.py`. **Aturan praktisnya:**
selama satu agent dengan tiga alat masih terbaca jelas, pakai satu agent.

### Bila jawabannya lama keluar

`tim.py` melakukan beberapa panggilan LLM berurutan. Di laptop tanpa GPU,
qwen3:8b bisa memakan beberapa menit. Yang bisa dilakukan:

```bash
MODEL_CHAT=qwen3:4b PAKAI_RERANKER=0 python tim.py "..."
```

(Cara menyetel variabel per-terminal ada di PANDUAN-PESERTA.md.) `MODE_TIRUAN=1`
**tidak** bisa dipakai di latihan ini — agent menuntut model dengan tool-calling,
dan mode tiruan tidak memilikinya. Ketiga berkas akan mengatakan demikian lalu
menampilkan satu panggilan RAG biasa sebagai gantinya.

## Berkas yang Anda kerjakan (starter/)

Cari komentar `# TODO` pada berkas berikut, lengkapi, lalu bandingkan dengan
`solution/`:

- `graf.py` — agent L3.1 ditulis ulang sebagai `StateGraph` + `ToolNode`
- `tim.py` — penyelia + dua agent spesialis (pencari, penghitung)

`agen.py` sengaja **tidak diubah**. Biarkan ia apa adanya sebagai pembanding —
seluruh latihan ini bertumpu pada perbandingan itu.

## Struktur

- `starter/` - kerangka dengan `# TODO`; **kerjakan di sini**.
- `solution/` - acuan lengkap yang sudah jalan.
- Setiap folder mandiri: dokumen & set_uji sudah disertakan.
