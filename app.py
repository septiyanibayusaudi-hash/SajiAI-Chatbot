"""
SajiAI — Asisten Memasak Pribadi
=================================
Aplikasi chatbot memasak berbasis Google Gemini API, dibangun dengan Streamlit.

SEBELUM MENJALANKAN INI:
    Jalankan dulu `python test_koneksi.py` untuk memastikan API key kamu
    benar-benar berfungsi. Ini akan menghemat waktu debugging.

Cara menjalankan aplikasi utuh:
    streamlit run app.py
"""

import html as html_lib
import json
import re
import time

import streamlit as st
from google import genai
from google.genai import types


# =========================================================
# KONFIGURASI DASAR
# =========================================================

MODEL_NAME = "gemini-3.6-flash"

SYSTEM_PROMPT = """
Kamu adalah SajiAI, asisten memasak pribadi yang ramah, hangat, dan mudah dipahami.

Peranmu:
- Membantu pengguna menemukan resep berdasarkan bahan yang mereka miliki.
- Memberikan rekomendasi menu yang praktis dan realistis.
- Menjawab pertanyaan seputar teknik memasak, alternatif bahan, penyesuaian porsi,
  dan estimasi waktu memasak.

Aturan penting:
- Jangan mengarang bahan yang sebenarnya tidak diperlukan.
- Jika informasi dari pengguna kurang jelas (misalnya bahan tidak disebutkan
  atau terlalu sedikit), tanyakan secara singkat dan relevan sebelum memberi resep.
- Jika pengguna bertanya di luar topik memasak, jawab dengan sopan bahwa SajiAI
  berfokus untuk membantu urusan memasak dan dapur.
- Gunakan bahasa Indonesia yang hangat dan mudah dipahami, seperti teman yang
  jago masak.

Format khusus untuk rekomendasi resep:
Jika, dan hanya jika, kamu memberikan rekomendasi SATU resep yang cukup lengkap
untuk dimasak, tulis dulu penjelasan singkat yang ramah dalam bentuk teks biasa,
lalu SELALU akhiri jawabanmu dengan blok data berikut (wajib berupa JSON valid,
diapit persis oleh penanda berikut, tanpa teks tambahan di dalam blok):

<<<RECIPE>>>
{
  "nama": "Nama masakan",
  "deskripsi": "Deskripsi singkat 1-2 kalimat",
  "waktu_memasak": "contoh: 20 menit",
  "tingkat_kesulitan": "Mudah / Sedang / Sulit",
  "porsi": "contoh: 2 porsi",
  "bahan": ["bahan 1", "bahan 2"],
  "langkah": ["langkah 1", "langkah 2"],
  "tips": ["tips 1"]
}
<<<END_RECIPE>>>

Jangan mengulang isi JSON tersebut di dalam teks penjelasanmu. Jika pengguna
hanya bertanya hal umum seputar memasak (bukan minta rekomendasi resep utuh),
jangan sertakan blok <<<RECIPE>>> sama sekali.
""".strip()


CHIP_PROMPTS = {
    "🔍 Cari resep": "Aku ingin mencari resep. Bisa bantu rekomendasikan menu yang enak dan mudah dibuat?",
    "🧺 Bahan yang saya punya": "Aku ingin masak sesuatu dari bahan yang aku punya di rumah. Bisa bantu aku?",
    "💰 Menu hemat": "Bisa kasih rekomendasi menu masakan hemat dan murah untuk hari ini?",
    "🥗 Makan malam sehat": "Bisa kasih rekomendasi menu makan malam yang sehat dan bergizi?",
}


RECIPE_PATTERN = re.compile(
    r"<<<RECIPE>>>(.*?)<<<END_RECIPE>>>",
    re.DOTALL
)


# =========================================================
# HALAMAN & GAYA (CSS)
# =========================================================

st.set_page_config(
    page_title="SajiAI — Asisten Memasak",
    page_icon="🥣",
    layout="wide"
)


CUSTOM_CSS = """
<style>

@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap');


:root {
    --cream: #FBF7EF;
    --card: #FFFFFF;
    --charcoal: #2E2B27;
    --charcoal-soft: #635C53;
    --sage: #6F8C69;
    --sage-dark: #55704F;
    --sage-light: #E9F0E4;
    --terracotta: #D2724A;
    --border-soft: #EAE1D0;
}


html,
body,
[data-testid="stAppViewContainer"] {
    background-color: var(--cream);
    color: var(--charcoal);
    font-family: 'Inter', sans-serif;
}


[data-testid="stHeader"] {
    background-color: transparent;
}


h1,
h2,
h3,
.sajiai-title {
    font-family: 'Fraunces', serif;
}


/* =========================================================
   SIDEBAR
   ========================================================= */

[data-testid="stSidebar"] {
    background-color: #FFFDF9;
    border-right: 1px solid var(--border-soft);
}


/* Menghilangkan jarak bawaan Streamlit */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0rem !important;
}


/* Padding utama sidebar */
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.8rem;
    padding-bottom: 0.8rem;
}


/* =========================================================
   BUTTON SIDEBAR
   ========================================================= */

[data-testid="stSidebar"] .stButton {
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}


/*
   BAGIAN PENTING:
   Memaksa isi tombol menjadi rata kiri.
*/
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;

    display: flex !important;
    flex-direction: row !important;

    align-items: center !important;
    justify-content: flex-start !important;

    text-align: left !important;

    background-color: transparent;
    color: var(--charcoal);

    border: none;

    font-weight: 500;

    padding: 0.55rem 0.75rem !important;

    border-radius: 10px;

    min-height: 40px;

    margin: 0.05rem 0 !important;

    transition:
        background-color 0.2s ease,
        color 0.2s ease;
}


/* Memaksa container isi tombol rata kiri */
[data-testid="stSidebar"] .stButton > button > div {
    width: 100% !important;

    display: flex !important;

    align-items: center !important;
    justify-content: flex-start !important;

    text-align: left !important;
}


/* Memaksa paragraf di dalam tombol rata kiri */
[data-testid="stSidebar"] .stButton > button p {
    width: auto !important;

    text-align: left !important;

    margin: 0 !important;
}


/* =========================================================
   CHAT BARU
   ========================================================= */

[data-testid="stSidebar"] button[kind="primary"] {
    background-color: var(--sage) !important;

    color: white !important;

    border: none !important;

    border-radius: 12px !important;

    font-weight: 600 !important;

    min-height: 44px !important;

    margin: 0.25rem 0 0.6rem 0 !important;

    display: flex !important;

    align-items: center !important;

    justify-content: center !important;
}


/* Isi Chat Baru tetap di tengah */
[data-testid="stSidebar"] button[kind="primary"] > div {
    justify-content: center !important;
}


[data-testid="stSidebar"] button[kind="primary"]:hover {
    background-color: var(--sage-dark) !important;
    color: white !important;
}


/* =========================================================
   MENU NAVIGASI
   ========================================================= */

/*
   Menu navigasi dibuat rapat dan rata kiri.
*/

[data-testid="stSidebar"] .nav-menu {
    width: 100%;
    margin: 0;
    padding: 0;
}


/* Hover menu */
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: var(--sage-light) !important;
    color: var(--sage-dark) !important;
}


/* =========================================================
   PEMISAH
   ========================================================= */

[data-testid="stSidebar"] hr {
    margin: 1.1rem 0 1rem 0 !important;
    border-color: var(--border-soft);
}


/* =========================================================
   STATUS SAJIAI
   ========================================================= */

.sajiai-status-card {
    background-color: var(--sage-light);

    border-radius: 14px;

    padding: 0.85rem 0.95rem;

    font-size: 0.82rem;

    line-height: 1.45;

    color: var(--charcoal-soft);

    margin: 0;

    text-align: left !important;
}


.sajiai-status-card b {
    color: var(--sage-dark);
}


/* =========================================================
   TOMBOL UTAMA
   ========================================================= */

button[kind="primary"] {
    background-color: var(--sage) !important;

    color: white !important;

    border: none !important;

    font-weight: 600 !important;

    border-radius: 12px !important;
}


button[kind="primary"]:hover {
    background-color: var(--sage-dark) !important;

    color: white !important;
}


/* =========================================================
   CHIP REKOMENDASI
   ========================================================= */

.chip-row .stButton button {
    background-color: var(--card);

    color: var(--charcoal);

    border: 1px solid var(--border-soft);

    border-radius: 999px;

    padding: 0.45rem 1rem;

    font-size: 0.85rem;

    font-weight: 500;

    box-shadow: 0 1px 2px rgba(46,43,39,0.04);
}


.chip-row .stButton button:hover {
    border-color: var(--sage);

    color: var(--sage-dark);
}


/* =========================================================
   AREA CHAT
   ========================================================= */

[data-testid="stChatMessage"] {
    background-color: var(--card);

    border: 1px solid var(--border-soft);

    border-radius: 16px;

    box-shadow: 0 1px 3px rgba(46,43,39,0.05);

    padding: 0.25rem 0.5rem;

    margin-bottom: 0.6rem;
}


/* =========================================================
   INPUT CHAT
   ========================================================= */

[data-testid="stChatInput"] textarea {
    border-radius: 999px !important;

    background-color: var(--card) !important;

    border: 1px solid var(--border-soft) !important;
}


[data-testid="stChatInput"] {
    border-radius: 999px;
}


/* =========================================================
   TOMBOL UMUM
   ========================================================= */

.stButton button {
    border-radius: 10px;
}


/* =========================================================
   KARTU RESEP
   ========================================================= */

.recipe-card {
    background-color: var(--card);

    border: 1px solid var(--border-soft);

    border-radius: 18px;

    padding: 1.2rem 1.4rem;

    margin: 0.6rem 0 0.3rem 0;

    box-shadow: 0 2px 10px rgba(46,43,39,0.06);
}


.recipe-card .recipe-icon {
    font-size: 2.1rem;

    margin-bottom: 0.2rem;
}


.recipe-card h4 {
    font-family: 'Fraunces', serif;

    margin: 0 0 0.25rem 0;

    color: var(--charcoal);
}


.recipe-card p.desc {
    color: var(--charcoal-soft);

    margin: 0 0 0.7rem 0;

    font-size: 0.94rem;
}


.recipe-meta {
    display: flex;

    gap: 1.1rem;

    font-size: 0.85rem;

    color: var(--sage-dark);

    font-weight: 500;

    margin-bottom: 0.8rem;
}


.recipe-card .bahan-title {
    font-weight: 600;

    font-size: 0.9rem;

    margin-bottom: 0.35rem;

    color: var(--charcoal);
}


.recipe-card ul.bahan-list {
    columns: 2;

    -webkit-columns: 2;

    padding-left: 1.1rem;

    margin: 0;

    font-size: 0.88rem;

    color: var(--charcoal-soft);
}


.recipe-card ul.bahan-list li {
    margin-bottom: 0.25rem;
}


/* =========================================================
   HEADER BERANDA
   ========================================================= */

.sajiai-header-wrap {
    padding: 0.5rem 0 1rem 0;
}


.sajiai-header-wrap h1 {
    font-size: 2.4rem;

    line-height: 1.15;

    margin-bottom: 0.4rem;

    color: var(--charcoal);
}


.sajiai-accent-dash {
    width: 46px;

    height: 4px;

    background-color: var(--terracotta);

    border-radius: 4px;

    margin: 0.5rem 0 0.9rem 0;
}


.sajiai-subtitle {
    color: var(--charcoal-soft);

    font-size: 1.02rem;

    margin-bottom: 0.2rem;
}

</style>
"""


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =========================================================
# GEMINI CLIENT
# =========================================================

@st.cache_resource(show_spinner=False)
def get_client(api_key: str):
    return genai.Client(api_key=api_key)


def new_chat_session():
    """Membuat sesi chat baru ke Gemini dengan system prompt SajiAI."""
    client = get_client(st.session_state.api_key)

    return client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        ),
    )


def ask_gemini(user_text: str) -> str:
    """Kirim pesan ke Gemini dan kembalikan teks jawabannya."""
    response = st.session_state.chat_session.send_message(user_text)

    return response.text or ""


def parse_recipe(reply_text: str):
    """Pisahkan teks biasa dan blok JSON resep (jika ada)."""

    match = RECIPE_PATTERN.search(reply_text)

    if not match:
        return reply_text.strip(), None

    clean_text = RECIPE_PATTERN.sub("", reply_text).strip()

    raw_json = match.group(1).strip()

    try:
        recipe = json.loads(raw_json)
    except json.JSONDecodeError:
        recipe = None

    return clean_text, recipe


# =========================================================
# SESSION STATE
# =========================================================

def init_state():

    if "page" not in st.session_state:
        st.session_state.page = "beranda"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "favorites" not in st.session_state:
        st.session_state.favorites = []

    if "init_error" not in st.session_state:
        st.session_state.init_error = None

    if "api_key" not in st.session_state:

        try:
            st.session_state.api_key = st.secrets.get(
                "GEMINI_API_KEY",
                ""
            )

        except Exception:
            st.session_state.api_key = ""

    if (
        "chat_session" not in st.session_state
        and st.session_state.api_key
    ):

        try:

            st.session_state.chat_session = new_chat_session()

        except Exception as e:

            st.session_state.chat_session = None

            st.session_state.init_error = (
                f"{type(e).__name__}: {e}"
            )


def clear_conversation():

    st.session_state.messages = []

    if st.session_state.api_key:

        try:

            st.session_state.chat_session = new_chat_session()

            st.session_state.init_error = None

        except Exception as e:

            st.session_state.chat_session = None

            st.session_state.init_error = (
                f"{type(e).__name__}: {e}"
            )


def is_favorited(nama: str) -> bool:

    return any(
        r.get("nama") == nama
        for r in st.session_state.favorites
    )


def toggle_favorite(recipe: dict):

    if is_favorited(recipe.get("nama")):

        st.session_state.favorites = [
            r
            for r in st.session_state.favorites
            if r.get("nama") != recipe.get("nama")
        ]

    else:

        st.session_state.favorites.append(recipe)


# =========================================================
# PENGIRIMAN PESAN
# =========================================================

def send_message(user_text: str):

    user_text = user_text.strip()

    if not user_text:
        return


    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_text,
            "recipe": None,
            "time": time.strftime("%H:%M"),
        }
    )


    if not st.session_state.api_key:

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Maaf, GEMINI_API_KEY belum diatur. "
                    "Tambahkan API key kamu di "
                    "`.streamlit/secrets.toml` agar SajiAI "
                    "bisa menjawab pertanyaanmu. 🙏"
                ),
                "recipe": None,
                "time": time.strftime("%H:%M"),
            }
        )

        return


    if not st.session_state.get("chat_session"):

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Maaf, SajiAI belum berhasil terhubung "
                    "ke Gemini API. Jalankan "
                    "`python test_koneksi.py` di terminal "
                    "untuk diagnosis, lalu klik "
                    "**Chat Baru** untuk mencoba lagi setelah "
                    "key diperbaiki."
                ),
                "recipe": None,
                "time": time.strftime("%H:%M"),
            }
        )

        return


    try:

        with st.spinner(
            "SajiAI sedang meracik jawaban... 🍳"
        ):

            raw_reply = ask_gemini(user_text)


        clean_text, recipe = parse_recipe(raw_reply)


        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    clean_text
                    or "Baik, dicatat! Ada lagi yang bisa dibantu?"
                ),
                "recipe": recipe,
                "time": time.strftime("%H:%M"),
            }
        )


    except Exception as e:

        error_detail = f"{type(e).__name__}: {e}"

        print(
            f"[SajiAI ERROR] {error_detail}"
        )


        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Waduh, SajiAI sedang kesulitan "
                    "menghubungi dapur digitalnya 🍳💨. "
                    "Coba kirim pesan itu lagi sebentar lagi, ya.\n\n"
                    f"<details>"
                    f"<summary>Detail teknis "
                    f"(untuk debugging)</summary>\n\n"
                    f"`{error_detail}`\n\n"
                    f"</details>"
                ),
                "recipe": None,
                "time": time.strftime("%H:%M"),
            }
        )


# =========================================================
# KOMPONEN TAMPILAN
# =========================================================

def render_recipe_card(
    recipe: dict,
    key_prefix: str
):

    if not recipe:
        return


    nama = html_lib.escape(
        str(recipe.get("nama", "Resep"))
    )

    deskripsi = html_lib.escape(
        str(recipe.get("deskripsi", ""))
    )

    waktu = html_lib.escape(
        str(recipe.get("waktu_memasak", "-"))
    )

    tingkat = html_lib.escape(
        str(recipe.get("tingkat_kesulitan", "-"))
    )

    porsi = html_lib.escape(
        str(recipe.get("porsi", "-"))
    )

    bahan = recipe.get("bahan", []) or []

    langkah = recipe.get("langkah", []) or []

    tips = recipe.get("tips", []) or []


    bahan_html = "".join(
        f"<li>{html_lib.escape(str(b))}</li>"
        for b in bahan
    )


    card_html = (
        '<div class="recipe-card">'
        '<div class="recipe-icon">🍲</div>'
        f'<h4>{nama}</h4>'
        f'<p class="desc">{deskripsi}</p>'
        '<div class="recipe-meta">'
        f'<span>⏱️ {waktu}</span>'
        f'<span>📊 {tingkat}</span>'
        f'<span>👥 {porsi}</span>'
        '</div>'
        '<div class="bahan-title">Bahan-bahan</div>'
        f'<ul class="bahan-list">{bahan_html}</ul>'
        '</div>'
    )


    st.markdown(
        card_html,
        unsafe_allow_html=True
    )


    col1, col2 = st.columns([1, 1])


    with col1:

        already_fav = is_favorited(
            recipe.get("nama")
        )

        fav_label = (
            "💚 Tersimpan di Favorit"
            if already_fav
            else "🤍 Simpan ke Favorit"
        )

        if st.button(
            fav_label,
            key=f"fav_{key_prefix}",
            use_container_width=True,
            type=(
                "primary"
                if already_fav
                else "secondary"
            ),
        ):

            toggle_favorite(recipe)

            st.rerun()


    with col2:

        with st.expander(
            "📖 Lihat langkah memasak lengkap"
        ):

            if langkah:

                for i, step in enumerate(
                    langkah,
                    start=1
                ):

                    st.markdown(
                        f"**{i}.** {step}"
                    )


            if tips:

                st.markdown(
                    "**💡 Tips:**"
                )

                for t in tips:

                    st.markdown(
                        f"- {t}"
                    )


def render_chat_history():

    for i, msg in enumerate(
        st.session_state.messages
    ):

        avatar = (
            "🥣"
            if msg["role"] == "assistant"
            else "🙂"
        )

        with st.chat_message(
            msg["role"],
            avatar=avatar
        ):

            st.markdown(
                msg["content"],
                unsafe_allow_html=True
            )

            if msg.get("recipe"):

                render_recipe_card(
                    msg["recipe"],
                    key_prefix=f"hist_{i}"
                )


# =========================================================
# SIDEBAR
# =========================================================

def render_sidebar():

    with st.sidebar:

        # -------------------------------------------------
        # LOGO
        # -------------------------------------------------

        logo_left, logo_center, logo_right = st.columns([1, 2, 1])
        with logo_center:
            st.image("Sajiai-logo-name.png", width=180)


        # -------------------------------------------------
        # CHAT BARU
        # -------------------------------------------------

        if st.button(
            "✨ Chat Baru",
            use_container_width=True,
            type="primary"
        ):

            clear_conversation()

            st.session_state.page = "beranda"

            st.rerun()


        # -------------------------------------------------
        # MENU NAVIGASI
        # -------------------------------------------------

        nav_items = [

            (
                "beranda",
                "🏠 Beranda"
            ),

            (
                "jelajahi",
                "🔎 Jelajahi Resep"
            ),

            (
                "favorit",
                "❤️ Favorit Saya"
            ),

            (
                "riwayat",
                "🕘 Riwayat Chat"
            ),

        ]


        for page_key, label in nav_items:

            # Tidak ada bullet "•"
            # Menu dibuat langsung rata kiri.

            if st.button(
                label,
                key=f"nav_{page_key}",
                use_container_width=True
            ):

                st.session_state.page = page_key

                st.rerun()


        # -------------------------------------------------
        # PEMISAH
        # -------------------------------------------------

        st.markdown("---")


        # -------------------------------------------------
        # STATUS SAJIAI
        # -------------------------------------------------

        st.markdown(
            '<div class="sajiai-status-card">'
            '<b>🍳 SajiAI siap membantu</b><br/>'
            'Asisten memasak cerdas untuk setiap dapur.'
            '<br/><br/>'
            '<span class="sajiai-status-online">● Online</span>'
            '</div>',
            unsafe_allow_html=True,
        )


# =========================================================
# BERANDA
# =========================================================

def render_beranda():

    st.markdown(
        '<div class="sajiai-header-wrap">'
        '<h1>Hari ini<br/>mau masak apa?</h1>'
        '<div class="sajiai-accent-dash"></div>'
        '<p class="sajiai-subtitle">'
        'Ubah bahan yang kamu punya menjadi hidangan lezat.'
        '</p></div>',
        unsafe_allow_html=True,
    )


    top_l, top_r = st.columns([6, 1])


    with top_r:

        if st.button(
            "🗑️ Hapus Riwayat",
            use_container_width=True
        ):

            clear_conversation()

            st.rerun()


    chat_box = st.container(
        border=True
    )


    with chat_box:

        if not st.session_state.messages:

            st.markdown(
                "<p style='color: var(--charcoal-soft);'>"
                "Ceritakan bahan yang ada di dapurmu, atau pilih salah satu ide "
                "cepat di bawah untuk memulai. 👇</p>",
                unsafe_allow_html=True,
            )


        render_chat_history()


    st.markdown(
        '<div class="chip-row">',
        unsafe_allow_html=True
    )


    chip_cols = st.columns(
        len(CHIP_PROMPTS)
    )


    for col, (
        label,
        prompt
    ) in zip(
        chip_cols,
        CHIP_PROMPTS.items()
    ):

        with col:

            if st.button(
                label,
                key=f"chip_{label}",
                use_container_width=True
            ):

                send_message(prompt)

                st.rerun()


    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


    user_input = st.chat_input(
        "Ceritakan bahan yang kamu punya..."
    )


    if user_input:

        send_message(user_input)

        st.rerun()


# =========================================================
# JELAJAHI RESEP
# =========================================================

def render_jelajahi():

    st.markdown(
        "## 🔎 Jelajahi Resep"
    )


    st.markdown(
        "<p style='color: var(--charcoal-soft);'>"
        "Pilih kategori untuk mendapatkan ide resep dari SajiAI.</p>",
        unsafe_allow_html=True,
    )


    kategori = {

        "🍚 Masakan Rumahan":
            "Kasih aku ide masakan rumahan sehari-hari yang praktis.",

        "🥦 Menu Diet & Sehat":
            "Kasih aku ide menu sehat rendah kalori untuk diet.",

        "🍰 Dessert Sederhana":
            "Kasih aku ide dessert atau camilan manis yang mudah dibuat di rumah.",

        "🌶️ Masakan Nusantara":
            "Kasih aku ide masakan tradisional Nusantara yang populer.",

        "⏱️ Masak Cepat < 15 Menit":
            "Kasih aku ide masakan yang bisa selesai dalam waktu kurang dari 15 menit.",

        "🍱 Bekal & Meal Prep":
            "Kasih aku ide menu bekal atau meal prep untuk seminggu.",
    }


    cols = st.columns(3)


    for idx, (
        label,
        prompt
    ) in enumerate(kategori.items()):

        with cols[idx % 3]:

            st.markdown(
                f'<div class="recipe-card" '
                'style="text-align:center; padding:1.4rem 1rem;">'
                f'<div class="recipe-icon">{label.split()[0]}</div>'
                f'<div style="font-weight:600;">'
                f"{' '.join(label.split()[1:])}</div></div>",
                unsafe_allow_html=True,
            )


            if st.button(
                "Cari ide",
                key=f"kategori_{idx}",
                use_container_width=True
            ):

                st.session_state.page = "beranda"

                send_message(prompt)

                st.rerun()


# =========================================================
# FAVORIT
# =========================================================

def render_favorit():

    st.markdown(
        "## ❤️ Favorit Saya"
    )


    if not st.session_state.favorites:

        st.markdown(
            "<p style='color: var(--charcoal-soft);'>"
            "Belum ada resep favorit. Simpan resep favoritmu langsung "
            "dari halaman chat!</p>",
            unsafe_allow_html=True,
        )

        return


    for i, recipe in enumerate(
        st.session_state.favorites
    ):

        render_recipe_card(
            recipe,
            key_prefix=f"fav_page_{i}"
        )


# =========================================================
# RIWAYAT CHAT
# =========================================================

def render_riwayat():

    st.markdown(
        "## 🕘 Riwayat Chat"
    )


    if not st.session_state.messages:

        st.markdown(
            "<p style='color: var(--charcoal-soft);'>"
            "Belum ada percakapan pada sesi ini.</p>",
            unsafe_allow_html=True,
        )

        return


    for msg in st.session_state.messages:

        label = (
            "Kamu"
            if msg["role"] == "user"
            else "SajiAI"
        )


        st.markdown(
            f"**{msg['time']} · {label}:** "
            f"{msg['content']}",
            unsafe_allow_html=True
        )


        st.markdown("---")


# =========================================================
# MAIN
# =========================================================

def main():

    init_state()

    render_sidebar()


    if not st.session_state.api_key:

        st.warning(
            """
            ⚠️ GEMINI_API_KEY belum ditemukan
            di `st.secrets`.

            Tambahkan file
            `.streamlit/secrets.toml`
            berisi:

            `GEMINI_API_KEY = "..."`

            lalu jalankan
            `python test_koneksi.py`
            untuk memastikan key-nya benar
            sebelum lanjut.
            """,
            icon="⚠️",
        )


    elif st.session_state.get("init_error"):

        st.error(
            f"""
            ⚠️ Gagal terhubung ke Gemini API:

            {st.session_state.init_error}

            Jalankan
            `python test_koneksi.py`
            di terminal untuk diagnosis lebih detail,
            lalu klik **Chat Baru** setelah diperbaiki.
            """,
            icon="🚫",
        )


    page = st.session_state.page


    if page == "beranda":

        render_beranda()


    elif page == "jelajahi":

        render_jelajahi()


    elif page == "favorit":

        render_favorit()


    elif page == "riwayat":

        render_riwayat()


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    main()