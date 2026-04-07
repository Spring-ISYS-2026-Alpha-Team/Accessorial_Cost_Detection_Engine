# File: pages/4_Cost_Estimate.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.database import get_connection, get_shipments, load_shipments_with_fallback
from utils.mock_data import generate_mock_shipments
from utils.styling import inject_css, top_nav, NAVY_500
from utils.cost_model import get_cost_model
from utils.risk_model import get_risk_model, predict_risk

st.set_page_config(
    page_title="PACE — Cost Estimate",
    page_icon="💰",
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

# ── Load data ─────────────────────────────────────────────────────────────────
_conn   = get_connection()
_df_raw = load_shipments_with_fallback(_conn)
if _df_raw.empty:
    _df_raw = generate_mock_shipments(300)
    st.info("Live database unavailable — showing demo data.", icon="ℹ️")

df = _df_raw.copy()
if "AppointmentType" not in df.columns:
    df["AppointmentType"] = "Drop"
df["AppointmentType"] = df["AppointmentType"].fillna("Drop")

cost_model = get_cost_model(len(df), df)
risk_model, _ = get_risk_model(len(df), df)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Cost & Risk Estimator")
st.caption("Predict total shipment cost and accessorial risk using machine learning.")
st.divider()

# ── Input form ────────────────────────────────────────────────────────────────
form_col, result_col = st.columns([2, 3], gap="large")

with form_col:
    with st.container(border=True):
        st.markdown("#### Shipment Details")
        carriers_list   = sorted(df["carrier"].dropna().unique())
        facilities_list = sorted(df["facility"].dropna().unique())
        appt_types_list = sorted(df["AppointmentType"].dropna().unique())

        carrier  = st.selectbox("Carrier",          carriers_list)
        facility = st.selectbox("Facility",         facilities_list)
        appt     = st.selectbox("Appointment Type", appt_types_list)
        weight   = st.number_input("Weight (lbs)", min_value=100,  max_value=44_000,
                                   value=10_000, step=500)
        miles    = st.number_input("Miles",        min_value=50,   max_value=2_400,
                                   value=500,    step=50)
        estimate_clicked = st.button("Estimate Cost & Risk →", type="primary",
                                     width="stretch")

    with st.expander("ℹ️ Model Info", expanded=False):
        st.markdown(f"""
**Cost model:** Random Forest Regressor
**Risk model:** LightGBM Regressor
**Training samples:** {len(df):,}
**Cost features:** Carrier, Facility, Weight, Miles
**Risk features:** Carrier, Facility, Appointment Type, Weight, Miles
**Risk target:** Accessorial risk score (0 – 1)
        """)

# ── Run predictions ───────────────────────────────────────────────────────────
with result_col:
    avg_cpm   = df["cost_per_mile"].mean()
    avg_total = df["total_cost_usd"].mean()

    if estimate_clicked:
        # Cost prediction
        X_cost = pd.DataFrame([{
            "carrier": carrier, "facility": facility,
            "weight_lbs": weight, "miles": miles,
        }])
        rf         = cost_model.named_steps["rf"]
        X_trans    = cost_model.named_steps["pre"].transform(X_cost)
        tree_preds = np.array([t.predict(X_trans)[0] for t in rf.estimators_])
        pred       = tree_preds.mean()
        lower      = max(0, pred - 1.96 * tree_preds.std())
        upper      = pred + 1.96 * tree_preds.std()

        # Risk prediction
        risk = predict_risk(risk_model, carrier, facility, appt, weight, miles, df)

        st.session_state["last_estimate"] = {
            "pred": pred, "lower": lower, "upper": upper,
            "simple_est": avg_cpm * miles, "avg_total": avg_total,
            "carrier": carrier, "facility": facility,
            "appt": appt, "weight": weight, "miles": miles,
            "risk": risk,
        }

    if "last_estimate" in st.session_state:
        e    = st.session_state["last_estimate"]
        pred, lower, upper = e["pred"], e["lower"], e["upper"]
        risk = e.get("risk")

        # ── Cost section ──────────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown("#### ML Cost Prediction")
            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("Predicted Total Cost", f"${pred:,.2f}")
            with r2:
                st.metric("95% Lower Bound", f"${lower:,.2f}")
            with r3:
                st.metric("95% Upper Bound", f"${upper:,.2f}")
            st.markdown(
                f"<div style='font-size:13px;color:#94A3B8;margin-top:8px;'>"
                f"Confidence range: <b style='color:#E2E8F0;'>${lower:,.0f} – ${upper:,.0f}</b>"
                f" &nbsp;|&nbsp; Spread: <b style='color:#E2E8F0;'>${upper - lower:,.0f}</b>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Risk section ──────────────────────────────────────────────────────
        if risk:
            with st.container(border=True):
                st.markdown("#### Accessorial Risk Assessment")

                gauge_col, factors_col = st.columns([1, 1], gap="large")

                with gauge_col:
                    gauge_fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=round(risk["score"] * 100, 1),
                        number={
                            "suffix": "%",
                            "font": {"size": 38, "color": risk["color"]},
                        },
                        title={
                            "text": f"<b>{risk['tier']} Risk</b>",
                            "font": {"size": 15, "color": risk["color"]},
                        },
                        gauge={
                            "axis": {
                                "range": [0, 100],
                                "tickcolor": "#475569",
                                "tickfont": {"color": "#94A3B8", "size": 11},
                            },
                            "bar":     {"color": risk["color"], "thickness": 0.28},
                            "bgcolor": "#0f0a1e",
                            "borderwidth": 0,
                            "steps": [
                                {"range": [0,  34], "color": "rgba(5,150,105,0.15)"},
                                {"range": [34, 67], "color": "rgba(217,119,6,0.15)"},
                                {"range": [67,100], "color": "rgba(220,38,38,0.15)"},
                            ],
                            "threshold": {
                                "line":      {"color": risk["color"], "width": 3},
                                "thickness": 0.8,
                                "value":     risk["score"] * 100,
                            },
                        },
                    ))
                    gauge_fig.update_layout(
                        height=220,
                        margin=dict(l=20, r=20, t=40, b=10),
                        paper_bgcolor="#0f0a1e",
                        font={"color": "#A78BFA"},
                    )
                    st.plotly_chart(gauge_fig, width="stretch")

                with factors_col:
                    st.markdown(
                        "<p style='color:#94A3B8;font-size:12px;"
                        "margin:0 0 10px;'>Key risk drivers</p>",
                        unsafe_allow_html=True,
                    )
                    sev_colors = {
                        "high":    ("#F87171", "rgba(220,38,38,0.12)"),
                        "low":     ("#34D399", "rgba(5,150,105,0.12)"),
                        "neutral": ("#A78BFA", "rgba(147,51,234,0.12)"),
                    }
                    for label, detail, sev in risk["factors"]:
                        fg, bg = sev_colors.get(sev, sev_colors["neutral"])
                        st.markdown(
                            f"<div style='background:{bg};border-left:3px solid {fg};"
                            f"border-radius:6px;padding:8px 12px;margin-bottom:8px;'>"
                            f"<div style='color:{fg};font-size:12px;font-weight:600;"
                            f"margin-bottom:2px;'>{label}</div>"
                            f"<div style='color:#CBD5E1;font-size:12px;'>{detail}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Comparison section ────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown("#### How This Compares")
            simple_est = e["simple_est"]
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("ML Prediction",      f"${pred:,.2f}")
            with c2:
                st.metric("Avg Cost/Mile Est.", f"${simple_est:,.2f}",
                          delta=f"${pred - simple_est:+,.2f} vs ML", delta_color="inverse")
            with c3:
                st.metric("Fleet Avg Total",    f"${avg_total:,.2f}",
                          delta=f"${pred - avg_total:+,.2f} vs ML",  delta_color="inverse")

            st.markdown("<br>", unsafe_allow_html=True)
            comp_fig = go.Figure(go.Bar(
                x=["ML Prediction",
                   f"Avg Cost/Mile\n(${avg_cpm:.2f}/mi × {e['miles']} mi)",
                   "Fleet Avg Total"],
                y=[pred, simple_est, avg_total],
                marker_color=["#9333EA", "#6D28D9", "#4C1D95"],
                text=[f"${v:,.0f}" for v in [pred, simple_est, avg_total]],
                textposition="outside",
                textfont={"color": "#E2E8F0"},
            ))
            comp_fig.update_layout(
                margin=dict(l=0, r=0, t=8, b=0), height=220,
                plot_bgcolor="#0f0a1e", paper_bgcolor="#0f0a1e",
                font=dict(color="#A78BFA"),
                yaxis=dict(tickprefix="$", gridcolor="rgba(150,50,200,0.15)",
                           color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
                xaxis=dict(gridcolor="rgba(150,50,200,0.15)",
                           color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
                showlegend=False,
            )
            st.plotly_chart(comp_fig, width="stretch")

    else:
        with st.container(border=True):
            st.markdown(
                "<div style='text-align:center;padding:80px 20px;color:#9CA3AF;'>"
                "<div style='font-size:36px;'>💰</div>"
                "<div style='font-size:14px;margin-top:10px;'>"
                "Fill in shipment details and click <b>Estimate Cost & Risk</b></div>"
                "</div>",
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)

# ── Feature importance ────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### What Drives Cost — Feature Importance")
    st.caption("Relative contribution of each input to the cost model's predictions")

    rf       = cost_model.named_steps["rf"]
    pre      = cost_model.named_steps["pre"]
    enc      = pre.named_transformers_["cat"]
    cat_names = list(enc.get_feature_names_out(["carrier", "facility"]))
    all_names = cat_names + ["weight_lbs", "miles"]

    importance = pd.DataFrame({
        "Feature":    all_names,
        "Importance": rf.feature_importances_,
    }).sort_values("Importance", ascending=True).tail(12)

    importance["Feature"] = (
        importance["Feature"]
        .str.replace("carrier_",  "Carrier: ",   regex=False)
        .str.replace("facility_", "Facility: ",  regex=False)
        .str.replace("weight_lbs","Weight (lbs)", regex=False)
        .str.replace("miles",     "Miles",        regex=False)
    )

    fi_fig = go.Figure(go.Bar(
        x=importance["Importance"],
        y=importance["Feature"],
        orientation="h",
        marker_color="#9333EA",
        text=importance["Importance"].apply(lambda v: f"{v:.1%}"),
        textposition="outside",
        textfont={"color": "#E2E8F0"},
    ))
    fi_fig.update_layout(
        margin=dict(l=0, r=60, t=8, b=0), height=340,
        plot_bgcolor="#0f0a1e", paper_bgcolor="#0f0a1e",
        font=dict(color="#A78BFA"),
        xaxis=dict(tickformat=".0%", gridcolor="rgba(150,50,200,0.15)",
                   color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
        yaxis=dict(gridcolor="rgba(150,50,200,0.15)",
                   color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
    )
    st.plotly_chart(fi_fig, width="stretch")

# ── Historical distribution ───────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Historical Total Cost Distribution")
    st.caption("Where your estimate falls relative to all past shipments")

    hist_fig = go.Figure()
    hist_fig.add_trace(go.Histogram(
        x=df["total_cost_usd"], nbinsx=30,
        marker_color="#2D1B4E", marker_line_color=NAVY_500, marker_line_width=1,
        name="Historical",
    ))
    if "last_estimate" in st.session_state:
        v = st.session_state["last_estimate"]["pred"]
        hist_fig.add_vline(
            x=v, line_width=2, line_dash="dash", line_color="#DC2626",
            annotation_text=f"Your estimate: ${v:,.0f}",
            annotation_position="top right",
            annotation_font_color="#DC2626",
        )
    hist_fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=0), height=220,
        plot_bgcolor="#0f0a1e", paper_bgcolor="#0f0a1e",
        font=dict(color="#A78BFA"),
        xaxis=dict(tickprefix="$", gridcolor="rgba(150,50,200,0.15)",
                   color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
        yaxis=dict(gridcolor="rgba(150,50,200,0.15)",
                   color="#94A3B8", linecolor="rgba(150,50,200,0.2)"),
    )
    st.plotly_chart(hist_fig, width="stretch")
