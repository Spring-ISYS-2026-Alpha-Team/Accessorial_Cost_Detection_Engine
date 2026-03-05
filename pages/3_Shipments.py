# File: pages/3_Shipments.py
import streamlit as st
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.mock_data import generate_mock_shipments, CARRIERS, FACILITIES
from utils.styling import (
    inject_css, top_nav,
    NAVY_500, NAVY_100,
    RISK_LOW_BG, RISK_LOW_FG,
    RISK_MED_BG, RISK_MED_FG,
    RISK_HIGH_BG, RISK_HIGH_FG,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PACE — Shipments",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

# ── Auth guard ────────────────────────────────────────────────────────────────
if not check_auth():
    st.warning("Please sign in to access this page.")
    st.page_link("app.py", label="Go to Sign In", icon="🔑")
    st.stop()

username = st.session_state.get("username", "User")
top_nav(username)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    return generate_mock_shipments(300)

df_all = load_data()

# ── Inline filters ────────────────────────────────────────────────────────────
with st.expander("⚙️ Filters", expanded=False):
    f1, f2, f3 = st.columns(3)
    with f1:
        sel_carriers = st.multiselect(
            "Carrier", sorted(CARRIERS), default=sorted(CARRIERS), key="ship_carriers"
        )
    with f2:
        sel_facilities = st.multiselect(
            "Facility", sorted(FACILITIES), default=sorted(FACILITIES), key="ship_facilities"
        )
    with f3:
        sel_tiers = st.multiselect(
            "Risk Tier", ["Low", "Medium", "High"],
            default=["Low", "Medium", "High"], key="ship_tiers"
        )

# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_all.copy()
if sel_carriers:
    df = df[df["carrier"].isin(sel_carriers)]
if sel_facilities:
    df = df[df["facility"].isin(sel_facilities)]
if sel_tiers:
    df = df[df["risk_tier"].isin(sel_tiers)]

# ── Session state for detail toggle ──────────────────────────────────────────
if "selected_shipment" not in st.session_state:
    st.session_state["selected_shipment"] = None

# ── Helper: render detail view ─────────────────────────────────────────────────
def render_detail(row: pd.Series):
    tier = row["risk_tier"]
    tier_colors = {
        "High":   (RISK_HIGH_BG, RISK_HIGH_FG),
        "Medium": (RISK_MED_BG,  RISK_MED_FG),
        "Low":    (RISK_LOW_BG,  RISK_LOW_FG),
    }
    bg, fg = tier_colors.get(tier, ("#F3F4F6", "#6B7280"))

    if st.button("← Back to Shipments"):
        st.session_state["selected_shipment"] = None
        st.rerun()

    st.markdown(
        f"<div style='font-size:12px; color:#9CA3AF; margin-bottom:12px;'>"
        f"Shipments / <b style='color:#374151'>{row['shipment_id']}</b></div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        h1, h2 = st.columns([6, 1])
        with h1:
            st.markdown(f"### {row['shipment_id']}")
        with h2:
            st.markdown(
                f"<div style='text-align:right; padding-top:6px;'>"
                f"<span style='background:{bg}; color:{fg}; padding:5px 14px; "
                f"border-radius:4px; font-size:13px; font-weight:700;'>{tier.upper()} RISK</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown("**Carrier**")
            st.write(row["carrier"])
        with m2:
            st.markdown("**Facility**")
            st.write(row["facility"])
        with m3:
            st.markdown("**Ship Date**")
            st.write(row["ship_date"])
        with m4:
            st.markdown("**Base Freight**")
            st.write(f"${row['base_freight_usd']:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    rc1, rc2 = st.columns([2, 3], gap="medium")

    with rc1:
        with st.container(border=True):
            st.markdown("#### Risk Score")
            score_pct = row["risk_score"] * 100
            color = fg

            st.markdown(
                f"<div style='font-size:48px; font-weight:700; color:{color}; "
                f"line-height:1; margin:8px 0;'>{score_pct:.0f}%</div>",
                unsafe_allow_html=True,
            )
            st.progress(float(row["risk_score"]))
            st.markdown(
                f"<span style='background:{bg}; color:{fg}; padding:3px 10px; "
                f"border-radius:4px; font-size:12px; font-weight:600;'>{tier}</span>",
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)

            est = row["accessorial_charge_usd"]
            st.markdown(
                f"<div style='font-size:13px; color:#6B7280; margin-top:8px;'>"
                f"Estimated accessorial exposure: "
                f"<b style='color:{fg};'>${est:,.2f}</b></div>",
                unsafe_allow_html=True,
            )

    with rc2:
        with st.container(border=True):
            st.markdown("#### Risk Factor Breakdown")
            st.caption("Top factors contributing to this prediction")

            weight_norm = min(float(row["weight_lbs"]) / 44_000, 1.0)
            miles_norm  = min(float(row["miles"])      /  5_000, 1.0)
            carrier_factor  = 0.30 + (0.10 if row["carrier"] in ["Werner Enterprises", "XPO Logistics"] else -0.05)
            facility_factor = 0.25 + (0.10 if "Memphis" in row["facility"] or "Chicago" in row["facility"] else -0.05)

            factors = {
                "Carrier History":   round(carrier_factor,  2),
                "Facility Profile":  round(facility_factor, 2),
                "Miles / Distance":  round(miles_norm * 0.20, 2),
                "Shipment Weight":   round(weight_norm * 0.15, 2),
                "Base Freight Rate": round(min(float(row["base_freight_usd"]) / 5_000 * 0.10, 0.10), 2),
            }
            total_weight = sum(factors.values()) or 1
            for factor, weight in sorted(factors.items(), key=lambda x: -x[1]):
                pct = (weight / total_weight) * 100
                fc1, fc2, fc3 = st.columns([3, 5, 1])
                with fc1:
                    st.markdown(
                        f"<span style='font-size:13px; color:#374151;'>{factor}</span>",
                        unsafe_allow_html=True,
                    )
                with fc2:
                    st.progress(pct / 100)
                with fc3:
                    st.markdown(
                        f"<span style='font-size:13px; font-weight:600; color:#111827;'>"
                        f"{pct:.0f}%</span>",
                        unsafe_allow_html=True,
                    )

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            f"<div style='border-left:4px solid {NAVY_500}; "
            f"background:{NAVY_100}; padding:16px 20px; border-radius:0 8px 8px 0;'>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Recommended Actions")

        actions = []
        if tier == "High":
            actions = [
                "Consider an alternative carrier with a lower historical detention rate for this lane.",
                "Request an early morning appointment window (before 10:00 AM) to reduce wait time risk.",
                f"Add an accessorial buffer of ${est * 0.8:,.0f} – ${est * 1.2:,.0f} to your quote.",
                "Confirm facility appointment and ensure dock availability before dispatch.",
            ]
        elif tier == "Medium":
            actions = [
                "Monitor appointment confirmation — delays increase detention likelihood.",
                f"Consider a ${est * 0.5:,.0f} – ${est:,.0f} contingency buffer in your pricing.",
                "Verify carrier's recent performance on similar lanes.",
            ]
        else:
            actions = [
                "Low risk profile — standard operating procedure applies.",
                "No additional accessorial buffer needed for this load.",
            ]

        for i, action in enumerate(actions, 1):
            st.markdown(
                f"<div style='display:flex; align-items:flex-start; gap:10px; margin:8px 0;'>"
                f"<span style='background:{NAVY_500}; color:white; border-radius:50%; "
                f"width:22px; height:22px; min-width:22px; display:flex; "
                f"align-items:center; justify-content:center; font-size:12px; "
                f"font-weight:700;'>{i}</span>"
                f"<span style='font-size:14px; color:#1F2937;'>{action}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Similar Shipments — Historical Comparison")
        st.caption(f"Last 10 shipments via {row['carrier']} to a similar facility")
        similar = (
            df_all[df_all["carrier"] == row["carrier"]]
            .head(10)
            [["shipment_id", "ship_date", "facility", "risk_score",
              "risk_tier", "accessorial_type", "accessorial_charge_usd"]]
            .rename(columns={
                "shipment_id":            "Shipment ID",
                "ship_date":              "Ship Date",
                "facility":               "Facility",
                "risk_score":             "Risk Score",
                "risk_tier":              "Risk Tier",
                "accessorial_type":       "Accessorial Type",
                "accessorial_charge_usd": "Actual Charge ($)",
            })
        )
        st.dataframe(
            similar,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Risk Score": st.column_config.ProgressColumn(
                    "Risk Score", format="%.0f%%", min_value=0, max_value=1
                ),
                "Actual Charge ($)": st.column_config.NumberColumn(format="$%.2f"),
            },
        )


# ── Main: list view vs. detail view ──────────────────────────────────────────
if st.session_state["selected_shipment"] is not None:
    sid = st.session_state["selected_shipment"]
    match = df_all[df_all["shipment_id"] == sid]
    if not match.empty:
        render_detail(match.iloc[0])
    else:
        st.warning("Shipment not found.")
        st.session_state["selected_shipment"] = None
        st.rerun()

else:
    st.markdown("## Shipments")
    st.caption(f"{len(df):,} shipments match current filters")
    st.divider()

    search = st.text_input(
        "", placeholder="🔍 Search by shipment ID…", label_visibility="collapsed"
    )
    if search:
        df = df[df["shipment_id"].str.contains(search.upper(), na=False)]

    with st.container(border=True):
        event = st.dataframe(
            df[[
                "shipment_id", "ship_date", "carrier", "facility",
                "weight_lbs", "miles", "risk_score", "risk_tier",
                "accessorial_type", "base_freight_usd", "accessorial_charge_usd",
            ]].rename(columns={
                "shipment_id":            "Shipment ID",
                "ship_date":              "Ship Date",
                "carrier":                "Carrier",
                "facility":               "Facility",
                "weight_lbs":             "Weight (lbs)",
                "miles":                  "Miles",
                "risk_score":             "Risk Score",
                "risk_tier":              "Risk Tier",
                "accessorial_type":       "Accessorial Type",
                "base_freight_usd":       "Base Freight ($)",
                "accessorial_charge_usd": "Est. Accessorial ($)",
            }),
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "Risk Score": st.column_config.ProgressColumn(
                    "Risk Score", format="%.0f%%", min_value=0, max_value=1
                ),
                "Base Freight ($)":     st.column_config.NumberColumn(format="$%.2f"),
                "Est. Accessorial ($)": st.column_config.NumberColumn(format="$%.2f"),
            },
            height=500,
        )

    selected_rows = event.selection.get("rows", []) if hasattr(event, "selection") else []
    if selected_rows:
        row_idx = selected_rows[0]
        sid = df.iloc[row_idx]["shipment_id"]
        st.session_state["selected_shipment"] = sid
        st.rerun()

    st.caption("Click any row to view shipment detail.")
