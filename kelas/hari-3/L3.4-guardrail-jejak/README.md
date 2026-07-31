# L3.4-guardrail-jejak  -  Hak Akses, Cache yang Tidak Bocor, dan Jejak

**Hari 3 - AI Agents, Orchestration, dan Deployment**

> Tiga hal yang selalu dituntut sistem sungguhan dan tidak pernah ada di demo:
> siapa boleh melihat apa, jawaban dipakai ulang tanpa bocor, dan bukti apa
> yang terjadi tadi sore.

Sampai L3.3, sistem ini melayani satu pengguna khayalan yang boleh membaca
segalanya. Latihan ini memasang tiga hal yang membuatnya bisa dipakai orang
sungguhan — dan memperlihatkan bahwa yang ketiga (cache) bisa membatalkan yang
pertama (izin) bila dipasang sembarangan.

## Cara menjalankan

```bash
# 1. (sekali) buat & aktifkan venv, lalu:
pip install -r requirements.txt
python indeks.py            # bila chroma_db/ belum ada di folder ini

# 2. peta hak akses, dan peragaan kebocoran cache (keduanya TANPA Ollama)
python izin.py
python singgahan.py

# 3. pertanyaan yang sama, dua peran
python tanya.py --bandingkan "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"

# 4. lihat jejaknya
python jejak.py
python jejak.py --akhir 3
```

## Yang harus terlihat

Pertanyaan uji di atas jawabannya **hanya ada di notulen rapat**
(Rp 180.000.000). Karena itu ia memisahkan kedua peran dengan bersih:

| peran | potongan yang terambil | jawaban |
|---|---|---|
| `staf` | hanya SOP & edaran | *"Informasi ini tidak ditemukan..."* |
| `pimpinan` | termasuk NR-04 (notulen) | `Rp 180.000.000 [1]` |

Angka ini dari jalan sungguhan saat lab disiapkan, bukan perkiraan.

- `python singgahan.py` mencetak dua kolom. Yang kiri (kunci tanpa hak akses)
  memberikan isi notulen kepada staf. Yang kanan meleset — dan meleset di sini
  **berarti aman**, karena pencarian jadi benar-benar dijalankan lengkap dengan
  penyaringnya.
- `python jejak.py` menampilkan p50/p95, rasio cache, rasio penolakan, dan
  rata-rata tiap langkah. Pada mesin uji, `jawab` memakan ~11.700 ms sementara
  `izin` dan `periksa` 0 ms — jadi jelas di mana waktunya habis, dan jelas pula
  bahwa guardrail itu **gratis**.

## Catatan

Isi tiga TODO:

- **TODO L3.4-1** (`izin.py`) — `saring_untuk()` dan `boleh_lihat()`. Sebelum
  dikerjakan, kedua peran sama-sama menerima Rp 180.000.000. Jalankan dulu apa
  adanya supaya Anda melihat keadaan yang sedang diperbaiki.
- **TODO L3.4-2** (`singgahan.py`) — satu baris: hak akses masuk ke kunci cache.
- **TODO L3.4-3** (`jejak.py`) — `langkah()` sebagai context manager dengan
  `try/finally`, supaya langkah yang **gagal** pun tetap tercatat durasinya.

### Kenapa di kode, bukan di prompt?

Ini kelanjutan langsung satu kalimat yang sudah ada di `cari.py` sejak Hari 2:
*aturan yang benar-benar tidak boleh dilanggar ditegakkan di kode.* Prompt
adalah imbauan, bukan pagar:

- potongan rahasianya sudah terlanjur masuk konteks model — kebocoran tinggal
  menunggu satu kalimat bujukan yang tepat;
- ia juga sudah terlanjur masuk ke cache, ke log, dan ke jejak;
- dan tidak ada yang bisa ditunjukkan ke auditor selain *"modelnya kami minta
  baik-baik."*

Penyaring di kode memutus semuanya di hulu: yang tidak boleh dilihat tidak
pernah terambil.

### Kebocoran datang dari jalan pintas, bukan dari pagar yang jebol

Bagian terpenting latihan ini. Pada peragaan `singgahan.py`, `izin.py` **tidak
rusak sedikit pun** — ia hanya *dilewati*, karena cache menjawab sebelum
pencarian dijalankan. Pola ini berulang di sistem sungguhan: setiap jalan
pintas yang dibangun belakangan (cache, ringkasan, ekspor, "mode cepat") harus
diperiksa apakah ia juga melewati pagarnya.

Karena itu ada **dua** lapis di `tanya.py`: penyaring di hulu sebelum
pencarian, dan `izin.saring_potongan()` sebagai pagar terakhir. Lapis kedua
seharusnya tidak pernah membuang apa pun — dan justru itu gunanya. Kalau
angkanya pernah bukan nol, ada jalur pengambilan yang lolos, dan Anda ingin
tahu hari itu juga.

### Yang sengaja TIDAK dicatat di jejak

Isi potongan dan teks jawaban tidak ikut ditulis ke `jejak.jsonl` — hanya nama
sumber, halaman, dan angka. Jejak berumur jauh lebih panjang daripada
jawabannya dan sering dikirim ke sistem pemantauan yang aturan aksesnya
berbeda. Mencatat isi dokumen di sana membatalkan seluruh kerja `izin.py` —
persis jalan pintas yang baru saja kita tutup.

### Batas yang jujur

- Kunci cache berbasis teks hanya menangkap pengulangan **persis**. "Berapa
  lama masa percobaan" dan "masa percobaan berapa lama" dianggap dua
  pertanyaan berbeda.
- Peta peran ditulis di `izin.py`. Di sistem sungguhan ia datang dari LDAP/SSO.
  Yang tidak berubah: keputusannya tetap diambil di kode, sebelum pencarian.
- Peran yang tidak dikenal **diturunkan** ke peran paling sempit, bukan
  ditolak. Sistem izin harus gagal ke arah aman.

## Berkas yang Anda kerjakan (starter/)

Cari komentar `# TODO` pada berkas berikut, lengkapi, lalu bandingkan dengan
`solution/`:

- `izin.py` — peta peran, penyaring, pagar terakhir, sidik hak akses
- `singgahan.py` — cache LRU yang dikunci per hak akses
- `jejak.py` — pencatatan per langkah + ringkasan

Berkas pendukung yang **sudah** lengkap dan layak dibaca:

- `tanya.py` — merangkai izin -> singgahan -> cari -> jawab -> periksa
- `cari.py` — `_untuk_chroma()` kini menerjemahkan penyaring ke sintaks Chroma
  (`$and` / `$in`). Chroma menolak dict dua kunci dengan pesan
  *"Expected where to have exactly one operator"* — aturan tak tertulis yang
  baru ketahuan saat dijalankan, dan pernah menjatuhkan lab ini.

## Struktur

- `starter/` - kerangka dengan `# TODO`; **kerjakan di sini**.
- `solution/` - acuan lengkap yang sudah jalan.
- Setiap folder mandiri: dokumen & set_uji sudah disertakan.
