# File: pages/4_Cost_Estimate.py
import os
import sys
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_utils import require_auth
from utils.styling import inject_css, top_nav, TIER_COLORS, CHARGE_COLORS
from pipeline.config import CHARGE_TYPE_LABELS, is_pace_model_ready

st.set_page_config(
    page_title="PACE — Cost Estimate",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

require_auth()
username = st.session_state.get("username", "User")
top_nav(username)

MODEL_READY = is_pace_model_ready()
API_ENABLED = os.environ.get("PACE_ENV", "").lower() == "production"

US_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
    "UNKNOWN",
]

UNIT_TYPES = [
    "TRUCK TRACTOR", "STRAIGHT TRUCK", "TRAILER",
    "VAN", "MOTOR COACH", "BUS", "UNKNOWN",
]

# ── Header ─────────────────────────────────────────────────────────
st.markdown("## Cost Estimator")
st.caption(
    "Enter a carrier DOT number and shipment context — PACE pulls the carrier "
    "profile automatically and predicts accessorial risk."
)

if not MODEL_READY:
    st.info(
        "PACE model not yet trained — predictions available after training. "
        "You can still fetch carrier data.",
        icon="⏳",
    )

st.divider()

# ── Layout ─────────────────────────────────────────────────────────
form_col, result_col = st.columns([2, 3], gap="large")

with form_col:

    # ── Step 1: DOT lookup ─────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### Carrier DOT Number")

        dot_col, btn_col = st.columns([3, 2], gap="small")
        with dot_col:
            dot_input = st.text_input(
                "USDOT Number",
                placeholder="e.g. 72011",
                label_visibility="collapsed",
                help="Enter the carrier's USDOT number",
            )
        with btn_col:
            fetch_clicked = st.button(
                "Fetch Carrier →",
                type="primary",
                use_container_width=True,
                disabled=not dot_input.strip(),
            )

        if fetch_clicked and dot_input.strip():
            try:
                dot_int = int(dot_input.strip())
            except ValueError:
                st.error("DOT number must be numeric.")
                st.stop()

            with st.spinner(f"Fetching DOT {dot_int}..."):
                carrier_data = {}
                if API_ENABLED:
                    try:
                        from pipeline.api_integration import get_enricher
                        enricher = get_enricher()
                        carrier_data = enricher.fmcsa.build_realtime_features(dot_int)
                    except Exception:
                        carrier_data = {}

                st.session_state["ce_dot"]     = dot_int
                st.session_state["ce_carrier"] = carrier_data
                st.rerun()

        # ── Carrier summary card ───────────────────────────────────
        if st.session_state.get("ce_dot"):
            dot_num  = st.session_state["ce_dot"]
            cd       = st.session_state.get("ce_carrier", {})
            name     = cd.get("carrier_name", f"DOT {dot_num}")
            status   = cd.get("carrier_status_code", "")
            safety   = cd.get("carrier_safety_rating", "")
            oos      = int(float(cd.get("oos_total", 0)))
            crashes  = int(float(cd.get("crash_count", 0)))
            pwr      = cd.get("carrier_power_units", "")
            state    = cd.get("carrier_phy_state", "")
            hm       = cd.get("carrier_hm_ind", "")

            src      = "Live FMCSA" if cd else "DOT entered — no live data"
            src_color = "#34D399" if cd else "#94A3B8"
            safety_color = (
                "#F87171" if safety == "UNSATISFACTORY" else
                "#FCD34D" if safety == "CONDITIONAL" else
                "#34D399" if safety == "SATISFACTORY" else
                "#94A3B8"
            )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='background:rgba(147,51,234,0.08);border:1px solid "
                f"rgba(147,51,234,0.3);border-radius:8px;padding:12px 16px;'>"
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:flex-start;margin-bottom:8px;'>"
                f"<div>"
                f"<div style='font-size:15px;font-weight:700;color:#E2E8F0;'>{name}</div>"
                f"<div style='font-size:12px;color:#64748B;margin-top:2px;'>USDOT {dot_num}</div>"
                f"</div>"
                f"<span style='border:1px solid {src_color};color:{src_color};"
                f"border-radius:4px;padding:2px 8px;font-size:10px;'>{src}</span>"
                f"</div>"
                f"<div style='display:flex;gap:16px;flex-wrap:wrap;font-size:12px;"
                f"color:#94A3B8;margin-top:4px;'>"
                + (f"<span>Status: <b style='color:#E2E8F0;'>{status}</b></span>" if status else "")
                + (f"<span>Safety: <b style='color:{safety_color};'>{safety}</b></span>" if safety else "")
                + (f"<span>State: <b style='color:#E2E8F0;'>{state}</b></span>" if state else "")
                + (f"<span>Power Units: <b style='color:#E2E8F0;'>{pwr}</b></span>" if pwr else "")
                + (f"<span>OOS: <b style='color:#F87171;'>{oos}</b></span>" if oos > 0 else
                   f"<span>OOS: <b style='color:#34D399;'>0</b></span>")
                + (f"<span>Crashes: <b style='color:#F87171;'>{crashes}</b></span>" if crashes > 0 else
                   f"<span>Crashes: <b style='color:#34D399;'>0</b></span>")
                + (f"<span>Hazmat: <b style='color:#FCD34D;'>Yes</b></span>" if hm == "Y" else "")
                + f"</div></div>",
                unsafe_allow_html=True,
            )

            if st.button("✕ Clear carrier", key="ce_clear", use_container_width=False):
                del st.session_state["ce_dot"]
                del st.session_state["ce_carrier"]
                st.rerun()

    # ── Step 2: Shipment context ───────────────────────────────────
    with st.container(border=True):
        st.markdown("#### Shipment Context")

        ctx1, ctx2 = st.columns(2)
        with ctx1:
            origin_state = st.selectbox("Origin State", US_STATES, key="ce_orig")
            unit_type    = st.selectbox("Unit Type", UNIT_TYPES)
            insp_month   = st.selectbox(
                "Month",
                options=list(range(1, 13)),
                format_func=lambda m: [
                    "January","February","March","April","May","June",
                    "July","August","September","October","November","December"
                ][m - 1],
                index=5,
            )
        with ctx2:
            dest_state = st.selectbox("Dest. State", US_STATES, key="ce_dest")
            insp_dow   = st.selectbox(
                "Day of Week",
                ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
            )
            is_holiday = st.toggle("Holiday Period")

    # ── Predict button ─────────────────────────────────────────────
    has_dot    = bool(st.session_state.get("ce_dot"))
    can_predict = MODEL_READY and has_dot

    estimate_clicked = st.button(
        "Predict Accessorial Risk →",
        type="primary",
        use_container_width=True,
        disabled=not can_predict,
    )

    if not has_dot:
        st.caption("Enter a DOT number above to enable prediction")
    elif not MODEL_READY:
        st.caption("⏳ Available after model training completes")

    with st.expander("ℹ️ Model Info", expanded=False):
        from pipeline.config import CHARGE_TYPE_LABELS, CATEGORICAL_COLUMNS, CONTINUOUS_COLUMNS
        st.markdown(f"""
**Model:** PACE FT-Transformer
**Architecture:** Feature Tokenizer + Transformer Encoder
**Regression target:** Accessorial risk score (0–100)
**Classification target:** Charge type ({len(CHARGE_TYPE_LABELS)} classes)
**Categorical features:** {len(CATEGORICAL_COLUMNS)}
**Continuous features:** {len(CONTINUOUS_COLUMNS)}
**Data source:** FMCSA SAFER + EIA + FRED + NWS
        """)

# ── Run prediction ──────────────────────────────────────────────────
if estimate_clicked and can_predict:
    dot_num = st.session_state["ce_dot"]
    cd      = st.session_state.get("ce_carrier", {})
    dow_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6,
    }

    with st.spinner(f"Running PACE prediction for DOT {dot_num}..."):
        try:
            from pipeline.inference import get_inference_engine
            from pipeline.data_pipeline import get_data_pipeline

            engine = get_inference_engine()

            # Merge fetched carrier data with user-supplied context
            user_inputs = {
                **cd,
                "dot_number":        dot_num,
                "insp_month":        insp_month,
                "insp_dow":          dow_map.get(insp_dow, 0),
                "is_holiday":        int(is_holiday),
                "is_near_holiday":   int(is_holiday),
                "unit_type_desc":    unit_type,
                "report_state":      origin_state,
                "carrier_crgo_genfreight": "X",
            }

            dp       = get_data_pipeline()
            features = dp.process_manual(user_inputs)
            result   = engine.predict_single(features)

            result.setdefault("carrier_name", cd.get("carrier_name", f"DOT {dot_num}"))
            result.setdefault("data_source", "live_fmcsa" if cd else "context_only")

            st.session_state["ce_result"] = result

        except Exception as e:
            st.error(f"Prediction failed: {e}")

# ── Results ─────────────────────────────────────────────────────────
with result_col:

    if "ce_result" in st.session_state:
        result  = st.session_state["ce_result"]
        score   = result["risk_score"]
        label   = result["risk_label"]
        charge  = result["charge_type"]
        probs   = result["probabilities"]
        color   = TIER_COLORS.get(label, "#94A3B8")
        c_color = CHARGE_COLORS.get(charge, "#A78BFA")

        cd  = st.session_state.get("ce_carrier", {})
        oos_total   = int(float(cd.get("oos_total", 0)))
        crash_count = int(float(cd.get("crash_count", 0)))
        viol_total  = sum(
            int(float(cd.get(k, 0)))
            for k in ["basic_viol","unsafe_viol","vh_maint_viol",
                      "fatigued_viol","dr_fitness_viol","hm_viol"]
        )
        safety_rating = cd.get("carrier_safety_rating", "UNKNOWN")
        hm_ind        = cd.get("carrier_hm_ind", "N")

        # ── Risk gauge ─────────────────────────────────────────────
        with st.container(border=True):
            st.markdown("#### Accessorial Risk Score")
            gauge_col, info_col = st.columns([1, 1], gap="large")

            with gauge_col:
                gauge_fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=round(score, 1),
                    number={"suffix": "%", "font": {"size": 42, "color": color}},
                    title={"text": f"<b>{label} Risk</b>",
                           "font": {"size": 16, "color": color}},
                    gauge={
                        "axis": {
                            "range": [0, 100],
                            "tickfont": {"color": "#94A3B8", "size": 11},
                        },
                        "bar":     {"color": color, "thickness": 0.28},
                        "bgcolor": "#0f0a1e",
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

        # ── Charge type probabilities ──────────────────────────────
        with st.container(border=True):
            st.markdown("#### Charge Type Probabilities")
            prob_data  = sorted(probs.items(), key=lambda x: x[1], reverse=True)
            p_labels   = [p[0] for p in prob_data]
            p_values   = [round(p[1] * 100, 1) for p in prob_data]
            bar_colors = [CHARGE_COLORS.get(l, "#A78BFA") for l in p_labels]

            prob_fig = go.Figure(go.Bar(
                x=p_values,
                y=p_labels,
                orientation="h",
                marker_color=bar_colors,
                text=[f"{v:.1f}%" for v in p_values],
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

        # ── Risk factor breakdown ──────────────────────────────────
        with st.container(border=True):
            st.markdown("#### Risk Factor Breakdown")
            factors = []

            if oos_total > 5:
                factors.append(("OOS Violations",
                    f"{oos_total} total OOS events — significantly above average", "high"))
            elif oos_total > 0:
                factors.append(("OOS Violations",
                    f"{oos_total} OOS event(s) recorded", "medium"))

            if viol_total > 10:
                factors.append(("Safety Violations",
                    f"{viol_total} combined violations on record", "high"))
            elif viol_total > 0:
                factors.append(("Safety Violations",
                    f"{viol_total} violation(s) on record", "medium"))

            if crash_count > 3:
                factors.append(("Crash History",
                    f"{crash_count} crashes — elevated accident exposure", "high"))
            elif crash_count > 0:
                factors.append(("Crash History",
                    f"{crash_count} crash(es) on record", "medium"))

            if hm_ind == "Y":
                factors.append(("Hazmat Exposure",
                    "Hazmat carrier — hazmat fee risk elevated", "high"))

            if safety_rating == "UNSATISFACTORY":
                factors.append(("Safety Rating",
                    "Unsatisfactory FMCSA safety rating — highest risk tier", "high"))
            elif safety_rating == "CONDITIONAL":
                factors.append(("Safety Rating",
                    "Conditional safety rating — moderate compliance concern", "medium"))

            if insp_dow == "Friday":
                factors.append(("Friday Dispatch",
                    "Friday shipments have 2× higher weekend detention risk", "medium"))

            if insp_month in (10, 11, 12):
                factors.append(("Peak Season Q4",
                    "Oct–Dec capacity crunch raises accessorial incidence 15–25%", "medium"))

            if not factors:
                factors.append(("Clean Profile",
                    "No significant risk factors identified — low accessorial exposure", "low"))

            sev_styles = {
                "high":   ("#F87171", "rgba(220,38,38,0.12)"),
                "medium": ("#FCD34D", "rgba(217,119,6,0.12)"),
                "low":    ("#34D399", "rgba(5,150,105,0.12)"),
            }
            for f_label, f_detail, f_sev in factors[:5]:
                fg, bg = sev_styles[f_sev]
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
        with st.container(border=True):
            st.markdown(
                "<div style='text-align:center;padding:100px 20px;color:#9CA3AF;'>"
                "<div style='font-size:48px;'>🚛</div>"
                "<div style='font-size:15px;font-weight:600;margin-top:16px;"
                "color:#E2E8F0;'>Enter a DOT number to start</div>"
                "<div style='font-size:13px;margin-top:8px;'>"
                "PACE will fetch the carrier profile automatically — "
                "just add shipment context and click "
                "<b style='color:#A78BFA;'>Predict Accessorial Risk</b>"
                "</div>"
                "</div>",
                unsafe_allow_html=True,
            )
