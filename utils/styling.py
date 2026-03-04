"""
utils/styling.py
Shared CSS theme and fixed top navigation bar for all PACE pages.
"""
import streamlit as st

# ── Color tokens ─────────────────────────────────────────────────────────────
NAVY_900  = "#0F2B4A"
NAVY_700  = "#1A3F6F"
NAVY_500  = "#2563A8"
NAVY_100  = "#DBEAFE"

RISK_LOW_BG   = "#D1FAE5"
RISK_LOW_FG   = "#059669"
RISK_MED_BG   = "#FEF3C7"
RISK_MED_FG   = "#D97706"
RISK_HIGH_BG  = "#FEE2E2"
RISK_HIGH_FG  = "#DC2626"

# ── Navigation pages (file paths for st.page_link — preserves session state) ──
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

# ── Base page CSS (injected on every page) ────────────────────────────────────
_BASE_CSS = f"""
<style>
/* ── Global ───────────────────────────────────────── */
.stApp {{
    background-color: #F9FAFB;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}}

/* ── Hide Streamlit chrome and sidebar ────────────── */
#MainMenu, header, footer {{ visibility: hidden; }}
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
section[data-testid="stSidebarNav"] {{
    display: none !important;
}}

/* ── Page content padding ──────────────────────────── */
.block-container {{
    padding-top: 1rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1400px !important;
}}

/* ── Nav bar: style the columns row that contains page links ── */
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) {{
    background: {NAVY_900} !important;
    border-bottom: 2px solid {NAVY_700} !important;
    padding: 5px 16px !important;
    margin-bottom: 1.5rem !important;
    border-radius: 6px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25) !important;
    align-items: center !important;
}}

/* Tighten column padding inside nav */
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
> div[data-testid="stColumn"] > div {{
    padding: 0 2px !important;
    gap: 0 !important;
}}

/* Reset default page link card styling */
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    min-height: unset !important;
}}

/* Nav link text — target a, p, span to cover all Streamlit versions */
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a,
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a p,
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a span,
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
[data-testid="stPageLink"] a div {{
    color: #FFFFFF !important;
    font-size: 15px !important;
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

/* Sign Out button inside nav */
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
.stButton > button {{
    background: transparent !important;
    color: rgba(255,255,255,0.7) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    font-size: 11px !important;
    padding: 2px 8px !important;
    min-height: unset !important;
    height: 26px !important;
    line-height: 1 !important;
    white-space: nowrap !important;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])
.stButton > button:hover {{
    color: #FFFFFF !important;
    border-color: rgba(255,255,255,0.5) !important;
    background: rgba(255,255,255,0.1) !important;
}}

/* ── Metric Cards ─────────────────────────────────── */
[data-testid="stMetric"] {{
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 20px 24px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}}
[data-testid="stMetricLabel"] > div {{
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.6px;
    color: #6B7280 !important;
    text-transform: uppercase;
}}
[data-testid="stMetricValue"] > div {{
    font-size: 26px !important;
    font-weight: 700 !important;
    color: #111827 !important;
}}

/* ── Primary Buttons ─────────────────────────────── */
.stButton > button[kind="primary"] {{
    background-color: {NAVY_900} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}
.stButton > button[kind="primary"]:hover {{
    background-color: {NAVY_700} !important;
    border: none !important;
}}

/* ── Headings ────────────────────────────────────── */
h1 {{ color: #111827 !important; font-weight: 700 !important; }}
h2 {{ color: #1F2937 !important; font-weight: 600 !important; }}
h3 {{ color: #374151 !important; font-weight: 600 !important; }}

/* ── Dataframe ───────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border: 1px solid #E5E7EB !important;
    border-radius: 8px;
    overflow: hidden;
}}

/* ── File uploader ───────────────────────────────── */
[data-testid="stFileUploader"] {{
    border: 2px dashed #D1D5DB;
    border-radius: 12px;
    background-color: #F9FAFB;
    padding: 16px;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {NAVY_500};
    background-color: {NAVY_100};
}}

/* ── Alerts ──────────────────────────────────────── */
[data-testid="stAlert"] {{ border-radius: 8px !important; }}
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
    # Logo | nav links × 8 | user label | sign-out button
    logo_col, *page_cols, user_col, out_col = st.columns(
        [1.4] + [1.0] * 8 + [1.0, 0.7]
    )

    with logo_col:
        st.markdown(
            f"<div style='color:#FFFFFF; font-size:15px; font-weight:700; "
            f"letter-spacing:1px; padding:4px 0;'>📦 PACE</div>",
            unsafe_allow_html=True,
        )

    for col, (label, page) in zip(page_cols, _NAV_PAGES):
        with col:
            st.page_link(page, label=label)

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
