# SajiAI — Asisten Memasak Pribadi

SajiAI adalah aplikasi chatbot memasak berbasis **Streamlit** dan **Google Gemini API**.
Ceritakan bahan yang kamu punya, dan SajiAI akan membantu menemukan resep, memberi
rekomendasi menu, serta menjawab pertanyaan seputar teknik memasak.

## ✨ Fitur

- Chat interaktif dengan Gemini (`st.chat_message` + `st.chat_input`)
- Riwayat percakapan tersimpan selama sesi berlangsung
- Kartu resep rapi: bahan, langkah, waktu, tingkat kesulitan, porsi, dan tips
- Quick suggestion chips: *Cari resep*, *Bahan yang saya punya*, *Menu hemat*, *Makan malam sehat*
- Simpan resep ke **Favorit**
- Halaman **Jelajahi Resep** dan **Riwayat Chat**
- Tombol **Chat Baru** dan **Hapus Riwayat**
- Script `test_koneksi.py` untuk mendiagnosis masalah API key **tanpa perlu Streamlit**
- Pesan error yang ramah + detail teknis jika Gemini API gagal dihubungi

## 📁 Struktur Project

```
sajiai/
├── app.py                          
├── test_koneksi.py                 
├── requirements.txt                
├── .streamlit/
│   └── secrets.toml   
└── README.md
