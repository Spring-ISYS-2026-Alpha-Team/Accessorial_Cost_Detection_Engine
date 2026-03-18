# File: pages/0_Home.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_utils import require_auth
from utils.database import load_shipments_with_fallback
from utils.styling import inject_css, top_nav, NAVY_500, NAVY_900, NAVY_100

st.set_page_config(page_title="PACE — Home", page_icon="🏠",
                   layout="wide", initial_sidebar_state="collapsed")
inject_css()

require_auth()
username = st.session_state.get("username", "User")
top_nav(username)

df_all = load_shipments_with_fallback()
df_all["ship_date_dt"] = pd.to_datetime(df_all["ship_date"])

# ── Shared chart layout helper ─────────────────────────────────────────────────
_DARK = dict(plot_bgcolor="#0f0a1e", paper_bgcolor="#0f0a1e",
             font=dict(color="#A78BFA"))
_GRID = dict(gridcolor="rgba(150,50,200,0.18)", color="#A78BFA")
_LEGEND = dict(orientation="h", y=1.05, font=dict(color="#FFFFFF"))


def _filter_by_range(df: pd.DataFrame, sel: str) -> pd.DataFrame:
    days_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365}
    if sel not in days_map:
        return df
    cutoff = df["ship_date_dt"].max() - pd.Timedelta(days=days_map[sel])
    return df[df["ship_date_dt"] >= cutoff]


def _range_buttons(chart_key: str):
    """Render 1M/3M/6M/1Y/All toggle buttons; return selected label."""
    opts = ["1M", "3M", "6M", "1Y", "All"]
    skey = f"popup_range_{chart_key}"
    if skey not in st.session_state:
        st.session_state[skey] = "All"
    cols = st.columns(len(opts))
    for col, lbl in zip(cols, opts):
        with col:
            kind = "primary" if st.session_state[skey] == lbl else "secondary"
            if st.button(lbl, key=f"rb_{chart_key}_{lbl}", type=kind,
                         width="stretch"):
                st.session_state[skey] = lbl
    return st.session_state[skey]


def _sort_buttons(chart_key: str):
    """Render sort-order toggle buttons for categorical charts; return selected label."""
    opts = ["Value ↑", "Value ↓", "A-Z"]
    skey = f"sort_{chart_key}"
    if skey not in st.session_state:
        st.session_state[skey] = "Value ↓"
    cols = st.columns(len(opts))
    for col, lbl in zip(cols, opts):
        with col:
            kind = "primary" if st.session_state[skey] == lbl else "secondary"
            if st.button(lbl, key=f"sb_{chart_key}_{lbl}", type=kind,
                         width="stretch"):
                st.session_state[skey] = lbl
    return st.session_state[skey]


def _build_volume_fig(df: pd.DataFrame, height=260) -> go.Figure:
    df = df.copy()
    df["week"] = df["ship_date_dt"].dt.to_period("W").dt.start_time
    wk = df.groupby("week").agg(shipments=("shipment_id", "count")).reset_index()
    fig = go.Figure(go.Scatter(
        x=wk["week"], y=wk["shipments"],
        mode="lines", fill="tozeroy",
        line=dict(color="#9333EA", width=2),
        fillcolor="rgba(147,51,234,0.25)",
    ))
    fig.update_layout(**_DARK, height=height, margin=dict(l=0, r=0, t=8, b=0),
                      xaxis=dict(**_GRID), yaxis=dict(**_GRID))
    return fig


def _build_rev_cost_fig(df: pd.DataFrame, height=260) -> go.Figure:
    df = df.copy()
    df["week"] = df["ship_date_dt"].dt.to_period("W").dt.start_time
    wk = df.groupby("week").agg(revenue=("base_freight_usd", "sum"),
                                 total_cost=("total_cost_usd", "sum")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=wk["week"], y=wk["revenue"], name="Revenue",
                             mode="lines", line=dict(color=NAVY_500, width=2)))
    fig.add_trace(go.Scatter(x=wk["week"], y=wk["total_cost"], name="Total Cost",
                             mode="lines", line=dict(color="#DC2626", width=2, dash="dash")))
    fig.update_layout(**_DARK, height=height, margin=dict(l=0, r=0, t=8, b=0),
                      legend=_LEGEND, xaxis=dict(**_GRID),
                      yaxis=dict(**_GRID, tickprefix="$"))
    return fig


def _build_cpm_fig(df: pd.DataFrame, height=280, sort_by="Value ↓") -> go.Figure:
    cpm = df.groupby("carrier")["cost_per_mile"].mean().reset_index()
    if sort_by == "Value ↑":
        cpm = cpm.sort_values("cost_per_mile", ascending=False)   # ascending bars = lowest on top
    elif sort_by == "Value ↓":
        cpm = cpm.sort_values("cost_per_mile", ascending=True)    # highest on top
    else:
        cpm = cpm.sort_values("carrier", ascending=False)         # A-Z top-to-bottom
    fig = go.Figure(go.Bar(
        x=cpm["cost_per_mile"], y=cpm["carrier"], orientation="h",
        marker_color=NAVY_500,
        text=cpm["cost_per_mile"].apply(lambda v: f"${v:.2f}"),
        textposition="outside",
    ))
    fig.update_layout(**_DARK, height=height,
                      margin=dict(l=0, r=130, t=8, b=0),
                      xaxis=dict(**_GRID, tickprefix="$"),
                      yaxis=dict(**_GRID))
    return fig


def _build_breakdown_fig(df: pd.DataFrame, height=280, sort_by="Value ↓") -> go.Figure:
    cb = (df.groupby("carrier")
            .agg(base=("base_freight_usd", "sum"),
                 acc=("accessorial_charge_usd", "sum"))
            .reset_index())
    cb["total"] = cb["base"] + cb["acc"]
    if sort_by == "Value ↑":
        cb = cb.sort_values("total", ascending=True)
    elif sort_by == "Value ↓":
        cb = cb.sort_values("total", ascending=False)
    else:
        cb = cb.sort_values("carrier")
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Base Freight", x=cb["carrier"],
                         y=cb["base"], marker_color=NAVY_500))
    fig.add_trace(go.Bar(name="Accessorial", x=cb["carrier"],
                         y=cb["acc"], marker_color="#DC2626"))
    fig.update_layout(barmode="stack", **_DARK, height=height,
                      margin=dict(l=0, r=0, t=8, b=0), legend=_LEGEND,
                      xaxis=dict(**_GRID),
                      yaxis=dict(**_GRID, tickprefix="$"))
    return fig


# ── Expand dialogs ─────────────────────────────────────────────────────────────
@st.dialog("Shipments Over Time", width="large")
def _popup_volume():
    sel = _range_buttons("volume")
    df_f = _filter_by_range(df_all, sel)
    st.caption(f"{len(df_f):,} shipments · {sel} view")
    st.plotly_chart(_build_volume_fig(df_f, height=480), width="stretch")


@st.dialog("Revenue vs Total Cost", width="large")
def _popup_rev_cost():
    sel = _range_buttons("rev_cost")
    df_f = _filter_by_range(df_all, sel)
    st.caption(f"{len(df_f):,} shipments · {sel} view")
    st.plotly_chart(_build_rev_cost_fig(df_f, height=480), width="stretch")


@st.dialog("Avg Cost per Mile by Carrier", width="large")
def _popup_cpm():
    sort_by = _sort_buttons("cpm")
    st.caption(f"{len(df_all):,} shipments · all carriers")
    st.plotly_chart(_build_cpm_fig(df_all, height=460, sort_by=sort_by), width="stretch")


@st.dialog("Cost Breakdown by Carrier", width="large")
def _popup_breakdown():
    sort_by = _sort_buttons("breakdown")
    st.caption(f"{len(df_all):,} shipments · all carriers")
    st.plotly_chart(_build_breakdown_fig(df_all, height=460, sort_by=sort_by), width="stretch")


# ── Inline date filter ────────────────────────────────────────────────────────
min_d = df_all["ship_date_dt"].min().date()
max_d = df_all["ship_date_dt"].max().date()

with st.expander("⚙️ Filters", expanded=False):
    f1, f2 = st.columns(2)
    with f1:
        date_range = st.date_input("Ship Date Range", value=(min_d, max_d),
                                   min_value=min_d, max_value=max_d, key="home_date")
    with f2:
        st.markdown("")  # spacer

df = df_all.copy()
if len(date_range) == 2:
    df = df[(df["ship_date_dt"] >= pd.Timestamp(date_range[0])) &
            (df["ship_date_dt"] <= pd.Timestamp(date_range[1]))]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Operations Overview")
st.caption("High-level freight performance metrics across all active shipments")
st.divider()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_shipments   = len(df)
total_revenue     = df["base_freight_usd"].sum()
total_accessorial = df["accessorial_charge_usd"].sum()
total_costs       = df["total_cost_usd"].sum()
avg_cpm           = df["cost_per_mile"].mean()
accessorial_rate  = (len(df[df["accessorial_charge_usd"] > 0]) / total_shipments * 100) if total_shipments else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: st.metric("Total Shipments",   f"{total_shipments:,}",
                   help="Total number of shipment records in the selected dataset.")
with k2: st.metric("Total Revenue",     f"${total_revenue:,.0f}",
                   help="Sum of all revenue billed to customers across every shipment.")
with k3: st.metric("Total Costs",       f"${total_costs:,.0f}",
                   help="Combined linehaul and accessorial costs paid to carriers.")
with k4: st.metric("Accessorial Costs", f"${total_accessorial:,.0f}",
                   help="Extra charges beyond base freight — detention, liftgate, fuel surcharges, etc.")
with k5: st.metric("Avg Cost / Mile",   f"${avg_cpm:.2f}",
                   help="Average carrier cost per mile across all shipments. Lower is more efficient.")
with k6: st.metric("Accessorial Rate",  f"{accessorial_rate:.1f}%",
                   help="Percentage of shipments that incurred at least one accessorial charge.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Shipments over time + Revenue vs Cost ─────────────────────────────────────
col_l, col_r = st.columns(2, gap="medium")

with col_l:
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Shipments Over Time")
            st.caption("Weekly shipment volume")
        with btn:
            if st.button("⤢", key="exp_vol", help="Expand chart"):
                _popup_volume()
        st.plotly_chart(_build_volume_fig(df), width="stretch")

with col_r:
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Revenue vs Total Cost")
            st.caption("Weekly — base revenue vs cost including accessorials")
        with btn:
            if st.button("⤢", key="exp_rev", help="Expand chart"):
                _popup_rev_cost()
        st.plotly_chart(_build_rev_cost_fig(df), width="stretch")

st.markdown("<br>", unsafe_allow_html=True)

# ── Avg cost per mile by carrier + cost breakdown ─────────────────────────────
col_a, col_b = st.columns(2, gap="medium")

with col_a:
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Avg Cost per Mile by Carrier")
            st.caption("Lower is more cost-efficient")
        with btn:
            if st.button("⤢", key="exp_cpm", help="Expand chart"):
                _popup_cpm()
        st.plotly_chart(_build_cpm_fig(df), width="stretch")

with col_b:
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Cost Breakdown by Carrier")
            st.caption("Base freight vs accessorial charges per carrier")
        with btn:
            if st.button("⤢", key="exp_bd", help="Expand chart"):
                _popup_breakdown()
        st.plotly_chart(_build_breakdown_fig(df), width="stretch")
