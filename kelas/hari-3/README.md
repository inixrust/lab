# Hari 3 - AI Agents, Orchestration, dan Deployment

Latihan berurutan (kumulatif). Tiap latihan adalah snapshot lengkap sampai titik
itu; kerjakan `starter/`, cocokkan dengan `solution/`. Mulai dari nomor 1.

1. **[L3.1-agent](L3.1-agent/README.md)** - Agent yang Memanggil Alat Sendiri
   Lingkaran agent ditulis tangan: model memilih alat, kita jalankan, ulangi.
2. **[L3.2-antarmuka](L3.2-antarmuka/README.md)** - Membungkus Pipeline Jadi Antarmuka
   Streamlit + Docker. Tiap sitasi bisa diklik untuk membuka halaman aslinya.
3. **[L3.3-graf-multiagen](L3.3-graf-multiagen/README.md)** - Dari Lingkaran Tulisan Tangan ke Graph & Tim Agent
   Agent yang sama ditulis ulang sebagai LangGraph, lalu dipecah jadi tim
   multi-agent dengan penyelia.
4. **[L3.4-guardrail-jejak](L3.4-guardrail-jejak/README.md)** - Hak Akses, Cache yang Tidak Bocor, dan Jejak
   Guardrail ditegakkan di kode, cache dikunci per hak akses, observability
   per langkah.
5. **[L3.5-graf-berkeadaan](L3.5-graf-berkeadaan/README.md)** - Langkah Pasti, Langkah Model, dan Manusia di Tengah
   Satu graf yang mencampur langkah deterministik (bisa diaudit), langkah
   model, dan persetujuan manusia lewat `interrupt()`.
6. **[L3.6-proyek-akhir](L3.6-proyek-akhir/README.md)** - Proyek Akhir: Pilih Dua Peningkatan, Lalu Ukur
   Snapshot lengkap seluruh kelas. Pilih dua peningkatan, pasang, buktikan
   dengan angka.

## Alurnya

L3.1 sampai L3.3 membangun **kemampuan**: agent bisa memilih langkahnya sendiri,
lalu cara menyatakan alur itu dinaikkan dari lingkaran `for` menjadi graph.

L3.4 dan L3.5 menambahkan yang selalu dituntut sistem sungguhan dan tidak pernah
ada di demo: **siapa boleh melihat apa**, **apa yang terjadi tadi sore**, dan
**di mana manusia menyela**. Keduanya berpasangan — L3.4 memasang guardrail,
cache, dan jejak sebagai berkas terpisah; L3.5 menyusunnya kembali menjadi satu
graf berkeadaan.

L3.6 adalah **penutup**, bukan latihan baru: seluruh kelas sudah ada di dalamnya
dan tinggal diperbaiki serta diukur.

Bila waktu kelas mepet, L3.4 sendirian sudah memberi pelajaran terpentingnya —
kebocoran datang dari jalan pintas yang melewati pagar, bukan dari pagar yang
jebol.
