# 🥣 SajiAI — Asisten Memasak Pribadi

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
├── app.py                          # Aplikasi utama Streamlit
├── test_koneksi.py                 # Alat bantu tes API key (jalankan ini dulu!)
├── requirements.txt                # Dependensi Python
├── .streamlit/
│   └── secrets.toml.example        # Contoh konfigurasi API key
└── README.md
```

## 🚀 Cara Menjalankan (urutan penting!)

### 1. Download & susun folder
Pastikan semua file di atas berada dalam satu folder yang sama.

### 2. Buat virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
> Kalau muncul error "running scripts is disabled", jalankan dulu:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` (ketik `Y` jika diminta), lalu ulangi.

**Mac/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

Pastikan prompt terminal sekarang menampilkan `(venv)` di depannya sebelum lanjut.

### 3. Install dependensi

```bash
pip install -r requirements.txt
```

### 4. Siapkan API key Gemini

1. Buka [Google AI Studio](https://aistudio.google.com/app/apikey), login, klik **Create API key**.
2. Salin `.streamlit/secrets.toml.example` menjadi `.streamlit/secrets.toml` (folder `.streamlit`
   mungkin "hidden" di Windows — aktifkan lewat File Explorer → View → centang *Hidden items*).
3. Buka `secrets.toml` dengan Notepad, isi:
   ```toml
   GEMINI_API_KEY = "tempel-api-key-kamu-disini"
   ```
4. Simpan file.

> ⚠️ Jangan pernah menuliskan API key langsung di dalam kode `app.py`, jangan commit
> `secrets.toml` ke Git/GitHub, dan jangan share API key ke siapa pun (termasuk ke chat AI).

### 5. WAJIB: Tes dulu API key-nya

Sebelum menjalankan aplikasi utuh, jalankan alat diagnostik ini:

```bash
python test_koneksi.py
```

- Kalau muncul **✅ BERHASIL** → lanjut ke langkah 6.
- Kalau muncul **❌ GAGAL** → script ini akan menjelaskan kemungkinan penyebabnya
  (key salah, kuota habis, atau masalah format key) beserta saran perbaikannya.
  Perbaiki dulu di sini sebelum lanjut — ini jauh lebih cepat daripada debug lewat
  aplikasi Streamlit yang penuh tampilan.

### 6. Jalankan aplikasinya

```bash
streamlit run app.py
```

Browser akan terbuka otomatis di `http://localhost:8501`.

## ☁️ Deploy ke Streamlit Community Cloud

1. Push project ini ke repository GitHub (**tanpa** file `secrets.toml` asli).
2. Buat aplikasi baru di [share.streamlit.io](https://share.streamlit.io).
3. Di menu **Settings → Secrets**, tempelkan isi `secrets.toml` kamu.
4. Deploy — aplikasi akan otomatis membaca secrets tersebut lewat `st.secrets`.

## 🛠️ Kustomisasi

- **Ganti model Gemini**: ubah `MODEL_NAME` di bagian atas `app.py` (dan `test_koneksi.py`).
- **Ubah persona/gaya bicara**: edit `SYSTEM_PROMPT` di `app.py`.
- **Ubah warna & tampilan**: cari `CUSTOM_CSS` di `app.py` (token warna: `--sage`, `--terracotta`, `--cream`).
- **Ubah quick suggestion chips**: edit dictionary `CHIP_PROMPTS`.

## ❗ Troubleshooting

| Masalah | Solusi |
|---|---|
| `pip` tidak dikenali di PowerShell | Virtual environment belum aktif. Jalankan `.\venv\Scripts\Activate.ps1` dulu — pastikan `(venv)` muncul di prompt. |
| "GEMINI_API_KEY belum ditemukan" | File harus bernama persis `secrets.toml` (bukan `.example`), di dalam folder `.streamlit/`. |
| `python test_koneksi.py` gagal dengan kode 401 / `ACCESS_TOKEN_TYPE_UNSUPPORTED` | Ini terkait migrasi format API key Google (dari `AIza...` ke `AQ...`) yang sedang berlangsung. Coba `pip install --upgrade google-genai`, buat key baru, atau tunggu — ini dilaporkan sebagai isu di sisi Google, bukan di kode kamu. |
| `ModuleNotFoundError` untuk `streamlit` atau `google` | Jalankan ulang `pip install -r requirements.txt` di venv yang aktif. |
| Jawaban Gemini tidak muncul sebagai kartu resep | Normal untuk pertanyaan umum (bukan minta resep). Kartu hanya muncul saat Gemini merekomendasikan satu resep utuh. |

Selamat memasak bersama SajiAI! 🍲
