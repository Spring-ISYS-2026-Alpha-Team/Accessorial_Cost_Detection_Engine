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
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Hide sidebar entirely on the login page
st.markdown("""
<style>
[data-testid="stSidebar"]       { display: none; }
[data-testid="collapsedControl"] { display: none; }
</style>
""", unsafe_allow_html=True)

# Already logged in → route by role
if check_auth():
    if st.session_state.get("role") == "admin":
        st.switch_page("pages/8_Admin.py")
    else:
        st.switch_page("pages/0_Home.py")

# ── Pre-warm ML model in background (so Cost Estimate page loads instantly) ───
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
        pass  # Silent — never block the login page

_prewarm_model()

# ── Splash video (drop assets/splash.mp4 to enable) ──────────────────────────
_splash = os.path.join(os.path.dirname(__file__), "assets", "splash.mp4")
if os.path.exists(_splash):
    st.markdown("""
    <style>
    .splash-video { border-radius:12px; overflow:hidden; margin:0 auto 24px; display:block; max-width:480px; }
    .splash-video video { width:100%; border-radius:12px; }
    </style>
    """, unsafe_allow_html=True)
    with open(_splash, "rb") as _f:
        _video_bytes = _f.read()
    st.markdown('<div class="splash-video">', unsafe_allow_html=True)
    st.video(_video_bytes, autoplay=True, loop=True, muted=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    # Default logo header
    st.markdown("""
    <div style="text-align:center; padding:48px 0 28px;">
        <div style="font-size:48px; line-height:1;">📦</div>
        <h1 style="font-size:34px; font-weight:700; color:#0F2B4A;
                   margin:10px 0 4px; letter-spacing:2px;">PACE</h1>
        <p style="color:#6B7280; font-size:14px; margin:0; letter-spacing:0.3px;">
            Predictive Accessorial Cost Engine
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Login card ────────────────────────────────────────────────────────────────
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

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<p style="text-align:center; color:#9CA3AF; font-size:11px; margin-top:40px;">
    © 2026 PACE &nbsp;·&nbsp; University of Arkansas &nbsp;·&nbsp; ISYS 43603
</p>
""", unsafe_allow_html=True)
