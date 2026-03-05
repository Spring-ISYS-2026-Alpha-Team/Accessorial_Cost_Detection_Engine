"""
utils/styling.py
Unified dark theme CSS and top navigation bar for all PACE pages.
"""
import streamlit as st

# ── Color tokens ──────────────────────────────────────────────────────────────
NAVY_BG    = "#161638"
CARD_BG    = "#1B435E"
BORDER     = "#38667E"
PLUM       = "#563457"
DEEP_PLUM  = "#3A2B50"

TEXT_PRIMARY   = "#F1F5F9"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED     = "#64748B"

BRIGHT_TEAL = "#2DD4BF"
CORAL       = "#FF6B6B"
LAVENDER    = "#A78BFA"
GOLD        = "#FBBF24"

# Legacy aliases
NAVY_900 = NAVY_BG
NAVY_700 = CARD_BG
NAVY_500 = BORDER
NAVY_100 = DEEP_PLUM

RISK_LOW_BG  = "#1A3A2E"
RISK_LOW_FG  = BRIGHT_TEAL
RISK_MED_BG  = "#3A2B1A"
RISK_MED_FG  = GOLD
RISK_HIGH_BG = "#3D1A1A"
RISK_HIGH_FG = CORAL

# ── Navigation pages (text labels only — no emojis) ───────────────────────────
_NAV_PAGES = [
    ("Home",        "pages/0_Home.py"),
    ("Dashboard",   "pages/1_Dashboard.py"),
    ("Upload",      "pages/2_Upload.py"),
    ("Shipments",   "pages/3_Shipments.py"),
    ("Cost Est.",   "pages/4_Cost_Estimate.py"),
    ("Routes",      "pages/5_Route_Analysis.py"),
    ("Carriers",    "pages/6_Carrier_Comparison.py"),
    ("Accessorial", "pages/7_Accessorial_Tracker.py"),
]

# ── Inline SVG icons ──────────────────────────────────────────────────────────
# Package / box icon (Feather-style) — used as PACE logo
_SVG_PACKAGE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" '
    'viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:middle;">'
    '<line x1="16.5" y1="9.4" x2="7.5" y2="4.21"/>'
    '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8'
    'a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>'
    '<polyline points="3.27 6.96 12 12.01 20.73 6.96"/>'
    '<line x1="12" y1="22.08" x2="12" y2="12"/>'
    '</svg>'
)

# User icon — shown next to username in nav
_SVG_USER = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" '
    'viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:middle;margin-right:4px;">'
    '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
    '<circle cx="12" cy="7" r="4"/>'
    '</svg>'
)

# Check / warning / error icons for validation feedback
SVG_CHECK = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
    'viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" stroke-width="2.5" '
    'stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:middle;margin-right:6px;">'
    '<polyline points="20 6 9 17 4 12"/>'
    '</svg>'
)
SVG_WARN = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
    'viewBox="0 0 24 24" fill="none" stroke="#FBBF24" stroke-width="2.5" '
    'stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:middle;margin-right:6px;">'
    '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94'
    'a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
    '<line x1="12" y1="9" x2="12" y2="13"/>'
    '<line x1="12" y1="17" x2="12.01" y2="17"/>'
    '</svg>'
)
SVG_ERROR = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
    'viewBox="0 0 24 24" fill="none" stroke="#FF6B6B" stroke-width="2.5" '
    'stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:middle;margin-right:6px;">'
    '<circle cx="12" cy="12" r="10"/>'
    '<line x1="15" y1="9" x2="9" y2="15"/>'
    '<line x1="9" y1="9" x2="15" y2="15"/>'
    '</svg>'
)

# ── Shared Plotly dark layout ─────────────────────────────────────────────────
DARK_LAYOUT = dict(
    plot_bgcolor=CARD_BG,
    paper_bgcolor=CARD_BG,
    font=dict(
        color=TEXT_PRIMARY,
        family="-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
        size=12,
    ),
    xaxis=dict(
        gridcolor=BORDER,
        tickfont=dict(color=TEXT_SECONDARY, size=11),
        title_font=dict(color=TEXT_SECONDARY, size=12),
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor=BORDER,
        tickfont=dict(color=TEXT_SECONDARY, size=11),
        title_font=dict(color=TEXT_SECONDARY, size=12),
        zeroline=False,
    ),
)

# ── Base page CSS ─────────────────────────────────────────────────────────────
_BASE_CSS = f"""
<style>
.stApp {{
    background-color: {NAVY_BG} !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
}}
#MainMenu, header, footer {{ visibility: hidden; }}
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
section[data-testid="stSidebarNav"] {{
    display: none !important;
}}
.block-container {{
    padding-top: 1rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1400px !important;
}}
.stApp, .stApp p, .stApp span, .stApp label,
.stApp .stMarkdown, .stApp [data-testid="stText"] {{
    color: {TEXT_PRIMARY} !important;
}}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
    color: {TEXT_PRIMARY} !important;
}}
.stApp .stCaption, .stApp small,
.stApp [data-testid="stCaptionContainer"] {{
    color: {TEXT_SECONDARY} !important;
}}
h1 {{ color: {TEXT_PRIMARY} !important; font-weight: 700 !important; }}
h2 {{ color: {TEXT_PRIMARY} !important; font-weight: 600 !important; }}
h3 {{ color: {TEXT_PRIMARY} !important; font-weight: 600 !important; }}
hr {{ border-color: {BORDER} !important; }}

/* ── Nav bar ── */
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) {{
    background: {NAVY_BG} !important;
    border-bottom: 2px solid {CARD_BG} !important;
    padding: 5px 16px !important;
    margin-bottom: 1.5rem !important;
    border-radius: 6px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.5) !important;
    align-items: center !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 999 !important;
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
    color: {TEXT_PRIMARY} !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    text-decoration: none !important;
    white-space: nowrap !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a {{
    padding: 4px 8px !important;
    border-radius: 6px !important;
    display: inline-block !important;
    transition: background 0.2s ease, color 0.2s ease !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a:hover,
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a:hover p,
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a:hover span {{
    color: {BRIGHT_TEAL} !important;
    background: rgba(56, 102, 126, 0.35) !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
.stButton > button {{
    background: {PLUM} !important;
    color: {TEXT_PRIMARY} !important;
    border: 1px solid {PLUM} !important;
    font-size: 10px !important;
    padding: 2px 10px !important;
    min-height: unset !important;
    height: 26px !important;
    line-height: 1 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    max-width: 80px !important;
    border-radius: 4px !important;
    transition: background 0.2s ease !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
.stButton > button:hover {{
    background: {DEEP_PLUM} !important;
    border-color: {LAVENDER} !important;
}}

/* ── Metric cards ── */
[data-testid="stMetric"] {{
    background-color: {CARD_BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    padding: 20px 24px !important;
    box-shadow: 0 2px 16px rgba(0,0,0,0.3) !important;
    transition: transform 0.2s ease, border-color 0.2s ease !important;
}}
[data-testid="stMetric"]:hover {{
    transform: translateY(-2px) !important;
    border-color: {BRIGHT_TEAL} !important;
}}
[data-testid="stMetricLabel"] > div {{
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    color: {TEXT_SECONDARY} !important;
    text-transform: uppercase !important;
}}
[data-testid="stMetricValue"] > div {{
    font-size: 26px !important;
    font-weight: 700 !important;
    color: {TEXT_PRIMARY} !important;
}}
[data-testid="stMetricDelta"] > div {{ font-size: 12px !important; }}

/* ── Card containers ── */
[data-testid="stVerticalBlock"] > div[data-testid="element-container"]
> div > div > div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {CARD_BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 16px rgba(0,0,0,0.3) !important;
    transition: border-color 0.2s ease !important;
}}
[data-testid="stVerticalBlock"] > div[data-testid="element-container"]
> div > div > div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    border-color: {BRIGHT_TEAL} !important;
}}
div:has(> [data-testid="stVerticalBlockBorderWrapper"]) {{
    border-color: {BORDER} !important;
}}

/* ── Buttons ── */
.stButton > button[kind="primary"] {{
    background-color: {PLUM} !important;
    color: {TEXT_PRIMARY} !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: background 0.2s ease, transform 0.2s ease !important;
}}
.stButton > button[kind="primary"]:hover {{
    background-color: {DEEP_PLUM} !important;
    transform: translateY(-1px) !important;
}}
.stButton > button {{
    background-color: {CARD_BG} !important;
    color: {TEXT_PRIMARY} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    transition: background 0.2s ease, border-color 0.2s ease !important;
}}
.stButton > button:hover {{
    background-color: {BORDER} !important;
    border-color: {BRIGHT_TEAL} !important;
}}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}}

/* ── File uploader ── */
[data-testid="stFileUploader"] {{
    border: 2px dashed {BORDER} !important;
    border-radius: 12px !important;
    background-color: {CARD_BG} !important;
    padding: 16px !important;
    transition: border-color 0.2s ease !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {BRIGHT_TEAL} !important;
}}

/* ── Alerts ── */
[data-testid="stAlert"] {{ border-radius: 8px !important; }}

/* ── Expander ── */
[data-testid="stExpander"] {{
    background: {CARD_BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
}}
[data-testid="stExpander"] details,
.streamlit-expanderHeader {{
    background: {CARD_BG} !important;
    border-color: {BORDER} !important;
    color: {TEXT_PRIMARY} !important;
}}
[data-testid="stExpander"] summary {{ color: {TEXT_PRIMARY} !important; }}
[data-testid="stExpander"] details summary span {{
    color: {TEXT_PRIMARY} !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    overflow: visible !important;
}}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input,
.stTextArea > div > div > textarea {{
    background: {CARD_BG} !important;
    color: {TEXT_PRIMARY} !important;
    border-color: {BORDER} !important;
    border-radius: 8px !important;
    transition: border-color 0.2s ease !important;
}}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {{
    border-color: {BRIGHT_TEAL} !important;
    box-shadow: 0 0 0 2px rgba(45,212,191,0.15) !important;
}}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {{
    color: {TEXT_MUTED} !important;
}}
.stSelectbox > div > div,
.stMultiSelect > div > div {{
    background: {CARD_BG} !important;
    border-color: {BORDER} !important;
    color: {TEXT_PRIMARY} !important;
    border-radius: 8px !important;
}}
[data-testid="stMultiSelect"],
[data-testid="stDateInput"] {{ color: {TEXT_PRIMARY} !important; }}
.stDateInput > div > div > input {{
    background: {CARD_BG} !important;
    color: {TEXT_PRIMARY} !important;
    border-color: {BORDER} !important;
}}

/* ── Controls ── */
[data-testid="stToggle"] label {{ color: {TEXT_PRIMARY} !important; }}
[data-testid="stRadio"] label {{ color: {TEXT_PRIMARY} !important; }}
[data-testid="stSlider"] label {{ color: {TEXT_PRIMARY} !important; }}
.stProgress > div > div > div {{ background-color: {BRIGHT_TEAL} !important; }}
.stSpinner > div {{ border-top-color: {BRIGHT_TEAL} !important; }}
</style>
"""


def inject_css() -> None:
    st.markdown(_BASE_CSS, unsafe_allow_html=True)


def top_nav(username: str) -> None:
    logo_col, *page_cols, user_col, out_col = st.columns(
        [1.2] + [1.1] * 8 + [1.0, 0.7]
    )

    with logo_col:
        st.markdown(
            f"<div style='display:flex; align-items:center; gap:8px; padding:4px 0;'>"
            f"{_SVG_PACKAGE}"
            f"<span style='color:{BRIGHT_TEAL}; font-size:15px; font-weight:700; "
            f"letter-spacing:1px;'>PACE</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    for col, (label, page) in zip(page_cols, _NAV_PAGES):
        with col:
            st.page_link(page, label=label)

    with user_col:
        st.markdown(
            f"<div style='color:{TEXT_SECONDARY}; font-size:11px; "
            f"text-align:right; padding:5px 4px 0;'>"
            f"{_SVG_USER}{username}</div>",
            unsafe_allow_html=True,
        )

    with out_col:
        if st.button("Sign Out", key="nav_signout"):
            from auth_utils import logout
            logout()


def risk_badge_html(tier: str) -> str:
    colors = {
        "High":   (RISK_HIGH_BG, RISK_HIGH_FG),
        "Medium": (RISK_MED_BG,  RISK_MED_FG),
        "Low":    (RISK_LOW_BG,  RISK_LOW_FG),
    }
    bg, fg = colors.get(tier, (CARD_BG, TEXT_MUTED))
    return (
        f'<span style="background:{bg}; color:{fg}; padding:3px 10px; '
        f'border-radius:4px; font-size:11px; font-weight:600;">{tier}</span>'
    )


def sidebar_header(username: str) -> None:
    pass
