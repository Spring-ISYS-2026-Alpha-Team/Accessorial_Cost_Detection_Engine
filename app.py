# File: app.py
import os
import streamlit as st
from auth_utils import check_auth
from utils.database import get_connection, verify_pace_user

# ── Fallback users if DB unavailable ──────────────────────────────────────────
_FALLBACK = {
    "admin": {"password": "admin", "role": "admin"},
    "user":  {"password": "user",  "role": "user"},
}

st.set_page_config(
    page_title="PACE — Sign In",
    page_icon="⬡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Dark glass login page CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.stApp {
    background:
        radial-gradient(ellipse 65% 55% at 8%  62%, rgba(120,20,180,0.45) 0%, transparent 58%),
        radial-gradient(ellipse 55% 45% at 92% 18%, rgba(200,20,100,0.38) 0%, transparent 52%),
        radial-gradient(ellipse 45% 40% at 78% 82%, rgba(100,10,160,0.28) 0%, transparent 48%),
        linear-gradient(155deg, #060012 0%, #09021a 40%, #06010f 100%);
    background-attachment: fixed;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: radial-gradient(rgba(180,80,220,0.06) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none;
    z-index: 0;
}
#MainMenu, header, footer { visibility: hidden; }
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

.block-container {
    position: relative;
    z-index: 1;
    padding-top: 0 !important;
}

/* Glass login card */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: rgba(12, 6, 30, 0.82) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(180, 80, 220, 0.28) !important;
    border-radius: 14px !important;
    box-shadow: 0 0 24px rgba(150,50,200,0.18), 0 4px 32px rgba(0,0,0,0.5) !important;
}

/* Form inputs */
[data-testid="stTextInput"] input, [data-baseweb="input"] {
    background: rgba(20,8,50,0.75) !important;
    border: 1px solid rgba(180,80,220,0.35) !important;
    border-radius: 8px !important;
    color: #F1F5F9 !important;
}
[data-testid="stTextInput"] label { color: #A78BFA !important; font-size: 13px !important; }
[data-testid="stForm"] { background: transparent !important; border: none !important; }

/* Sign In button */
.stButton > button[kind="primary"], .stFormSubmitButton > button {
    background: linear-gradient(135deg, #9333EA, #C2185B) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    box-shadow: 0 0 20px rgba(147,51,234,0.45) !important;
    transition: box-shadow 0.2s !important;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button:hover {
    box-shadow: 0 0 36px rgba(147,51,234,0.7) !important;
}

h4, h5 { color: #E2E8F0 !important; }
p, .stMarkdown p { color: #94A3B8 !important; }
[data-testid="stAlert"] {
    background: rgba(20,8,50,0.7) !important;
    border: 1px solid rgba(180,80,220,0.3) !important;
    border-radius: 8px !important;
    color: #F1F5F9 !important;
}
</style>
""", unsafe_allow_html=True)

# Already logged in → route by role
if check_auth():
    if st.session_state.get("role") == "admin":
        st.switch_page("pages/8_Admin.py")
    else:
        st.switch_page("pages/0_Home.py")

# ── Pre-warm ML model in background ───────────────────────────────────────────
def _prewarm_model():
    try:
        from utils.database import get_shipments
        from utils.mock_data import generate_mock_shipments
        from utils.cost_model import get_cost_model
        conn = get_connection()
        df = get_shipments(conn) if conn is not None else None
        if df is None or df.empty:
            df = generate_mock_shipments(1000)
        get_cost_model(len(df), df)
    except Exception:
        pass

_prewarm_model()

# ── Splash video or logo header ────────────────────────────────────────────────
_splash = os.path.join(os.path.dirname(__file__), "assets", "splash.mp4")
if os.path.exists(_splash):
    with open(_splash, "rb") as _f:
        _video_bytes = _f.read()
    st.markdown('<div style="border-radius:12px;overflow:hidden;margin:32px auto 0;max-width:480px;">', unsafe_allow_html=True)
    st.video(_video_bytes, autoplay=True, loop=True, muted=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align:center; padding:52px 0 32px;">
        <div style="font-size:52px; line-height:1; filter:drop-shadow(0 0 18px rgba(147,51,234,0.7));">⬡</div>
        <h1 style="font-size:36px; font-weight:800; letter-spacing:3px; margin:12px 0 4px;
                   background:linear-gradient(135deg,#9333EA,#E040FB);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;">PACE</h1>
        <p style="color:#64748B; font-size:13px; margin:0; letter-spacing:0.5px;">
            Predictive Accessorial Cost Engine
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Login card ─────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Sign in to your account")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input(
            "Password", type="password", placeholder="Enter your password"
        )
        submitted = st.form_submit_button(
            "Sign In", use_container_width=True, type="primary"
        )

    if submitted:
        u = (username or "").strip()
        p = password or ""
        if not u or not p:
            st.error("Please enter both username and password.")
        else:
            conn = get_connection()
            role = verify_pace_user(conn, u, p)
            if role is None and u in _FALLBACK and p == _FALLBACK[u]["password"]:
                role = _FALLBACK[u]["role"]
            if role:
                st.session_state["authenticated"] = True
                st.session_state["username"] = u
                st.session_state["role"] = role
                if role == "admin":
                    st.switch_page("pages/8_Admin.py")
                else:
                    st.switch_page("pages/0_Home.py")
            else:
                st.error("Invalid username or password.")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<p style="text-align:center; color:#334155; font-size:11px; margin-top:36px;">
    © 2026 PACE &nbsp;·&nbsp; University of Arkansas &nbsp;·&nbsp; ISYS 43603
</p>
""", unsafe_allow_html=True)
