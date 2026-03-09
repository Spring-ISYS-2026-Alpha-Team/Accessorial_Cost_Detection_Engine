# PACE — Project Snapshot (main branch)
**Predictive Accessorial Cost Detection Engine**
University of Arkansas · ISYS 43603 · Team Alpha · Spring 2026

---

## Project Overview

PACE is a Streamlit multi-page web app that predicts accessorial charges on freight shipments.
It uses a Random Forest ML model, Azure SQL backend (not yet wired to pages), and synthetic mock data for all current pages.

**Tech stack:** Python 3.10+, Streamlit 1.54, Plotly, pandas, scikit-learn, pyodbc, Azure SQL
**Deployment:** Streamlit Cloud watching the `dev` branch
**GitHub:** https://github.com/Spring-ISYS-2026-Alpha-Team/Accessorial_Cost_Detection_Engine
**Git flow:** feature branches -> dev -> main

---

## File Structure

```
app.py                          Login page (any credentials accepted — no real auth yet)
auth_utils.py                   check_auth(), logout() using st.session_state
pages/
  0_Home.py                     KPI dashboard, 6 charts, hero section
  1_Dashboard.py                Risk dashboard, filters, carrier/facility/tier charts, shipments table
  2_Upload.py                   CSV upload, validation, mock risk scoring
  3_Shipments.py                List + detail view, risk factor breakdown, recommendations
  4_Cost_Estimate.py            Random Forest ML cost predictor with 95% CI
  5_Route_Analysis.py           Lane analysis — most expensive, most efficient, scatter, table
  6_Carrier_Comparison.py       Carrier metrics, bar charts, radar chart
  7_Accessorial_Tracker.py      Accessorial cost tracker — donut, carrier/facility bars, trend
utils/
  styling.py                    inject_css(), top_nav(username), color tokens, risk_badge_html()
  mock_data.py                  generate_mock_shipments(n, seed) — 300 synthetic rows
  database.py                   Azure SQL connection helpers (NOT yet used by any page)
assets/
  shippingcontainers.jpg        Hero background image
tests/
  test_validation_and_upload.py BROKEN — imports non-existent functions from app.py
.github/workflows/ci.yml        4 CI jobs: lint (flake8), security (bandit), install, test (pytest)
```

---

## Current Theme (main branch)

Pages use a **light theme** (`#F9FAFB` background, navy `#0F2B4A` accents).
Dashboard (page 1) has its own inline dark CSS (`#0B1120` background).
Navigation: sticky navy bar across all pages via `top_nav()`.

A full **dark theme redesign** is on the `feature/home-page-redesign` branch (not yet merged).

---

## Mock Data Schema

`generate_mock_shipments()` returns 300 rows with these columns:

| Column | Type | Notes |
|---|---|---|
| shipment_id | str | SHP-00001 format |
| ship_date | str | YYYY-MM-DD, last 90 days |
| carrier | str | 6 carriers |
| facility | str | 5 facilities |
| origin_city | str | 8 cities |
| destination_city | str | 8 cities |
| lane | str | "Origin -> Dest" |
| weight_lbs | int | 500 – 44,000 |
| miles | int | 50 – 2,400 |
| base_freight_usd | float | weight * 0.04 + miles * 0.80 + noise |
| accessorial_charge_usd | float | $200-850 (High), $50-350 (Med), $0 (Low) |
| total_cost_usd | float | base + accessorial |
| cost_per_mile | float | total / miles |
| risk_score | float | 0.05 – 0.98 |
| risk_tier | str | Low (<0.34), Medium (0.34-0.67), High (>=0.67) |
| accessorial_type | str | Detention, Lumper Fee, Layover, Re-delivery, None |

**6 Carriers:** XPO Logistics, J.B. Hunt, Werner Enterprises, Schneider National, Old Dominion, FedEx Freight
**5 Facilities:** Warehouse A - Dallas, Warehouse B - Memphis, Distribution Center C - Atlanta, Warehouse D - Chicago, Cold Storage E - Houston

---

## Azure SQL Database

- **Server:** essql1.database.windows.net
- **Database:** ISYS43603_Spring2026_Sec02_Alice_db
- **Connection:** `utils/database.py` reads from `st.secrets["azure_sql"]` (cloud) or `.env` (local)
- **Status:** NOT yet wired to any page — all pages use mock data

---

## Known Issues / Backlog

- **Tests broken:** `tests/test_validation_and_upload.py` imports `validate_shipments_df`, `CFG`, `add_target`, `score_shipments`, `train_baseline_on_synthetic` from `app.py` — none exist there
- **No real auth:** Login accepts any username/password
- **No DB integration:** All pages use `utils/mock_data.py`

---

## Source Code — All Files (main branch)

---

### `app.py`

```python
# File: app.py
import streamlit as st
from auth_utils import check_auth

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

# Already logged in → go straight to home
if check_auth():
    st.switch_page("pages/0_Home.py")

# ── Page layout ───────────────────────────────────────────────────────────────
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
        if username and password:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.switch_page("pages/0_Home.py")
        else:
            st.error("Please enter both username and password.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<p style="text-align:center; color:#9CA3AF; font-size:11px; margin-top:40px;">
    © 2026 PACE · University of Arkansas · ISYS 43603
</p>
""", unsafe_allow_html=True)
```

---

### `auth_utils.py`

```python
# File: auth_utils.py
import streamlit as st

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.cache_data.clear()
    st.cache_resource.clear()
    st.switch_page("app.py")

def check_auth():
    return st.session_state.get('authenticated', False)
```

---

### `utils/styling.py`

```python
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
]

# ── Base page CSS ─────────────────────────────────────────────────────────────
# (light theme: #F9FAFB background, navy accents)
# Full CSS omitted for brevity — key points:
#   - hides Streamlit sidebar + chrome
#   - nav bar: navy #0F2B4A background, white bold text, hover highlight
#   - metric cards: white bg, #E5E7EB border, 20-24px padding
#   - primary buttons: navy bg
#   - file uploader: dashed border, hover to blue tint
_BASE_CSS = "..." # ~200 lines of CSS

def inject_css() -> None:
    """Inject PACE base CSS. Call at the top of every page."""
    st.markdown(_BASE_CSS, unsafe_allow_html=True)

def top_nav(username: str) -> None:
    """Render the top navigation bar. Call after inject_css() on every page."""
    logo_col, *page_cols, user_col, out_col = st.columns(
        [1.4] + [1.0] * 8 + [1.0, 0.7]
    )
    with logo_col:
        st.markdown(f"<div style='color:#FFFFFF; font-size:15px; font-weight:700; "
                    f"letter-spacing:1px; padding:4px 0;'>📦 PACE</div>",
                    unsafe_allow_html=True)
    for col, (label, page) in zip(page_cols, _NAV_PAGES):
        with col:
            st.page_link(page, label=label)
    with user_col:
        st.markdown(f"<div style='color:rgba(255,255,255,0.7); font-size:11px; "
                    f"text-align:right; padding:5px 4px 0;'>👤 {username}</div>",
                    unsafe_allow_html=True)
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
    return (f'<span style="background:{bg}; color:{fg}; padding:3px 10px; '
            f'border-radius:4px; font-size:11px; font-weight:600;">{tier}</span>')

def sidebar_header(username: str) -> None:
    pass  # no-op, kept for backwards compatibility
```

---

### `utils/mock_data.py`

```python
"""
utils/mock_data.py
Generates synthetic shipment data for PACE demo/development use.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

CARRIERS = [
    "XPO Logistics", "J.B. Hunt", "Werner Enterprises",
    "Schneider National", "Old Dominion", "FedEx Freight",
]

FACILITIES = [
    "Warehouse A - Dallas", "Warehouse B - Memphis",
    "Distribution Center C - Atlanta", "Warehouse D - Chicago",
    "Cold Storage E - Houston",
]

ORIGIN_CITIES = [
    "Dallas, TX", "Chicago, IL", "Los Angeles, CA", "New York, NY",
    "Atlanta, GA", "Denver, CO", "Phoenix, AZ", "Seattle, WA",
]

DESTINATION_CITIES = [
    "Memphis, TN", "Houston, TX", "Nashville, TN", "Louisville, KY",
    "Charlotte, NC", "Indianapolis, IN", "Columbus, OH", "Kansas City, MO",
]

ACCESSORIAL_TYPES = ["Detention", "Lumper Fee", "Layover", "Re-delivery"]

CARRIER_BIAS = {
    "XPO Logistics": 0.10, "J.B. Hunt": -0.05, "Werner Enterprises": 0.15,
    "Schneider National": -0.10, "Old Dominion": -0.20, "FedEx Freight": 0.05,
}

FACILITY_BIAS = {
    "Warehouse A - Dallas": 0.05, "Warehouse B - Memphis": 0.20,
    "Distribution Center C - Atlanta": -0.10, "Warehouse D - Chicago": 0.15,
    "Cold Storage E - Houston": -0.05,
}

def generate_mock_shipments(n: int = 300, seed: int = 42) -> pd.DataFrame:
    """Return a DataFrame of n synthetic shipments with risk scores."""
    rng = np.random.default_rng(seed)
    base_date = datetime.today()
    ship_dates = [base_date - timedelta(days=int(rng.integers(0, 90))) for _ in range(n)]
    carriers     = rng.choice(CARRIERS, n)
    facilities   = rng.choice(FACILITIES, n)
    origins      = rng.choice(ORIGIN_CITIES, n)
    destinations = rng.choice(DESTINATION_CITIES, n)
    c_bias = np.array([CARRIER_BIAS[c] for c in carriers])
    f_bias = np.array([FACILITY_BIAS[f] for f in facilities])
    base_risk    = rng.uniform(0.10, 0.90, n)
    risk_scores  = np.clip(base_risk + c_bias + f_bias, 0.05, 0.98).round(3)
    weight_lbs   = rng.uniform(500, 44_000, n).round(0).astype(int)
    miles        = rng.uniform(50, 2_400, n).round(0).astype(int)
    base_freight = (weight_lbs * 0.04 + miles * 0.80 + rng.uniform(100, 500, n)).round(2)
    accessorial_charges = np.array([
        round(float(rng.uniform(200, 850)), 2) if rs >= 0.67
        else round(float(rng.uniform(50, 350)), 2) if rs >= 0.34
        else 0.0
        for rs in risk_scores
    ])
    risk_tiers = ["High" if rs >= 0.67 else "Medium" if rs >= 0.34 else "Low"
                  for rs in risk_scores]
    accessorial_types = [str(rng.choice(ACCESSORIAL_TYPES)) if rs >= 0.34 else "None"
                         for rs in risk_scores]
    total_costs   = (base_freight + accessorial_charges).round(2)
    cost_per_mile = np.where(miles > 0, total_costs / miles, 0).round(4)
    df = pd.DataFrame({
        "shipment_id":            [f"SHP-{str(i).zfill(5)}" for i in range(1, n + 1)],
        "ship_date":              [d.strftime("%Y-%m-%d") for d in ship_dates],
        "carrier": carriers, "facility": facilities,
        "origin_city": origins, "destination_city": destinations,
        "lane":                   [f"{o} -> {d}" for o, d in zip(origins, destinations)],
        "weight_lbs": weight_lbs, "miles": miles,
        "base_freight_usd": base_freight,
        "accessorial_charge_usd": accessorial_charges,
        "total_cost_usd": total_costs, "cost_per_mile": cost_per_mile,
        "risk_score": risk_scores, "risk_tier": risk_tiers,
        "accessorial_type": accessorial_types,
    })
    return df.sort_values("ship_date", ascending=False).reset_index(drop=True)
```

---

### `utils/database.py`

```python
"""
utils/database.py
Azure SQL database connection for PACE.
Reads credentials from .env (local) or st.secrets (Streamlit Cloud).
NOT yet wired to any page — all pages use mock_data.py.
"""
import os
import streamlit as st
import pandas as pd

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

def _get_secret(key: str) -> str:
    try:
        return st.secrets["azure_sql"][key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, "")

@st.cache_resource
def get_connection():
    if not PYODBC_AVAILABLE:
        st.error("pyodbc is not installed.")
        return None
    server   = _get_secret("DB_SERVER")    # essql1.database.windows.net
    database = _get_secret("DB_DATABASE")  # ISYS43603_Spring2026_Sec02_Alice_db
    username = _get_secret("DB_USERNAME")
    password = _get_secret("DB_PASSWORD")
    driver   = _get_secret("DB_DRIVER") or "ODBC Driver 18 for SQL Server"
    if not all([server, database, username, password]):
        return None
    conn_str = (
        f"DRIVER={{{driver}}};SERVER=tcp:{server},1433;DATABASE={database};"
        f"UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        st.error(f"Azure SQL connection failed: {e}")
        return None

@st.cache_data
def get_shipments(_conn, row_limit: int = 1000) -> pd.DataFrame:
    if _conn is None:
        return pd.DataFrame()
    query = f"""
        SELECT TOP {row_limit}
            shipment_id, ship_date, carrier, facility, weight_lbs, miles,
            base_freight_usd, accessorial_charge_usd
        FROM shipments ORDER BY ship_date DESC
    """
    try:
        return pd.read_sql(query, _conn)
    except Exception:
        return pd.DataFrame()
```

---

### `pages/0_Home.py`

```python
# File: pages/0_Home.py
# Light theme. 6 KPI cards, 6 Plotly charts (white bg, navy accents).
# Charts: Shipments Over Time, Revenue vs Cost, Avg CPM by Carrier,
#         Cost Breakdown by Carrier, Risk Tier Distribution (bar),
#         Accessorial Rate by Facility.
# Imports: inject_css, top_nav, NAVY_500, NAVY_900, NAVY_100 from styling

# Key layout:
#   - Date filter expander at top
#   - 6 st.metric() KPI cards
#   - 2x2 grid of charts + 2 more below
#   - No dark theme on this page (light bg)
```

**Full source — 0_Home.py:**

```python
# File: pages/0_Home.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.mock_data import generate_mock_shipments
from utils.styling import inject_css, top_nav, NAVY_500, NAVY_900, NAVY_100

st.set_page_config(page_title="PACE — Home", page_icon="🏠",
                   layout="wide", initial_sidebar_state="collapsed")
inject_css()

if not check_auth():
    st.warning("Please sign in.")
    st.page_link("app.py", label="Go to Sign In", icon="🔑")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)

@st.cache_data
def load_data():
    return generate_mock_shipments(300)

df_all = load_data()
df_all["ship_date_dt"] = pd.to_datetime(df_all["ship_date"])

min_d = df_all["ship_date_dt"].min().date()
max_d = df_all["ship_date_dt"].max().date()

with st.expander("Filters", expanded=False):
    f1, f2 = st.columns(2)
    with f1:
        date_range = st.date_input("Ship Date Range", value=(min_d, max_d),
                                   min_value=min_d, max_value=max_d, key="home_date")
    with f2:
        st.markdown("")

df = df_all.copy()
if len(date_range) == 2:
    df = df[(df["ship_date_dt"] >= pd.Timestamp(date_range[0])) &
            (df["ship_date_dt"] <= pd.Timestamp(date_range[1]))]

st.markdown("## Operations Overview")
st.caption("High-level freight performance metrics across all active shipments")
st.divider()

total_shipments   = len(df)
total_revenue     = df["base_freight_usd"].sum()
total_accessorial = df["accessorial_charge_usd"].sum()
total_costs       = df["total_cost_usd"].sum()
avg_cpm           = df["cost_per_mile"].mean()
accessorial_rate  = (len(df[df["accessorial_charge_usd"] > 0]) / total_shipments * 100) if total_shipments else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: st.metric("Total Shipments",   f"{total_shipments:,}")
with k2: st.metric("Total Revenue",     f"${total_revenue:,.0f}")
with k3: st.metric("Total Costs",       f"${total_costs:,.0f}")
with k4: st.metric("Accessorial Costs", f"${total_accessorial:,.0f}")
with k5: st.metric("Avg Cost / Mile",   f"${avg_cpm:.2f}")
with k6: st.metric("Accessorial Rate",  f"{accessorial_rate:.1f}%")

# Charts: weekly shipments area, revenue vs cost line, avg CPM bar,
#         stacked cost breakdown, risk tier bar, accessorial rate by facility
# All charts: plot_bgcolor="white", paper_bgcolor="white", NAVY_500 color
```

---

### `pages/1_Dashboard.py`

```python
# File: pages/1_Dashboard.py
# DARK theme (DARK_BG="#0B1120", DARK_CARD="#111827").
# Defines its own DARK_LAYOUT dict locally (not imported from styling).
# Charts: Risk Score Distribution (bar), Avg Risk by Carrier (bar),
#         Risk Tier Breakdown (donut), Risk by Facility (bar),
#         Risk Trend Over Time (area line), Recent Shipments table.
# Inline CSS override applied via st.markdown() to force dark background.
# Filters: date range, carrier multiselect, facility multiselect, risk tier multiselect.

# Color palette (local to this file):
DARK_BG        = "#0B1120"
DARK_CARD      = "#111827"
DARK_SURFACE   = "#1F2937"
TEXT_PRIMARY   = "#F9FAFB"
TEXT_SECONDARY = "#9CA3AF"
TEXT_MUTED     = "#6B7280"
ACCENT_BLUE    = "#3B82F6"
ACCENT_CYAN    = "#06B6D4"
ACCENT_GREEN   = "#10B981"
ACCENT_AMBER   = "#F59E0B"
ACCENT_RED     = "#EF4444"
ACCENT_PURPLE  = "#8B5CF6"
```

---

### `pages/2_Upload.py`

```python
# File: pages/2_Upload.py
# Light theme. CSV upload + validation + mock risk scoring.
# Required columns: shipment_id, ship_date, carrier, facility,
#                   weight_lbs, miles, base_freight_usd, accessorial_charge_usd
# validate_dataframe(): returns (errors, warnings) lists
# mock_score(): adds risk_score and risk_tier columns using weight+miles formula
# UI: file uploader, "Use sample data" button, validation results (pass/warn/err counts),
#     data preview table, "Generate Risk Scores" button

# Validation icons use emoji in main branch: checkmark=✅, warn=⚠️, error=❌
```

---

### `pages/3_Shipments.py`

```python
# File: pages/3_Shipments.py
# Light theme. Two views: list view (filterable table) and detail view.
# List: filterable by carrier, facility, risk tier; searchable by shipment_id
#       clickable rows navigate to detail view (uses st.session_state)
# Detail: risk score display, progress bar, risk factor breakdown (5 bars),
#         recommended actions (tier-specific), similar shipments table
# Risk factor weights: carrier history, facility profile, miles, weight, base freight
```

---

### `pages/4_Cost_Estimate.py`

```python
# File: pages/4_Cost_Estimate.py
# Light theme. Random Forest cost predictor (scikit-learn).
# Model: RandomForestRegressor(n_estimators=200), trained on 300 mock rows
# Features: carrier (one-hot), facility (one-hot), weight_lbs, miles
# Output: predicted total cost + 95% CI (±1.96σ from tree variance)
# Charts: comparison bar (ML vs avg CPM vs fleet avg), feature importance (h-bar),
#         historical cost distribution (histogram + vline for prediction)
```

---

### `pages/5_Route_Analysis.py`

```python
# File: pages/5_Route_Analysis.py
# Light theme. Lane-level cost analysis.
# Group by: Lane (origin->dest), Origin City, or Destination City
# Filter: min shipments per lane
# Charts: Most Expensive Lanes (h-bar, red), Most Efficient Lanes (h-bar, green),
#         Volume vs Cost scatter (bubble, color=avg risk), Full lane table
# KPIs: active lanes, busiest lane, cheapest $/mile, most expensive $/mile
```

---

### `pages/6_Carrier_Comparison.py`

```python
# File: pages/6_Carrier_Comparison.py
# Light theme. Multi-carrier comparison.
# Carrier selector with "All" / "Clear" buttons
# Charts: Avg $/Mile (bar), High Risk % (bar, color-coded by threshold),
#         Accessorial Cost Rate (bar), Performance Radar (Scatterpolar)
# Radar dimensions: Cost Efficiency, Low Risk, Low Accessorial, Volume
# Metrics: shipments, avg_cost, avg_cpm, avg_risk, high_risk_pct,
#           avg_accessorial, accessorial_rate, total_spend
```

---

### `pages/7_Accessorial_Tracker.py`

```python
# File: pages/7_Accessorial_Tracker.py
# Light theme. Accessorial charge tracking.
# Filters: accessorial type multiselect, carrier multiselect, date range
# KPIs: total accessorial $, affected shipments, accessorial rate %,
#       avg per affected shipment, % of total spend
# Charts: Cost by Type (donut), Cost by Carrier (h-bar),
#         Cost by Facility (h-bar), Weekly Trend (area line)
# Risk tier analysis: 3 stat cards (Low/Med/High) with border-left styling
# Table: top 15 most expensive accessorial shipments
```

---

### `tests/test_validation_and_upload.py`

```python
# BROKEN — imports from app.py that don't exist:
# validate_shipments_df, CFG, add_target, score_shipments, train_baseline_on_synthetic
# These functions were never implemented in app.py.
# Tests cover: validate good df, validate missing columns,
#              malformed CSV raises error, scoring pipeline runs.
# CI will fail on the "test" job until these are fixed.
```

---

## CI Pipeline (`.github/workflows/ci.yml`)

4 jobs run on every push:
1. **lint** — `flake8` on all `.py` files
2. **security** — `bandit` security scan
3. **install** — pip install requirements
4. **test** — `pytest tests/` (currently fails due to broken test imports)
