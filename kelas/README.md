# Kode Kelas TX-AI11 - Starter & Solution per Latihan

Building Intelligent Applications with RAG and AI Agents.

Kode dipecah **per hari** dan **per latihan** (L1.1 ... L3.6). Tiap latihan
adalah proyek MANDIRI yang bisa langsung dijalankan, dan bertambah sedikit demi
sedikit dari latihan sebelumnya - sehingga progres inkrementalnya terlihat.

```
kelas/
  hari-1/
    L1.1-lingkungan/  (starter/ + solution/)
    L1.2-indeks-pertama/  (starter/ + solution/)
    L1.3-tanya-baca-potongan/  (starter/ + solution/)
    L1.4-embedding-menentukan/  (starter/ + solution/)
  hari-2/
    L2.1-amati-chunking/  (starter/ + solution/)
    L2.2-metadata-dicabut/  (starter/ + solution/)
    L2.3-tiga-cara-cari/  (starter/ + solution/)
    L2.4-ukur-rusak-ukur/  (starter/ + solution/)
  hari-3/
    L3.1-agent/  (starter/ + solution/)
    L3.2-antarmuka/  (starter/ + solution/)
    L3.3-graf-multiagen/  (starter/ + solution/)
    L3.4-guardrail-jejak/  (starter/ + solution/)
    L3.5-graf-berkeadaan/  (starter/ + solution/)
    L3.6-proyek-akhir/  (starter/ + solution/)     <- penutup
```

## Cara pakai

1. Masuk ke folder latihan, mis. `kelas/hari-1/L1.2-indeks-pertama/starter/`.
2. `pip install -r requirements.txt` (sekali per hari sudah cukup bila venv sama).
3. Buka berkas, cari komentar `# TODO`, lengkapi mengikuti README latihan.
4. Bandingkan dengan `../solution/`. Jalankan perintah di README untuk memverifikasi.

## Prasyarat

- Python 3.10+ dan Ollama berjalan lokal (model `qwen3:8b`/`qwen3:4b` + `bge-m3`).
- Bila Ollama bermasalah: `MODE_TIRUAN=1` menjalankan seluruh alur tanpa Ollama
  (mutu embedding buruk - memang untuk berjaga-jaga, bukan hasil sebenarnya).

## Peta hari

- **[Hari 1](hari-1/README.md)** - Fondasi: AI Knowledge Stack & RAG
- **[Hari 2](hari-2/README.md)** - Building Blocks: Vector DB, Enhancement, Prompt, Evaluasi
- **[Hari 3](hari-3/README.md)** - AI Agents, Orchestration, dan Deployment
