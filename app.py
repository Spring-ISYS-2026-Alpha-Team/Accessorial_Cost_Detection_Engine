# File: app.py
import os
import base64
import streamlit as st
from auth_utils import check_auth


def _bg_css() -> str:
    """Return background CSS props for the ::before blur layer."""
    img_path = os.path.join(os.path.dirname(__file__), "assets", "background.png")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return (
            f"background-image:url('data:image/png;base64,{b64}');"
            "background-size:cover;background-position:center;"
        )
    return "background:linear-gradient(155deg,#060012 0%,#09021a 40%,#06010f 100%);"


_bg_props = _bg_css()

# ── Fallback users if DB unavailable ──────────────────────────────────────────
# Passwords loaded from environment variables — never hardcoded.
# Defaults are intentionally weak placeholders; override via .env on the server.
_FALLBACK = {
    os.environ.get("PACE_ADMIN_USER", "admin"): {
        "password": os.environ.get("PACE_ADMIN_PASS", "admin"),
        "role": "admin",
    },
    os.environ.get("PACE_USER_USER", "user"): {
        "password": os.environ.get("PACE_USER_PASS", "user"),
        "role": "user",
    },
}

st.set_page_config(
    page_title="PACE — Sign In",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

@keyframes pace-in {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── App shell — no direct background, handled by ::before ── */
.stApp {
    background: none;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    animation: pace-in 0.4s ease-out;
}

/* ── Blurred background layer ── */
.stApp::before {
    content: '';
    position: fixed;
    inset: -20px;
    z-index: -1;
    """ + _bg_props + """
    filter: blur(2px);
}

/* ── Dot grid overlay ── */
.stApp::after {
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
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: rgba(147,51,234,0.8) !important;
    box-shadow: 0 0 0 3px rgba(147,51,234,0.18) !important;
    outline: none !important;
}
[data-testid="stTextInput"] label { color: #A78BFA !important; font-size: 13px !important; font-weight: 500 !important; letter-spacing: 0.3px !important; }
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

# Already logged in → only redirect if user deliberately navigated to /login.
# Do NOT redirect if Streamlit is just running app.py as part of multipage routing.
# We detect "deliberate login visit" by checking if there's no referrer page in session.
if check_auth():
    # Only auto-redirect on first load after login (loading screen sets _data_preloaded)
    # Don't redirect on subsequent app.py runs caused by multipage navigation
    if not st.session_state.get("_data_preloaded"):
        st.session_state["post_load_dest"] = (
            "pages/8_Admin.py" if st.session_state.get("role") == "admin"
            else "pages/0_Home.py"
        )
        st.switch_page("pages/loading.py")

# ── Logo header ───────────────────────────────────────────────────────────────
_logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as _f:
        _logo_b64 = base64.b64encode(_f.read()).decode()
    st.markdown(
        f"""<div style="text-align:center; padding:36px 0 24px;">
            <div style="display:inline-block; padding:3px; border-radius:50%;
                        background:linear-gradient(135deg,#9333EA,#C2185B);
                        box-shadow:0 0 32px rgba(147,51,234,0.45);">
                <div style="width:108px; height:108px; border-radius:50%;
                            overflow:hidden; background:#0a041a;">
                    <img src="data:image/png;base64,{_logo_b64}"
                         style="width:100%; height:100%; object-fit:cover;" />
                </div>
            </div>
            <h1 style="font-size:26px; font-weight:800; letter-spacing:5px; margin:14px 0 4px;
                       background:linear-gradient(135deg,#A78BFA,#E040FB);
                       -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                P.A.C.E
            </h1>
            <p style="color:#64748B; font-size:11px; margin:0; letter-spacing:2px;
                      text-transform:uppercase;">
                Predictive Accessorial Cost Engine
            </p>
        </div>""",
        unsafe_allow_html=True,
    )
else:
    st.markdown("""
    <div style="text-align:center; padding:52px 0 32px;">
        <div style="font-size:52px; line-height:1; filter:drop-shadow(0 0 18px rgba(147,51,234,0.7));">⬡</div>
        <h1 style="font-size:36px; font-weight:800; letter-spacing:3px; margin:12px 0 4px;
                   background:linear-gradient(135deg,#9333EA,#E040FB);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;">PACE</h1>
        <p style="color:#64748B; font-size:11px; margin:0; letter-spacing:2px; text-transform:uppercase;">
            Predictive Accessorial Cost Engine
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Login card ─────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("""
    <div style="margin:-4px -4px 16px -4px;">
        <div style="height:3px; border-radius:3px 3px 0 0;
                    background:linear-gradient(90deg,#9333EA,#C2185B,transparent);"></div>
    </div>
    <div style="padding:0 2px 12px;">
        <h3 style="color:#F1F5F9; font-weight:700; font-size:20px; margin:0 0 4px;
                   letter-spacing:0.2px;">Welcome back</h3>
        <p style="color:#64748B; font-size:13px; margin:0;">Sign in to your PACE account</p>
    </div>
    """, unsafe_allow_html=True)

    # Show error passed back from loading screen (bad DB credentials)
    _err = st.session_state.pop("_login_error", None)
    if _err:
        st.error(_err)

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input(
            "Password", type="password", placeholder="Enter your password"
        )
        submitted = st.form_submit_button(
            "Sign In", width="stretch", type="primary"
        )
        if submitted:
            if username and password:
                u, p = username.strip(), password

                # Check fallback dict first — instant, no DB call
                if u in _FALLBACK and p == _FALLBACK[u]["password"]:
                    role = _FALLBACK[u]["role"]
                else:
                    # Non-fallback user: defer DB verification to loading screen
                    role = "pending"
                    st.session_state["_pending_password"] = p

                st.session_state["authenticated"] = True
                st.session_state["username"] = u
                st.session_state["role"] = role
                st.session_state["_data_preloaded"] = False
                st.session_state["post_load_dest"] = (
                    "pages/8_Admin.py" if role == "admin" else "pages/0_Home.py"
                )
                # st.switch_page inside st.form doesn't work reliably —
                # set a flag and navigate outside the form block
                st.session_state["_do_login_redirect"] = True
                st.rerun()
            else:
                st.error("Please enter both username and password.")

# ── Post-form redirect (must be outside form block) ───────────────────────────
if st.session_state.pop("_do_login_redirect", False):
    st.switch_page("pages/loading.py")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<p style="text-align:center; color:#475569; font-size:11px; margin-top:28px; letter-spacing:0.3px;">
    © 2026 PACE &nbsp;·&nbsp; University of Arkansas &nbsp;·&nbsp; ISYS 43603
</p>
""", unsafe_allow_html=True)
