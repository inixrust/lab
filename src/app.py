# -*- coding: utf-8 -*-
"""Antarmuka Streamlit — modul A5.

    streamlit run app.py

Tiga hal yang membuat antarmuka ini layak ditunjukkan ke atasan:
sumber yang bisa dibuka, penanda saat sistem menolak, dan keterangan bahwa
seluruh proses berjalan di mesin sendiri.
"""
import streamlit as st

import konfig
import util
from jawab import jawab, TIDAK_DITEMUKAN

st.set_page_config(page_title="Tanya SOP", page_icon=":page_facing_up:",
                   layout="centered")


def tampilkan_sumber(daftar):
    if not daftar:
        return
    with st.expander(f"Lihat {len(daftar)} sumber"):
        for i, s in enumerate(daftar, 1):
            st.markdown(f"**[{i}] {s['berkas']} — {s['lokasi']}**")
            st.caption(s["cuplikan"])


# ------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Pengaturan")
    peran = st.selectbox("Peran pengguna", ["staf", "pimpinan"])
    k = st.slider("Jumlah potongan diambil", 2, 8, konfig.JUMLAH_AKHIR)
    tampil_sumber = st.checkbox("Tampilkan sumber", value=True)

    st.divider()
    st.caption(
        "Seluruh proses berjalan di mesin ini. Tidak ada dokumen yang "
        "dikirim ke luar organisasi."
    )
    st.caption(f"Model: `{konfig.MODEL_CHAT}` · Embedding: `{konfig.MODEL_EMBEDDING}`")
    if konfig.MODE_TIRUAN:
        st.warning("Mode tiruan aktif — jawaban tidak dirangkai model sungguhan.")

    if st.button("Bersihkan percakapan"):
        st.session_state.riwayat = []
        st.rerun()

# ------------------------------------------------------------- kepala
st.title("Tanya SOP Perusahaan")
st.caption("Menjawab hanya dari dokumen internal yang masih berlaku.")

if "riwayat" not in st.session_state:
    st.session_state.riwayat = []

for p in st.session_state.riwayat:
    with st.chat_message(p["peran"]):
        st.markdown(p["isi"])
        if p.get("sumber"):
            tampilkan_sumber(p["sumber"])

# ------------------------------------------------------------- masukan
if tanya := st.chat_input("Contoh: Berapa lama masa percobaan karyawan baru?"):
    st.session_state.riwayat.append({"peran": "user", "isi": tanya})
    with st.chat_message("user"):
        st.markdown(tanya)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Mencari di dokumen..."):
                isi, potongan, lapor = jawab(
                    tanya, {"peran": peran}, k=k, tampilkan_potongan=False)
        except FileNotFoundError as e:
            st.error(f"{e}")
            st.stop()
        except Exception as e:
            st.error(
                f"Gagal memproses: {type(e).__name__}. "
                f"Periksa apakah layanan Ollama berjalan, lalu coba lagi."
            )
            st.stop()

        st.markdown(isi)

        # Penanda kejujuran — bagian dari rancangan, bukan hiasan.
        if TIDAK_DITEMUKAN in isi:
            st.info(
                "Sistem tidak menemukan dasar di dokumen yang tersedia. "
                "Ini perilaku yang benar, bukan kegagalan."
            )
        elif lapor["cakupan"] < konfig.AMBANG_CAKUPAN:
            st.warning(
                f"Sebagian pernyataan belum membawa sumber "
                f"(cakupan sitasi {lapor['cakupan']:.0%}). "
                f"Mohon diperiksa sebelum dipakai."
            )
        if lapor["hantu"]:
            st.error(
                f"Ada sitasi yang menunjuk potongan tidak ada: {lapor['hantu']}. "
                f"Jawaban ini tidak dapat diverifikasi."
            )

        sumber = [{"berkas": d.metadata.get("source", "?"),
                   "lokasi": util.lokasi(d.metadata),
                   "cuplikan": " ".join(d.page_content.split())[:280] + "..."}
                  for d in potongan] if tampil_sumber else []
        tampilkan_sumber(sumber)

    st.session_state.riwayat.append(
        {"peran": "assistant", "isi": isi, "sumber": sumber})
