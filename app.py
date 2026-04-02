# File: app.py
# Pre-login landing page — hero, features, CTA → Sign In.
# The login form lives in pages/1_Login.py.
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

st.set_page_config(
    page_title="PACE — Predictive Accessorial Cost Engine",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

@keyframes pace-in {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}

.stApp {{
    background: none;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    animation: pace-in 0.5s ease-out;
}}

.stApp::before {{
    content: '';
    position: fixed;
    inset: -20px;
    z-index: -1;
    {_bg_props}
    filter: blur(2px);
}}

.stApp::after {{
    content: '';
    position: fixed;
    inset: 0;
    background-image: radial-gradient(rgba(180,80,220,0.06) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none;
    z-index: 0;
}}

#MainMenu, header, footer {{ visibility: hidden; }}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {{ display: none !important; }}

.block-container {{
    position: relative;
    z-index: 1;
    padding-top: 0 !important;
    max-width: 960px;
}}

.pace-hero {{
    text-align: center;
    padding: 72px 0 48px;
}}

.pace-feature-card {{
    background: rgba(12, 6, 30, 0.75);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(180, 80, 220, 0.22);
    border-radius: 12px;
    padding: 24px 20px;
    height: 100%;
}}

.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #9333EA, #C2185B) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 10px 32px !important;
    box-shadow: 0 0 24px rgba(147,51,234,0.45) !important;
    transition: box-shadow 0.2s !important;
}}
.stButton > button[kind="primary"]:hover {{
    box-shadow: 0 0 40px rgba(147,51,234,0.7) !important;
}}

.stButton > button[kind="secondary"] {{
    background: transparent !important;
    border: 1px solid rgba(180,80,220,0.4) !important;
    color: #A78BFA !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}}
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

# ── Hero section ──────────────────────────────────────────────────────────────
_logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as _f:
        _logo_b64 = base64.b64encode(_f.read()).decode()
    st.markdown(
        f"""<div class="pace-hero">
            <div style="display:inline-block; padding:3px; border-radius:50%;
                        background:linear-gradient(135deg,#9333EA,#C2185B);
                        box-shadow:0 0 40px rgba(147,51,234,0.5);">
                <div style="width:120px; height:120px; border-radius:50%;
                            overflow:hidden; background:#0a041a;">
                    <img src="data:image/png;base64,{_logo_b64}"
                         style="width:100%; height:100%; object-fit:cover;" />
                </div>
            </div>
            <h1 style="font-size:48px; font-weight:800; letter-spacing:6px; margin:20px 0 8px;
                       background:linear-gradient(135deg,#A78BFA,#E040FB);
                       -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                P.A.C.E
            </h1>
            <p style="color:#94A3B8; font-size:13px; margin:0 0 16px; letter-spacing:3px;
                      text-transform:uppercase;">
                Predictive Accessorial Cost Engine
            </p>
            <p style="color:#CBD5E1; font-size:17px; max-width:560px; margin:0 auto 36px;
                      line-height:1.6;">
                AI-powered accessorial risk detection for freight carriers —
                score any shipment or carrier in seconds using live FMCSA,
                economic, and weather data.
            </p>
        </div>""",
        unsafe_allow_html=True,
    )
else:
    st.markdown("""
    <div class="pace-hero">
        <div style="font-size:64px; line-height:1;
                    filter:drop-shadow(0 0 24px rgba(147,51,234,0.7));">⬡</div>
        <h1 style="font-size:48px; font-weight:800; letter-spacing:5px; margin:16px 0 8px;
                   background:linear-gradient(135deg,#9333EA,#E040FB);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;">PACE</h1>
        <p style="color:#94A3B8; font-size:12px; margin:0 0 16px; letter-spacing:3px;
                  text-transform:uppercase;">Predictive Accessorial Cost Engine</p>
        <p style="color:#CBD5E1; font-size:17px; max-width:560px; margin:0 auto 36px;
                  line-height:1.6;">
            AI-powered accessorial risk detection for freight carriers —
            score any shipment or carrier in seconds.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── CTA buttons ───────────────────────────────────────────────────────────────
_, cta_col, _ = st.columns([2, 1, 2])
with cta_col:
    if st.button("Sign In →", type="primary", use_container_width=True):
        st.switch_page("pages/1_Login.py")

st.markdown("<br>", unsafe_allow_html=True)

# ── Feature cards ─────────────────────────────────────────────────────────────
f1, f2, f3 = st.columns(3, gap="large")

with f1:
    st.markdown("""
    <div class="pace-feature-card">
        <div style="font-size:28px; margin-bottom:12px;">🔍</div>
        <h4 style="color:#E2E8F0; font-weight:700; margin:0 0 8px; font-size:15px;">
            DOT Number Lookup
        </h4>
        <p style="color:#94A3B8; font-size:13px; margin:0; line-height:1.6;">
            Instantly score any carrier by USDOT number. Live FMCSA data, SMS
            violations, crash history, and economic signals — all in one click.
        </p>
    </div>
    """, unsafe_allow_html=True)

with f2:
    st.markdown("""
    <div class="pace-feature-card">
        <div style="font-size:28px; margin-bottom:12px;">📁</div>
        <h4 style="color:#E2E8F0; font-weight:700; margin:0 0 8px; font-size:15px;">
            Batch Upload & Scoring
        </h4>
        <p style="color:#94A3B8; font-size:13px; margin:0; line-height:1.6;">
            Upload CSV or Excel files to validate, clean, and score thousands of
            shipments at once. Export results with risk scores and charge type predictions.
        </p>
    </div>
    """, unsafe_allow_html=True)

with f3:
    st.markdown("""
    <div class="pace-feature-card">
        <div style="font-size:28px; margin-bottom:12px;">📊</div>
        <h4 style="color:#E2E8F0; font-weight:700; margin:0 0 8px; font-size:15px;">
            Risk Analytics Dashboard
        </h4>
        <p style="color:#94A3B8; font-size:13px; margin:0; line-height:1.6;">
            Interactive dashboards showing carrier risk tiers, accessorial trends,
            cost per mile benchmarks, and route analysis across your network.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<p style="text-align:center; color:#475569; font-size:11px; margin-top:52px; letter-spacing:0.3px;">
    © 2026 PACE &nbsp;·&nbsp; University of Arkansas &nbsp;·&nbsp; ISYS 43603
</p>
""", unsafe_allow_html=True)
