"""
utils/styling.py
Dark glass theme — PACE Predictive Accessorial Cost Engine.
Purple-magenta gradient background, glass cards, glowing accents.
"""
import streamlit as st

# ── Color tokens ──────────────────────────────────────────────────────────────
# Background / structure
DARK_BASE   = "#060012"
DARK_MID    = "#09021a"
GLASS_BG    = "rgba(12, 6, 30, 0.82)"
GLASS_BORDER = "rgba(180, 80, 220, 0.28)"
GLASS_GLOW  = "rgba(150, 50, 200, 0.18)"

# Accent palette
ACCENT_PURPLE = "#9333EA"   # primary purple
ACCENT_HOT    = "#E040FB"   # magenta/pink
ACCENT_PINK   = "#C2185B"   # deep pink
ACCENT_SOFT   = "#A78BFA"   # soft lavender

# Text
TEXT_PRIMARY  = "#F1F5F9"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED    = "#64748B"

# Legacy color tokens — kept so existing pages don't break
NAVY_900 = "#0A0520"
NAVY_700 = "#1A0A40"
NAVY_500 = ACCENT_PURPLE    # purple (was blue)
NAVY_100 = "#2D1B4E"        # dark purple fill

# Risk tier colors — glowing on dark bg
RISK_HIGH_BG  = "rgba(220, 38, 38, 0.18)"
RISK_HIGH_FG  = "#F87171"
RISK_MED_BG   = "rgba(217, 119, 6, 0.18)"
RISK_MED_FG   = "#FCD34D"
RISK_LOW_BG   = "rgba(5, 150, 105, 0.18)"
RISK_LOW_FG   = "#34D399"

# Chart theme defaults (pass as **chart_theme() in update_layout)
def chart_theme(**overrides) -> dict:
    """Dark-themed Plotly layout defaults. Merge with page-specific layout kwargs."""
    base = {
        "plot_bgcolor":  "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "font":   {"color": TEXT_SECONDARY, "family": "Inter, Segoe UI, sans-serif"},
        "xaxis":  {"gridcolor": "rgba(150,50,200,0.15)", "color": TEXT_SECONDARY,
                   "linecolor": "rgba(150,50,200,0.2)", "zerolinecolor": "rgba(150,50,200,0.2)"},
        "yaxis":  {"gridcolor": "rgba(150,50,200,0.15)", "color": TEXT_SECONDARY,
                   "linecolor": "rgba(150,50,200,0.2)", "zerolinecolor": "rgba(150,50,200,0.2)"},
        "legend": {"bgcolor": "rgba(0,0,0,0)", "font": {"color": TEXT_SECONDARY}},
    }
    base.update(overrides)
    return base


# ── Navigation pages ──────────────────────────────────────────────────────────
_NAV_PAGES = [
    ("Home",        "pages/0_Home.py"),
    ("Dashboard",   "pages/1_Dashboard.py"),
    ("Upload",      "pages/2_Upload.py"),
    ("Shipments",   "pages/3_Shipments.py"),
    ("Cost Est.",   "pages/4_Cost_Estimate.py"),
    ("Routes",      "pages/5_Route_Analysis.py"),
    ("Carriers",    "pages/6_Carrier_Comparison.py"),
    ("Accessorial", "pages/7_Accessorial_Tracker.py"),
    ("Admin",       "pages/8_Admin.py"),
]

# ── Base CSS ──────────────────────────────────────────────────────────────────
_BASE_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Global background — dark purple/magenta gradient ── */
.stApp {{
    background:
        radial-gradient(ellipse 65% 55% at 8%  62%, rgba(120,20,180,0.45) 0%, transparent 58%),
        radial-gradient(ellipse 55% 45% at 92% 18%, rgba(200,20,100,0.38) 0%, transparent 52%),
        radial-gradient(ellipse 45% 40% at 78% 82%, rgba(100,10,160,0.28) 0%, transparent 48%),
        radial-gradient(ellipse 35% 35% at 45% 35%, rgba(80,10,140,0.22) 0%, transparent 42%),
        linear-gradient(155deg, #060012 0%, #09021a 40%, #06010f 100%);
    background-attachment: fixed;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    color: {TEXT_PRIMARY};
    /* Subtle dot grid overlay */
    background-size: auto, auto, auto, auto, auto;
}}

/* Dot particle overlay */
.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    background-image: radial-gradient(rgba(180,80,220,0.06) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none;
    z-index: 0;
}}

/* ── Hide Streamlit chrome and sidebar ── */
#MainMenu, header, footer {{ visibility: hidden; }}
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
section[data-testid="stSidebarNav"] {{
    display: none !important;
}}

/* ── Page content padding ── */
.block-container {{
    padding-top: 1rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1400px !important;
    position: relative;
    z-index: 1;
}}

/* ── Glass card containers ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background: {GLASS_BG} !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid {GLASS_BORDER} !important;
    border-radius: 12px !important;
    box-shadow: 0 0 24px {GLASS_GLOW}, 0 4px 32px rgba(0,0,0,0.45) !important;
}}

/* ── Nav bar ── */
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) {{
    background: rgba(6,0,18,0.92) !important;
    border-bottom: 1px solid rgba(180,80,220,0.35) !important;
    padding: 5px 16px !important;
    margin-bottom: 1.5rem !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 20px rgba(150,50,200,0.25) !important;
    align-items: center !important;
    backdrop-filter: blur(20px) !important;
}}

[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
> div[data-testid="stColumn"] > div {{
    padding: 0 2px !important;
    gap: 0 !important;
}}

[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    min-height: unset !important;
}}

[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a,
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a p,
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a span,
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a div {{
    color: rgba(220,200,255,0.88) !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-decoration: none !important;
    white-space: nowrap !important;
    letter-spacing: 0.3px !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a {{
    padding: 4px 8px !important;
    border-radius: 5px !important;
    display: inline-block !important;
    transition: background 0.15s, color 0.15s !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a:hover,
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a:hover p,
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a:hover span {{
    color: #FFFFFF !important;
    background: rgba(147,51,234,0.25) !important;
}}

/* Sign Out button inside nav */
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
.stButton > button {{
    background: rgba(147,51,234,0.15) !important;
    color: rgba(220,200,255,0.8) !important;
    border: 1px solid rgba(180,80,220,0.4) !important;
    font-size: 11px !important;
    padding: 2px 8px !important;
    min-height: unset !important;
    height: 26px !important;
    border-radius: 5px !important;
    white-space: nowrap !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
.stButton > button:hover {{
    color: #FFFFFF !important;
    background: rgba(147,51,234,0.35) !important;
    border-color: rgba(224,64,251,0.6) !important;
}}

/* ── Metric Cards ── */
[data-testid="stMetric"] {{
    background: rgba(20, 8, 50, 0.7) !important;
    border: 1px solid rgba(180,80,220,0.3) !important;
    border-radius: 12px !important;
    padding: 20px 24px !important;
    box-shadow: 0 0 18px rgba(150,50,200,0.12) !important;
    backdrop-filter: blur(10px) !important;
}}
[data-testid="stMetricLabel"] > div {{
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.6px !important;
    color: {ACCENT_SOFT} !important;
    text-transform: uppercase !important;
}}
[data-testid="stMetricValue"] > div {{
    font-size: 26px !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
}}
[data-testid="stMetricDelta"] > div {{
    font-size: 12px !important;
}}

/* ── Primary Buttons ── */
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {ACCENT_PURPLE}, {ACCENT_PINK}) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    box-shadow: 0 0 16px rgba(147,51,234,0.4) !important;
    transition: box-shadow 0.2s !important;
}}
.stButton > button[kind="primary"]:hover {{
    box-shadow: 0 0 28px rgba(147,51,234,0.65) !important;
    background: linear-gradient(135deg, #A855F7, #E91E8C) !important;
}}

/* Secondary buttons */
.stButton > button:not([kind="primary"]) {{
    background: rgba(30,10,60,0.7) !important;
    color: {TEXT_PRIMARY} !important;
    border: 1px solid rgba(180,80,220,0.35) !important;
    border-radius: 8px !important;
}}
.stButton > button:not([kind="primary"]):hover {{
    background: rgba(60,20,100,0.7) !important;
    border-color: rgba(224,64,251,0.55) !important;
}}

/* ── Headings ── */
h1 {{ color: #FFFFFF !important; font-weight: 700 !important; text-shadow: 0 0 30px rgba(180,80,220,0.4); }}
h2 {{ color: #F1F5F9 !important; font-weight: 600 !important; }}
h3 {{ color: #E2E8F0 !important; font-weight: 600 !important; }}
h4, h5, h6 {{ color: #CBD5E1 !important; font-weight: 600 !important; }}
p, .stMarkdown p {{ color: {TEXT_SECONDARY} !important; }}
.stCaption {{ color: {TEXT_MUTED} !important; }}
.stDivider hr {{ border-color: rgba(180,80,220,0.25) !important; }}

/* ── Inputs & Forms ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div,
[data-baseweb="input"],
[data-baseweb="select"] {{
    background: rgba(20,8,50,0.75) !important;
    border: 1px solid rgba(180,80,220,0.35) !important;
    border-radius: 8px !important;
    color: {TEXT_PRIMARY} !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {{
    border-color: {ACCENT_PURPLE} !important;
    box-shadow: 0 0 12px rgba(147,51,234,0.3) !important;
}}
[data-testid="stForm"] {{
    background: transparent !important;
    border: none !important;
}}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
    border: 1px solid rgba(180,80,220,0.25) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}}
.stDataFrame thead th {{
    background: rgba(30,10,60,0.9) !important;
    color: {ACCENT_SOFT} !important;
}}
.stDataFrame tbody tr {{
    background: rgba(15,6,35,0.7) !important;
    color: {TEXT_PRIMARY} !important;
}}
.stDataFrame tbody tr:hover {{
    background: rgba(50,20,90,0.7) !important;
}}

/* ── Tabs ── */
[data-baseweb="tab-list"] {{
    background: rgba(15,6,35,0.6) !important;
    border-radius: 8px !important;
    border: 1px solid rgba(180,80,220,0.2) !important;
}}
[data-baseweb="tab"] {{
    color: {TEXT_SECONDARY} !important;
}}
[aria-selected="true"][data-baseweb="tab"] {{
    color: #FFFFFF !important;
    background: rgba(147,51,234,0.3) !important;
}}

/* ── Alerts / Info / Success / Error ── */
[data-testid="stAlert"] {{
    border-radius: 8px !important;
    background: rgba(20,8,50,0.7) !important;
    border: 1px solid rgba(180,80,220,0.3) !important;
    color: {TEXT_PRIMARY} !important;
}}

/* ── Expanders ── */
[data-testid="stExpander"] {{
    background: rgba(15,6,35,0.6) !important;
    border: 1px solid rgba(180,80,220,0.2) !important;
    border-radius: 8px !important;
}}

/* ── File uploader ── */
[data-testid="stFileUploader"] {{
    border: 2px dashed rgba(147,51,234,0.4) !important;
    border-radius: 12px !important;
    background: rgba(20,8,50,0.5) !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {ACCENT_HOT} !important;
    background: rgba(30,10,70,0.6) !important;
}}

/* ── Selectbox dropdown ── */
[data-baseweb="popover"] {{
    background: rgba(15,6,35,0.97) !important;
    border: 1px solid rgba(180,80,220,0.4) !important;
    border-radius: 8px !important;
    backdrop-filter: blur(20px) !important;
}}
[role="option"] {{
    color: {TEXT_PRIMARY} !important;
}}
[role="option"]:hover {{
    background: rgba(147,51,234,0.25) !important;
}}

/* ── Slider ── */
[data-testid="stSlider"] [role="slider"] {{
    background: {ACCENT_PURPLE} !important;
    box-shadow: 0 0 10px rgba(147,51,234,0.6) !important;
}}
</style>
"""


def inject_css() -> None:
    """Inject PACE dark glass CSS. Call at the top of every page."""
    st.markdown(_BASE_CSS, unsafe_allow_html=True)


def top_nav(username: str) -> None:
    """
    Render the top navigation bar using st.page_link() so that navigation
    stays within the existing WebSocket session (no page reload, no auth loss).
    """
    logo_col, *page_cols, user_col, out_col = st.columns(
        [1.4] + [1.0] * 9 + [1.0, 0.7]
    )

    with logo_col:
        st.markdown(
            "<div style='background:linear-gradient(135deg,#9333EA,#E040FB);"
            "-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
            "font-size:15px;font-weight:800;letter-spacing:1.5px;padding:4px 0;'>"
            "⬡ PACE</div>",
            unsafe_allow_html=True,
        )

    for col, (label, page) in zip(page_cols, _NAV_PAGES):
        with col:
            st.page_link(page, label=label)

    with user_col:
        st.markdown(
            f"<div style='color:rgba(167,139,250,0.85);font-size:11px;"
            f"text-align:right;padding:5px 4px 0;'>◎ {username}</div>",
            unsafe_allow_html=True,
        )

    with out_col:
        if st.button("Sign Out", key="nav_signout"):
            from auth_utils import logout
            logout()


def risk_badge_html(tier: str) -> str:
    """Return an HTML badge string for a risk tier label."""
    colors = {
        "High":   (RISK_HIGH_BG, RISK_HIGH_FG,  "rgba(248,113,113,0.4)"),
        "Medium": (RISK_MED_BG,  RISK_MED_FG,   "rgba(252,211,77,0.3)"),
        "Low":    (RISK_LOW_BG,  RISK_LOW_FG,   "rgba(52,211,153,0.3)"),
    }
    bg, fg, shadow = colors.get(tier, ("rgba(30,10,60,0.4)", "#94A3B8", "transparent"))
    return (
        f'<span style="background:{bg};color:{fg};padding:3px 10px;'
        f'border-radius:4px;font-size:11px;font-weight:600;'
        f'box-shadow:0 0 8px {shadow};border:1px solid {shadow};">{tier}</span>'
    )


# Keep for backwards compatibility
def sidebar_header(username: str) -> None:
    pass
