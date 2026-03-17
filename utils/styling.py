"""Global styling utilities for PACE.

Mara-inspired editorial system:
- Dark neutral background
- Warm off-white typography
- Gold accent for subtle states
"""
import os
import base64
import streamlit as st


def _bg_css() -> str:
    """Return background CSS props for the ::before layer."""
    return "background:#0e0e0e;"


# ── Color tokens (Mara-inspired) ─────────────────────────────────────────────
# Background / structure
BG_APP       = "#0e0e0e"  # near black
SURFACE_SUBTLE = "rgba(255,255,255,0.03)"
SURFACE_LIFT   = "rgba(255,255,255,0.04)"
DIVIDER_SOFT   = "rgba(255,255,255,0.08)"
CARD_TOP_BORDER = "rgba(255,255,255,0.10)"

# Typography colors
TEXT_PRIMARY   = "#f0f0ee"
TEXT_MUTED     = "rgba(240,240,238,0.45)"

# Accent (used sparingly)
ACCENT_GOLD    = "#c8a96e"

# Risk tier colors — softened, non-neon
RISK_HIGH_BG  = "rgba(190, 62, 62, 0.12)"
RISK_HIGH_FG  = "#f2a0a0"
RISK_MED_BG   = "rgba(200, 150, 80, 0.12)"
RISK_MED_FG   = "#e7c599"
RISK_LOW_BG   = "rgba(80, 150, 120, 0.12)"
RISK_LOW_FG   = "#a6d7b8"

# Chart theme defaults (neutral)
CHART_BG      = "rgba(0,0,0,0.4)"
CHART_GRID    = "rgba(240,240,238,0.10)"
CHART_AXIS    = TEXT_MUTED

# Chart palette (muted)
CHART_PURPLE   = "#5b5664"
CHART_BLUE     = "#7d8fa3"
CHART_RED      = "#b56a6a"
CHART_BURGUNDY = "#7a4b52"
CHART_LAVENDER = "#9a8fa6"


def chart_theme(**overrides) -> dict:
    """Dark-themed Plotly layout defaults. Merge with page-specific layout kwargs."""
    base = {
        "plot_bgcolor":  CHART_BG,
        "paper_bgcolor": BG_APP,
        "font":   {"color": CHART_AXIS, "family": "DM Sans, system-ui, -apple-system, BlinkMacSystemFont, sans-serif"},
        "xaxis":  {"gridcolor": CHART_GRID, "color": CHART_AXIS},
        "yaxis":  {"gridcolor": CHART_GRID, "color": CHART_AXIS},
        "legend": {"bgcolor": "rgba(14,14,14,0.9)", "font": {"color": TEXT_MUTED}},
    }
    base.update(overrides)
    return base


def _role_normalize(role: str | None) -> str:
    """Normalize legacy roles to the new RBAC names."""
    r = (role or "").strip().lower()
    if r in {"admin"}:
        return "admin"
    # legacy role names in this repo
    if r in {"user", "pending", ""}:
        return "analyst"
    if r in {"analyst", "viewer"}:
        return r
    return "analyst"


def nav_pages_for_role(role: str | None) -> list[tuple[str, str]]:
    """Return nav items for a given role (RBAC)."""
    r = _role_normalize(role)
    base = [
        ("Home",        "pages/0_Home.py"),
        ("Dashboards",  "pages/1_Dashboard.py"),
        ("Upload",      "pages/2_Upload.py"),
        ("Risk Est.",   "pages/4_Cost_Estimate.py"),
        ("Routes",      "pages/5_Route_Analysis.py"),
        ("Carriers",    "pages/6_Carrier_Comparison.py"),
        ("Accessorial", "pages/7_Accessorial_Tracker.py"),
    ]
    if r == "admin":
        base.append(("Admin", "pages/8_Admin.py"))
    return base

# ── Base page CSS (injected on every page) ────────────────────────────────────
_BASE_CSS = f"""
<style>
/* Typography imports */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&display=swap');

html, body, .stApp {{
    background: none;
    color: {TEXT_PRIMARY};
    font-family: "Söhne", "DM Sans", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 16px;
    line-height: 1.7;
}}

.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    z-index: -1;
    {_bg_css()}
}}

/* Hide Streamlit chrome and sidebar */
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

/* Content width and section spacing */
.block-container {{
    max-width: 1200px !important;
    margin: 0 auto !important;
    padding-left: 80px !important;
    padding-right: 80px !important;
}}

section[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stVerticalBlock"]) {{
    padding-top: 120px !important;
    padding-bottom: 120px !important;
    border-top: 1px solid {DIVIDER_SOFT};
}}

/* Sticky nav */
[data-testid="stHorizontalBlock"]:has([data-testid='pace-nav']) {{
    position: sticky;
    top: 0;
    z-index: 20;
    background: rgba(14,14,14,0.88) !important;
    backdrop-filter: blur(16px);
    padding: 10px 0 !important;
    margin-bottom: 40px !important;
    border-bottom: 1px solid {DIVIDER_SOFT};
}}
[data-testid="stHorizontalBlock"]:has([data-testid='pace-nav'])
> div[data-testid="stColumn"] > div {{
    padding: 0 !important;
    gap: 0 !important;
}}

[data-testid="stHorizontalBlock"]:has([data-testid='pace-nav'])
.stButton > button {{
    background: transparent !important;
    color: {TEXT_PRIMARY} !important;
    border: 1px solid rgba(240,240,238,0.3) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 13px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 14px 32px !important;
    border-radius: 4px !important;
    white-space: nowrap !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid='pace-nav'])
.stButton > button:hover {{
    border-color: {ACCENT_GOLD} !important;
    color: {ACCENT_GOLD} !important;
}}

/* Hide caret icon on nav popover so only menu lines show */
[data-testid="stHorizontalBlock"]:has([data-testid='pace-nav'])
button svg {{
    display: none !important;
}}

/* Nav links (page_link) */
[data-testid="stHorizontalBlock"]:has([data-testid='pace-nav']) a {{
    background: transparent !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 0 14px !important;
    font-size: 13px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: {TEXT_MUTED} !important;
    position: relative;
}}
[data-testid="stHorizontalBlock"]:has([data-testid='pace-nav']) a::after {{
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: -6px;
    height: 1px;
    background: {ACCENT_GOLD};
    transform: scaleX(0);
    transform-origin: center;
    transition: transform 160ms ease-out;
}}
[data-testid="stHorizontalBlock"]:has([data-testid='pace-nav']) a:hover::after {{
    transform: scaleX(1);
}}
[data-testid="stHorizontalBlock"]:has([data-testid='pace-nav']) a[aria-current="page"] {{
    color: {TEXT_PRIMARY} !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid='pace-nav']) a[aria-current="page"]::after {{
    transform: scaleX(1);
}}

/* Global buttons (primary style) */
.stButton > button {{
    background: transparent !important;
    color: {TEXT_PRIMARY} !important;
    border: 1px solid rgba(240,240,238,0.3) !important;
    border-radius: 4px !important;
    font-size: 13px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 14px 32px !important;
}}
.stButton > button:hover {{
    border-color: {ACCENT_GOLD} !important;
    color: {ACCENT_GOLD} !important;
}}

/* Secondary text-only buttons (link-like) */
button[kind="secondary"] {{
    border: none !important;
    background: transparent !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}}

/* Headings */
h1, h2, h3, h4, h5, h6 {{
    color: {TEXT_PRIMARY} !important;
    font-family: "Tiempos Headline", "Georgia", serif !important;
    font-weight: 300 !important;
    letter-spacing: -0.03em !important;
}}
h1 {{
    font-size: clamp(2.5rem, 5vw, 4rem) !important;
}}
h2, h3 {{
    font-size: 1.75rem !important;
    font-weight: 400 !important;
}}

p, .stMarkdown p {{
    color: {TEXT_MUTED} !important;
    font-family: "Söhne", "DM Sans", system-ui, -apple-system, BlinkMacSystemFont, sans-serif !important;
}}

.stCaption, [data-testid="stCaptionContainer"] p {{
    color: {TEXT_MUTED} !important;
    font-size: 13px !important;
}}

.stDivider hr {{
    border-color: {DIVIDER_SOFT} !important;
}}

/* Metrics: typographic only */
[data-testid="stMetric"] {{
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    box-shadow: none !important;
}}
[data-testid="stMetricLabel"] > div {{
    font-size: 12px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: {TEXT_MUTED} !important;
}}
[data-testid="stMetricValue"] > div {{
    font-size: 32px !important;
    font-weight: 400 !important;
    color: {TEXT_PRIMARY} !important;
}}

/* Cards / containers */
[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background: {SURFACE_SUBTLE} !important;
    border-top: 1px solid {CARD_TOP_BORDER} !important;
    border-radius: 4px !important;
    box-shadow: none !important;
}}

/* DataFrames */
[data-testid="stDataFrame"] {{
    border: none !important;
    border-radius: 0 !important;
}}

/* Inputs */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div,
[data-baseweb="input"],
[data-baseweb="select"] {{
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid {DIVIDER_SOFT} !important;
    border-radius: 4px !important;
    color: {TEXT_PRIMARY} !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {{
    border-color: {ACCENT_GOLD} !important;
    box-shadow: none !important;
}}

/* Plotly */
[data-testid="stPlotlyChart"] > div {{
    background: transparent !important;
}}
.modebar-container {{ display: none !important; }}

/* Alerts */
[data-testid="stAlert"] {{
    border-radius: 4px !important;
    background: {SURFACE_LIFT} !important;
    border: 1px solid {DIVIDER_SOFT} !important;
}}
</style>
"""


def inject_css() -> None:
    """Inject PACE base CSS. Call at the top of every page."""
    st.markdown(_BASE_CSS, unsafe_allow_html=True)


def top_nav(username: str) -> None:
    """
    Render the top navigation bar using st.page_link() so that navigation
    stays within the existing WebSocket session (no page reload, no auth loss).
    Call this at the top of every authenticated page, after inject_css().
    """
    role = _role_normalize(st.session_state.get("role"))
    pages = nav_pages_for_role(role)

    with st.container():
        # Logo left, compact hamburger + user + signout on the right.
        left, right = st.columns([1.5, 3.5])

        with left:
            st.markdown(
                "<div data-testid='pace-nav' style=\"font-family:'Tiempos Headline','Georgia',serif;"
                "font-size:18px;letter-spacing:0.08em;text-transform:uppercase;\">PACE</div>",
                unsafe_allow_html=True,
            )

        with right:
            menu_col, user_col, out_col = st.columns([0.6, 1.4, 1.0])

            with menu_col:
                with st.popover("≡", use_container_width=True):
                    for label, page in pages:
                        st.page_link(page, label=label)

            with user_col:
                st.markdown(
                    f"<div style='color:{TEXT_MUTED}; font-size:13px; "
                    f"letter-spacing:0.08em; text-transform:uppercase; text-align:right;'>"
                    f"{username} · {role.title()}</div>",
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
