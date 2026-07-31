# Deployment on-premise aplikasi Tanya SOP — modul A5.
#
# Container ini HANYA membungkus aplikasi. Ollama tetap berjalan di HOST
# (bukan di dalam container) supaya model tidak perlu diunduh ulang dan GPU
# host bisa dipakai. Aplikasi menjangkau Ollama lewat OLLAMA_BASE_URL.
# Lihat DEPLOY.md untuk cara menjalankan di Windows/Mac maupun Linux.

FROM python:3.11-slim

WORKDIR /app

# Pasang paket lebih dulu agar lapisan ini tersimpan di cache selama
# daftar paketnya tidak berubah.
#
# Sengaja memakai requirements-docker.txt, bukan requirements.txt: container
# menyetel PAKAI_RERANKER=0, jadi sentence-transformers tidak pernah diimpor —
# tetapi memasangnya menarik torch + CUDA sebesar 3,9 GB yang tidak dipakai
# sama sekali. Lihat penjelasan lengkapnya di requirements-docker.txt.
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Salin kode dan korpus. Indeks (chroma_db/, potongan.pkl) sengaja TIDAK
# disalin — dibangun saat container pertama kali start, dengan embedding yang
# sama seperti di kelas. Lihat .dockerignore.
COPY src/ ./src/
COPY dokumen/ ./dokumen/
COPY set_uji.json ./
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# host.docker.internal = alamat host dari dalam container (Docker Desktop).
# Di Linux, jalankan dengan --add-host=host.docker.internal:host-gateway.
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434

# Reranker (2 GB, dari Hugging Face) dimatikan secara bawaan untuk deployment
# agar image ringan dan start cepat. Nyalakan dengan -e PAKAI_RERANKER=1 bila
# host punya cukup memori.
ENV PAKAI_RERANKER=0

WORKDIR /app/src
EXPOSE 8501
ENTRYPOINT ["/app/docker-entrypoint.sh"]
