# Deployment on-premise dengan Docker — modul A5

Aplikasi `app.py` dibungkus menjadi satu container. **Ollama tetap berjalan di
host**, bukan di dalam container — supaya model tidak perlu diunduh ulang dan
GPU host bisa dipakai. Container menjangkau Ollama lewat `OLLAMA_BASE_URL`.

Ini penting untuk konteks kelas: semuanya tetap on-premise. Tidak ada dokumen
atau pertanyaan yang keluar dari mesin sendiri — hanya lalu lintas lokal antara
container dan Ollama di host.

---

## Prasyarat

- Docker Desktop (Windows/Mac) atau Docker Engine (Linux).
- Ollama berjalan di host, dengan model sudah ditarik:
  ```bash
  ollama pull bge-m3
  ollama pull qwen3:8b
  ```

## Bangun image

```bash
cd lab
docker build -t tanya-sop .
```

## Jalankan

**Windows / macOS (Docker Desktop):**

```bash
docker run --rm -p 127.0.0.1:8501:8501 tanya-sop
```

**Linux** (butuh pemetaan host-gateway agar `host.docker.internal` dikenal):

```bash
docker run --rm -p 127.0.0.1:8501:8501 \
  --add-host=host.docker.internal:host-gateway \
  tanya-sop
```

> **Perhatikan `127.0.0.1:` di depan pemetaan port.** Tanpa itu, `-p 8501:8501`
> mengikat ke seluruh antarmuka jaringan, dan Streamlit akan menampilkan
> "External URL" berisi alamat publik mesin Anda — siapa pun di jaringan yang
> sama bisa membuka aplikasi dan membaca isi dokumen internal, tanpa perlu
> kata sandi. Untuk demo di kantor atau ruang kelas, selalu ikat ke localhost.

Saat start pertama, container membangun indeks (butuh Ollama hidup). Setelah
muncul `You can now view your Streamlit app`, buka `http://localhost:8501`.

## Opsi

| Ubah | Perintah |
|---|---|
| Model chat lain | `docker run -e MODEL_CHAT=qwen3:4b -p 127.0.0.1:8501:8501 tanya-sop` |
| Ollama di host lain | `docker run -e OLLAMA_BASE_URL=http://192.168.1.10:11434 -p 127.0.0.1:8501:8501 tanya-sop` |

**Reranker tidak ikut di image ini.** `requirements-docker.txt` sengaja tidak
memuat `sentence-transformers`, karena container menyetel `PAKAI_RERANKER=0`
dan memasangnya akan menambah 3,9 GB (torch + CUDA) yang tidak pernah dipakai.
Menyetel `-e PAKAI_RERANKER=1` pada image ini tidak membuatnya aktif — kode
menangani ketiadaan paket dengan baik dan melanjutkan tanpa penyusunan ulang.
Bila Anda benar-benar membutuhkannya, ganti `requirements-docker.txt` menjadi
`requirements.txt` di `Dockerfile`, lalu bangun ulang.

## Menyimpan indeks antar-jalankan

Secara bawaan indeks dibangun ulang tiap container baru. Untuk menyimpannya,
pasang volume ke folder `/app`:

```bash
docker run --rm -p 8501:8501 -v tanyasop-indeks:/app tanya-sop
```

> **Peringatan (pelajaran F3):** indeks pada volume terikat pada model embedding
> yang membangunnya. Kalau Anda mengganti `MODEL_EMBEDDING`, hapus volume itu
> agar indeks dibangun ulang — kalau tidak, hasil pencarian menjadi acak tanpa
> galat. `meta.py` di dalam container akan memperingatkan bila ketidakcocokan
> ini terdeteksi.

## Catatan produksi (arah lanjut, di luar lab)

- Container ini untuk demo internal, bukan beban banyak pengguna. Untuk produksi,
  jalankan di belakang reverse proxy dan batasi akses jaringannya.
- Streamlit menyimpan riwayat per sesi di memori; tidak ada data yang disimpan
  permanen selain indeks.
