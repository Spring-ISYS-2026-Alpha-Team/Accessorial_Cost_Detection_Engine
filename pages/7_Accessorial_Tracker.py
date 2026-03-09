# File: pages/7_Accessorial_Tracker.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.database import get_connection, get_shipments_with_charges
from utils.mock_data import generate_mock_shipments
from utils.styling import (
    inject_css, top_nav,
    NAVY_500, NAVY_900, NAVY_100,
    RISK_HIGH_FG, RISK_MED_FG, RISK_LOW_FG,
    chart_theme,
)

st.set_page_config(
    page_title="PACE — Accessorial Tracker",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

if not check_auth():
    st.warning("Please sign in to access this page.")
    st.page_link("app.py", label="Go to Sign In", icon="🔑")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)

conn = get_connection()
df_all = get_shipments_with_charges(conn) if conn is not None else pd.DataFrame()
if df_all.empty:
    # Fall back to mock data — filter to only rows with accessorial charges for consistency
    _mock = generate_mock_shipments(300)
    df_all = _mock[_mock["accessorial_charge_usd"] > 0].copy()
    df_all["accessorial_type"] = df_all.get("accessorial_type", "Unknown")
    st.info("Live database unavailable — showing demo data.", icon="ℹ️")

df_all["ship_date_dt"] = pd.to_datetime(df_all["ship_date"])

# ── Inline filters ────────────────────────────────────────────────────────────
acc_types = sorted(df_all["accessorial_type"].dropna().unique())
min_date  = df_all["ship_date_dt"].min().date()
max_date  = df_all["ship_date_dt"].max().date()

with st.expander("⚙️ Filters", expanded=False):
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
    df = df[df["accessorial_type"].isin(sel_types)]
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
st.caption("Understand where unexpected charges come from, which lanes carry the most risk, and why costs vary.")
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
    st.metric("Total Accessorial", f"${total_acc:,.0f}",
              help="Sum of all accessorial charges — extra fees beyond the base linehaul cost.")
with k2:
    st.metric("Affected Shipments", f"{shipments_w_acc:,} of {total_shipments:,}",
              help="Number of shipments that incurred at least one accessorial charge out of the total.")
with k3:
    st.metric("Accessorial Rate", f"{acc_rate:.1f}%",
              help="Percentage of shipments with accessorial charges. Industry average is typically 30–50%.")
with k4:
    st.metric("Avg per Affected Shipment", f"${avg_acc:,.2f}",
              help="Average accessorial dollar amount on shipments that had at least one charge.")
with k5:
    st.metric("% of Total Spend", f"{pct_of_total:.1f}%",
              help="Accessorial costs as a share of total carrier spend (linehaul + accessorial combined).")

st.markdown("<br>", unsafe_allow_html=True)

# ── Breakdown by type (donut) + by carrier (bar) ──────────────────────────────
col_l, col_r = st.columns(2, gap="medium")

with col_l:
    with st.container(border=True):
        st.markdown("#### Accessorial Costs by Type")
        st.caption("Which charges are costing the most?")

        type_data = (
            df_with_acc.groupby("accessorial_type")["accessorial_charge_usd"]
            .agg(total="sum", count="count")
            .reset_index()
            .sort_values("total", ascending=False)
        )
        if not type_data.empty:
            donut_fig = go.Figure(go.Pie(
                labels=type_data["accessorial_type"],
                values=type_data["total"],
                hole=0.55,
                marker_colors=[RISK_HIGH_FG, RISK_MED_FG, NAVY_500, "#7C3AED"],
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Total: $%{value:,.0f}<br>Share: %{percent}<extra></extra>",
            ))
            donut_fig.add_annotation(
                text=f"${total_acc:,.0f}", x=0.5, y=0.5,
                font_size=16, font_color="#111827", showarrow=False, font_family="Inter",
            )
            donut_fig.update_layout(
                margin=dict(l=0, r=0, t=8, b=0), height=280,
                paper_bgcolor="rgba(0,0,0,0)", showlegend=True,
                font=dict(color="#94A3B8"),
                legend=dict(orientation="v", x=1.0, y=0.5, bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")),
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
        st.caption("Which carriers generate the most unexpected charges?")

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
                marker_color=NAVY_500,
                text=carrier_acc["total"].apply(lambda v: f"${v:,.0f}"),
                textposition="outside",
                customdata=carrier_acc[["count", "avg"]].values,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Total: $%{x:,.0f}<br>"
                    "Occurrences: %{customdata[0]}<br>"
                    "Avg per shipment: $%{customdata[1]:,.2f}<extra></extra>"
                ),
            ))
            fig_c.update_layout(
                margin=dict(l=0, r=80, t=8, b=0), height=280,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8"),
                xaxis=dict(tickprefix="$", gridcolor="rgba(150,50,200,0.15)", color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
                yaxis=dict(gridcolor="rgba(150,50,200,0.15)", color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
            )
            st.plotly_chart(fig_c, use_container_width=True)
        else:
            st.info("No data for the current filter selection.")

st.markdown("<br>", unsafe_allow_html=True)

# ── By facility + trend over time ─────────────────────────────────────────────
col_a, col_b = st.columns(2, gap="medium")

with col_a:
    with st.container(border=True):
        st.markdown("#### Accessorial Costs by Facility")
        st.caption("Which facilities trigger the most charges?")

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
                marker_color=RISK_HIGH_FG,
                text=fac_acc["total"].apply(lambda v: f"${v:,.0f}"),
                textposition="outside",
            ))
            fac_fig.update_layout(
                margin=dict(l=0, r=80, t=8, b=0), height=260,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8"),
                xaxis=dict(tickprefix="$", gridcolor="rgba(150,50,200,0.15)", color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
                yaxis=dict(gridcolor="rgba(150,50,200,0.15)", color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
            )
            st.plotly_chart(fac_fig, use_container_width=True)
        else:
            st.info("No data for the current filter selection.")

with col_b:
    with st.container(border=True):
        st.markdown("#### Accessorial Cost Trend")
        st.caption("Weekly accessorial spend over time")

        df_with_acc["week"] = df_with_acc["ship_date_dt"].dt.to_period("W").dt.start_time
        weekly_acc = (
            df_with_acc.groupby("week")["accessorial_charge_usd"]
            .sum()
            .reset_index()
            .rename(columns={"accessorial_charge_usd": "total"})
        )
        if not weekly_acc.empty:
            trend_fig = go.Figure(go.Scatter(
                x=weekly_acc["week"], y=weekly_acc["total"],
                mode="lines+markers",
                line=dict(color=RISK_HIGH_FG, width=2),
                marker=dict(color=RISK_HIGH_FG, size=6),
                fill="tozeroy",
                fillcolor="rgba(220,38,38,0.08)",
            ))
            trend_fig.update_layout(
                margin=dict(l=0, r=0, t=8, b=0), height=260,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8"),
                xaxis=dict(gridcolor="rgba(150,50,200,0.15)", color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
                yaxis=dict(tickprefix="$", gridcolor="rgba(150,50,200,0.15)", color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
            )
            st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.info("No trend data available for this filter.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Why costs vary: risk tier analysis ───────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Why Do Some Shipments Cost So Much More?")
    st.caption(
        "Shipments with high risk scores consistently have higher accessorial charges. "
        "This table compares cost outcomes by risk tier."
    )

    tier_analysis = (
        df.groupby("risk_tier")
        .agg(
            count        =("shipment_id",            "count"),
            avg_acc      =("accessorial_charge_usd", "mean"),
            total_acc    =("accessorial_charge_usd", "sum"),
            pct_with_acc =("accessorial_charge_usd",
                           lambda x: (x > 0).mean() * 100),
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
        with col_widget:
            st.markdown(
                f"<div style='border-left:4px solid {color}; padding:12px 16px; "
                f"background:#FAFAFA; border-radius:0 8px 8px 0; margin-bottom:8px;'>"
                f"<div style='font-size:13px; font-weight:700; color:{color}; "
                f"text-transform:uppercase; letter-spacing:0.5px;'>{tier} Risk</div>"
                f"<div style='font-size:22px; font-weight:700; color:#111827; margin:6px 0;'>"
                f"${row['avg_acc']:,.2f}</div>"
                f"<div style='font-size:12px; color:#6B7280;'>avg accessorial charge</div>"
                f"<hr style='border:none; border-top:1px solid #E5E7EB; margin:10px 0;'>"
                f"<div style='font-size:12px; color:#374151;'>"
                f"<b>{row['pct_with_acc']:.0f}%</b> of shipments charged<br>"
                f"<b>{row['count']:.0f}</b> total shipments<br>"
                f"Avg total cost: <b>${row['avg_total']:,.2f}</b>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)

# ── Top 15 most expensive shipments ──────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Top 15 Most Expensive Accessorial Shipments")
    st.caption("Individual shipments with the highest unexpected charges")

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

st.markdown("<br>", unsafe_allow_html=True)

# ── Risk Explanation & Recommended Actions (from ML pipeline write-back) ──────
st.markdown("## Shipment Risk Details")
st.caption(
    "Individual shipment risk scores, explanations, and recommended actions "
    "generated by the ML pipeline."
)

@st.cache_data(ttl=300)
def load_risk_details(_conn):
    """Load shipment risk details including ML-generated explanations."""
    if _conn is None:
        return pd.DataFrame()
    query = """
        SELECT TOP 500
            s.ShipmentId,
            s.ShipDate,
            s.OriginRegion,
            s.DestRegion,
            s.AppointmentType,
            s.DistanceMiles,
            s.weight_lbs,
            s.risk_score,
            s.risk_tier,
            s.risk_reason,
            s.recommended_action
        FROM Shipments s
        WHERE s.risk_score IS NOT NULL
        ORDER BY s.risk_score DESC
    """
    try:
        return pd.read_sql(query, _conn)
    except Exception:
        return pd.DataFrame()

risk_df = load_risk_details(conn)

if risk_df.empty:
    st.info(
        "Risk explanations are generated by the ML pipeline. "
        "Run `python scripts/ml_pipeline.py` to populate this section.",
        icon="ℹ️",
    )
else:
    # ── Filters ───────────────────────────────────────────────────────────────
    with st.expander("⚙️ Risk Detail Filters", expanded=False):
        rd1, rd2, rd3 = st.columns(3)
        with rd1:
            tier_opts = sorted(risk_df["risk_tier"].dropna().astype(str).unique().tolist())
            sel_risk_tiers = st.multiselect("Risk Tier", tier_opts, default=tier_opts, key="risk_detail_tier")
        with rd2:
            min_s = float(risk_df["risk_score"].min())
            max_s = float(risk_df["risk_score"].max())
            score_range = st.slider("Risk Score Range", 0.0, 1.0,
                                    (min_s, max_s), 0.01, key="risk_score_range")
        with rd3:
            search_id = st.text_input("Search Shipment ID", key="risk_search_id")

    filtered_risk = risk_df.copy()
    if sel_risk_tiers:
        filtered_risk = filtered_risk[filtered_risk["risk_tier"].astype(str).isin(sel_risk_tiers)]
    filtered_risk = filtered_risk[
        (filtered_risk["risk_score"] >= score_range[0]) &
        (filtered_risk["risk_score"] <= score_range[1])
    ]
    if search_id.strip():
        filtered_risk = filtered_risk[
            filtered_risk["ShipmentId"].astype(str).str.contains(search_id.strip(), na=False)
        ]

    # ── KPI row ───────────────────────────────────────────────────────────────
    rk1, rk2, rk3, rk4 = st.columns(4)
    with rk1:
        st.metric("Shipments Shown", len(filtered_risk))
    with rk2:
        high_n = int((filtered_risk["risk_tier"].astype(str) == "High").sum())
        st.metric("High Risk", high_n)
    with rk3:
        med_n = int((filtered_risk["risk_tier"].astype(str) == "Medium").sum())
        st.metric("Medium Risk", med_n)
    with rk4:
        avg_s = filtered_risk["risk_score"].mean() if not filtered_risk.empty else 0
        st.metric("Avg Risk Score", f"{avg_s:.3f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Shipment cards ────────────────────────────────────────────────────────
    if filtered_risk.empty:
        st.info("No shipments match the selected filters.")
    else:
        TIER_COLORS = {
            "High":   (RISK_HIGH_FG, "#FEE2E2"),
            "Medium": (RISK_MED_FG,  "#FEF3C7"),
            "Low":    (RISK_LOW_FG,  "#D1FAE5"),
        }
        for _, row in filtered_risk.iterrows():
            tier  = str(row.get("risk_tier", "Unknown"))
            score = row.get("risk_score", 0)
            fg_c, bg_c = TIER_COLORS.get(tier, ("#6B7280", "#F3F4F6"))
            badge = {"High": "🔴 High", "Medium": "🟠 Medium", "Low": "🟢 Low"}.get(tier, tier)

            with st.container(border=True):
                hc1, hc2 = st.columns([5, 1])
                with hc1:
                    st.markdown(f"#### Shipment #{row.get('ShipmentId', '')} — {badge}")
                with hc2:
                    st.markdown(
                        f"<div style='text-align:right; padding-top:6px;'>"
                        f"<span style='background:{bg_c}; color:{fg_c}; padding:4px 12px; "
                        f"border-radius:4px; font-size:13px; font-weight:700;'>"
                        f"{score:.3f}</span></div>",
                        unsafe_allow_html=True,
                    )

                ic1, ic2, ic3 = st.columns(3)
                ic1.write(f"**Ship Date:** {row.get('ShipDate', '')}")
                ic1.write(f"**Appointment:** {row.get('AppointmentType', '')}")
                ic2.write(f"**Route:** {row.get('OriginRegion', '')} → {row.get('DestRegion', '')}")
                ic2.write(f"**Distance:** {row.get('DistanceMiles', '')} mi")
                ic3.write(f"**Weight:** {row.get('weight_lbs', '')} lbs")
                ic3.write(f"**Risk Tier:** {tier}")

                reason = row.get("risk_reason", "")
                action = row.get("recommended_action", "")

                st.markdown("**Why this shipment is risky**")
                st.info(
                    reason if pd.notna(reason) and str(reason).strip()
                    else "No explanation available."
                )

                st.markdown("**Recommended action**")
                st.success(
                    action if pd.notna(action) and str(action).strip()
                    else "No recommendation available."
                )
