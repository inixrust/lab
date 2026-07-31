# -*- coding: utf-8 -*-
"""Antarmuka Streamlit — modul A5.

    streamlit run app.py

Tiga hal yang membuat antarmuka ini layak ditunjukkan ke atasan:
sumber yang bisa dibuka, penanda saat sistem menolak, dan keterangan bahwa
seluruh proses berjalan di mesin sendiri.

Tiap sitasi [1]..[4] bisa DIKLIK untuk membuka halaman aslinya. Yang dibuka
bukan potongan yang tersimpan di indeks, melainkan dokumen sungguhan yang
dibaca ulang dari folder dokumen/ — lihat sumber.py. Bedanya penting: kalau
potongannya sendiri yang keliru, cuplikan dari indeks akan ikut keliru dan
tidak ada yang bisa menangkapnya. Dengan membuka berkas asli, pengguna
memeriksa sistem, bukan mempercayainya.

Sumbernya BACA SAJA: yang dikirim ke peramban hanya teks halaman yang
bersangkutan, tidak pernah berkasnya. Cukup untuk memeriksa sitasi, tanpa
membagikan salinan dokumen internal yang tak bisa ditarik kembali.
"""
import streamlit as st

import izin
import konfig
import sumber as modul_sumber
import util
from jawab import jawab, TIDAK_DITEMUKAN

st.set_page_config(page_title="Tanya SOP", page_icon=":page_facing_up:",
                   layout="centered")


def tampilkan_sumber(daftar):
    """Satu kotak lipat per sumber, berisi halaman asli yang bisa diperiksa.

    Sengaja satu expander per sumber, bukan satu expander berisi empat:
    pengguna sedang memeriksa SATU sitasi tertentu, dan tidak semestinya
    menggulir melewati tiga lainnya untuk sampai ke sana.

    BACA SAJA — berkasnya tidak bisa diunduh. Yang dikirim ke peramban hanya
    TEKS halaman yang bersangkutan, bukan berkas aslinya. Pengguna tetap bisa
    memeriksa sitasi (itu tujuannya), tetapi tidak bisa membawa pulang salinan
    dokumen internal — sesuatu yang sulit ditarik kembali begitu tersebar.
    Perhatikan bahwa ini ditegakkan dengan TIDAK PERNAH mengirim isi berkasnya,
    bukan dengan menyembunyikan tombol: yang tidak dikirim tidak bisa diambil.
    """
    if not daftar:
        return
    st.caption(f"{len(daftar)} sumber — klik untuk membuka dokumen aslinya "
               f"dan memeriksa sendiri.")

    for i, s in enumerate(daftar, 1):
        with st.expander(f"[{i}]  {s['berkas']} — {s['lokasi']}"):
            teks, keterangan = modul_sumber.halaman_asli(s["metadata"])

            if teks is None:
                # Katakan apa adanya. Menampilkan kotak kosong akan terbaca
                # seolah-olah dokumen aslinya memang tidak berisi apa-apa.
                st.warning(keterangan)
                st.caption("Yang dibaca model:")
                st.markdown(f"> {s['isi'][:400]}")
                continue

            st.caption(f"{keterangan} — bagian bersorot inilah yang dibaca "
                       f"model.")

            # st.html(), BUKAN st.markdown(unsafe_allow_html=True). Keduanya
            # menampilkan HTML, tapi st.markdown juga menafsirkan isinya
            # sebagai Markdown — dan dokumen notulen kita memang Markdown.
            # Akibatnya "# Notulen" berubah jadi judul besar dan "**Nomor:**"
            # jadi tebal: pengguna melihat hasil OLAHAN, bukan berkas aslinya,
            # padahal justru keaslian itulah yang sedang ia periksa.
            # (Teruji: st.markdown memunculkan 5 heading + 5 anchor palsu di
            # dalam kotak; st.html nol.)
            st.html(modul_sumber.sorot_html(teks, s["isi"]))


# ------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Pengaturan")
    # PENINGKATAN 5 — daftar peran dibaca dari izin.PERAN_TERURUT, bukan
    # ditulis ulang di sini. Daftar peran yang disalin ke antarmuka adalah
    # cara paling umum sebuah peran baru terlupakan.
    peran = st.selectbox("Peran pengguna", izin.PERAN_TERURUT)
    st.caption("Jenis dokumen yang boleh dibaca peran ini: "
               + ", ".join(sorted(izin.jenis_boleh({"peran": peran}))))
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

        # `isi` disimpan UTUH, bukan dipotong 280 karakter seperti dulu —
        # ia dipakai untuk mencari posisi sorotan di halaman asli, dan
        # cuplikan yang terpotong tidak akan pernah ketemu.
        sumber = [{"berkas": d.metadata.get("source", "?"),
                   "lokasi": util.lokasi(d.metadata),
                   "isi": modul_sumber.isi_asli(d),
                   "metadata": dict(d.metadata)}
                  for d in potongan] if tampil_sumber else []
        tampilkan_sumber(sumber)

    st.session_state.riwayat.append(
        {"peran": "assistant", "isi": isi, "sumber": sumber})
