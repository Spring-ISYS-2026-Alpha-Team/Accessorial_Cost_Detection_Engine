# File: app.py
import os
import base64
import streamlit as st
from auth_utils import check_auth


def _bg_css() -> str:
    """Return background CSS props for the ::before blur layer (login page)."""
    return "background:#0e0e1a;"


_bg_props = _bg_css()

# ── Fallback users if DB unavailable ──────────────────────────────────────────
_FALLBACK = {
    "admin": {"password": "admin", "role": "admin"},
    "user":  {"password": "user",  "role": "analyst"},
}

st.set_page_config(
    page_title="PACE — Sign In",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&display=swap');

.stApp {
    background: none;
    font-family: "Söhne","DM Sans",system-ui,-apple-system,BlinkMacSystemFont,sans-serif;
}

.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    z-index: -1;
    """ + _bg_props + """
}

#MainMenu, header, footer { visibility: hidden; }
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

.block-container {
    position: relative;
    z-index: 1;
    max-width: 420px !important;
    margin: 0 auto !important;
    padding-top: 48px !important;
}

/* Login card */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: rgba(255,255,255,0.03) !important;
    border-top: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 4px !important;
    box-shadow: none !important;
}

/* Form inputs */
[data-testid="stTextInput"] input, [data-baseweb="input"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 4px !important;
    color: #f0f0ee !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #c8a96e !important;
    box-shadow: none !important;
    outline: none !important;
}
[data-testid="stTextInput"] label {
    color: rgba(240,240,238,0.45) !important;
    font-size: 12px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}
[data-testid="stForm"] { background: transparent !important; border: none !important; }

/* Buttons — match editorial primary */
.stButton > button, .stFormSubmitButton > button {
    background: transparent !important;
    color: #f0f0ee !important;
    border: 1px solid rgba(240,240,238,0.3) !important;
    border-radius: 4px !important;
    font-size: 13px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 14px 32px !important;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    border-color: #c8a96e !important;
    color: #c8a96e !important;
}

h4, h5 { color: #f0f0ee !important; }
p, .stMarkdown p { color: rgba(240,240,238,0.45) !important; }
[data-testid="stAlert"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 4px !important;
    color: #f0f0ee !important;
}
</style>
""", unsafe_allow_html=True)

# Already logged in → route by role (skip loading if already pre-loaded)
if check_auth():
    if st.session_state.get("_data_preloaded"):
        if st.session_state.get("role") == "admin":
            st.switch_page("pages/8_Admin.py")
        else:
            st.switch_page("pages/0_Home.py")
    else:
        st.session_state["post_load_dest"] = (
            "pages/8_Admin.py" if st.session_state.get("role") == "admin"
            else "pages/0_Home.py"
        )
        st.switch_page("pages/loading.py")
else:
    # First-time / unauthenticated visits should land on the public Home page
    if not st.session_state.get("show_login"):
        st.switch_page("pages/9_Landing.py")

# Public entry points (UI refresh)
top_links = st.columns([1, 1, 1])
with top_links[0]:
    st.page_link("pages/9_Landing.py", label="Home")
with top_links[1]:
    st.page_link("pages/10_Create_Account.py", label="Create Account")
with top_links[2]:
    st.markdown("")

# ── Logo header ───────────────────────────────────────────────────────────────
_logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as _f:
        _logo_b64 = base64.b64encode(_f.read()).decode()
    st.markdown(
        f"""<div style="text-align:center; padding:32px 0 24px;">
            <img src="data:image/png;base64,{_logo_b64}"
                 style="width:200px; max-width:60vw; height:auto;" />
            <h1 style="font-family:'Tiempos Headline','Georgia',serif;
                       font-size:28px; font-weight:300; letter-spacing:0.08em;
                       margin:18px 0 4px; text-transform:uppercase; color:#f0f0ee;">
                PACE
            </h1>
            <p style="color:rgba(240,240,238,0.45); font-size:12px; margin:0;
                      letter-spacing:0.12em; text-transform:uppercase;">
                Predictive Accessorial Cost Engine
            </p>
        </div>""",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        "<div style='text-align:center; padding:40px 0 24px;'>"
        "<div style=\"font-family:'Tiempos Headline','Georgia',serif;"
        "font-size:28px; font-weight:300; letter-spacing:0.08em; text-transform:uppercase; color:#f0f0ee;\">"
        "PACE</div>"
        "<p style='color:rgba(240,240,238,0.45); font-size:12px; margin:4px 0 0;"
        "letter-spacing:0.12em; text-transform:uppercase;'>Predictive Accessorial Cost Engine</p>"
        "</div>",
        unsafe_allow_html=True,
    )

# ── Login card ─────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("""
    <div style="padding:0 2px 12px;">
        <h3 style="font-family:'Tiempos Headline','Georgia',serif;
                   font-size:22px; font-weight:300; margin:0 0 4px;
                   letter-spacing:-0.03em; color:#f0f0ee;">
            Sign in to PACE
        </h3>
        <p style="color:rgba(240,240,238,0.45); font-size:13px; margin:0;">
            Predictive Accessorial Cost Engine
        </p>
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
                st.switch_page("pages/loading.py")
            else:
                st.error("Please enter both username and password.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<p style="text-align:center; color:rgba(240,240,238,0.45); font-size:11px; margin-top:28px; letter-spacing:0.3px;">
    © 2026 PACE &nbsp;·&nbsp; University of Arkansas &nbsp;·&nbsp; ISYS 43603
</p>
""", unsafe_allow_html=True)
