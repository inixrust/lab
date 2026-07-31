# -*- coding: utf-8 -*-
"""Antarmuka Streamlit — modul A5.

Tiga hal yang membuat antarmuka ini layak ditunjukkan ke atasan:
sumber yang bisa dibuka, penanda saat sistem menolak, dan keterangan bahwa
seluruh proses berjalan di mesin sendiri.

Tiap sitasi [1]..[4] bisa DIKLIK untuk membuka halaman aslinya. Yang dibuka
bukan potongan yang tersimpan di indeks, melainkan dokumen sungguhan yang
dibaca ulang dari folder dokumen — lihat `dokumen_asli.py`. Bedanya penting:
kalau potongannya sendiri keliru, cuplikan dari indeks akan ikut keliru dan
tidak ada yang bisa menangkapnya. Dengan membuka berkas asli, pengguna
memeriksa sistem, bukan mempercayainya.

Sumbernya BACA SAJA: yang dikirim ke peramban hanya teks halaman yang
bersangkutan, tidak pernah berkasnya. Cukup untuk memeriksa sitasi, tanpa
membagikan salinan dokumen internal yang tak bisa ditarik kembali.

Seluruh isi halaman dibungkus fungsi `jalankan()` supaya `app.py` cukup satu
panggilan, dan supaya modul ini bisa diimpor (mis. untuk memeriksa fungsi
pembantunya) tanpa langsung menggambar halaman.
"""
from __future__ import annotations

from typing import Any, Sequence

import streamlit as st

from . import dokumen_asli, konfig, tampilan
from .pembangkitan import TIDAK_DITEMUKAN, jawab

PANJANG_CUPLIKAN = 400


def ringkas_sumber(potongan: Sequence[Any]) -> list[dict[str, Any]]:
    """Ubah potongan menjadi keterangan sumber yang siap ditampilkan.

    `isi` disimpan UTUH, bukan dipotong seperti cuplikan satu baris: ia dipakai
    untuk mencari posisi sorotan di halaman asli, dan kutipan yang terpotong
    tidak akan pernah ketemu. `metadata` ikut dibawa agar berkas aslinya bisa
    dibuka kembali saat riwayat digambar ulang.
    """
    return [
        {
            "berkas": tampilan.sumber(d),
            "lokasi": tampilan.lokasi(d.metadata),
            "isi": dokumen_asli.isi_asli(d),
            "metadata": dict(d.metadata),
        }
        for d in potongan
    ]


def _tampilkan_sumber(daftar: Sequence[dict[str, Any]]) -> None:
    """Satu kotak lipat per sumber, berisi halaman asli yang bisa diperiksa.

    Sengaja satu expander per sumber, bukan satu expander berisi empat:
    pengguna sedang memeriksa SATU sitasi tertentu, dan tidak semestinya
    menggulir melewati tiga lainnya untuk sampai ke sana.

    BACA SAJA — berkasnya tidak bisa diunduh. Yang dikirim ke peramban hanya
    TEKS halaman yang bersangkutan. Ditegakkan dengan TIDAK PERNAH mengirim isi
    berkasnya, bukan dengan menyembunyikan tombol: yang tidak dikirim tidak
    bisa diambil.
    """
    if not daftar:
        return
    st.caption(
        f"{len(daftar)} sumber — klik untuk membuka dokumen aslinya "
        f"dan memeriksa sendiri."
    )

    for nomor, s in enumerate(daftar, start=1):
        with st.expander(f"[{nomor}]  {s['berkas']} — {s['lokasi']}"):
            teks, keterangan = dokumen_asli.halaman_asli(s["metadata"])

            if teks is None:
                # Katakan apa adanya. Kotak kosong akan terbaca seolah-olah
                # dokumen aslinya memang tidak berisi apa-apa.
                st.warning(keterangan)
                st.caption("Yang dibaca model:")
                st.markdown(f"> {s['isi'][:PANJANG_CUPLIKAN]}")
                continue

            st.caption(f"{keterangan} — bagian bersorot inilah yang dibaca model.")

            # st.html(), BUKAN st.markdown(unsafe_allow_html=True). Keduanya
            # menampilkan HTML, tapi st.markdown juga menafsirkan isinya
            # sebagai Markdown — dan notulen kita memang Markdown. Akibatnya
            # "# Notulen" jadi judul besar dan "**Nomor:**" jadi tebal:
            # pengguna melihat hasil OLAHAN, bukan berkas aslinya, padahal
            # justru keaslian itulah yang sedang ia periksa. (Teruji:
            # st.markdown memunculkan 5 heading + 5 anchor palsu; st.html nol.)
            st.html(dokumen_asli.sorot_html(teks, s["isi"]))


def _sidebar() -> tuple[str, int, bool]:
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
        st.caption(
            f"Model: `{konfig.MODEL_CHAT}` · Embedding: `{konfig.MODEL_EMBEDDING}`"
        )
        if konfig.MODE_TIRUAN:
            st.warning("Mode tiruan aktif — jawaban tidak dirangkai model sungguhan.")

        if st.button("Bersihkan percakapan"):
            st.session_state.riwayat = []
            st.rerun()
    return peran, k, tampil_sumber


def _tampilkan_riwayat() -> None:
    for pesan in st.session_state.riwayat:
        with st.chat_message(pesan["peran"]):
            st.markdown(pesan["isi"])
            if pesan.get("sumber"):
                _tampilkan_sumber(pesan["sumber"])


def _tandai_kejujuran(isi: str, laporan) -> None:
    """Penanda kejujuran — bagian dari rancangan, bukan hiasan."""
    if TIDAK_DITEMUKAN in isi:
        st.info(
            "Sistem tidak menemukan dasar di dokumen yang tersedia. "
            "Ini perilaku yang benar, bukan kegagalan."
        )
    elif laporan.cakupan_rendah:
        st.warning(
            f"Sebagian pernyataan belum membawa sumber "
            f"(cakupan sitasi {laporan.cakupan:.0%}). "
            f"Mohon diperiksa sebelum dipakai."
        )
    if laporan.hantu:
        st.error(
            f"Ada sitasi yang menunjuk potongan tidak ada: {list(laporan.hantu)}. "
            f"Jawaban ini tidak dapat diverifikasi."
        )


def _jawab_pertanyaan(tanya: str, peran: str, k: int, tampil_sumber: bool) -> None:
    with st.chat_message("assistant"):
        try:
            with st.spinner("Mencari di dokumen..."):
                isi, potongan, laporan = jawab(
                    tanya, {"peran": peran}, k=k, tampilkan_potongan=False
                )
        except FileNotFoundError as e:
            st.error(f"{e}")
            st.stop()
        except Exception as e:
            # Pengguna antarmuka butuh saran yang bisa ditindaklanjuti,
            # bukan traceback. Rincinya tetap muncul di konsol Streamlit.
            st.error(
                f"Gagal memproses: {type(e).__name__}. "
                f"Periksa apakah layanan Ollama berjalan, lalu coba lagi."
            )
            st.stop()

        st.markdown(isi)
        _tandai_kejujuran(isi, laporan)

        sumber = ringkas_sumber(potongan) if tampil_sumber else []
        _tampilkan_sumber(sumber)

    st.session_state.riwayat.append(
        {"peran": "assistant", "isi": isi, "sumber": sumber}
    )


def jalankan() -> None:
    """Gambar seluruh halaman. Dipanggil sekali dari app.py."""
    st.set_page_config(
        page_title="Tanya SOP", page_icon=":page_facing_up:", layout="centered"
    )

    if "riwayat" not in st.session_state:
        st.session_state.riwayat = []

    peran, k, tampil_sumber = _sidebar()

    st.title("Tanya SOP Perusahaan")
    st.caption("Menjawab hanya dari dokumen internal yang masih berlaku.")

    _tampilkan_riwayat()

    tanya = st.chat_input("Contoh: Berapa lama masa percobaan karyawan baru?")
    if not tanya:
        return

    st.session_state.riwayat.append({"peran": "user", "isi": tanya})
    with st.chat_message("user"):
        st.markdown(tanya)

    _jawab_pertanyaan(tanya, peran, k, tampil_sumber)
