# File: app.py
import streamlit as st
from auth_utils import check_auth

st.set_page_config(
    page_title="PACE — Sign In",
    page_icon="P",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Dark theme + package animation CSS ────────────────────────────────────────
st.markdown("""
<style>
/* ── Global dark ── */
.stApp {
    background-color: #161638 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
}
#MainMenu, header, footer { visibility: hidden; }
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
.block-container { padding-top: 2rem !important; }

/* ── Text ── */
.stApp, .stApp p, .stApp span, .stApp label { color: #F1F5F9 !important; }
.stApp h1, .stApp h2, .stApp h3 { color: #F1F5F9 !important; }

/* ── Login card container ── */
[data-testid="stVerticalBlock"] > div[data-testid="element-container"]
> div > div > div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #1B435E !important;
    border: 1px solid #38667E !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 40px rgba(0,0,0,0.5) !important;
    animation: cardRise 0.7s ease-out 0.9s both !important;
}

/* ── Form inputs ── */
.stTextInput > div > div > input {
    background: #161638 !important;
    color: #F1F5F9 !important;
    border-color: #38667E !important;
    border-radius: 8px !important;
    transition: border-color 0.2s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: #2DD4BF !important;
    box-shadow: 0 0 0 2px rgba(45,212,191,0.15) !important;
}
.stTextInput > div > div > input::placeholder { color: #64748B !important; }
.stTextInput label { color: #94A3B8 !important; font-size: 13px !important; }

/* ── Sign In button ── */
.stButton > button[kind="primary"] {
    background-color: #563457 !important;
    color: #F1F5F9 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 10px 0 !important;
    transition: background 0.2s ease, transform 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #3A2B50 !important;
    transform: translateY(-1px) !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 8px !important; }

/* ── Package animation keyframes ── */
@keyframes pkgDrop {
    0%   { opacity: 0; transform: translateY(-40px) scale(0.8); }
    60%  { opacity: 1; transform: translateY(6px) scale(1.05); }
    80%  { transform: translateY(-3px) scale(0.98); }
    100% { transform: translateY(0) scale(1); }
}
@keyframes lidOpen {
    0%   { transform: perspective(500px) rotateX(0deg); }
    100% { transform: perspective(500px) rotateX(-140deg); }
}
@keyframes cardRise {
    0%   { opacity: 0; transform: translateY(24px); }
    100% { opacity: 1; transform: translateY(0); }
}
@keyframes tagSwing {
    0%, 100% { transform: rotate(-6deg); }
    50%       { transform: rotate(6deg); }
}

/* ── Package graphic ── */
.pkg-scene {
    display: flex;
    justify-content: center;
    padding: 10px 0 24px;
    animation: pkgDrop 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) 0.1s both;
}
.pkg-outer { position: relative; width: 96px; }
.pkg-lid {
    width: 100%;
    height: 28px;
    background: #563457;
    border: 2px solid #38667E;
    border-radius: 6px 6px 0 0;
    position: relative;
    animation: lidOpen 0.55s ease-in 0.45s both;
    transform-origin: bottom center;
    z-index: 2;
}
.pkg-lid::before {
    content: '';
    position: absolute;
    left: 50%; top: 50%;
    transform: translate(-50%, -50%);
    width: 32px; height: 4px;
    background: rgba(45,212,191,0.5);
    border-radius: 2px;
}
.pkg-body {
    width: 100%;
    height: 64px;
    background: #1B435E;
    border: 2px solid #38667E;
    border-top: none;
    border-radius: 0 0 6px 6px;
    position: relative;
    overflow: hidden;
}
.pkg-tape-v {
    position: absolute;
    left: 50%; top: 0; bottom: 0;
    width: 14px;
    background: rgba(86,52,87,0.55);
    transform: translateX(-50%);
}
.pkg-tape-h {
    position: absolute;
    top: 50%; left: 0; right: 0;
    height: 14px;
    background: rgba(86,52,87,0.55);
    transform: translateY(-50%);
}
.pkg-label {
    position: absolute;
    bottom: 6px; left: 8px; right: 8px;
    height: 20px;
    background: rgba(45,212,191,0.12);
    border: 1px solid rgba(45,212,191,0.3);
    border-radius: 3px;
    display: flex; align-items: center; justify-content: center;
    font-size: 8px; font-weight: 700;
    color: rgba(45,212,191,0.8);
    letter-spacing: 1.5px;
}
.pkg-tag {
    position: absolute;
    top: -20px; right: 10px;
    width: 14px; height: 18px;
    background: #FBBF24;
    border-radius: 2px 2px 0 0;
    animation: tagSwing 2s ease-in-out 1.5s infinite;
    transform-origin: top center;
}
.pkg-tag::after {
    content: '';
    position: absolute;
    bottom: -4px; left: 50%;
    transform: translateX(-50%);
    width: 5px; height: 5px;
    background: #161638;
    border-radius: 50%;
}
.pkg-string {
    position: absolute;
    top: -2px; right: 16px;
    width: 1px; height: 4px;
    background: #94A3B8;
}
</style>
""", unsafe_allow_html=True)

# Already logged in → go straight to home
if check_auth():
    st.switch_page("pages/0_Home.py")

# ── Package animation (birds-eye view of box opening) ─────────────────────────
st.markdown("""
<div class="pkg-scene">
  <div class="pkg-outer">
    <div class="pkg-string"></div>
    <div class="pkg-tag"></div>
    <div class="pkg-lid"></div>
    <div class="pkg-body">
      <div class="pkg-tape-v"></div>
      <div class="pkg-tape-h"></div>
      <div class="pkg-label">PACE</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Brand header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:0 0 28px;">
    <h1 style="font-size:34px; font-weight:700; color:#F1F5F9;
               margin:0 0 4px; letter-spacing:2px;">PACE</h1>
    <p style="color:#94A3B8; font-size:14px; margin:0; letter-spacing:0.3px;">
        Predictive Accessorial Cost Engine
    </p>
</div>
""", unsafe_allow_html=True)

# ── Login card ────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(
        "<h4 style='color:#F1F5F9; margin:0 0 20px; font-weight:600;'>"
        "Sign in to your account</h4>",
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input(
            "Password", type="password", placeholder="Enter your password"
        )
        submitted = st.form_submit_button(
            "Sign In", use_container_width=True, type="primary"
        )

    if submitted:
        if username and password:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.switch_page("pages/0_Home.py")
        else:
            st.error("Please enter both username and password.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<p style="text-align:center; color:#64748B; font-size:11px; margin-top:40px;">
    &copy; 2026 PACE &nbsp;&middot;&nbsp; University of Arkansas
    &nbsp;&middot;&nbsp; ISYS 43603
</p>
""", unsafe_allow_html=True)
