# File: pages/7_Accessorial_Tracker.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.mock_data import generate_mock_shipments
from utils.styling import (
    inject_css, top_nav,
    CARD_BG, BORDER, PLUM,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    BRIGHT_TEAL, CORAL, LAVENDER, GOLD,
    RISK_HIGH_FG, RISK_MED_FG, RISK_LOW_FG,
    DARK_LAYOUT,
)

st.set_page_config(
    page_title="PACE — Accessorial Tracker",
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


@st.cache_data
def load_data():
    return generate_mock_shipments(300)


df_all = load_data()
df_all["ship_date_dt"] = pd.to_datetime(df_all["ship_date"])

# ── Filters ───────────────────────────────────────────────────────────────────
acc_types = sorted([t for t in df_all["accessorial_type"].unique() if t != "None"])
min_date  = df_all["ship_date_dt"].min().date()
max_date  = df_all["ship_date_dt"].max().date()

with st.expander("Filters", expanded=False):
    f1, f2, f3 = st.columns(3)
    with f1:
        sel_types = st.multiselect("Accessorial Type", acc_types, default=acc_types)
    with f2:
        sel_carriers = st.multiselect(
            "Carrier", sorted(df_all["carrier"].unique()),
            default=sorted(df_all["carrier"].unique())
        )
    with f3:
        date_range = st.date_input("Date Range", value=(min_date, max_date),
                                   min_value=min_date, max_value=max_date)

# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_all.copy()
if sel_types:
    df = df[df["accessorial_type"].isin(sel_types + ["None"])]
if sel_carriers:
    df = df[df["carrier"].isin(sel_carriers)]
if len(date_range) == 2:
    df = df[
        (df["ship_date_dt"] >= pd.Timestamp(date_range[0])) &
        (df["ship_date_dt"] <= pd.Timestamp(date_range[1]))
    ]

df_with_acc = df[df["accessorial_charge_usd"] > 0].copy()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Accessorial Cost Tracker")
st.caption(
    "Track where unexpected charges come from, which lanes and carriers carry the most risk, "
    "and how accessorial costs correlate with risk tier."
)
st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
total_acc       = df["accessorial_charge_usd"].sum()
shipments_w_acc = len(df_with_acc)
total_shipments = len(df)
acc_rate        = (shipments_w_acc / total_shipments * 100) if total_shipments else 0
avg_acc         = df_with_acc["accessorial_charge_usd"].mean() if len(df_with_acc) else 0
max_acc         = df_with_acc["accessorial_charge_usd"].max()  if len(df_with_acc) else 0
pct_of_total    = (total_acc / df["total_cost_usd"].sum() * 100) if df["total_cost_usd"].sum() else 0

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Total Accessorial",        f"${total_acc:,.0f}")
with k2:
    st.metric("Affected Shipments",       f"{shipments_w_acc:,} of {total_shipments:,}")
with k3:
    st.metric("Accessorial Rate",         f"{acc_rate:.1f}%")
with k4:
    st.metric("Avg per Affected Shipment", f"${avg_acc:,.2f}")
with k5:
    st.metric("% of Total Spend",         f"{pct_of_total:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)

# ── Breakdown by type + carrier ───────────────────────────────────────────────
col_l, col_r = st.columns(2, gap="medium")

with col_l:
    with st.container(border=True):
        st.markdown("#### Accessorial Costs by Type")
        st.caption(
            "Which charge categories are costing the most — "
            "Detention and Lumper Fees are the most common culprits"
        )
        type_data = (
            df_with_acc.groupby("accessorial_type")["accessorial_charge_usd"]
            .agg(total="sum", count="count")
            .reset_index()
            .sort_values("total", ascending=False)
        )
        if not type_data.empty:
            donut_colors = [CORAL, GOLD, BRIGHT_TEAL, LAVENDER]
            donut_fig = go.Figure(go.Pie(
                labels=type_data["accessorial_type"],
                values=type_data["total"],
                hole=0.55,
                marker_colors=donut_colors[:len(type_data)],
                textinfo="label+percent",
                textfont=dict(color=TEXT_PRIMARY, size=12),
                hovertemplate="<b>%{label}</b><br>Total: $%{value:,.0f}<br>Share: %{percent}<extra></extra>",
            ))
            donut_fig.add_annotation(
                text=f"${total_acc:,.0f}", x=0.5, y=0.5,
                font_size=16, font_color=TEXT_PRIMARY, showarrow=False,
            )
            donut_fig.update_layout(
                margin=dict(l=0, r=0, t=8, b=0), height=280,
                paper_bgcolor=CARD_BG,
                showlegend=True,
                legend=dict(
                    orientation="v", x=1.0, y=0.5,
                    font=dict(color=TEXT_SECONDARY, size=11),
                ),
                font=dict(color=TEXT_PRIMARY),
            )
            st.plotly_chart(donut_fig, use_container_width=True)

            st.dataframe(
                type_data.rename(columns={
                    "accessorial_type": "Type",
                    "total":            "Total Cost ($)",
                    "count":            "Occurrences",
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Total Cost ($)": st.column_config.NumberColumn(format="$%.2f")
                },
            )
        else:
            st.info("No accessorial charges match the current filters.")

with col_r:
    with st.container(border=True):
        st.markdown("#### Accessorial Costs by Carrier")
        st.caption(
            "Which carriers generate the most unexpected charges — "
            "high totals may indicate systemic detention or lumper fee issues"
        )
        carrier_acc = (
            df_with_acc.groupby("carrier")
            .agg(total=("accessorial_charge_usd", "sum"),
                 count=("accessorial_charge_usd", "count"),
                 avg  =("accessorial_charge_usd", "mean"))
            .reset_index()
            .sort_values("total", ascending=True)
        )
        if not carrier_acc.empty:
            fig_c = go.Figure(go.Bar(
                x=carrier_acc["total"],
                y=carrier_acc["carrier"],
                orientation="h",
                marker_color=LAVENDER,
                marker_line_width=0,
                text=carrier_acc["total"].apply(lambda v: f"${v:,.0f}"),
                textposition="outside",
                textfont=dict(color=TEXT_SECONDARY, size=11),
                customdata=carrier_acc[["count", "avg"]].values,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Total: $%{x:,.0f}<br>"
                    "Occurrences: %{customdata[0]}<br>"
                    "Avg per shipment: $%{customdata[1]:,.2f}<extra></extra>"
                ),
            ))
            fig_c.update_layout(**DARK_LAYOUT, margin=dict(l=0, r=80, t=8, b=0), height=280)
            fig_c.update_xaxes(tickprefix="$")
            st.plotly_chart(fig_c, use_container_width=True)
        else:
            st.info("No data for the current filter selection.")

st.markdown("<br>", unsafe_allow_html=True)

# ── By facility + trend ───────────────────────────────────────────────────────
col_a, col_b = st.columns(2, gap="medium")

with col_a:
    with st.container(border=True):
        st.markdown("#### Accessorial Costs by Facility")
        st.caption(
            "Which facilities trigger the most charges — "
            "facilities with limited dock availability or strict appointment windows often rank highest"
        )
        fac_acc = (
            df_with_acc.groupby("facility")
            .agg(total=("accessorial_charge_usd", "sum"),
                 avg  =("accessorial_charge_usd", "mean"),
                 count=("accessorial_charge_usd", "count"))
            .reset_index()
            .sort_values("total", ascending=True)
        )
        if not fac_acc.empty:
            fac_fig = go.Figure(go.Bar(
                x=fac_acc["total"],
                y=fac_acc["facility"].apply(lambda v: v if len(v) <= 30 else v[:27] + "…"),
                orientation="h",
                marker_color=CORAL,
                marker_line_width=0,
                text=fac_acc["total"].apply(lambda v: f"${v:,.0f}"),
                textposition="outside",
                textfont=dict(color=TEXT_SECONDARY, size=11),
            ))
            fac_fig.update_layout(**DARK_LAYOUT, margin=dict(l=0, r=80, t=8, b=0), height=260)
            fac_fig.update_xaxes(tickprefix="$")
            st.plotly_chart(fac_fig, use_container_width=True)
        else:
            st.info("No data for the current filter selection.")

with col_b:
    with st.container(border=True):
        st.markdown("#### Accessorial Cost Trend")
        st.caption(
            "Weekly accessorial spend over time — "
            "spikes often align with weather events, peak shipping seasons, or carrier staffing gaps"
        )
        df_with_acc["week"] = df_with_acc["ship_date_dt"].dt.to_period("W").dt.start_time
        weekly_acc = (
            df_with_acc.groupby("week")["accessorial_charge_usd"]
            .sum().reset_index()
            .rename(columns={"accessorial_charge_usd": "total"})
        )
        if not weekly_acc.empty:
            trend_fig = go.Figure(go.Scatter(
                x=weekly_acc["week"], y=weekly_acc["total"],
                mode="lines+markers",
                line=dict(color=GOLD, width=2),
                marker=dict(color=GOLD, size=6, line=dict(color=CARD_BG, width=1)),
                fill="tozeroy",
                fillcolor="rgba(251, 191, 36, 0.10)",
            ))
            trend_fig.update_layout(**DARK_LAYOUT, margin=dict(l=0, r=0, t=8, b=0), height=260)
            trend_fig.update_yaxes(tickprefix="$")
            st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.info("No trend data available for this filter.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Risk tier analysis ─────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Why Do Some Shipments Cost So Much More?")
    st.caption(
        "Shipments with high risk scores consistently incur higher accessorial charges. "
        "This breakdown shows how cost outcomes differ across risk tiers."
    )

    tier_analysis = (
        df.groupby("risk_tier")
        .agg(
            count        =("shipment_id",            "count"),
            avg_acc      =("accessorial_charge_usd", "mean"),
            total_acc    =("accessorial_charge_usd", "sum"),
            pct_with_acc =("accessorial_charge_usd", lambda x: (x > 0).mean() * 100),
            avg_base     =("base_freight_usd",       "mean"),
            avg_total    =("total_cost_usd",         "mean"),
        )
        .reset_index()
    )
    tier_order = {"Low": 0, "Medium": 1, "High": 2}
    tier_analysis["sort"] = tier_analysis["risk_tier"].map(tier_order)
    tier_analysis = tier_analysis.sort_values("sort").drop(columns="sort")

    t1, t2, t3 = st.columns(3)
    for col_widget, (_, row) in zip([t1, t2, t3], tier_analysis.iterrows()):
        tier  = row["risk_tier"]
        color = {"High": RISK_HIGH_FG, "Medium": RISK_MED_FG, "Low": RISK_LOW_FG}[tier]
        bg    = {"High": "rgba(255,107,107,0.08)",
                 "Medium": "rgba(251,191,36,0.08)",
                 "Low": "rgba(45,212,191,0.08)"}[tier]
        with col_widget:
            st.markdown(
                f"<div style='border-left:4px solid {color}; padding:12px 16px; "
                f"background:{bg}; border-radius:0 8px 8px 0; margin-bottom:8px;'>"
                f"<div style='font-size:13px; font-weight:700; color:{color}; "
                f"text-transform:uppercase; letter-spacing:0.5px;'>{tier} Risk</div>"
                f"<div style='font-size:22px; font-weight:700; color:{TEXT_PRIMARY}; "
                f"margin:6px 0;'>${row['avg_acc']:,.2f}</div>"
                f"<div style='font-size:12px; color:{TEXT_SECONDARY};'>"
                f"avg accessorial charge</div>"
                f"<hr style='border:none; border-top:1px solid {BORDER}; margin:10px 0;'>"
                f"<div style='font-size:12px; color:{TEXT_SECONDARY};'>"
                f"<b style='color:{TEXT_PRIMARY};'>{row['pct_with_acc']:.0f}%</b> "
                f"of shipments charged<br>"
                f"<b style='color:{TEXT_PRIMARY};'>{row['count']:.0f}</b> total shipments<br>"
                f"Avg total cost: <b style='color:{TEXT_PRIMARY};'>${row['avg_total']:,.2f}</b>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)

# ── Top 15 most expensive ──────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Top 15 Most Expensive Accessorial Shipments")
    st.caption("Individual shipments with the highest unexpected charges — use these to identify patterns in carrier, facility, or lane")

    top15 = (
        df_with_acc.nlargest(15, "accessorial_charge_usd")
        [[
            "shipment_id", "ship_date", "carrier", "facility",
            "accessorial_type", "accessorial_charge_usd",
            "base_freight_usd", "total_cost_usd", "risk_tier",
        ]]
        .rename(columns={
            "shipment_id":            "Shipment ID",
            "ship_date":              "Ship Date",
            "carrier":                "Carrier",
            "facility":               "Facility",
            "accessorial_type":       "Type",
            "accessorial_charge_usd": "Accessorial ($)",
            "base_freight_usd":       "Base Freight ($)",
            "total_cost_usd":         "Total Cost ($)",
            "risk_tier":              "Risk Tier",
        })
    )
    st.dataframe(
        top15,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Accessorial ($)":  st.column_config.NumberColumn(format="$%.2f"),
            "Base Freight ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Total Cost ($)":   st.column_config.NumberColumn(format="$%.2f"),
        },
    )
