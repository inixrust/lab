#!/bin/sh
# Titik masuk container. Bangun indeks bila belum ada, lalu jalankan antarmuka.
set -e

if [ ! -f /app/potongan.pkl ]; then
  echo "Indeks belum ada di dalam container — membangun sekarang."
  echo "Ini membutuhkan Ollama hidup di: ${OLLAMA_BASE_URL}"
  python indeks.py
fi

exec streamlit run app.py --server.address=0.0.0.0 --server.port=8501
