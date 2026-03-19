# File: pages/1_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_utils import require_auth
from utils.database import load_shipments_with_fallback
from utils.styling import (
    inject_css, top_nav,
    NAVY_900, NAVY_500, chart_theme, risk_badge_html,
    TIER_BG_FG, CHARGE_COLORS,
)
from pipeline.config import CHARGE_TYPE_LABELS, is_pace_model_ready

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PACE — Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Auth guard ────────────────────────────────────────────────────────────────
require_auth()
username = st.session_state.get("username", "User")
top_nav(username)

# ── Model availability ────────────────────────────────────────────────────────
MODEL_READY = is_pace_model_ready()

# ── Load data ─────────────────────────────────────────────────────────────────
df_raw = load_shipments_with_fallback()
df_raw["ship_date_dt"] = pd.to_datetime(df_raw["ship_date"])
df_all = df_raw

# ── Schema normalization (support both mock and PACE schema) ──────────────────
if "risk_score_pct" not in df_all.columns:
    if "risk_score" in df_all.columns:
        df_all["risk_score_pct"] = df_all["risk_score"] * 100
    else:
        df_all["risk_score_pct"] = 0.0

if "risk_label" not in df_all.columns:
    if "risk_tier" in df_all.columns:
        df_all["risk_label"] = df_all["risk_tier"]
    else:
        df_all["risk_label"] = df_all["risk_score_pct"].apply(
            lambda s: "Critical" if s >= 75 else
                      "High"     if s >= 50 else
                      "Medium"   if s >= 25 else
                      "Low"      if s > 0  else "None"
        )

if "risk_tier" not in df_all.columns:
    df_all["risk_tier"] = df_all["risk_label"]

if "charge_type" not in df_all.columns:
    df_all["charge_type"] = df_all.get("accessorial_type", "Unknown")

# Merge in PACE scored data from upload if available
if st.session_state.get("upload_scored") is not None:
    scored = st.session_state["upload_scored"]
    id_col = next(
        (c for c in ["unique_id", "dot_number", "shipment_id"]
         if c in scored.columns and c in df_all.columns),
        None,
    )
    if id_col and "charge_type" in scored.columns:
        df_all = df_all.merge(
            scored[[id_col, "charge_type", "risk_score_pct", "risk_label"]],
            on=id_col, how="left", suffixes=("", "_pace"),
        )
        for col in ["charge_type", "risk_score_pct", "risk_label"]:
            if f"{col}_pace" in df_all.columns:
                df_all[col] = df_all[f"{col}_pace"].fillna(df_all[col])
                df_all.drop(columns=[f"{col}_pace"], inplace=True)

# ── ID column detection ───────────────────────────────────────────────────────
ID_COL = next(
    (c for c in ["shipment_id", "unique_id", "dot_number"]
     if c in df_all.columns),
    df_all.columns[0] if len(df_all.columns) > 0 else "id",
)

# ── Shared chart style constants ──────────────────────────────────────────────
_DARK = dict(plot_bgcolor="#0f0a1e", paper_bgcolor="#0f0a1e",
             font=dict(color="#A78BFA"))
_GRID = dict(gridcolor="rgba(150,50,200,0.15)", color="#94A3B8",
             linecolor="rgba(150,50,200,0.2)")


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


# ── Chart builders ────────────────────────────────────────────────────────────
def _build_risk_dist_fig(df: pd.DataFrame, height=260) -> go.Figure:
    if len(df) == 0:
        return go.Figure()
    hist_df = df.copy()
    hist_df["bucket"] = pd.cut(
        hist_df["risk_score"],
        bins=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        labels=["0–10%", "10–20%", "20–30%", "30–40%", "40–50%",
                "50–60%", "60–70%", "70–80%", "80–90%", "90–100%"],
        include_lowest=True,
    )
    bucket_counts = hist_df["bucket"].value_counts().sort_index().reset_index()
    bucket_counts.columns = ["Bracket", "Count"]

    def bucket_color(label):
        pct = int(label.split("–")[0])
        if pct >= 67: return "#EF4444"
        if pct >= 34: return "#A855F7"
        return "#34D399"

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
        marker_color="#9333EA",
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


# ── Expand dialogs ────────────────────────────────────────────────────────────
@st.dialog("Risk Score Distribution", width="large")
def _popup_risk_dist():
    st.caption(f"{len(df_all):,} shipments · all time")
    st.plotly_chart(_build_risk_dist_fig(df_all, height=480), width="stretch")


@st.dialog("Avg Risk Score by Carrier", width="large")
def _popup_carrier_risk():
    sort_by = _sort_buttons("carrier_risk")
    st.caption(f"{len(df_all):,} shipments · all carriers")
    if len(df_all) == 0:
        st.info("No data available.")
    else:
        st.plotly_chart(_build_carrier_risk_fig(df_all, height=480, sort_by=sort_by),
                        width="stretch")


# ── Route Analysis helpers ────────────────────────────────────────────────────
def _filter_by_range(df: pd.DataFrame, sel: str) -> pd.DataFrame:
    days_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365}
    if sel not in days_map:
        return df
    cutoff = df["ship_date_dt"].max() - pd.Timedelta(days=days_map[sel])
    return df[df["ship_date_dt"] >= cutoff]


def _range_buttons(chart_key: str):
    opts = ["1M", "3M", "6M", "1Y", "All"]
    skey = f"popup_range_{chart_key}"
    if skey not in st.session_state:
        st.session_state[skey] = "All"
    cols = st.columns(len(opts))
    for col, lbl in zip(cols, opts):
        with col:
            kind = "primary" if st.session_state[skey] == lbl else "secondary"
            if st.button(lbl, key=f"rb_{chart_key}_{lbl}", type=kind, width="stretch"):
                st.session_state[skey] = lbl
    return st.session_state[skey]


def _build_lane_metrics(df: pd.DataFrame, group_col: str, label: str,
                        min_vol: int = 1) -> pd.DataFrame:
    lm = (
        df.groupby(group_col)
        .agg(
            shipments        =("shipment_id",            "count"),
            avg_cost         =("total_cost_usd",          "mean"),
            total_cost       =("total_cost_usd",          "sum"),
            avg_cpm          =("cost_per_mile",           "mean"),
            avg_miles        =("miles",                   "mean"),
            avg_risk         =("risk_score",              "mean"),
            accessorial_cost =("accessorial_charge_usd",  "sum"),
            high_risk_count  =("risk_tier", lambda x: (x == "High").sum()),
        )
        .reset_index()
        .rename(columns={group_col: label})
    )
    lm = lm[lm["shipments"] >= min_vol].copy()
    lm["accessorial_rate"] = (lm["accessorial_cost"] / lm["total_cost"] * 100).round(1)
    lm["high_risk_pct"]    = (lm["high_risk_count"]  / lm["shipments"]  * 100).round(1)
    return lm


_ROUTE_LAYOUT = dict(
    plot_bgcolor="#0f0a1e", paper_bgcolor="#0f0a1e", font=dict(color="#A78BFA"),
    xaxis=dict(gridcolor="rgba(150,50,200,0.15)", color="#94A3B8",
               linecolor="rgba(150,50,200,0.2)"),
    yaxis=dict(gridcolor="rgba(150,50,200,0.15)", color="#94A3B8",
               linecolor="rgba(150,50,200,0.2)"),
)


def _build_expensive_fig(lane_metrics: pd.DataFrame, label: str, height=300) -> go.Figure:
    top_exp = lane_metrics.nlargest(8, "avg_cpm").sort_values("avg_cpm")
    fig = go.Figure(go.Bar(
        x=top_exp["avg_cpm"],
        y=top_exp[label].apply(lambda v: v if len(v) <= 28 else v[:25] + "…"),
        orientation="h", marker_color="#DC2626",
        text=top_exp["avg_cpm"].apply(lambda v: f"${v:.2f}/mi"),
        textposition="outside",
    ))
    fig.update_layout(**_ROUTE_LAYOUT, margin=dict(l=0, r=160, t=8, b=0), height=height,
                      xaxis_tickprefix="$")
    return fig


def _build_efficient_fig(lane_metrics: pd.DataFrame, label: str, height=300) -> go.Figure:
    top_cheap = lane_metrics.nsmallest(8, "avg_cpm").sort_values("avg_cpm", ascending=False)
    fig = go.Figure(go.Bar(
        x=top_cheap["avg_cpm"],
        y=top_cheap[label].apply(lambda v: v if len(v) <= 28 else v[:25] + "…"),
        orientation="h", marker_color="#059669",
        text=top_cheap["avg_cpm"].apply(lambda v: f"${v:.2f}/mi"),
        textposition="outside",
    ))
    fig.update_layout(**_ROUTE_LAYOUT, margin=dict(l=0, r=160, t=8, b=0), height=height,
                      xaxis_tickprefix="$")
    return fig


def _build_scatter_fig(lane_metrics: pd.DataFrame, label: str, height=320) -> go.Figure:
    fig = px.scatter(
        lane_metrics, x="shipments", y="avg_cost", size="total_cost", color="avg_risk",
        hover_name=label,
        color_continuous_scale=["#059669", "#D97706", "#DC2626"],
        labels={"shipments": "Shipment Volume", "avg_cost": "Avg Total Cost ($)",
                "avg_risk": "Avg Risk Score", "total_cost": "Total Spend"},
        hover_data={"avg_cpm": ":.2f", "accessorial_rate": ":.1f"},
    )
    fig.update_layout(**_ROUTE_LAYOUT, margin=dict(l=0, r=0, t=8, b=0), height=height,
                      yaxis_tickprefix="$")
    return fig


def _resolve_group():
    view_by = st.session_state.get("route_view_by", "Lane (Origin → Dest)")
    if view_by == "Lane (Origin → Dest)":
        return "lane", "Lane"
    elif "Origin" in view_by:
        return "origin_city", "Origin"
    else:
        return "destination_city", "Destination"


@st.dialog("Most Expensive Lanes", width="large")
def _popup_expensive():
    sel = _range_buttons("expensive")
    df_f = _filter_by_range(df_all, sel)
    group_col, label = _resolve_group()
    lm = _build_lane_metrics(df_f, group_col, label, min_vol=1)
    st.caption(f"{len(df_f):,} shipments · {sel} view")
    if lm.empty:
        st.info("No data for the selected range.")
    else:
        st.plotly_chart(_build_expensive_fig(lm, label, height=480), width="stretch")


@st.dialog("Most Efficient Lanes", width="large")
def _popup_efficient():
    sel = _range_buttons("efficient")
    df_f = _filter_by_range(df_all, sel)
    group_col, label = _resolve_group()
    lm = _build_lane_metrics(df_f, group_col, label, min_vol=1)
    st.caption(f"{len(df_f):,} shipments · {sel} view")
    if lm.empty:
        st.info("No data for the selected range.")
    else:
        st.plotly_chart(_build_efficient_fig(lm, label, height=480), width="stretch")


@st.dialog("Lane Volume vs Avg Cost", width="large")
def _popup_scatter():
    sel = _range_buttons("scatter")
    df_f = _filter_by_range(df_all, sel)
    group_col, label = _resolve_group()
    lm = _build_lane_metrics(df_f, group_col, label, min_vol=1)
    st.caption(f"{len(df_f):,} shipments · {sel} view")
    if lm.empty:
        st.info("No data for the selected range.")
    else:
        st.plotly_chart(_build_scatter_fig(lm, label, height=500), width="stretch")


# ── Session state ─────────────────────────────────────────────────────────────
if "selected_shipment" not in st.session_state:
    st.session_state["selected_shipment"] = None


# ── Detail view ───────────────────────────────────────────────────────────────
def render_detail(row: pd.Series):
    label   = str(row.get("risk_label", row.get("risk_tier", "Unknown")))
    score   = float(row.get("risk_score_pct", row.get("risk_score", 0) * 100))
    charge  = str(row.get("charge_type", row.get("accessorial_type", "Unknown")))
    bg, fg  = TIER_BG_FG.get(label, ("#1E293B", "#94A3B8"))
    c_color = CHARGE_COLORS.get(charge, "#A78BFA")
    ship_id = row.get(ID_COL, "Unknown")

    if st.button("← Back to Dashboard"):
        st.session_state["selected_shipment"] = None
        st.rerun()

    st.markdown(
        f"<div style='font-size:12px;color:#94A3B8;margin-bottom:12px;'>"
        f"Dashboard / Shipments / <b style='color:#E2E8F0'>{ship_id}</b></div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        h1, h2, h3 = st.columns([5, 1, 1])
        with h1:
            st.markdown(f"### {ship_id}")
        with h2:
            st.markdown(
                f"<div style='text-align:right;padding-top:6px;'>"
                f"<span style='background:{bg};color:{fg};padding:4px 12px;"
                f"border-radius:4px;font-size:12px;font-weight:700;'>"
                f"{label.upper()}</span></div>",
                unsafe_allow_html=True,
            )
        with h3:
            st.markdown(
                f"<div style='text-align:right;padding-top:6px;'>"
                f"<span style='border:1px solid {c_color};color:{c_color};"
                f"padding:4px 10px;border-radius:4px;font-size:11px;"
                f"font-weight:600;'>{charge}</span></div>",
                unsafe_allow_html=True,
            )

        field_map = {
            "carrier":                "Carrier",
            "facility":               "Facility",
            "ship_date":              "Ship Date",
            "dot_number":             "DOT Number",
            "carrier_phy_state":      "State",
            "base_freight_usd":       "Base Freight",
            "accessorial_charge_usd": "Accessorial ($)",
        }
        available = {
            lbl: row[col]
            for col, lbl in field_map.items()
            if col in row.index and pd.notna(row.get(col))
        }
        if available:
            cols = st.columns(min(len(available), 5))
            for i, (lbl, val) in enumerate(list(available.items())[:5]):
                with cols[i]:
                    st.markdown(f"**{lbl}**")
                    if isinstance(val, float):
                        st.write(f"${val:,.2f}" if "($)" in lbl or "Freight" in lbl
                                 else f"{val:,.0f}")
                    else:
                        st.write(str(val)[:10] if "Date" in lbl else str(val))

    st.markdown("<br>", unsafe_allow_html=True)
    left_col, right_col = st.columns([2, 3], gap="medium")

    with left_col:
        with st.container(border=True):
            st.markdown("#### PACE Risk Score")
            gauge_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=round(score, 1),
                number={"suffix": "%", "font": {"size": 36, "color": fg}},
                title={"text": f"<b>{label}</b>", "font": {"size": 14, "color": fg}},
                gauge={
                    "axis": {"range": [0, 100],
                             "tickfont": {"color": "#94A3B8", "size": 10}},
                    "bar":  {"color": fg, "thickness": 0.25},
                    "bgcolor": "#0f0a1e",
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0,  25], "color": "rgba(5,150,105,0.15)"},
                        {"range": [25, 50], "color": "rgba(251,146,60,0.10)"},
                        {"range": [50, 75], "color": "rgba(217,119,6,0.15)"},
                        {"range": [75,100], "color": "rgba(220,38,38,0.15)"},
                    ],
                },
            ))
            gauge_fig.update_layout(
                height=200, margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="#0f0a1e", font={"color": "#A78BFA"},
            )
            st.plotly_chart(gauge_fig, use_container_width=True)

            st.markdown(
                f"<div style='background:rgba(0,0,0,0.3);border:1px solid "
                f"{c_color};border-radius:6px;padding:10px 14px;margin-top:8px;'>"
                f"<div style='color:#94A3B8;font-size:10px;font-weight:600;"
                f"letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;'>"
                f"Predicted Charge Type</div>"
                f"<div style='color:{c_color};font-size:16px;font-weight:700;'>"
                f"{charge}</div></div>",
                unsafe_allow_html=True,
            )

            prob_cols = [c for c in row.index if str(c).startswith("prob_")]
            if prob_cols:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    "<p style='color:#94A3B8;font-size:11px;margin:0 0 6px;'>"
                    "Charge Probabilities</p>",
                    unsafe_allow_html=True,
                )
                for pc in sorted(prob_cols, key=lambda x: float(row[x]), reverse=True)[:4]:
                    pct = float(row[pc]) * 100
                    lbl = pc.replace("prob_", "").replace("_", " ").title()
                    bar_color = CHARGE_COLORS.get(lbl, "#A78BFA")
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>"
                        f"<span style='color:#94A3B8;font-size:11px;min-width:120px;'>{lbl}</span>"
                        f"<div style='flex:1;background:rgba(255,255,255,0.08);border-radius:3px;height:6px;'>"
                        f"<div style='width:{pct:.0f}%;background:{bar_color};height:6px;border-radius:3px;'></div></div>"
                        f"<span style='color:#E2E8F0;font-size:11px;min-width:36px;text-align:right;'>{pct:.1f}%</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

    with right_col:
        with st.container(border=True):
            st.markdown("#### Risk Factor Breakdown")
            viol_factors = {}
            if "oos_total" in row.index:
                viol_factors["OOS Violations"]    = float(row.get("oos_total", 0))
            if "basic_viol" in row.index:
                viol_factors["Basic Violations"]  = float(row.get("basic_viol", 0))
            if "unsafe_viol" in row.index:
                viol_factors["Unsafe Violations"] = float(row.get("unsafe_viol", 0))
            if "crash_count" in row.index:
                viol_factors["Crash History"]     = float(row.get("crash_count", 0)) * 5
            if "vh_maint_viol" in row.index:
                viol_factors["Vehicle Maint."]    = float(row.get("vh_maint_viol", 0))

            if not viol_factors:
                w = float(row.get("weight_lbs", 0))
                m = float(row.get("miles", 0))
                viol_factors = {
                    "Carrier History":  0.30,
                    "Facility Profile": 0.25,
                    "Miles / Distance": min(m / 5000 * 0.20, 0.20),
                    "Shipment Weight":  min(w / 44000 * 0.15, 0.15),
                    "Base Freight":     0.10,
                }

            total_w = sum(viol_factors.values()) or 1
            for factor, weight in sorted(viol_factors.items(), key=lambda x: -x[1])[:6]:
                pct = (weight / total_w) * 100
                fc1, fc2, fc3 = st.columns([3, 5, 1])
                with fc1:
                    st.markdown(f"<span style='font-size:12px;color:#CBD5E1;'>{factor}</span>",
                                unsafe_allow_html=True)
                with fc2:
                    st.progress(pct / 100)
                with fc3:
                    st.markdown(f"<span style='font-size:12px;font-weight:600;color:#E2E8F0;'>{pct:.0f}%</span>",
                                unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("#### Recommended Actions")
            oos     = float(row.get("oos_total", 0))
            viols   = float(row.get("basic_viol", 0)) + float(row.get("unsafe_viol", 0))
            acc_est = float(row.get("accessorial_charge_usd", 0))

            if label in ("Critical", "High"):
                actions = [
                    "Escalate to carrier compliance team before dispatch.",
                    f"Add accessorial buffer of ${acc_est * 0.8:,.0f}–${acc_est * 1.3:,.0f} to quote.",
                    "Request morning appointment window to reduce detention risk.",
                    "Verify dock availability and confirm appointment 24h in advance.",
                ]
                if oos > 5:
                    actions.append(f"Carrier has {oos:.0f} OOS events — consider alternative carrier for this lane.")
                if viols > 10:
                    actions.append(f"High violation count ({viols:.0f}) — flag for safety review before booking.")
            elif label == "Medium":
                actions = [
                    "Monitor appointment confirmation — delays increase detention risk.",
                    f"Consider ${acc_est * 0.5:,.0f}–${acc_est:,.0f} contingency buffer.",
                    "Verify carrier's recent performance on similar lanes.",
                ]
            else:
                actions = [
                    "Low risk profile — standard operating procedure applies.",
                    "No additional accessorial buffer needed for this load.",
                ]

            for i, action in enumerate(actions, 1):
                st.markdown(
                    f"<div style='display:flex;align-items:flex-start;gap:10px;margin:8px 0;'>"
                    f"<span style='background:{NAVY_500};color:white;border-radius:50%;"
                    f"width:22px;height:22px;min-width:22px;display:flex;align-items:center;"
                    f"justify-content:center;font-size:12px;font-weight:700;'>{i}</span>"
                    f"<span style='font-size:13px;color:#E2E8F0;'>{action}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Similar Shipments — Historical Comparison")
        carrier_val = row.get("carrier", row.get("carrier_phy_state", None))
        carrier_col = "carrier" if "carrier" in df_all.columns else None
        if carrier_val and carrier_col:
            similar = df_all[df_all[carrier_col] == carrier_val].head(10)
        else:
            similar = df_all.head(10)

        sim_cols = [c for c in [
            ID_COL, "ship_date", "facility", "carrier_phy_state",
            "risk_score_pct", "risk_label", "charge_type", "accessorial_charge_usd",
        ] if c in similar.columns]

        col_config = {}
        if "risk_score_pct" in sim_cols:
            col_config["risk_score_pct"] = st.column_config.ProgressColumn(
                "Risk Score", format="%.1f%%", min_value=0, max_value=100
            )
        if "accessorial_charge_usd" in sim_cols:
            col_config["accessorial_charge_usd"] = st.column_config.NumberColumn(
                "Actual Charge ($)", format="$%.2f"
            )
        st.dataframe(similar[sim_cols], use_container_width=True, hide_index=True, column_config=col_config)


# ── Show detail view if a shipment is selected ────────────────────────────────
if st.session_state["selected_shipment"] is not None:
    sid   = st.session_state["selected_shipment"]
    match = df_all[df_all[ID_COL].astype(str) == str(sid)]
    if not match.empty:
        render_detail(match.iloc[0])
    else:
        st.warning("Shipment not found.")
        st.session_state["selected_shipment"] = None
        st.rerun()
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

# ── Filters ───────────────────────────────────────────────────────────────────
min_date  = df_all["ship_date_dt"].min().date()
max_date  = df_all["ship_date_dt"].max().date()
carriers  = sorted(df_all["carrier"].unique()) if "carrier" in df_all.columns else []

with st.expander("⚙️ Filters", expanded=False):
    f1, f2, f3 = st.columns(3)
    with f1:
        date_range = st.date_input(
            "Ship Date Range", value=(min_date, max_date),
            min_value=min_date, max_value=max_date, key="dash_date",
        )
    with f2:
        sel_carriers = st.multiselect("Carrier", carriers, default=carriers, key="dash_carriers")
    with f3:
        sel_tiers = st.multiselect(
            "Risk Tier", ["Low", "Medium", "High"],
            default=["Low", "Medium", "High"], key="dash_tiers",
        )

# ── Apply dashboard filters ───────────────────────────────────────────────────
df = df_all.copy()
if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    df = df[(df["ship_date_dt"] >= start) & (df["ship_date_dt"] <= end)]
if sel_carriers and "carrier" in df.columns:
    df = df[df["carrier"].isin(sel_carriers)]
if sel_tiers and "risk_tier" in df.columns:
    df = df[df["risk_tier"].isin(sel_tiers)]

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("## Risk Dashboard")
st.caption(f"Showing {len(df):,} shipments matching current filters")
st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
total        = len(df)
avg_risk     = df["risk_score"].mean() * 100 if total and "risk_score" in df.columns else 0
high_risk    = len(df[df["risk_tier"] == "High"]) if "risk_tier" in df.columns else 0
est_cost     = df["accessorial_charge_usd"].sum() if "accessorial_charge_usd" in df.columns else 0

total_delta     = total - len(df_all)
avg_risk_delta  = (df["risk_score"].mean() - df_all["risk_score"].mean()) * 100 if total and "risk_score" in df.columns else 0
high_risk_delta = high_risk - len(df_all[df_all["risk_tier"] == "High"]) if "risk_tier" in df_all.columns else 0
est_cost_delta  = est_cost - (df_all["accessorial_charge_usd"].sum() if "accessorial_charge_usd" in df_all.columns else 0)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Shipments",       f"{total:,}",          delta=f"{total_delta:+,} vs all")
with c2:
    st.metric("Avg Risk Score",        f"{avg_risk:.1f}%",    delta=f"{avg_risk_delta:+.1f}%")
with c3:
    st.metric("High-Risk Shipments",   f"{high_risk:,}",      delta=f"{high_risk_delta:+,} vs all")
with c4:
    st.metric("Est. Accessorial Cost", f"${est_cost:,.0f}",   delta=f"${est_cost_delta:+,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts row ────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2, gap="medium")

with col_left:
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Risk Score Distribution")
            st.caption("Number of shipments by risk score bracket")
        with btn:
            if st.button("⤢", key="exp_risk_dist", help="Expand chart"):
                _popup_risk_dist()
        if total > 0 and "risk_score" in df.columns:
            st.plotly_chart(_build_risk_dist_fig(df), width="stretch")
        else:
            st.info("No data matches the current filters.")

with col_right:
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Avg Risk Score by Carrier")
            st.caption("Carriers ranked by average predicted risk")
        with btn:
            if st.button("⤢", key="exp_carrier_risk", help="Expand chart"):
                _popup_carrier_risk()
        if total > 0 and "carrier" in df.columns and "risk_score" in df.columns:
            st.plotly_chart(_build_carrier_risk_fig(df), width="stretch")
        else:
            st.info("No data matches the current filters.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Risk tier summary ─────────────────────────────────────────────────────────
if "risk_tier" in df.columns:
    with st.container(border=True):
        st.markdown("#### Risk Tier Breakdown")
        st.caption("Shipment counts and accessorial exposure by tier")
        t1, t2, t3 = st.columns(3)
        for col, tier, bg, fg in [
            (t1, "Low",    "rgba(5,150,105,0.85)",  "#34D399"),
            (t2, "Medium", "rgba(80,20,160,0.85)",   "#A78BFA"),
            (t3, "High",   "rgba(180,20,20,0.85)",   "#F87171"),
        ]:
            tier_df = df[df["risk_tier"] == tier]
            with col:
                acc_sum = tier_df["accessorial_charge_usd"].sum() if "accessorial_charge_usd" in tier_df.columns else 0
                st.markdown(
                    f"<div style='background:{bg};border:1px solid {fg}33;border-radius:10px;"
                    f"padding:16px 20px;text-align:center;'>"
                    f"<div style='font-size:11px;font-weight:600;letter-spacing:0.8px;"
                    f"color:{fg};text-transform:uppercase;margin-bottom:6px;'>{tier} Risk</div>"
                    f"<div style='font-size:28px;font-weight:700;color:#FFFFFF;'>{len(tier_df):,}</div>"
                    f"<div style='font-size:12px;color:{fg};margin-top:4px;'>"
                    f"${acc_sum:,.0f} accessorial</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SHIPMENTS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("## Shipments")

if not MODEL_READY:
    st.info(
        "PACE model not yet trained — risk scores are placeholders. "
        "Scores will update automatically after training completes.",
        icon="ℹ️",
    )

# ── Shipment filters ──────────────────────────────────────────────────────────
with st.expander("⚙️ Shipment Filters", expanded=False):
    sf1, sf2, sf3, sf4 = st.columns(4)
    carrier_col  = "carrier"  if "carrier"  in df_all.columns else None
    facility_col = "facility" if "facility" in df_all.columns else None

    with sf1:
        s_carriers = []
        if carrier_col:
            all_carriers = sorted(df_all[carrier_col].dropna().unique())
            s_carriers = st.multiselect("Carrier", all_carriers, default=all_carriers, key="ship_carriers")

    with sf2:
        s_facilities = []
        if facility_col:
            all_facilities = sorted(df_all[facility_col].dropna().unique())
            s_facilities = st.multiselect("Facility", all_facilities, default=all_facilities, key="ship_facilities")

    with sf3:
        all_labels = sorted(df_all["risk_label"].dropna().unique()) if "risk_label" in df_all.columns else []
        s_labels = st.multiselect("Risk Label", all_labels, default=all_labels, key="ship_labels")

    with sf4:
        all_charges = sorted(df_all["charge_type"].dropna().unique()) if "charge_type" in df_all.columns else []
        s_charges = st.multiselect("Charge Type", all_charges, default=all_charges, key="ship_charges")

# ── Apply shipment filters ────────────────────────────────────────────────────
df_ship = df_all.copy()
if s_carriers and carrier_col:
    df_ship = df_ship[df_ship[carrier_col].isin(s_carriers)]
if s_facilities and facility_col:
    df_ship = df_ship[df_ship[facility_col].isin(s_facilities)]
if s_labels and "risk_label" in df_ship.columns:
    df_ship = df_ship[df_ship["risk_label"].isin(s_labels)]
if s_charges and "charge_type" in df_ship.columns:
    df_ship = df_ship[df_ship["charge_type"].isin(s_charges)]

st.caption(f"{len(df_ship):,} shipments match current filters")
st.divider()

# ── Search ────────────────────────────────────────────────────────────────────
search = st.text_input(
    "Search",
    placeholder="🔍 Search by shipment ID, carrier, or DOT number...",
    label_visibility="collapsed",
)
if search.strip():
    str_cols = df_ship.select_dtypes(include=["object"]).columns
    mask = pd.Series(False, index=df_ship.index)
    for col in str_cols:
        mask |= df_ship[col].astype(str).str.contains(search.strip(), case=False, na=False)
    df_ship = df_ship[mask]

# ── Build display columns ─────────────────────────────────────────────────────
candidate_cols = [
    ID_COL, "ship_date", "carrier", "facility",
    "dot_number", "carrier_phy_state",
    "weight_lbs", "miles",
    "risk_score_pct", "risk_label", "charge_type",
    "accessorial_charge_usd", "base_freight_usd",
]
display_cols = [c for c in candidate_cols if c in df_ship.columns]

col_config = {}
if "risk_score_pct" in display_cols:
    col_config["risk_score_pct"] = st.column_config.ProgressColumn(
        "Risk Score", format="%.1f%%", min_value=0, max_value=100
    )
if "base_freight_usd" in display_cols:
    col_config["base_freight_usd"] = st.column_config.NumberColumn(
        "Base Freight ($)", format="$%.2f"
    )
if "accessorial_charge_usd" in display_cols:
    col_config["accessorial_charge_usd"] = st.column_config.NumberColumn(
        "Est. Accessorial ($)", format="$%.2f"
    )

with st.container(border=True):
    event = st.dataframe(
        df_ship[display_cols].head(500),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config=col_config,
        height=500,
    )

selected_rows = (
    event.selection.get("rows", [])
    if hasattr(event, "selection") else []
)
if selected_rows:
    row_idx = selected_rows[0]
    sid = df_ship[display_cols].head(500).iloc[row_idx][ID_COL]
    st.session_state["selected_shipment"] = sid
    st.rerun()

st.caption("Click any row to view full shipment detail and PACE prediction.")
if len(df_ship) > 500:
    st.caption(f"Showing first 500 of {len(df_ship):,} records. Use filters to narrow results.")

# ═══════════════════════════════════════════════════════════════════════════════
# ROUTE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("## Route Analysis")
st.caption("Identify your most and least expensive shipping lanes and optimize route selection.")

# ── Route filters ─────────────────────────────────────────────────────────────
with st.expander("⚙️ Route Filters", expanded=False):
    rf1, rf2 = st.columns(2)
    with rf1:
        min_vol = st.slider("Minimum shipments per lane", 1, 10, 2,
                            help="Filter out low-volume lanes")
    with rf2:
        view_by = st.radio(
            "Analyze by",
            ["Lane (Origin → Dest)", "Origin City", "Destination City"],
            horizontal=True, key="route_view_by",
        )

st.divider()

# ── Build lane metrics ────────────────────────────────────────────────────────
if view_by == "Lane (Origin → Dest)":
    route_group_col, route_label = "lane", "Lane"
else:
    route_group_col = "origin_city" if "Origin" in view_by else "destination_city"
    route_label     = "Origin"      if "Origin" in view_by else "Destination"

lane_metrics = _build_lane_metrics(df_raw.copy(), route_group_col, route_label, min_vol=min_vol)

# ── Route KPIs ────────────────────────────────────────────────────────────────
total_lanes   = len(lane_metrics)
busiest_lane  = lane_metrics.loc[lane_metrics["shipments"].idxmax(), route_label] if total_lanes else "—"
cheapest_lane = lane_metrics.loc[lane_metrics["avg_cpm"].idxmin(),   route_label] if total_lanes else "—"
most_exp_lane = lane_metrics.loc[lane_metrics["avg_cpm"].idxmax(),   route_label] if total_lanes else "—"

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Active Lanes",    f"{total_lanes}")
with k2:
    st.metric("Busiest Lane",    busiest_lane  if len(busiest_lane)  < 30 else busiest_lane[:27]  + "…")
with k3:
    st.metric("Cheapest $/Mile", cheapest_lane if len(cheapest_lane) < 30 else cheapest_lane[:27] + "…")
with k4:
    st.metric("Most Expensive",  most_exp_lane if len(most_exp_lane) < 30 else most_exp_lane[:27] + "…")

st.markdown("<br>", unsafe_allow_html=True)

# ── Route charts ──────────────────────────────────────────────────────────────
rc_left, rc_right = st.columns(2, gap="medium")

with rc_left:
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Most Expensive Lanes")
            st.caption("Top 8 by average cost per mile")
        with btn:
            if st.button("⤢", key="exp_expensive", help="Expand chart"):
                _popup_expensive()
        st.plotly_chart(_build_expensive_fig(lane_metrics, route_label), width="stretch")

with rc_right:
    with st.container(border=True):
        hdr, btn = st.columns([9, 1])
        with hdr:
            st.markdown("#### Most Efficient Lanes")
            st.caption("Top 8 by lowest average cost per mile")
        with btn:
            if st.button("⤢", key="exp_efficient", help="Expand chart"):
                _popup_efficient()
        st.plotly_chart(_build_efficient_fig(lane_metrics, route_label), width="stretch")

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    hdr, btn = st.columns([9, 1])
    with hdr:
        st.markdown("#### Lane Volume vs Avg Cost")
        st.caption("Identify high-volume expensive lanes — biggest opportunity for savings")
    with btn:
        if st.button("⤢", key="exp_scatter", help="Expand chart"):
            _popup_scatter()
    st.plotly_chart(_build_scatter_fig(lane_metrics, route_label), width="stretch")

st.markdown("<br>", unsafe_allow_html=True)

# ── Full lane table ───────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### All Lanes — Full Breakdown")
    display = lane_metrics.copy()
    display["avg_cost"]  = display["avg_cost"].round(2)
    display["avg_cpm"]   = display["avg_cpm"].round(3)
    display["avg_miles"] = display["avg_miles"].round(0).astype(int)
    display["avg_risk"]  = display["avg_risk"].round(3)

    st.dataframe(
        display[[route_label, "shipments", "avg_cost", "avg_cpm", "avg_miles",
                 "avg_risk", "accessorial_rate", "high_risk_pct", "total_cost"]]
        .rename(columns={
            "shipments":        "Shipments",
            "avg_cost":         "Avg Cost ($)",
            "avg_cpm":          "Avg $/Mile",
            "avg_miles":        "Avg Miles",
            "avg_risk":         "Avg Risk",
            "accessorial_rate": "Accessorial %",
            "high_risk_pct":    "High Risk %",
            "total_cost":       "Total Spend ($)",
        })
        .sort_values("Avg $/Mile", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "Avg Risk":        st.column_config.ProgressColumn("Avg Risk", format="%.0f%%", min_value=0, max_value=1),
            "Avg Cost ($)":    st.column_config.NumberColumn(format="$%.2f"),
            "Avg $/Mile":      st.column_config.NumberColumn(format="$%.3f"),
            "Total Spend ($)": st.column_config.NumberColumn(format="$%.0f"),
        },
        height=420,
    )
