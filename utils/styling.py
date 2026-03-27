"""
utils/styling.py
Dark glass theme — PACE Predictive Accessorial Cost Engine.
Purple-magenta background image, glass cards, glowing accents.
"""
import os
import base64
import streamlit as st


def _bg_css() -> str:
    """Return background CSS props for the ::before blur layer."""
    _root = os.path.dirname(os.path.dirname(__file__))
    img_path = os.path.join(_root, "assets", "background.png")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return (
            f"background-image: url('data:image/png;base64,{b64}');"
            "background-size: cover;"
            "background-position: center center;"
        )
    return (
        "background: "
        "radial-gradient(ellipse 65% 55% at 8% 62%, rgba(120,20,180,0.45) 0%, transparent 58%),"
        "radial-gradient(ellipse 55% 45% at 92% 18%, rgba(200,20,100,0.38) 0%, transparent 52%),"
        "linear-gradient(155deg, #060012 0%, #09021a 40%, #06010f 100%);"
    )


# ── Color tokens ──────────────────────────────────────────────────────────────
# Background / structure
DARK_BASE    = "#060012"
DARK_MID     = "#09021a"
GLASS_BG     = "rgba(12, 6, 30, 0.82)"
GLASS_BORDER = "rgba(180, 80, 220, 0.28)"
GLASS_GLOW   = "rgba(150, 50, 200, 0.18)"

# Accent colors
ACCENT_PURPLE = "#9333EA"
ACCENT_SOFT   = "#A78BFA"

# Text
TEXT_PRIMARY   = "#F1F5F9"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED     = "#64748B"

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

# Risk tier foreground colors (single hex — for text, borders, badges)
TIER_COLORS = {
    "Critical": "#F87171",
    "High":     "#FB923C",
    "Medium":   "#FCD34D",
    "Low":      "#34D399",
    "None":     "#94A3B8",
}

# Risk tier (bg, fg) pairs — for two-tone cell/card styling
TIER_BG_FG = {
    "Critical": ("#7F1D1D",   "#F87171"),
    "High":     (RISK_HIGH_BG, RISK_HIGH_FG),
    "Medium":   (RISK_MED_BG,  RISK_MED_FG),
    "Low":      (RISK_LOW_BG,  RISK_LOW_FG),
    "None":     ("#1E293B",   "#94A3B8"),
}

# Charge type foreground colors
CHARGE_COLORS = {
    "No Charge":            "#34D399",
    "Detention":            "#FCD34D",
    "Safety Surcharge":     "#FB923C",
    "Compliance Fee":       "#F87171",
    "Hazmat Fee":           "#C084FC",
    "High Risk / Multiple": "#EF4444",
}

# Chart theme defaults
CHART_BG      = "#0f0a1e"
CHART_GRID    = "rgba(150,50,200,0.18)"
CHART_AXIS    = "#A78BFA"

# Chart palette
CHART_PURPLE   = "#9333EA"
CHART_BLUE     = "#38BDF8"
CHART_RED      = "#EF4444"
CHART_BURGUNDY = "#9F1239"
CHART_LAVENDER = "#C4B5FD"


def chart_theme(**overrides) -> dict:
    """Dark-themed Plotly layout defaults. Merge with page-specific layout kwargs."""
    base = {
        "plot_bgcolor":  CHART_BG,
        "paper_bgcolor": "#0f0a1e",
        "font":   {"color": CHART_AXIS, "family": "Inter, Segoe UI, sans-serif"},
        "xaxis":  {"gridcolor": CHART_GRID, "color": CHART_AXIS,
                   "linecolor": "rgba(150,50,200,0.25)", "zerolinecolor": "rgba(150,50,200,0.2)"},
        "yaxis":  {"gridcolor": CHART_GRID, "color": CHART_AXIS,
                   "linecolor": "rgba(150,50,200,0.25)", "zerolinecolor": "rgba(150,50,200,0.2)"},
        "legend": {"bgcolor": "rgba(15,10,30,0.7)", "font": {"color": "#FFFFFF"},
                   "bordercolor": "rgba(150,50,200,0.3)", "borderwidth": 1},
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

# Slug map for absolute URL navigation
_NAV_SLUGS = {
    "pages/0_Home.py":              "/Home",
    "pages/1_Dashboard.py":         "/Dashboard",
    "pages/2_Upload.py":            "/Upload",
    "pages/3_Shipments.py":         "/Shipments",
    "pages/4_Cost_Estimate.py":     "/Cost_Estimate",
    "pages/5_Route_Analysis.py":    "/Route_Analysis",
    "pages/6_Carrier_Comparison.py":"/Carrier_Comparison",
    "pages/7_Accessorial_Tracker.py":"/Accessorial_Tracker",
    "pages/8_Admin.py":             "/Admin",
}

# ── Base page CSS (injected on every page) ────────────────────────────────────
_BASE_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

@keyframes pace-in {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}

/* ── App shell — no direct background ── */
.stApp {{
    background: none;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    color: {TEXT_PRIMARY};
    animation: pace-in 0.4s ease-out;
}}

/* ── Blurred background layer ── */
.stApp::before {{
    content: '';
    position: fixed;
    inset: -20px;
    z-index: -1;
    {_bg_css()}
    filter: blur(2px);
}}

/* ── Hide Streamlit chrome and sidebar ── */
#MainMenu, header, footer {{ visibility: hidden; }}
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarNav"],
section[data-testid="stSidebarNav"],
button[kind="header"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"] {{
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
}}

/* ── Page content padding ── */
.block-container {{
    padding-top: 1rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1400px !important;
}}

/* ── Nav bar ── */
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) {{
    background: {NAVY_900} !important;
    border-bottom: 2px solid {NAVY_700} !important;
    padding: 5px 16px !important;
    margin-bottom: 1.5rem !important;
    border-radius: 6px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25) !important;
    align-items: center !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    scrollbar-width: none !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])::-webkit-scrollbar {{
    display: none !important;
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
    color: #FFFFFF !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    text-decoration: none !important;
    white-space: nowrap !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a {{
    padding: 4px 7px !important;
    border-radius: 4px !important;
    display: inline-block !important;
    transition: background 0.15s !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a:hover,
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a:hover p,
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a:hover span {{
    color: #FFFFFF !important;
    background: rgba(255,255,255,0.12) !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
.stButton > button {{
    background: rgba(147,51,234,0.15) !important;
    color: rgba(220,200,255,0.8) !important;
    border: 1px solid rgba(180,80,220,0.4) !important;
    font-size: 12px !important;
    padding: 4px 14px !important;
    min-height: unset !important;
    height: auto !important;
    line-height: 1.4 !important;
    border-radius: 5px !important;
    white-space: nowrap !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
.stButton > button:hover {{
    color: #FFFFFF !important;
    border-color: rgba(255,255,255,0.5) !important;
    background: rgba(255,255,255,0.1) !important;
}}

/* ── Metric Cards ── */
[data-testid="stMetric"] {{
    background: rgba(12, 6, 30, 0.82) !important;
    border: 1px solid rgba(180, 80, 220, 0.28) !important;
    border-radius: 12px !important;
    padding: 20px 24px !important;
    box-shadow: 0 0 18px rgba(150,50,200,0.12), 0 4px 16px rgba(0,0,0,0.35) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
}}
[data-testid="stMetricLabel"] > div {{
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.8px !important;
    color: {ACCENT_SOFT} !important;
    text-transform: uppercase !important;
}}
[data-testid="stMetricValue"] > div {{
    font-size: 26px !important;
    font-weight: 700 !important;
    color: {TEXT_PRIMARY} !important;
}}
[data-testid="stMetricDelta"] > div {{
    font-size: 12px !important;
    color: {TEXT_SECONDARY} !important;
}}

/* ── Buttons ── */
.stButton > button[kind="primary"] {{
    background-color: {NAVY_900} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}
.stButton > button[kind="primary"]:hover {{
    box-shadow: 0 0 28px rgba(147,51,234,0.65) !important;
    background: linear-gradient(135deg, #A855F7, #E91E8C) !important;
}}
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
p, .stMarkdown p {{ color: #CBD5E1 !important; }}
strong, b {{ color: #F1F5F9 !important; }}
.stCaption, [data-testid="stCaptionContainer"] p {{ color: #94A3B8 !important; font-size: 13px !important; }}
.stDivider hr {{ border-color: rgba(180,80,220,0.25) !important; }}

/* ── Plotly chart containers ── */
[data-testid="stPlotlyChart"] {{
    background: transparent !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}}
[data-testid="stPlotlyChart"] > div {{
    background: transparent !important;
}}

/* ── Hide Plotly modebar ── */
.modebar-container {{ display: none !important; }}

/* ── Hide "Running..." status widget ── */
[data-testid="stStatusWidget"] {{ display: none !important; }}

/* ── Expand (⤢) buttons ── */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="baseButton-secondary"] {{
    background: rgba(20, 8, 50, 0.7) !important;
    border: 1px solid rgba(180,80,220,0.3) !important;
    border-radius: 10px !important;
    color: {ACCENT_SOFT} !important;
    font-size: 16px !important;
    padding: 6px 10px !important;
    line-height: 1 !important;
    box-shadow: 0 0 12px rgba(150,50,200,0.12) !important;
    backdrop-filter: blur(10px) !important;
    transition: box-shadow 0.2s, border-color 0.2s, color 0.2s !important;
}}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="baseButton-secondary"]:hover {{
    background: rgba(30, 10, 70, 0.85) !important;
    border-color: rgba(180,80,220,0.6) !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 20px rgba(150,50,200,0.35) !important;
}}

/* ── Chart container hover elevation ── */
[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stPlotlyChart"]) > div {{
    transition: transform 0.3s cubic-bezier(0.34,1.56,0.64,1),
                box-shadow 0.3s ease !important;
    cursor: pointer;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stPlotlyChart"]) > div:hover {{
    transform: translateY(-6px) scale(1.012) !important;
    box-shadow: 0 20px 60px rgba(150,50,200,0.5),
                0 0 40px rgba(150,50,200,0.3),
                0 0 0 1px rgba(180,80,220,0.45) !important;
}}

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
    border: 1px solid rgba(180,80,220,0.3) !important;
    border-radius: 0 !important;
    overflow: hidden !important;
}}
[data-testid="stDataFrame"] ::-webkit-scrollbar {{
    width: 6px !important;
    height: 6px !important;
}}
[data-testid="stDataFrame"] ::-webkit-scrollbar-track {{
    background: #0f0a1e !important;
}}
[data-testid="stDataFrame"] ::-webkit-scrollbar-thumb {{
    background: rgba(147,51,234,0.5) !important;
    border-radius: 0 !important;
}}

/* ── Alerts ── */
[data-testid="stAlert"] {{ border-radius: 8px !important; }}
</style>
"""


def inject_css() -> None:
    """Inject PACE base CSS. Call at the top of every page."""
    st.markdown(_BASE_CSS, unsafe_allow_html=True)


def top_nav(username: str) -> None:
    """
    Render the top navigation bar using absolute URL anchors to avoid
    relative-path issues when the session base is /login/.
    Call this at the top of every authenticated page, after inject_css().
    """
    logo_col, *page_cols, user_col, out_col = st.columns(
        [1.4] + [1.0] * 9 + [1.0, 0.7]
    )

    with logo_col:
        st.markdown(
            "<div style='color:#FFFFFF; font-size:15px; font-weight:700; "
            "letter-spacing:1px; padding:4px 0;'>📦 PACE</div>",
            unsafe_allow_html=True,
        )

    for col, (label, page) in zip(page_cols, _NAV_PAGES):
        slug = _NAV_SLUGS.get(page, "/")
        with col:
            st.markdown(
                f"<a href='{slug}' target='_self' style='"
                f"color:#FFFFFF;font-size:13px;font-weight:700;"
                f"text-decoration:none;padding:4px 7px;border-radius:4px;"
                f"display:inline-block;transition:background 0.15s;'"
                f" onmouseover=\"this.style.background='rgba(255,255,255,0.12)'\""
                f" onmouseout=\"this.style.background='transparent'\">"
                f"{label}</a>",
                unsafe_allow_html=True,
            )

    with user_col:
        st.markdown(
            f"<div style='color:rgba(255,255,255,0.7); font-size:11px; "
            f"text-align:right; padding:5px 4px 0;'>👤 {username}</div>",
            unsafe_allow_html=True,
        )

    with out_col:
        if st.button("Sign Out", key="nav_signout"):
            from auth_utils import logout
            logout()


def risk_badge_html(tier: str) -> str:
    """Return an HTML badge string for a risk tier label."""
    colors = {
        "High":   (RISK_HIGH_BG, RISK_HIGH_FG),
        "Medium": (RISK_MED_BG,  RISK_MED_FG),
        "Low":    (RISK_LOW_BG,  RISK_LOW_FG),
    }
    bg, fg = colors.get(tier, ("#F3F4F6", "#6B7280"))
    return (
        f'<span style="background:{bg}; color:{fg}; padding:3px 10px; '
        f'border-radius:4px; font-size:11px; font-weight:600;">{tier}</span>'
    )


# Keep for backwards compatibility — now a no-op
def sidebar_header(username: str) -> None:
    pass
