# L3.5-graf-berkeadaan  -  Langkah Pasti, Langkah Model, dan Manusia di Tengah

**Hari 3 - AI Agents, Orchestration, dan Deployment**

> Tidak semua langkah perlu model. Yang bisa dipastikan, pastikan — sisanya
> baru serahkan ke model, dan sediakan tempat bagi manusia untuk menyela.

Di L3.3 seluruh simpul adalah panggilan model. Alur di sini sengaja dicampur,
dan pembagiannya adalah inti pelajarannya.

## Cara menjalankan

```bash
# 1. (sekali) buat & aktifkan venv, lalu:
pip install -r requirements.txt
python indeks.py            # bila chroma_db/ belum ada di folder ini

# 2. dua peran, alur yang sama
python alur.py --peran pimpinan "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"
python alur.py --peran staf     "Berapa nilai perkiraan pengadaan penyimpanan tambahan?"

# 3. tanpa menunggu ketikan (untuk demo di depan kelas)
python alur.py --otomatis tolak  "Apa saja tahapan pengadaan langsung?"
python alur.py --otomatis setuju "Apa saja tahapan pengadaan langsung?"
```

## Peta alur

```
START -> izin -> singgahan --kena--------------------------> catat -> END
                     |
                  meleset
                     v
                    cari --kosong--> tolak ----------------> catat -> END
                     |
                   ada isi
                     v
                   jawab -> periksa --bersih--------------> catat -> END
                                |
                            mencurigakan
                                v
                          persetujuan --disetujui---------> catat -> END
                                |
                            ditolak -> tolak -------------> catat -> END
```

| jenis | simpul | sifat |
|---|---|---|
| **pasti** | izin, singgahan, cari, periksa, tolak, catat | bisa diaudit, bisa diuji, nyaris gratis |
| **model** | jawab | mahal, tak bisa diulang persis, tak bisa dijamin |
| **manusia** | persetujuan | alur benar-benar berhenti |

## Yang harus terlihat

Setiap jalan mencetak jejak audit lengkap dengan **jenis** tiap langkah. Dari
jalan sungguhan saat lab ini disiapkan:

```
pasti    izin         {'peran': 'pimpinan', 'jenis_boleh': ['edaran', 'notulen', 'sop']}
pasti    singgahan    {'hasil': 'meleset'}
pasti    cari         {'jumlah': 4, 'dibuang_pagar_akhir': 0, 'sumber': [...]}
model    jawab        {'panjang': 18}
pasti    periksa      {'cakupan': 1.0, 'hantu': [], 'alasan': '-'}
pasti    catat        {'id_jejak': '7e356c7e70f9'}

5 langkah pasti, 1 langkah model.
JAWABAN: Rp 180.000.000 [1]
```

- **Lima banding satu.** Sebagian besar sistem RAG yang baik bukan model —
  melainkan cabang `if` biasa yang diletakkan di tempat yang tepat.
- Jalankan sebagai `staf`: `jenis_boleh` menyusut, notulen tak pernah terambil,
  dan jawabannya menjadi penolakan.
- Pada pertanyaan yang tak ada jawabannya, alur melompat `cari -> tolak` dan
  **model tidak dipanggil sama sekali** — nol detik, nol token, dan kalimat
  penolakannya persis sama setiap kali.

## Catatan

Isi dua TODO:

- **TODO L3.5-1** (`simpul_persetujuan`) — panggil `interrupt()` dengan berkas
  perkaranya. Sebelum dikerjakan, simpul ini menyetujui apa pun diam-diam.
- **TODO L3.5-2** (`arah_periksa`) — gerbang yang memutuskan apakah manusia
  perlu dilibatkan. Sebelum dikerjakan, tidak ada yang pernah dieskalasi:
  jawaban dengan sitasi hantu pun langsung dicatat sebagai final.

### Kenapa penolakan tidak dibuat oleh model?

Kalimat penolakan diambil dari `konfig.TIDAK_DITEMUKAN` — sumber yang sama
persis dengan yang dicocokkan `nilai.py`. Kalau penolakan dirangkai model,
kata-katanya bergeser sedikit setiap kali, dan metrik penolakan Anda diam-diam
melaporkan nol tanpa ada yang menyadarinya. Ini kegagalan senyap yang sudah
diperingatkan sejak `konfig.py` di Hari 1; di sini ia ditutup secara struktural.

### Jejak audit sebagai bagian dari keadaan

`langkah` adalah bidang di dalam `Keadaan`, memakai reducer `operator.add`.
Setiap simpul mengembalikan satu barisnya sendiri dan daftarnya tersambung
otomatis. Akibatnya jejak audit **mustahil tertinggal**: ia bukan log yang
ditempel di samping alur, melainkan sesuatu yang ikut mengalir bersamanya.
Bandingkan dengan `jejak.py` di L3.4 yang harus dipanggil dengan tertib di
setiap cabang — di sini ketertiban itu dijamin strukturnya.

### `interrupt()` bukan `input()`

Ini perbedaan yang paling sering disalahpahami:

| | `input()` di tengah fungsi | `interrupt()` |
|---|---|---|
| Proses harus tetap hidup | ya | **tidak** |
| Keadaan saat menunggu | hanya di RAM | disimpan checkpointer |
| Saat dilanjutkan | fungsi diulang dari awal | lanjut **dari simpul itu** |
| Cocok untuk web/antrean | tidak | ya |

Karena itu `jalankan()` memakai `while "__interrupt__" in hasil`, bukan `if` —
satu alur boleh berhenti lebih dari sekali. Di lab ini checkpointer-nya
`InMemorySaver` (hilang saat proses mati). Untuk sungguhan, ganti dengan
checkpointer yang menulis ke basis data; alur ini tidak perlu diubah.

### Yang sengaja TIDAK dieskalasi

Penolakan tidak pernah dikirim ke manusia. Sistem yang menjawab "tidak
ditemukan" sedang berperilaku **benar**, dan membanjiri penyelia dengan itu
hanya melatih mereka menekan "setuju" tanpa membaca. Persetujuan yang selalu
"ya" sama saja dengan tidak ada persetujuan — karena itu pula `interrupt()`
mengirimkan **alasan**, bukan hanya jawabannya.

Jawaban yang ditolak penyelia juga **tidak** disimpan ke singgahan. Menyimpannya
berarti menyebarkan satu jawaban meragukan ke semua penanya berikutnya tanpa
ada yang memeriksanya lagi.

### Batas yang jujur

- Ambang eskalasi (`konfig.AMBANG_CAKUPAN`) adalah angka yang dipilih, bukan
  ditemukan. Terlalu rendah: penyelia kebanjiran. Terlalu tinggi: jawaban buruk
  lolos. Ukur dengan `nilai.py` sebelum menetapkannya.
- Cakupan sitasi hanya memeriksa **struktur** — apakah kalimat punya penanda
  sumber. Ia tidak tahu apakah sumbernya benar-benar mendukung klaimnya. Lihat
  pembahasan halusinasi bersitasi di modul B5.

## Berkas yang Anda kerjakan (starter/)

- `alur.py` — seluruh alur; dua `# TODO` ada di dalamnya.

Berkas dari latihan sebelumnya yang dipakai apa adanya: `izin.py`,
`singgahan.py`, `jejak.py` (L3.4), `cari.py`, `jawab.py`, `konfig.py`.

## Struktur

- `starter/` - kerangka dengan `# TODO`; **kerjakan di sini**.
- `solution/` - acuan lengkap yang sudah jalan.
- Setiap folder mandiri: dokumen & set_uji sudah disertakan.
