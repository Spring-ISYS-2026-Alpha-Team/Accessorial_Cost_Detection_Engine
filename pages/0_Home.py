# File: pages/0_Home.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os, base64

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.mock_data import generate_mock_shipments
from utils.styling import (
    inject_css, top_nav,
    NAVY_BG, CARD_BG, BORDER, PLUM,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    BRIGHT_TEAL, CORAL, LAVENDER, GOLD,
    DARK_LAYOUT,
)

st.set_page_config(page_title="PACE — Home", page_icon="P",
                   layout="wide", initial_sidebar_state="collapsed")
inject_css()

if not check_auth():
    st.warning("Please sign in.")
    st.page_link("app.py", label="Go to Sign In")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)

# ── Page-level CSS overrides ──────────────────────────────────────────────────
st.markdown(
    '<style>'
    '.stApp { background-color: #161638 !important; }'
    '.stApp, .stApp p, .stApp span, .stApp label, .stApp .stMarkdown,'
    ' .stApp [data-testid="stText"] { color: #F1F5F9 !important; }'
    '.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #F1F5F9 !important; }'
    '.stApp .stCaption, .stApp small, .stApp [data-testid="stCaptionContainer"]'
    '  { color: #94A3B8 !important; }'
    '@keyframes fadeUp { from { opacity:0; transform:translateY(20px); }'
    ' to { opacity:1; transform:translateY(0); } }'
    '.anim1 { animation: fadeUp 0.5s ease-out forwards; }'
    '.anim2 { animation: fadeUp 0.5s ease-out 0.1s forwards; opacity:0; }'
    '.anim3 { animation: fadeUp 0.5s ease-out 0.25s forwards; opacity:0; }'
    'hr { border-color: #38667E !important; }'
    '.block-container { padding-top: 1rem !important; }'
    '</style>',
    unsafe_allow_html=True,
)

# ── Load hero background image ────────────────────────────────────────────────
@st.cache_data
def load_hero_image():
    img_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "assets", "shippingcontainers.jpg")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

hero_b64 = load_hero_image()

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    return generate_mock_shipments(300)

df_all = load_data()
df_all["ship_date_dt"] = pd.to_datetime(df_all["ship_date"])

# ── Hero Section ──────────────────────────────────────────────────────────────
if hero_b64:
    bg_style = (
        "background: linear-gradient(160deg,"
        " rgba(22,22,56,0.88) 0%,"
        " rgba(27,67,94,0.78) 40%,"
        " rgba(58,43,80,0.72) 65%,"
        " rgba(22,22,56,0.90) 100%),"
        " url('data:image/jpeg;base64," + hero_b64 + "');"
        " background-size: cover; background-position: center;"
    )
else:
    bg_style = (
        "background: linear-gradient(160deg, #161638 0%, #1B435E 40%,"
        " #3A2B50 65%, #161638 100%);"
    )

hero_html = (
    '<div class="anim1" style="'
    + bg_style
    + ' border: 1px solid #38667E; border-radius: 20px; padding: 52px 52px 44px;'
    ' margin-bottom: 24px; position: relative; overflow: hidden;">'
    '<div style="position:relative; z-index:1;">'
    '<div class="anim2" style="display:inline-block; background:rgba(45,212,191,0.12);'
    ' border:1px solid rgba(45,212,191,0.25); border-radius:6px; padding:4px 12px;'
    ' font-size:11px; font-weight:700; color:#2DD4BF; letter-spacing:2px;'
    ' text-transform:uppercase; margin-bottom:18px;">PACE</div>'
    '<h1 class="anim2" style="font-size:38px; font-weight:700; color:#F1F5F9 !important;'
    ' margin:0 0 10px 0; letter-spacing:-1px; line-height:1.15;'
    ' text-shadow: 0 2px 12px rgba(0,0,0,0.6);">Welcome back, '
    + username
    + '</h1>'
    '<p class="anim3" style="font-size:15px; color:#CBD5E1; margin:0;'
    ' max-width:520px; line-height:1.7;'
    ' text-shadow: 0 1px 8px rgba(0,0,0,0.5);">'
    'Your fleet performance at a glance — risk predictions, cost analytics,'
    ' and carrier insights powered by machine learning.</p>'
    '</div></div>'
)
st.markdown(hero_html, unsafe_allow_html=True)

# ── Filter toggle ─────────────────────────────────────────────────────────────
min_d = df_all["ship_date_dt"].min().date()
max_d = df_all["ship_date_dt"].max().date()

show_filters = st.toggle("Show Filters", value=False, key="home_filter_toggle")
if show_filters:
    f1, f2 = st.columns(2)
    with f1:
        date_range = st.date_input("Ship Date Range", value=(min_d, max_d),
                                   min_value=min_d, max_value=max_d, key="home_date")
    with f2:
        st.markdown("")
else:
    date_range = (min_d, max_d)

df = df_all.copy()
if len(date_range) == 2:
    df = df[(df["ship_date_dt"] >= pd.Timestamp(date_range[0])) &
            (df["ship_date_dt"] <= pd.Timestamp(date_range[1]))]

# ── Section header ────────────────────────────────────────────────────────────
st.markdown(
    f"<h2 style='font-size:24px; font-weight:700; margin:0 0 4px 0;"
    f" color:{TEXT_PRIMARY};'>Operations Overview</h2>"
    f"<p style='font-size:14px; color:{TEXT_SECONDARY}; margin:0 0 8px 0;'>"
    f"High-level freight performance metrics across all active shipments</p>",
    unsafe_allow_html=True,
)
st.divider()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_shipments   = len(df)
total_revenue     = df["base_freight_usd"].sum()
total_accessorial = df["accessorial_charge_usd"].sum()
total_costs       = df["total_cost_usd"].sum()
avg_cpm           = df["cost_per_mile"].mean()
accessorial_rate  = (
    len(df[df["accessorial_charge_usd"] > 0]) / total_shipments * 100
) if total_shipments else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: st.metric("Shipments",   f"{total_shipments:,}")
with k2: st.metric("Revenue",     f"${total_revenue:,.0f}")
with k3: st.metric("Total Costs", f"${total_costs:,.0f}")
with k4: st.metric("Accessorial", f"${total_accessorial:,.0f}")
with k5: st.metric("Avg $/Mile",  f"${avg_cpm:.2f}")
with k6: st.metric("Acc. Rate",   f"{accessorial_rate:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)

# ── Weekly aggregation ────────────────────────────────────────────────────────
df["week"] = df["ship_date_dt"].dt.to_period("W").dt.start_time
weekly = (
    df.groupby("week")
    .agg(shipments=("shipment_id", "count"),
         revenue=("base_freight_usd", "sum"),
         total_cost=("total_cost_usd", "sum"),
         acc_cost=("accessorial_charge_usd", "sum"))
    .reset_index()
)

# ── Row 1: Shipments Over Time + Revenue vs Cost ──────────────────────────────
col_l, col_r = st.columns(2, gap="medium")

with col_l:
    with st.container(border=True):
        st.markdown(f"#### Shipments Over Time")
        st.caption("Weekly shipment volume — trend shows demand changes across the fleet")
        fig = go.Figure(go.Scatter(
            x=weekly["week"], y=weekly["shipments"],
            mode="lines", fill="tozeroy",
            line=dict(color=BRIGHT_TEAL, width=2.5, shape="spline"),
            fillcolor="rgba(45, 212, 191, 0.10)",
            hovertemplate="<b>Week of %{x|%b %d}</b><br>%{y} shipments<extra></extra>",
        ))
        fig.update_layout(**DARK_LAYOUT, margin=dict(l=0, r=0, t=8, b=0), height=280)
        st.plotly_chart(fig, use_container_width=True)

with col_r:
    with st.container(border=True):
        st.markdown("#### Revenue vs Total Cost")
        st.caption("Weekly — gap between lines reveals margin pressure; narrowing gap signals cost overruns")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=weekly["week"], y=weekly["revenue"], name="Revenue", mode="lines",
            line=dict(color=BRIGHT_TEAL, width=2, shape="spline"),
            hovertemplate="Revenue: $%{y:,.0f}<extra></extra>",
        ))
        fig2.add_trace(go.Scatter(
            x=weekly["week"], y=weekly["total_cost"], name="Total Cost", mode="lines",
            line=dict(color=CORAL, width=2, dash="dot", shape="spline"),
            hovertemplate="Total Cost: $%{y:,.0f}<extra></extra>",
        ))
        fig2.update_layout(
            **DARK_LAYOUT, margin=dict(l=0, r=0, t=8, b=0), height=280,
            legend=dict(orientation="h", y=1.12, font=dict(color=TEXT_SECONDARY, size=12)),
        )
        fig2.update_yaxes(tickprefix="$")
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 2: Stacked Area + Cost per Mile ──────────────────────────────────────
col_a, col_b = st.columns(2, gap="medium")

with col_a:
    with st.container(border=True):
        st.markdown("#### Cost Composition Over Time")
        st.caption("Base freight vs accessorial charges stacked — rising accessorial band signals escalating risk exposure")
        fig_area = go.Figure()
        fig_area.add_trace(go.Scatter(
            x=weekly["week"], y=weekly["total_cost"] - weekly["acc_cost"],
            name="Base Freight", mode="lines",
            line=dict(width=0.5, color=BRIGHT_TEAL, shape="spline"),
            stackgroup="costs", fillcolor="rgba(45, 212, 191, 0.20)",
            hovertemplate="Base: $%{y:,.0f}<extra></extra>",
        ))
        fig_area.add_trace(go.Scatter(
            x=weekly["week"], y=weekly["acc_cost"],
            name="Accessorial", mode="lines",
            line=dict(width=0.5, color=CORAL, shape="spline"),
            stackgroup="costs", fillcolor="rgba(255, 107, 107, 0.35)",
            hovertemplate="Accessorial: $%{y:,.0f}<extra></extra>",
        ))
        fig_area.update_layout(
            **DARK_LAYOUT, margin=dict(l=0, r=0, t=8, b=0), height=300,
            legend=dict(orientation="h", y=1.12, font=dict(color=TEXT_SECONDARY, size=12)),
        )
        fig_area.update_yaxes(tickprefix="$")
        st.plotly_chart(fig_area, use_container_width=True)

with col_b:
    with st.container(border=True):
        st.markdown("#### Avg Cost per Mile by Carrier")
        st.caption("Lower is better — identifies which carriers deliver the most cost-efficient freight movement")
        cpm = (df.groupby("carrier")["cost_per_mile"].mean()
               .reset_index().sort_values("cost_per_mile"))
        palette = [BRIGHT_TEAL, LAVENDER, GOLD, CORAL, "#38667E", PLUM]
        bar_colors = [palette[i % len(palette)] for i in range(len(cpm))]
        fig3 = go.Figure(go.Bar(
            x=cpm["cost_per_mile"], y=cpm["carrier"], orientation="h",
            marker_color=bar_colors, marker_line_width=0,
            text=cpm["cost_per_mile"].apply(lambda v: f"${v:.2f}"),
            textposition="outside", textfont=dict(color=TEXT_SECONDARY, size=11),
            hovertemplate="<b>%{y}</b><br>$%{x:.2f}/mile<extra></extra>",
        ))
        fig3.update_layout(**DARK_LAYOUT, margin=dict(l=0, r=60, t=8, b=0), height=300)
        fig3.update_xaxes(tickprefix="$")
        fig3.update_yaxes(tickfont=dict(color=TEXT_PRIMARY, size=12))
        st.plotly_chart(fig3, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 3: Sunburst + Cost Breakdown ─────────────────────────────────────────
col_c, col_d = st.columns(2, gap="medium")

with col_c:
    with st.container(border=True):
        st.markdown("#### Cost Hierarchy")
        st.caption("Click a carrier to drill into facility-level costs — identifies which combinations drive the most spend")
        sun_data = (
            df.groupby(["carrier", "facility"])
            .agg(total_cost=("total_cost_usd", "sum"))
            .reset_index()
        )
        labels = ["All Shipments"]
        parents = [""]
        values = [df["total_cost_usd"].sum()]
        colors_list = [NAVY_BG]
        carrier_palette = [BRIGHT_TEAL, LAVENDER, CORAL, GOLD, "#38667E", PLUM]
        carrier_list = sorted(sun_data["carrier"].unique())
        for i, carrier in enumerate(carrier_list):
            carrier_total = sun_data[sun_data["carrier"] == carrier]["total_cost"].sum()
            labels.append(carrier)
            parents.append("All Shipments")
            values.append(carrier_total)
            colors_list.append(carrier_palette[i % len(carrier_palette)])
            for _, row in sun_data[sun_data["carrier"] == carrier].iterrows():
                labels.append(row["facility"])
                parents.append(carrier)
                values.append(row["total_cost"])
                colors_list.append(carrier_palette[i % len(carrier_palette)])
        fig_sun = go.Figure(go.Sunburst(
            labels=labels, parents=parents, values=values,
            marker=dict(colors=colors_list, line=dict(color=CARD_BG, width=2)),
            branchvalues="total",
            textfont=dict(color=TEXT_PRIMARY, size=11),
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<extra></extra>",
            insidetextorientation="radial",
        ))
        fig_sun.update_layout(
            margin=dict(l=0, r=0, t=8, b=0), height=380,
            paper_bgcolor=CARD_BG, font=dict(color=TEXT_PRIMARY),
        )
        st.plotly_chart(fig_sun, use_container_width=True)

with col_d:
    with st.container(border=True):
        st.markdown("#### Cost Breakdown by Carrier")
        st.caption("Base freight vs accessorial charges per carrier — coral bars show carriers generating the most unexpected charges")
        cb = (df.groupby("carrier")
              .agg(base=("base_freight_usd", "sum"),
                   acc=("accessorial_charge_usd", "sum"))
              .reset_index().sort_values("base", ascending=False))
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            name="Base Freight", x=cb["carrier"], y=cb["base"],
            marker_color=BRIGHT_TEAL, marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Base: $%{y:,.0f}<extra></extra>",
        ))
        fig4.add_trace(go.Bar(
            name="Accessorial", x=cb["carrier"], y=cb["acc"],
            marker_color=CORAL, marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Accessorial: $%{y:,.0f}<extra></extra>",
        ))
        fig4.update_layout(
            **DARK_LAYOUT, barmode="stack",
            margin=dict(l=0, r=0, t=8, b=0), height=380,
            legend=dict(orientation="h", y=1.08, font=dict(color=TEXT_SECONDARY, size=12)),
        )
        fig4.update_yaxes(tickprefix="$")
        st.plotly_chart(fig4, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f"<div style='text-align:center; padding:28px 0 12px; color:{TEXT_MUTED};"
    f" font-size:11px; border-top:1px solid {BORDER}; margin-top:40px;"
    f" letter-spacing:0.5px;'>"
    f"&copy; 2026 PACE &middot; University of Arkansas &middot; ISYS 43603"
    f" &middot; Team Alpha</div>",
    unsafe_allow_html=True,
)
