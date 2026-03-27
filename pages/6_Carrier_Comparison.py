# File: pages/6_Carrier_Comparison.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_utils import require_auth
from utils.database import load_shipments_with_fallback
from utils.styling import inject_css, top_nav, NAVY_500, NAVY_900

st.set_page_config(
    page_title="PACE — Carrier Comparison",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

require_auth()
username = st.session_state.get("username", "User")
top_nav(username)

df_raw = load_shipments_with_fallback()
df_raw["ship_date_dt"] = pd.to_datetime(df_raw["ship_date"])
df_all = df_raw  # module-level alias used by dialogs

ALL_CARRIERS = sorted(df_all["carrier"].dropna().unique())

CARRIER_COLORS = [
    "#0F2B4A", "#2563A8", "#059669", "#D97706",
    "#DC2626", "#7C3AED", "#0891B2", "#BE185D",
]
color_map = {c: CARRIER_COLORS[i % len(CARRIER_COLORS)]
             for i, c in enumerate(ALL_CARRIERS)}



def _sort_buttons(chart_key: str):
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


# ── Carrier metrics builder ───────────────────────────────────────────────────
def _build_metrics(df: pd.DataFrame) -> pd.DataFrame:
    m = (
        df.groupby("carrier")
        .agg(
            shipments        =("shipment_id",            "count"),
            avg_cost         =("total_cost_usd",          "mean"),
            total_spend      =("total_cost_usd",          "sum"),
            avg_cpm          =("cost_per_mile",           "mean"),
            avg_risk         =("risk_score",              "mean"),
            high_risk_count  =("risk_tier",
                               lambda x: (x == "High").sum()),
            total_accessorial=("accessorial_charge_usd",  "sum"),
            avg_accessorial  =("accessorial_charge_usd",  "mean"),
            avg_miles        =("miles",                   "mean"),
            avg_weight       =("weight_lbs",              "mean"),
        )
        .reset_index()
    )
    m["high_risk_pct"]    = (m["high_risk_count"]   / m["shipments"] * 100).round(1)
    m["accessorial_rate"] = (m["total_accessorial"] / m["total_spend"] * 100).round(1)
    return m


# ── Chart-builder functions ───────────────────────────────────────────────────
def _build_cpm_fig(metrics: pd.DataFrame, height=280, sort_by="Value ↓") -> go.Figure:
    if sort_by == "Value ↑":
        sorted_m = metrics.sort_values("avg_cpm", ascending=True)
    elif sort_by == "Value ↓":
        sorted_m = metrics.sort_values("avg_cpm", ascending=False)
    else:
        sorted_m = metrics.sort_values("carrier")
    fig = go.Figure(go.Bar(
        x=sorted_m["carrier"],
        y=sorted_m["avg_cpm"],
        marker_color=[color_map.get(c, "#9333EA") for c in sorted_m["carrier"]],
        text=sorted_m["avg_cpm"].apply(lambda v: f"${v:.2f}"),
        textposition="outside",
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=36, b=0), height=height,
        plot_bgcolor="#0f0a1e", paper_bgcolor="#0f0a1e",
        font=dict(color="#A78BFA"),
        yaxis=dict(tickprefix="$", gridcolor="rgba(150,50,200,0.15)",
                   color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
        xaxis=dict(gridcolor="rgba(150,50,200,0.15)", color="#94A3B8",
                   linecolor="rgba(150,50,200,0.2)"),
        showlegend=False,
    )
    return fig


def _build_high_risk_fig(metrics: pd.DataFrame, height=280, sort_by="Value ↓") -> go.Figure:
    if sort_by == "Value ↑":
        sorted_m2 = metrics.sort_values("high_risk_pct", ascending=True)
    elif sort_by == "Value ↓":
        sorted_m2 = metrics.sort_values("high_risk_pct", ascending=False)
    else:
        sorted_m2 = metrics.sort_values("carrier")
    bar_colors = ["#DC2626" if p > 40 else "#D97706" if p > 25 else "#059669"
                  for p in sorted_m2["high_risk_pct"]]
    fig = go.Figure(go.Bar(
        x=sorted_m2["carrier"],
        y=sorted_m2["high_risk_pct"],
        marker_color=bar_colors,
        text=sorted_m2["high_risk_pct"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=36, b=0), height=height,
        plot_bgcolor="#0f0a1e", paper_bgcolor="#0f0a1e",
        font=dict(color="#A78BFA"),
        yaxis=dict(ticksuffix="%", gridcolor="rgba(150,50,200,0.15)",
                   color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
        xaxis=dict(gridcolor="rgba(150,50,200,0.15)", color="#94A3B8",
                   linecolor="rgba(150,50,200,0.2)"),
        showlegend=False,
    )
    return fig


def _build_acc_rate_fig(metrics: pd.DataFrame, height=260, sort_by="Value ↓") -> go.Figure:
    if sort_by == "Value ↑":
        sorted_m3 = metrics.sort_values("accessorial_rate", ascending=True)
    elif sort_by == "Value ↓":
        sorted_m3 = metrics.sort_values("accessorial_rate", ascending=False)
    else:
        sorted_m3 = metrics.sort_values("carrier")
    fig = go.Figure(go.Bar(
        x=sorted_m3["carrier"],
        y=sorted_m3["accessorial_rate"],
        marker_color=[color_map.get(c, "#9333EA") for c in sorted_m3["carrier"]],
        text=sorted_m3["accessorial_rate"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=36, b=0), height=height,
        plot_bgcolor="#0f0a1e", paper_bgcolor="#0f0a1e",
        font=dict(color="#A78BFA"),
        yaxis=dict(ticksuffix="%", gridcolor="rgba(150,50,200,0.15)",
                   color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
        xaxis=dict(gridcolor="rgba(150,50,200,0.15)", color="#94A3B8",
                   linecolor="rgba(150,50,200,0.2)"),
        showlegend=False,
    )
    return fig


def _build_radar_fig(metrics: pd.DataFrame, height=260) -> go.Figure:
    def norm(series, invert=True):
        mn, mx = series.min(), series.max()
        if mx == mn:
            return pd.Series([0.5] * len(series), index=series.index)
        n = (series - mn) / (mx - mn)
        return 1 - n if invert else n

    radar_df = metrics.copy()
    radar_df["cost_score"]      = norm(radar_df["avg_cpm"],          invert=True)
    radar_df["risk_score_norm"] = norm(radar_df["avg_risk"],         invert=True)
    radar_df["acc_score"]       = norm(radar_df["accessorial_rate"], invert=True)
    radar_df["volume_score"]    = norm(radar_df["shipments"],        invert=False)

    categories = ["Cost Efficiency", "Low Risk", "Low Accessorial", "Volume"]
    radar_fig = go.Figure()
    for _, row in radar_df.iterrows():
        vals = [row["cost_score"], row["risk_score_norm"],
                row["acc_score"],  row["volume_score"]]
        vals += [vals[0]]
        radar_fig.add_trace(go.Scatterpolar(
            r=vals,
            theta=categories + [categories[0]],
            fill="toself",
            name=row["carrier"],
            line_color=color_map.get(row["carrier"], "#9333EA"),
            opacity=0.6,
        ))
    radar_fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        margin=dict(l=20, r=20, t=20, b=20),
        height=height,
        paper_bgcolor="#0f0a1e",
        font=dict(color="#A78BFA"),
        legend=dict(bgcolor="rgba(15,10,30,0.7)", font=dict(size=10, color="#FFFFFF")),
    )
    return radar_fig


# ── Helper: get active carriers for dialogs ───────────────────────────────────
def _active_carriers_df(base_df: pd.DataFrame) -> pd.DataFrame:
    active = st.session_state.get("active_carriers", ALL_CARRIERS)
    if not active:
        return base_df
    return base_df[base_df["carrier"].isin(active)]


# ── Expand dialogs (module-level) ─────────────────────────────────────────────
@st.dialog("Avg Cost per Mile", width="large")
def _popup_cpm():
    sort_by = _sort_buttons("cpm")
    m = _build_metrics(_active_carriers_df(df_all))
    st.caption(f"{len(_active_carriers_df(df_all)):,} shipments · all carriers")
    if m.empty:
        st.info("No data available.")
    else:
        st.plotly_chart(_build_cpm_fig(m, height=460, sort_by=sort_by), width="stretch")


@st.dialog("High Risk Shipment Rate", width="large")
def _popup_high_risk():
    sort_by = _sort_buttons("high_risk")
    m = _build_metrics(_active_carriers_df(df_all))
    st.caption(f"{len(_active_carriers_df(df_all)):,} shipments · all carriers")
    if m.empty:
        st.info("No data available.")
    else:
        st.plotly_chart(_build_high_risk_fig(m, height=460, sort_by=sort_by), width="stretch")


@st.dialog("Accessorial Cost Rate", width="large")
def _popup_acc_rate():
    sort_by = _sort_buttons("acc_rate")
    m = _build_metrics(_active_carriers_df(df_all))
    st.caption(f"{len(_active_carriers_df(df_all)):,} shipments · all carriers")
    if m.empty:
        st.info("No data available.")
    else:
        st.plotly_chart(_build_acc_rate_fig(m, height=460, sort_by=sort_by), width="stretch")


@st.dialog("Carrier Performance Radar", width="large")
def _popup_radar():
    m = _build_metrics(_active_carriers_df(df_all))
    st.caption(f"{len(_active_carriers_df(df_all)):,} shipments · all carriers")
    if m.empty:
        st.info("No data available.")
    else:
        st.plotly_chart(_build_radar_fig(m, height=500), width="stretch")


# ── Persist active carriers in session state ──────────────────────────────────
if "active_carriers" not in st.session_state:
    st.session_state["active_carriers"] = ALL_CARRIERS

# ── DOT number search ─────────────────────────────────────────────────────────
_has_dot = "dot_number" in df_raw.columns

dot_search_col, dot_btn_col, dot_clear_col = st.columns([3, 1, 1], gap="small")
with dot_search_col:
    dot_query = st.text_input(
        "Search by DOT Number",
        placeholder="e.g. 72011",
        label_visibility="collapsed",
        help="Enter a USDOT number to filter to the matching carrier",
        key="cc_dot_search",
    )
with dot_btn_col:
    dot_search_clicked = st.button(
        "Search DOT",
        type="primary",
        use_container_width=True,
        disabled=not dot_query.strip(),
    )
with dot_clear_col:
    if st.button("Clear", use_container_width=True, key="cc_dot_clear"):
        st.session_state["active_carriers"] = ALL_CARRIERS
        st.rerun()

if dot_search_clicked and dot_query.strip():
    try:
        dot_int = int(dot_query.strip())
    except ValueError:
        st.error("DOT number must be numeric.")
        st.stop()

    if _has_dot:
        matched = (
            df_raw[df_raw["dot_number"] == dot_int]["carrier"]
            .dropna()
            .unique()
            .tolist()
        )
        if matched:
            st.session_state["active_carriers"] = matched
            st.success(
                f"Showing carrier{'s' if len(matched) > 1 else ''}: "
                + ", ".join(matched)
            )
            st.rerun()
        else:
            st.warning(f"No carrier found for DOT {dot_int} in current dataset.")
    else:
        st.info(
            f"DOT lookup requires uploaded PACE data with a `dot_number` column. "
            f"Use **Carrier Lookup** (page 9) for live FMCSA lookup of DOT {dot_int}.",
            icon="ℹ️",
        )

# ── Inline carrier selector ───────────────────────────────────────────────────
with st.expander("⚙️ Manage Carriers", expanded=False):
    f1, f2 = st.columns([5, 1])
    with f1:
        selected = st.multiselect(
            "Active Carriers",
            options=ALL_CARRIERS,
            default=[c for c in st.session_state["active_carriers"] if c in ALL_CARRIERS],
        )
        st.session_state["active_carriers"] = selected
    with f2:
        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("All", width="stretch"):
                st.session_state["active_carriers"] = ALL_CARRIERS
                st.rerun()
        with col_b:
            if st.button("Clear", width="stretch"):
                st.session_state["active_carriers"] = []
                st.rerun()

# ── Guard: need at least 1 carrier ───────────────────────────────────────────
active_carriers = st.session_state["active_carriers"]
if not active_carriers:
    st.markdown("## Carrier Comparison")
    st.warning("No carriers selected. Use the filter above to add carriers to the comparison.")
    st.stop()

df = df_all[df_all["carrier"].isin(active_carriers)].copy()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Carrier Comparison")
st.caption(f"Comparing {len(active_carriers)} carrier{'s' if len(active_carriers) != 1 else ''} across cost, risk, and performance metrics.")
st.divider()

# ── Build carrier metrics table ───────────────────────────────────────────────
metrics = _build_metrics(df)

# ── Summary metrics table ─────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Carrier Summary")
    display = metrics.copy()
    for col in ["avg_cost", "avg_cpm", "avg_risk", "avg_accessorial", "total_spend"]:
        display[col] = display[col].round(2)
    display["avg_miles"]  = display["avg_miles"].round(0).astype(int)
    display["avg_weight"] = display["avg_weight"].round(0).astype(int)

    st.dataframe(
        display[[
            "carrier", "shipments", "avg_cost", "avg_cpm", "avg_risk",
            "high_risk_pct", "avg_accessorial", "accessorial_rate", "total_spend",
        ]].rename(columns={
            "carrier":         "Carrier",
            "shipments":       "Shipments",
            "avg_cost":        "Avg Total Cost",
            "avg_cpm":         "Avg $/Mile",
            "avg_risk":        "Avg Risk",
            "high_risk_pct":   "High Risk %",
            "avg_accessorial": "Avg Accessorial",
            "accessorial_rate":"Accessorial %",
            "total_spend":     "Total Spend",
        }).sort_values("Avg $/Mile"),
        width="stretch",
        hide_index=True,
        column_config={
            "Avg Risk":       st.column_config.ProgressColumn(
                "Avg Risk", format="%.1f", min_value=0, max_value=100),
            "Avg Total Cost": st.column_config.NumberColumn(format="$%.2f"),
            "Avg $/Mile":     st.column_config.NumberColumn(format="$%.3f"),
            "Avg Accessorial":st.column_config.NumberColumn(format="$%.2f"),
            "Total Spend":    st.column_config.NumberColumn(format="$%.0f"),
        },
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Bar chart comparisons ─────────────────────────────────────────────────────
ch1, ch2 = st.columns(2, gap="medium")

with ch1:
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Avg Cost per Mile")
        with btn:
            if st.button("⤢", key="exp_cpm", help="Expand chart"):
                _popup_cpm()
        st.plotly_chart(_build_cpm_fig(metrics), width="stretch")

with ch2:
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### High Risk Shipment Rate")
        with btn:
            if st.button("⤢", key="exp_high_risk", help="Expand chart"):
                _popup_high_risk()
        st.plotly_chart(_build_high_risk_fig(metrics), width="stretch")

st.markdown("<br>", unsafe_allow_html=True)

ch3, ch4 = st.columns(2, gap="medium")

with ch3:
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Accessorial Cost Rate")
            st.caption("Accessorial charges as % of total spend")
        with btn:
            if st.button("⤢", key="exp_acc_rate", help="Expand chart"):
                _popup_acc_rate()
        st.plotly_chart(_build_acc_rate_fig(metrics), width="stretch")

with ch4:
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Carrier Performance Radar")
            st.caption("Normalized across cost, risk, and accessorial rate (lower = better)")
        with btn:
            if st.button("⤢", key="exp_radar", help="Expand chart"):
                _popup_radar()
        st.plotly_chart(_build_radar_fig(metrics), width="stretch")
