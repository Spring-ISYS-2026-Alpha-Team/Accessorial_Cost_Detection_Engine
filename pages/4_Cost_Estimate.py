# File: pages/4_Cost_Estimate.py
import os
import sys
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_utils import require_auth
from utils.styling import inject_css, top_nav, TIER_COLORS, CHARGE_COLORS
from pipeline.data_pipeline import get_data_pipeline
from pipeline.config import CHARGE_TYPE_LABELS, CATEGORICAL_COLUMNS, CONTINUOUS_COLUMNS, is_pace_model_ready

st.set_page_config(
    page_title="PACE — Cost Estimate",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

require_auth()
username = st.session_state.get("username", "User")
top_nav(username)

# ── Model availability ────────────────────────────────────────────
MODEL_READY = is_pace_model_ready()

# ── US States for dropdowns ───────────────────────────────────────
US_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
    "UNKNOWN",
]

CARRIER_OPERATIONS = ["A", "B", "C", "D", "E", "F", "UNKNOWN"]
CARRIER_SIZES      = ["A", "B", "C", "D", "E", "F", "G", "UNKNOWN"]
SAFETY_RATINGS     = ["SATISFACTORY", "CONDITIONAL", "UNSATISFACTORY", "UNKNOWN"]
UNIT_TYPES         = [
    "STRAIGHT TRUCK", "TRUCK TRACTOR", "TRAILER", "BUS",
    "MOTOR COACH", "VAN", "UNKNOWN",
]

# ── Header ────────────────────────────────────────────────────────
st.markdown("## Manual Shipment Estimator")
st.caption("Enter carrier and shipment details to predict accessorial risk with the PACE model.")

if not MODEL_READY:
    st.info(
        "The PACE model is not yet trained. Predictions will be available once "
        "training completes. You can still fill in details and save them.",
        icon="⏳"
    )

st.divider()

# ── Layout ────────────────────────────────────────────────────────
form_col, result_col = st.columns([2, 3], gap="large")

with form_col:

    # ── Carrier Profile ───────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### Carrier Profile")

        dot_number = st.number_input(
            "DOT Number",
            min_value=0, max_value=9999999, value=0, step=1,
            help="Enter USDOT number to auto-fill carrier data (production only)"
        )

        c1, c2 = st.columns(2)
        with c1:
            carrier_status = st.selectbox(
                "Carrier Status", ["A", "I", "UNKNOWN"],
                help="A=Active, I=Inactive"
            )
            carrier_operation = st.selectbox(
                "Carrier Operation", CARRIER_OPERATIONS
            )
            carrier_fleetsize = st.selectbox(
                "Fleet Size", CARRIER_SIZES
            )
            carrier_state = st.selectbox(
                "Carrier State", US_STATES
            )

        with c2:
            power_units = st.number_input(
                "Power Units", min_value=0, max_value=100000, value=10, step=1
            )
            total_drivers = st.number_input(
                "Total Drivers", min_value=0, max_value=500000, value=15, step=1
            )
            safety_rating = st.selectbox(
                "Safety Rating", SAFETY_RATINGS
            )
            hm_ind = st.selectbox(
                "Hazmat Carrier", ["N", "Y"]
            )

    # ── Inspection & Violations ───────────────────────────────────
    with st.container(border=True):
        st.markdown("#### Inspection & Violations")

        v1, v2, v3 = st.columns(3)
        with v1:
            oos_total      = st.number_input("OOS Total",      0, 1000, 0)
            driver_oos     = st.number_input("Driver OOS",     0, 1000, 0)
            vehicle_oos    = st.number_input("Vehicle OOS",    0, 1000, 0)
        with v2:
            basic_viol     = st.number_input("Basic Viol.",    0, 500, 0)
            unsafe_viol    = st.number_input("Unsafe Viol.",   0, 500, 0)
            vh_maint_viol  = st.number_input("Veh. Maint.",    0, 500, 0)
        with v3:
            fatigued_viol  = st.number_input("Fatigued Viol.", 0, 500, 0)
            dr_fitness     = st.number_input("Driver Fitness", 0, 500, 0)
            hm_viol        = st.number_input("Hazmat Viol.",   0, 500, 0)

    # ── Crash History ─────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### Crash History")
        cr1, cr2, cr3 = st.columns(3)
        with cr1:
            crash_count    = st.number_input("Crash Count",    0, 10000, 0)
        with cr2:
            crash_injuries = st.number_input("Injuries",       0, 10000, 0)
        with cr3:
            crash_fatals   = st.number_input("Fatalities",     0, 1000,  0)

    # ── Context ───────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### Shipment Context")
        ctx1, ctx2 = st.columns(2)
        with ctx1:
            origin_state = st.selectbox("Origin State", US_STATES, key="orig_st")
            unit_type    = st.selectbox("Unit Type", UNIT_TYPES)
            insp_month   = st.slider("Month", 1, 12, 6)
        with ctx2:
            dest_state   = st.selectbox("Dest. State", US_STATES, key="dest_st")
            insp_dow     = st.selectbox(
                "Day of Week",
                ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            )
            is_holiday   = st.toggle("Holiday Period")

    estimate_clicked = st.button(
        "Predict Accessorial Risk →",
        type="primary",
        use_container_width=True,
        disabled=not MODEL_READY,
    )

    if not MODEL_READY:
        st.caption("⏳ Available after model training completes")

    # ── Model info ────────────────────────────────────────────────
    with st.expander("ℹ️ Model Info", expanded=False):
        st.markdown(f"""
**Model:** PACE FT-Transformer
**Architecture:** Feature Tokenizer + Transformer Encoder
**Regression target:** Accessorial risk score (0–100)
**Classification target:** Charge type ({len(CHARGE_TYPE_LABELS)} classes)
**Categorical features:** {len(CATEGORICAL_COLUMNS)}
**Continuous features:** {len(CONTINUOUS_COLUMNS)}
**Data source:** FMCSA SAFER + EIA + FRED + NWS
        """)

# ── Results column ────────────────────────────────────────────────
with result_col:

    if estimate_clicked and MODEL_READY:
        # Build input dict
        dow_map = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2,
            "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        user_inputs = {
            "dot_number":                dot_number,
            "carrier_status_code":       carrier_status,
            "carrier_carrier_operation": carrier_operation,
            "carrier_fleetsize":         carrier_fleetsize,
            "carrier_power_units":       power_units,
            "carrier_truck_units":       power_units,
            "carrier_total_drivers":     total_drivers,
            "carrier_total_cdl":         total_drivers,
            "carrier_phy_state":         carrier_state,
            "carrier_phy_country":       "US",
            "carrier_safety_rating":     safety_rating,
            "carrier_hm_ind":            hm_ind,
            "oos_total":                 oos_total,
            "driver_oos_total":          driver_oos,
            "vehicle_oos_total":         vehicle_oos,
            "basic_viol":                basic_viol,
            "unsafe_viol":               unsafe_viol,
            "vh_maint_viol":             vh_maint_viol,
            "fatigued_viol":             fatigued_viol,
            "dr_fitness_viol":           dr_fitness,
            "hm_viol":                   hm_viol,
            "crash_count":               crash_count,
            "crash_injuries_total":      crash_injuries,
            "crash_fatalities_total":    crash_fatals,
            "crash_avg_severity": (
                (crash_fatals * 3 + crash_injuries * 2) / max(crash_count, 1)
            ),
            "insp_month":                insp_month,
            "insp_dow":                  dow_map.get(insp_dow, 0),
            "is_holiday":                int(is_holiday),
            "is_near_holiday":           int(is_holiday),
            "unit_type_desc":            unit_type,
            "report_state":              origin_state,
            "carrier_crgo_genfreight":   "X",
        }

        try:
            from pipeline.inference import get_inference_engine
            from pipeline.data_pipeline import get_data_pipeline

            dp       = get_data_pipeline()
            engine   = get_inference_engine()
            features = dp.process_manual(user_inputs)
            result   = engine.predict_single(features)

            st.session_state["last_estimate"] = {
                "result":      result,
                "user_inputs": user_inputs,
            }

        except Exception as e:
            st.error(f"Prediction failed: {e}")

    # ── Display results ───────────────────────────────────────────
    if "last_estimate" in st.session_state:
        e      = st.session_state["last_estimate"]
        result = e["result"]
        score  = result["risk_score"]
        label  = result["risk_label"]
        charge = result["charge_type"]
        probs  = result["probabilities"]
        color  = TIER_COLORS.get(label, "#94A3B8")
        c_color = CHARGE_COLORS.get(charge, "#A78BFA")

        # ── Risk score gauge ──────────────────────────────────────
        with st.container(border=True):
            st.markdown("#### Accessorial Risk Score")

            gauge_col, info_col = st.columns([1, 1], gap="large")

            with gauge_col:
                gauge_fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=round(score, 1),
                    number={
                        "suffix": "%",
                        "font": {"size": 42, "color": color},
                    },
                    title={
                        "text": f"<b>{label} Risk</b>",
                        "font": {"size": 16, "color": color},
                    },
                    gauge={
                        "axis": {
                            "range": [0, 100],
                            "tickcolor": "#475569",
                            "tickfont": {"color": "#94A3B8", "size": 11},
                        },
                        "bar":      {"color": color, "thickness": 0.28},
                        "bgcolor":  "#0f0a1e",
                        "borderwidth": 0,
                        "steps": [
                            {"range": [0,  25], "color": "rgba(5,150,105,0.15)"},
                            {"range": [25, 50], "color": "rgba(251,146,60,0.10)"},
                            {"range": [50, 75], "color": "rgba(217,119,6,0.15)"},
                            {"range": [75,100], "color": "rgba(220,38,38,0.15)"},
                        ],
                        "threshold": {
                            "line":      {"color": color, "width": 3},
                            "thickness": 0.8,
                            "value":     score,
                        },
                    },
                ))
                gauge_fig.update_layout(
                    height=240,
                    margin=dict(l=20, r=20, t=50, b=10),
                    paper_bgcolor="#0f0a1e",
                    font={"color": "#A78BFA"},
                )
                st.plotly_chart(gauge_fig, use_container_width=True)

            with info_col:
                st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

                # Predicted charge type
                st.markdown(
                    f"<div style='background:rgba(0,0,0,0.3);border:1px solid "
                    f"{c_color};border-radius:8px;padding:14px;margin-bottom:12px;'>"
                    f"<div style='color:#94A3B8;font-size:11px;font-weight:600;"
                    f"letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;'>"
                    f"Predicted Charge Type</div>"
                    f"<div style='color:{c_color};font-size:20px;font-weight:700;'>"
                    f"{charge}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                # Quick stats
                viol_total = sum([
                    basic_viol, unsafe_viol, vh_maint_viol,
                    fatigued_viol, dr_fitness, hm_viol
                ])
                st.markdown(
                    f"<div style='background:rgba(147,51,234,0.08);border-radius:8px;"
                    f"padding:12px;font-size:13px;color:#CBD5E1;'>"
                    f"<div>OOS Total: <b style='color:#E2E8F0;'>{oos_total}</b></div>"
                    f"<div>Total Violations: <b style='color:#E2E8F0;'>{viol_total}</b></div>"
                    f"<div>Crash Count: <b style='color:#E2E8F0;'>{crash_count}</b></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Charge type probabilities ─────────────────────────────
        with st.container(border=True):
            st.markdown("#### Charge Type Probabilities")

            prob_data = sorted(probs.items(), key=lambda x: x[1], reverse=True)
            labels    = [p[0] for p in prob_data]
            values    = [round(p[1] * 100, 1) for p in prob_data]
            bar_colors = [CHARGE_COLORS.get(l, "#A78BFA") for l in labels]

            prob_fig = go.Figure(go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker_color=bar_colors,
                text=[f"{v:.1f}%" for v in values],
                textposition="outside",
                textfont={"color": "#E2E8F0"},
            ))
            prob_fig.update_layout(
                margin=dict(l=0, r=60, t=8, b=0), height=260,
                plot_bgcolor="#0f0a1e", paper_bgcolor="#0f0a1e",
                font=dict(color="#A78BFA"),
                xaxis=dict(
                    ticksuffix="%", range=[0, 110],
                    gridcolor="rgba(150,50,200,0.15)", color="#94A3B8",
                ),
                yaxis=dict(
                    gridcolor="rgba(150,50,200,0.15)", color="#94A3B8",
                    autorange="reversed",
                ),
            )
            st.plotly_chart(prob_fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Risk breakdown ────────────────────────────────────────
        with st.container(border=True):
            st.markdown("#### Risk Factor Breakdown")

            factors = []

            # OOS risk
            if oos_total > 5:
                factors.append(("OOS Violations",
                    f"{oos_total} total OOS events — significantly above average",
                    "high"))
            elif oos_total > 0:
                factors.append(("OOS Violations",
                    f"{oos_total} OOS event(s) recorded",
                    "medium"))

            # Violation risk
            viol_sum = basic_viol + unsafe_viol + vh_maint_viol
            if viol_sum > 10:
                factors.append(("Safety Violations",
                    f"{viol_sum} combined basic/unsafe/maintenance violations",
                    "high"))
            elif viol_sum > 0:
                factors.append(("Safety Violations",
                    f"{viol_sum} violation(s) on record",
                    "medium"))

            # Crash risk
            if crash_count > 3:
                factors.append(("Crash History",
                    f"{crash_count} crashes — elevated accident exposure",
                    "high"))
            elif crash_count > 0:
                factors.append(("Crash History",
                    f"{crash_count} crash(es) on record",
                    "medium"))

            # Hazmat
            if hm_viol > 0 or hm_ind == "Y":
                factors.append(("Hazmat Exposure",
                    "Hazmat carrier or violations — hazmat fee risk elevated",
                    "high"))

            # Driver fitness
            if dr_fitness > 0 or fatigued_viol > 0:
                factors.append(("Driver Compliance",
                    f"{dr_fitness + fatigued_viol} driver fitness/fatigue violations",
                    "high"))

            # Safety rating
            if safety_rating == "UNSATISFACTORY":
                factors.append(("Safety Rating",
                    "Unsatisfactory FMCSA safety rating — highest risk tier",
                    "high"))
            elif safety_rating == "CONDITIONAL":
                factors.append(("Safety Rating",
                    "Conditional safety rating — moderate compliance concern",
                    "medium"))

            # Friday dispatch
            if insp_dow == "Friday":
                factors.append(("Friday Dispatch",
                    "Friday shipments have 2× higher weekend detention risk",
                    "medium"))

            # Peak season
            if insp_month in (10, 11, 12):
                factors.append(("Peak Season Q4",
                    "Oct–Dec capacity crunch raises accessorial incidence 15–25%",
                    "medium"))

            if not factors:
                factors.append(("Clean Profile",
                    "No significant risk factors identified — low accessorial exposure",
                    "low"))

            sev_styles = {
                "high":   ("#F87171", "rgba(220,38,38,0.12)"),
                "medium": ("#FCD34D", "rgba(217,119,6,0.12)"),
                "low":    ("#34D399", "rgba(5,150,105,0.12)"),
            }

            for f_label, f_detail, f_sev in factors[:5]:
                fg, bg = sev_styles.get(f_sev, sev_styles["low"])
                st.markdown(
                    f"<div style='background:{bg};border-left:3px solid {fg};"
                    f"border-radius:6px;padding:8px 12px;margin-bottom:8px;'>"
                    f"<div style='color:{fg};font-size:12px;font-weight:600;"
                    f"margin-bottom:2px;'>{f_label}</div>"
                    f"<div style='color:#CBD5E1;font-size:12px;'>{f_detail}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    else:
        # Empty state
        with st.container(border=True):
            st.markdown(
                "<div style='text-align:center;padding:100px 20px;color:#9CA3AF;'>"
                "<div style='font-size:48px;'>🚛</div>"
                "<div style='font-size:15px;font-weight:600;margin-top:16px;"
                "color:#E2E8F0;'>Enter carrier details</div>"
                "<div style='font-size:13px;margin-top:8px;'>"
                "Fill in the form and click "
                "<b style='color:#A78BFA;'>Predict Accessorial Risk</b>"
                " to get a PACE prediction</div>"
                "</div>",
                unsafe_allow_html=True,
            )