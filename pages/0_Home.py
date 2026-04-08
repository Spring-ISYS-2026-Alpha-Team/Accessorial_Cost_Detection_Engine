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
display_name = str(username).split("@")[0].replace(".", " ").replace("_", " ").title()
top_nav(username)

df_all = load_shipments_with_fallback()
df_all["ship_date_dt"] = pd.to_datetime(df_all["ship_date"])

# ── Shared chart layout helper ─────────────────────────────────────────────────
_DARK = dict(plot_bgcolor="#0f0a1e", paper_bgcolor="#0f0a1e",
             font=dict(color="#A78BFA"))
_GRID = dict(gridcolor="rgba(150,50,200,0.18)", color="#A78BFA")
_LEGEND = dict(orientation="h", y=1.05, font=dict(color="#FFFFFF"))


def _filter_by_range(df: pd.DataFrame, sel: str) -> pd.DataFrame:
    """Handle filter by range."""
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
    """Handle build volume fig."""
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
    """Handle build rev cost fig."""
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


def _build_carrier_list(df: pd.DataFrame) -> pd.DataFrame:
    """Return unique carriers used with shipment volume."""
    carriers = (df.groupby("carrier", dropna=True)
                  .agg(shipments=("shipment_id", "count"))
                  .reset_index()
                  .rename(columns={"carrier": "Carrier", "shipments": "Shipments"})
                  .sort_values(["Shipments", "Carrier"], ascending=[False, True]))
    return carriers


def _build_accessorial_by_carrier_fig(df: pd.DataFrame, height=280) -> go.Figure:
    """Build a ranked chart of total accessorial charges by carrier."""
    acc = (df.groupby("carrier", dropna=True)["accessorial_charge_usd"]
             .sum()
             .reset_index()
             .rename(columns={"carrier": "Carrier", "accessorial_charge_usd": "Accessorial"})
             .sort_values("Accessorial", ascending=False)
             .head(12))

    fig = go.Figure(go.Bar(
        x=acc["Accessorial"],
        y=acc["Carrier"],
        orientation="h",
        marker=dict(
            color=acc["Accessorial"],
            colorscale="Reds",
            line=dict(color="#7F1D1D", width=1),
            showscale=False,
        ),
        text=acc["Accessorial"].apply(lambda v: f"${v:,.0f}"),
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Accessorial: $%{x:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        **_DARK,
        height=height,
        margin=dict(l=0, r=16, t=8, b=0),
        xaxis=dict(**_GRID, tickprefix="$"),
        yaxis=dict(**_GRID, automargin=True, categoryorder="total ascending"),
        showlegend=False,
    )
    return fig


# ── Expand dialogs ─────────────────────────────────────────────────────────────
@st.dialog("Weekly Shipping Volume", width="large")
def _popup_volume():
    """Handle popup volume."""
    sel = _range_buttons("volume")
    df_f = _filter_by_range(df_all, sel)
    st.caption(f"{len(df_f):,} shipments · {sel} view")
    st.plotly_chart(_build_volume_fig(df_f, height=480), width="stretch")


@st.dialog("Operational Efficiency", width="large")
def _popup_rev_cost():
    """Handle popup rev cost."""
    sel = _range_buttons("rev_cost")
    df_f = _filter_by_range(df_all, sel)
    st.caption(f"{len(df_f):,} shipments · {sel} view")
    st.plotly_chart(_build_rev_cost_fig(df_f, height=480), width="stretch")


@st.dialog("Carriers Used", width="large")
def _popup_cpm():
    """Handle popup cpm."""
    carrier_df = _build_carrier_list(df_all)
    st.caption(f"{len(carrier_df):,} carriers across {len(df_all):,} shipments")
    st.dataframe(carrier_df, width="stretch", hide_index=True)


@st.dialog("Total Accessorial Charges by Carrier", width="large")
def _popup_breakdown():
    """Handle popup breakdown."""
    st.caption(f"{len(df_all):,} shipments · ranked by total accessorial charges")
    st.plotly_chart(_build_accessorial_by_carrier_fig(df_all, height=480), width="stretch")


# ── Inline date filter ────────────────────────────────────────────────────────
min_d = df_all["ship_date_dt"].min().date()
max_d = df_all["ship_date_dt"].max().date()

with st.expander("Shipment Date Range", expanded=False):
    f1, f2 = st.columns(2)
    with f1:
        date_range = st.date_input("Change the date range to view different data.", value=(min_d, max_d),
                                   min_value=min_d, max_value=max_d, key="home_date")
    with f2:
        st.markdown("")  # spacer

df = df_all.copy()
if len(date_range) == 2:
    df = df[(df["ship_date_dt"] >= pd.Timestamp(date_range[0])) &
            (df["ship_date_dt"] <= pd.Timestamp(date_range[1]))]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"## Welcome back, {display_name}")
st.caption("Real-time visibility into your freight operations.")
st.divider()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_shipments   = len(df)
total_revenue     = df["base_freight_usd"].sum()
total_accessorial = df["accessorial_charge_usd"].sum()
total_costs       = df["total_cost_usd"].sum()
avg_cpm           = df["cost_per_mile"].mean()
accessorial_rate  = (len(df[df["accessorial_charge_usd"] > 0]) / total_shipments * 100) if total_shipments else 0

# Ensure KPI text wraps instead of truncating in narrow columns.
st.markdown("""
<style>
div[data-testid="stMetric"] label[data-testid="stMetricLabel"] > div,
div[data-testid="stMetric"] label[data-testid="stMetricLabel"] p,
div[data-testid="stMetricValue"] > div {
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    word-break: break-word !important;
}
div[data-testid="stMetric"] {
    min-height: 110px !important;
}
</style>
""", unsafe_allow_html=True)

def _fmt_dollars(v: float) -> str:
    """Format large dollar values as $1.2M, $345K, or $1,234."""
    if v >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"

main_left, main_right = st.columns([3.2, 1.15], gap="medium")

with main_right:
    st.markdown("#### KPI Snapshot")
    kpis = [
        ("Shipments", f"{total_shipments:,}",
         "Total number of shipment records in the selected dataset."),
        ("Revenue", _fmt_dollars(total_revenue),
         "Sum of all revenue billed to customers across every shipment."),
        ("TLC", _fmt_dollars(total_costs),
         "Total Logistics Costs, all expenditures incurred from moving products."),
        ("Accessorial", _fmt_dollars(total_accessorial),
         "Extra charges beyond base freight."),
        ("CPM", f"${avg_cpm:.2f}",
         "Average Cost Per Mile across all shipments."),
        ("Accessorial Usage Rate", f"{accessorial_rate:.1f}%",
         "How often shipments incur extra charges beyond the base linehaul rate."),
    ]

    for label, value, help_text in kpis:
        with st.container(border=True):
            st.metric(label, value, help=help_text)

with main_left:
    # ── Remaining charts (stacked) ─────────────────────────────────────────────
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Carrier Breakdown")
        with btn:
            if st.button("⤢", key="exp_cpm", help="Expand list"):
                _popup_cpm()
        carriers_used_df = _build_carrier_list(df)
        st.caption(f"{len(carriers_used_df):,} Carriers in current date range.")
        st.dataframe(carriers_used_df, width="stretch", hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Total Accessorial Charges by Carrier")
        with btn:
            if st.button("⤢", key="exp_bd", help="Expand chart"):
                _popup_breakdown()
        st.plotly_chart(_build_accessorial_by_carrier_fig(df), width="stretch")
