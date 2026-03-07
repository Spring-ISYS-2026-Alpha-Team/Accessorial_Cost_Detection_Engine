# File: pages/6_Carrier_Comparison.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.database import load_shipments
from utils.styling import (
    inject_css, top_nav,
    NAVY_BG, CARD_BG, BORDER, PLUM,
    TEXT_PRIMARY, TEXT_SECONDARY,
    BRIGHT_TEAL, CORAL, LAVENDER, GOLD,
    DARK_LAYOUT,
)

st.set_page_config(
    page_title="PACE — Carrier Comparison",
    page_icon="P",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

if not check_auth():
    st.warning("Please sign in to access this page.")
    st.page_link("app.py", label="Go to Sign In")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)


df_all = load_shipments()
_all_carriers = sorted(df_all["carrier"].dropna().unique())

# ── Carrier selector ──────────────────────────────────────────────────────────
if "active_carriers" not in st.session_state:
    st.session_state["active_carriers"] = _all_carriers

with st.expander("Manage Carriers", expanded=False):
    f1, f2 = st.columns([5, 1])
    with f1:
        selected = st.multiselect(
            "Active Carriers",
            options=_all_carriers,
            default=st.session_state["active_carriers"],
        )
        st.session_state["active_carriers"] = selected
    with f2:
        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("All", use_container_width=True):
                st.session_state["active_carriers"] = _all_carriers
                st.rerun()
        with col_b:
            if st.button("Clear", use_container_width=True):
                st.session_state["active_carriers"] = []
                st.rerun()

active_carriers = st.session_state["active_carriers"]
if not active_carriers:
    st.markdown("## Carrier Comparison")
    st.warning("No carriers selected. Use the filter above to add carriers to the comparison.")
    st.stop()

df = df_all[df_all["carrier"].isin(active_carriers)].copy()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Carrier Comparison")
st.caption(
    f"Comparing {len(active_carriers)} carrier{'s' if len(active_carriers) != 1 else ''} "
    "across cost efficiency, risk profile, and accessorial charge rates."
)
st.divider()

# ── Carrier color map ─────────────────────────────────────────────────────────
CARRIER_COLORS = [BRIGHT_TEAL, LAVENDER, CORAL, GOLD, BORDER, PLUM, "#38BDF8", "#FB7185"]
color_map = {c: CARRIER_COLORS[i % len(CARRIER_COLORS)]
             for i, c in enumerate(_all_carriers)}

# ── Carrier metrics ───────────────────────────────────────────────────────────
metrics = (
    df.groupby("carrier")
    .agg(
        shipments         =("shipment_id",           "count"),
        avg_cost          =("total_cost_usd",         "mean"),
        total_spend       =("total_cost_usd",         "sum"),
        avg_cpm           =("cost_per_mile",          "mean"),
        avg_risk          =("risk_score",             "mean"),
        high_risk_count   =("risk_tier", lambda x: (x == "High").sum()),
        total_accessorial =("accessorial_charge_usd", "sum"),
        avg_accessorial   =("accessorial_charge_usd", "mean"),
        avg_miles         =("miles",                  "mean"),
        avg_weight        =("weight_lbs",             "mean"),
    )
    .reset_index()
)
metrics["high_risk_pct"]    = (metrics["high_risk_count"]   / metrics["shipments"]   * 100).round(1)
metrics["accessorial_rate"] = (metrics["total_accessorial"] / metrics["total_spend"] * 100).round(1)

# ── Summary table ─────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Carrier Summary")
    st.caption("All carriers ranked by cost per mile — lower $/mile = more efficient freight spend")
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
        use_container_width=True,
        hide_index=True,
        column_config={
            "Avg Risk":       st.column_config.ProgressColumn(
                "Avg Risk", format="%.0f%%", min_value=0, max_value=1
            ),
            "Avg Total Cost": st.column_config.NumberColumn(format="$%.2f"),
            "Avg $/Mile":     st.column_config.NumberColumn(format="$%.3f"),
            "Avg Accessorial":st.column_config.NumberColumn(format="$%.2f"),
            "Total Spend":    st.column_config.NumberColumn(format="$%.0f"),
        },
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Bar charts ────────────────────────────────────────────────────────────────
ch1, ch2 = st.columns(2, gap="medium")

with ch1:
    with st.container(border=True):
        st.markdown("#### Avg Cost per Mile")
        st.caption("Lower bars indicate more cost-efficient carriers for your freight lanes")
        sorted_m = metrics.sort_values("avg_cpm")
        fig = go.Figure(go.Bar(
            x=sorted_m["carrier"],
            y=sorted_m["avg_cpm"],
            marker_color=[color_map[c] for c in sorted_m["carrier"]],
            marker_line_width=0,
            text=sorted_m["avg_cpm"].apply(lambda v: f"${v:.2f}"),
            textposition="outside",
            textfont=dict(color=TEXT_SECONDARY, size=11),
        ))
        fig.update_layout(**DARK_LAYOUT, margin=dict(l=0, r=0, t=8, b=0), height=280,
                          showlegend=False)
        fig.update_yaxes(tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)

with ch2:
    with st.container(border=True):
        st.markdown("#### High Risk Shipment Rate")
        st.caption("Percentage of shipments flagged as high-risk — carriers above 40% warrant closer contract review")
        sorted_m2 = metrics.sort_values("high_risk_pct", ascending=False)
        bar_colors = [
            CORAL if p > 40 else GOLD if p > 25 else BRIGHT_TEAL
            for p in sorted_m2["high_risk_pct"]
        ]
        fig2 = go.Figure(go.Bar(
            x=sorted_m2["carrier"],
            y=sorted_m2["high_risk_pct"],
            marker_color=bar_colors,
            marker_line_width=0,
            text=sorted_m2["high_risk_pct"].apply(lambda v: f"{v:.1f}%"),
            textposition="outside",
            textfont=dict(color=TEXT_SECONDARY, size=11),
        ))
        fig2.update_layout(**DARK_LAYOUT, margin=dict(l=0, r=0, t=8, b=0), height=280,
                           showlegend=False)
        fig2.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

ch3, ch4 = st.columns(2, gap="medium")

with ch3:
    with st.container(border=True):
        st.markdown("#### Accessorial Cost Rate")
        st.caption("Accessorial charges as % of total spend — high rates signal frequent detention, layovers, or re-deliveries")
        sorted_m3 = metrics.sort_values("accessorial_rate", ascending=False)
        fig3 = go.Figure(go.Bar(
            x=sorted_m3["carrier"],
            y=sorted_m3["accessorial_rate"],
            marker_color=[color_map[c] for c in sorted_m3["carrier"]],
            marker_line_width=0,
            text=sorted_m3["accessorial_rate"].apply(lambda v: f"{v:.1f}%"),
            textposition="outside",
            textfont=dict(color=TEXT_SECONDARY, size=11),
        ))
        fig3.update_layout(**DARK_LAYOUT, margin=dict(l=0, r=0, t=8, b=0), height=260,
                           showlegend=False)
        fig3.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig3, use_container_width=True)

with ch4:
    with st.container(border=True):
        st.markdown("#### Carrier Performance Radar")
        st.caption(
            "Normalized scores across four dimensions — "
            "larger filled area = better overall carrier. Lower cost, risk, and accessorial rate is better."
        )

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
                line_color=color_map[row["carrier"]],
                fillcolor=color_map[row["carrier"]],
                opacity=0.25,
            ))
        radar_fig.update_layout(
            polar=dict(
                bgcolor=NAVY_BG,
                radialaxis=dict(
                    visible=True, range=[0, 1],
                    gridcolor=BORDER,
                    tickfont=dict(color=TEXT_SECONDARY, size=9),
                ),
                angularaxis=dict(
                    gridcolor=BORDER,
                    tickfont=dict(color=TEXT_SECONDARY, size=10),
                ),
            ),
            paper_bgcolor=CARD_BG,
            font=dict(color=TEXT_PRIMARY),
            margin=dict(l=30, r=30, t=30, b=30),
            height=260,
            legend=dict(font=dict(color=TEXT_SECONDARY, size=10)),
        )
        st.plotly_chart(radar_fig, use_container_width=True)
