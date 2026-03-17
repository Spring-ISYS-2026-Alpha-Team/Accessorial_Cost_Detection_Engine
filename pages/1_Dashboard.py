# File: pages/1_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.database import get_connection, get_shipments
from utils.mock_data import generate_mock_shipments
from utils.styling import inject_css, top_nav

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PACE | Dashboards",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

# ── Auth guard ────────────────────────────────────────────────────────────────
if not check_auth():
    st.warning("Please sign in to access this page.")
    st.page_link("app.py", label="Go to Sign In")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)

# ── Load data (live DB with mock fallback) ────────────────────────────────────
conn = get_connection()
df_raw = get_shipments(conn) if conn is not None else pd.DataFrame()
using_live = not df_raw.empty
if not using_live:
    df_raw = generate_mock_shipments(300)
    st.info("Live database unavailable — showing demo data.")
df_raw["ship_date_dt"] = pd.to_datetime(df_raw["ship_date"])
df_all = df_raw  # module-level alias used by dialogs

# ── Shared chart style constants ──────────────────────────────────────────────
_DARK = dict(
    plot_bgcolor="rgba(0,0,0,0.16)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94A3B8", family="Inter, Segoe UI, sans-serif"),
)
_GRID = dict(gridcolor="rgba(241,245,249,0.08)", color="#94A3B8", linecolor="rgba(241,245,249,0.10)")



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


# ── Chart-builder functions ───────────────────────────────────────────────────
def _build_risk_dist_fig(df: pd.DataFrame, height=260) -> go.Figure:
    if len(df) == 0:
        return go.Figure()
    hist_df = df.copy()
    hist_df["bucket"] = pd.cut(
        hist_df["risk_score"],
        bins=[0, 0.20, 0.40, 0.60, 0.80, 1.0],
        labels=["0–20%", "21–40%", "41–60%", "61–80%", "81–100%"],
        include_lowest=True,
    )
    bucket_counts = hist_df["bucket"].value_counts().sort_index().reset_index()
    bucket_counts.columns = ["Bracket", "Count"]

    def bucket_color(label):
        pct = int(str(label).split("–")[0])
        if pct >= 61:
            return "#EF4444"  # high risk
        if pct >= 41:
            return "#F59E0B"  # medium
        return "#10B981"      # low

    bar_colors = [bucket_color(b) for b in bucket_counts["Bracket"].astype(str)]
    fig = go.Figure(go.Bar(
        x=bucket_counts["Bracket"].astype(str),
        y=bucket_counts["Count"],
        marker_color=bar_colors,
        hovertemplate="<b>%{x}</b><br>%{y} shipments<extra></extra>",
    ))
    fig.update_layout(
        **_DARK, height=height,
        margin=dict(l=0, r=0, t=8, b=0),
        xaxis=dict(tickfont=dict(size=11), **_GRID),
        yaxis=dict(tickfont=dict(size=11), **_GRID),
    )
    return fig


def _build_carrier_risk_fig(df: pd.DataFrame, height=260, sort_by="Value ↓") -> go.Figure:
    if len(df) == 0:
        return go.Figure()
    carrier_risk = df.groupby("carrier")["risk_score"].mean().reset_index()
    carrier_risk["risk_pct"] = (carrier_risk["risk_score"] * 100).round(1)
    if sort_by == "Value ↑":
        carrier_risk = carrier_risk.sort_values("risk_score", ascending=False)
    elif sort_by == "Value ↓":
        carrier_risk = carrier_risk.sort_values("risk_score", ascending=True)
    else:
        carrier_risk = carrier_risk.sort_values("carrier", ascending=False)
    fig = go.Figure(go.Bar(
        x=carrier_risk["risk_pct"],
        y=carrier_risk["carrier"],
        orientation="h",
        marker_color="#563457",
        text=carrier_risk["risk_pct"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Avg Risk: %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        **_DARK, height=height,
        margin=dict(l=0, r=80, t=8, b=0),
        xaxis=dict(title="Avg Risk Score (%)", range=[0, 100],
                   tickfont=dict(size=11), **_GRID),
        yaxis=dict(tickfont=dict(size=11), color="#94A3B8"),
    )
    return fig


def _build_tier_breakdown_fig(df: pd.DataFrame, height=260) -> go.Figure:
    if len(df) == 0:
        return go.Figure()
    tiers = ["Low", "Medium", "High"]
    counts = [int((df["risk_tier"] == t).sum()) for t in tiers]
    costs = [float(df.loc[df["risk_tier"] == t, "accessorial_charge_usd"].sum()) for t in tiers]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Shipments", x=tiers, y=counts, marker_color="#1B435E"))
    fig.add_trace(go.Bar(name="Est. Accessorial ($)", x=tiers, y=costs, marker_color="#2DD4BF", opacity=0.9))
    fig.update_layout(
        barmode="group",
        **_DARK,
        height=height,
        margin=dict(l=0, r=0, t=8, b=0),
        legend=dict(orientation="h", y=1.12, x=0, font=dict(color="#F1F5F9")),
        xaxis=dict(**_GRID),
        yaxis=dict(**_GRID),
    )
    return fig


def _build_shipments_over_time_fig(df: pd.DataFrame, height=260) -> go.Figure:
    if len(df) == 0:
        return go.Figure()
    dfx = df.copy()
    dfx["week"] = dfx["ship_date_dt"].dt.to_period("W").dt.start_time
    wk = (
        dfx.groupby("week")
        .agg(shipments=("shipment_id", "count"), avg_risk=("risk_score", "mean"))
        .reset_index()
        .sort_values("week")
    )
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Shipments",
        x=wk["week"],
        y=wk["shipments"],
        marker_color="rgba(27,67,94,0.85)",
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>%{y} shipments<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        name="Avg Risk (%)",
        x=wk["week"],
        y=(wk["avg_risk"] * 100).round(1),
        mode="lines+markers",
        line=dict(color="#F59E0B", width=2),
        marker=dict(size=6),
        yaxis="y2",
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>%{y:.1f}% avg risk<extra></extra>",
    ))
    fig.update_layout(
        **_DARK,
        height=height,
        margin=dict(l=0, r=0, t=8, b=0),
        legend=dict(orientation="h", y=1.12, x=0, font=dict(color="#F1F5F9")),
        xaxis=dict(**_GRID),
        yaxis=dict(title="Shipments", **_GRID),
        yaxis2=dict(
            title="Avg Risk (%)",
            overlaying="y",
            side="right",
            range=[0, 100],
            ticksuffix="%",
            gridcolor="rgba(0,0,0,0)",
            color="#94A3B8",
        ),
    )
    return fig


# ── Expand dialogs (module-level) ─────────────────────────────────────────────
@st.dialog("Risk Score Distribution", width="large")
def _popup_risk_dist():
    st.caption(f"{len(df_all):,} shipments · all time")
    st.plotly_chart(_build_risk_dist_fig(df_all, height=480),
                    width="stretch")


@st.dialog("Avg Risk Score by Carrier", width="large")
def _popup_carrier_risk():
    sort_by = _sort_buttons("carrier_risk")
    st.caption(f"{len(df_all):,} shipments · all carriers")
    if len(df_all) == 0:
        st.info("No data available.")
    else:
        st.plotly_chart(_build_carrier_risk_fig(df_all, height=480, sort_by=sort_by),
                        width="stretch")


# ── Inline filters ────────────────────────────────────────────────────────────
min_date = df_all["ship_date_dt"].min().date()
max_date = df_all["ship_date_dt"].max().date()
carriers = sorted(df_all["carrier"].unique())
facilities = sorted(df_all["facility"].astype(str).fillna("Unknown").unique())

with st.expander("⚙️ Filters", expanded=False):
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        date_range = st.date_input(
            "Ship Date Range", value=(min_date, max_date),
            min_value=min_date, max_value=max_date, key="dash_date"
        )
    with f2:
        sel_carriers = st.multiselect("Carrier", carriers, default=carriers, key="dash_carriers")
    with f3:
        sel_tiers = st.multiselect(
            "Risk Tier", ["Low", "Medium", "High"],
            default=["Low", "Medium", "High"], key="dash_tiers"
        )
    with f4:
        sel_facilities = st.multiselect("Facility Type", facilities, default=facilities, key="dash_facility")

# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_all.copy()
if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    df = df[(df["ship_date_dt"] >= start) & (df["ship_date_dt"] <= end)]
if sel_carriers:
    df = df[df["carrier"].isin(sel_carriers)]
if sel_tiers:
    df = df[df["risk_tier"].isin(sel_tiers)]
if sel_facilities:
    df = df[df["facility"].astype(str).isin(sel_facilities)]

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("## Risk Dashboard")
st.caption(f"Showing {len(df):,} shipments matching current filters")
st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
total        = len(df)
avg_risk     = df["risk_score"].mean() * 100 if total else 0
high_risk    = len(df[df["risk_tier"] == "High"])
est_cost     = df["accessorial_charge_usd"].sum()

total_delta     = total - len(df_all)
avg_risk_delta  = (df["risk_score"].mean() - df_all["risk_score"].mean()) * 100 if total else 0
high_risk_delta = high_risk - len(df_all[df_all["risk_tier"] == "High"])
est_cost_delta  = est_cost - df_all["accessorial_charge_usd"].sum()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Shipments",     f"{total:,}",            delta=f"{total_delta:+,} vs all")
with c2:
    st.metric("Avg Risk Score",      f"{avg_risk:.1f}%",      delta=f"{avg_risk_delta:+.1f}%")
with c3:
    st.metric("High-Risk Shipments", f"{high_risk:,}",        delta=f"{high_risk_delta:+,} vs all")
with c4:
    st.metric("Est. Accessorial Cost", f"${est_cost:,.0f}",  delta=f"${est_cost_delta:+,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Main visualizations (2-column layout) ─────────────────────────────────────
col_left, col_right = st.columns(2, gap="medium")

with col_left:
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Risk Score Distribution")
            st.caption("Number of shipments by risk score bracket (0–20 … 81–100)")
        with btn:
            if st.button("⤢", key="exp_risk_dist", help="Expand chart"):
                _popup_risk_dist()

        if total > 0:
            st.plotly_chart(_build_risk_dist_fig(df), width="stretch")
        else:
            st.info("No data matches the current filters.")

    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Avg Risk Score by Carrier")
            st.caption("Carriers ranked by average predicted risk")
        with btn:
            if st.button("Expand", key="exp_carrier_risk", help="Expand chart"):
                _popup_carrier_risk()
        if total > 0:
            sort_by = _sort_buttons("carrier_risk_inline")
            st.plotly_chart(_build_carrier_risk_fig(df, sort_by=sort_by), width="stretch")
        else:
            st.info("No data matches the current filters.")

with col_right:
    with st.container(border=True):
        st.markdown("#### Risk Tier Breakdown")
        st.caption("Shipment counts and expected accessorial exposure by tier")
        if total > 0:
            st.plotly_chart(_build_tier_breakdown_fig(df), width="stretch")
        else:
            st.info("No data matches the current filters.")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Shipments Over Time (with Risk Overlay)")
        st.caption("Shipment volume over time with average risk overlay")
        if total > 0:
            st.plotly_chart(_build_shipments_over_time_fig(df), width="stretch")
        else:
            st.info("No data matches the current filters.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Shipments table ───────────────────────────────────────────────────────────
with st.container(border=True):
    th_col, search_col = st.columns([3, 1])
    with th_col:
        st.markdown("#### Shipments")
        st.caption("Searchable shipments table with a detail preview selector")
    with search_col:
        search = st.text_input("Search", placeholder="🔍 Search shipment ID…", label_visibility="collapsed")

    table_df = df.copy()
    if search:
        table_df = table_df[table_df["shipment_id"].astype(str).str.contains(search.upper(), na=False)]

    st.dataframe(
        table_df[[
            "shipment_id", "ship_date", "OriginRegion", "DestRegion", "carrier", "facility",
            "risk_score", "risk_tier",
        ]].rename(columns={
            "shipment_id":            "Shipment ID",
            "ship_date":              "Ship Date",
            "OriginRegion":           "Origin",
            "DestRegion":             "Destination",
            "carrier":                "Carrier",
            "facility":               "Facility Type",
            "risk_score":             "Risk Score",
            "risk_tier":              "Risk Tier",
        }),
        width="stretch",
        hide_index=True,
        column_config={
            "Risk Score": st.column_config.ProgressColumn(
                "Risk Score", format="%.0f%%", min_value=0, max_value=1,
            ),
        },
        height=400,
    )
    st.caption(f"{len(table_df):,} shipments shown")

    if len(table_df) > 0:
        st.divider()
        pick = st.selectbox(
            "View details",
            options=table_df["shipment_id"].astype(str).tolist()[:200],
            help="Prototype interaction for shipment details. Implement row actions in a dedicated details page later.",
        )
        row = table_df[table_df["shipment_id"].astype(str) == str(pick)].head(1)
        if not row.empty:
            r = row.iloc[0]
            st.markdown(
                f"**{r['shipment_id']}** · {r.get('OriginRegion','?')} → {r.get('DestRegion','?')} · "
                f"{r.get('carrier','?')} · Facility: {r.get('facility','?')}"
            )
            st.caption(
                f"Risk: {(float(r.get('risk_score',0))*100):.1f}% ({r.get('risk_tier','—')}) · "
                f"Est. Accessorial: ${float(r.get('accessorial_charge_usd',0)):,.0f}"
            )
