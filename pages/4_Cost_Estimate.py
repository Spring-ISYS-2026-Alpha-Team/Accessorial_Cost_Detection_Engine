import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth_utils import check_auth
from utils.database import get_connection, get_shipments
from utils.mock_data import generate_mock_shipments
from utils.styling import inject_css, top_nav, NAVY_500
from utils.risk_model import predict_risk

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

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
FEATURE_COLUMNS_PATH = os.path.join(MODELS_DIR, "feature_columns.json")
MODEL_METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")

# ── Load data ─────────────────────────────────────────────────────────────────
_conn = get_connection()
_df_raw = get_shipments(_conn) if _conn is not None else pd.DataFrame()

if _df_raw.empty:
    _df_raw = generate_mock_shipments(300)
    st.info("Live database unavailable — showing demo data.", icon="ℹ️")

df = _df_raw.copy()

if "AppointmentType" not in df.columns:
    df["AppointmentType"] = "Drop"
df["AppointmentType"] = df["AppointmentType"].fillna("Drop")

# ── Use preloaded models from session ─────────────────────────────────────────
cost_model = st.session_state.get("cost_model")
risk_model = st.session_state.get("risk_model")

if cost_model is None:
    st.error("Cost model is not loaded. Please sign out and sign in again.")
    st.stop()

if risk_model is None:
    st.warning(
        "Risk model is not loaded. Cost estimate will still work, but risk scoring may be unavailable."
    )


# ── Helpers ───────────────────────────────────────────────────────────────────
def _unwrap_model(model):
    if isinstance(model, dict) and "model" in model:
        return model["model"]
    return model


def _is_pipeline_model(model) -> bool:
    return hasattr(model, "named_steps")


def _load_feature_columns():
    if not os.path.exists(FEATURE_COLUMNS_PATH):
        return None
    try:
        with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
            cols = json.load(f)
        return cols if isinstance(cols, list) else None
    except Exception:
        return None


def _load_model_metadata():
    if not os.path.exists(MODEL_METADATA_PATH):
        return {}
    try:
        with open(MODEL_METADATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _build_raw_cost_input(carrier, facility, weight, miles):
    return pd.DataFrame(
        [{
            "carrier": carrier,
            "facility": facility,
            "weight_lbs": float(weight),
            "miles": float(miles),
        }]
    )


def _build_encoded_cost_input(carrier, facility, weight, miles):
    feature_cols = _load_feature_columns() or []

    # create one full row with all expected training columns
    row = {col: 0 for col in feature_cols}

    # numeric inputs
    if "weight_lbs" in row:
        row["weight_lbs"] = float(weight)
    if "miles" in row:
        row["miles"] = float(miles)

    # default values for engineered features that may exist in the trained model
    defaults = {
        "holiday_flag": 0,
        "storm_flag": 0,
        "traffic_risk": 0,
        "weather_risk": 0,
        "avg_dwell_hrs": 3.0,
        "day_of_week": 1,
        "month": 1,
    }

    for key, value in defaults.items():
        if key in row:
            row[key] = value

    # one-hot encoded carrier/facility columns
    carrier_key = f"carrier_{carrier}"
    facility_key = f"facility_{facility}"

    if carrier_key in row:
        row[carrier_key] = 1
    if facility_key in row:
        row[facility_key] = 1

    # fallback in case the trained model used raw categorical columns
    if "carrier" in row:
        row["carrier"] = carrier
    if "facility" in row:
        row["facility"] = facility

    return pd.DataFrame([row], columns=feature_cols)


def _predict_cost_with_interval(model, carrier, facility, weight, miles):
    model = _unwrap_model(model)

    # Case 1: Pipeline model with preprocessor + rf
    if _is_pipeline_model(model):
        raw = _build_raw_cost_input(carrier, facility, weight, miles)
        rf = model.named_steps["rf"]
        X_trans = model.named_steps["pre"].transform(raw)

        if hasattr(rf, "estimators_") and len(rf.estimators_) > 0:
            tree_preds = np.array([tree.predict(X_trans)[0] for tree in rf.estimators_], dtype=float)
            pred = float(tree_preds.mean())
            std = float(tree_preds.std())
            lower = max(0.0, pred - 1.96 * std)
            upper = pred + 1.96 * std
        else:
            pred = float(model.predict(raw)[0])
            lower = pred
            upper = pred

        return pred, lower, upper

    # Case 2: Plain sklearn model saved directly
    X = _build_encoded_cost_input(carrier, facility, weight, miles)

    if hasattr(model, "estimators_") and len(model.estimators_) > 0:
        try:
            tree_preds = np.array([tree.predict(X)[0] for tree in model.estimators_], dtype=float)
            pred = float(tree_preds.mean())
            std = float(tree_preds.std())
            lower = max(0.0, pred - 1.96 * std)
            upper = pred + 1.96 * std
            return pred, lower, upper
        except Exception:
            pass

    pred = float(model.predict(X)[0])
    return pred, pred, pred


def _get_feature_importance(model):
    model = _unwrap_model(model)

    # Pipeline model
    if _is_pipeline_model(model):
        rf = model.named_steps["rf"]
        pre = model.named_steps["pre"]
        enc = pre.named_transformers_["cat"]
        cat_names = list(enc.get_feature_names_out(["carrier", "facility"]))
        all_names = cat_names + ["weight_lbs", "miles"]

        if hasattr(rf, "feature_importances_"):
            return all_names, rf.feature_importances_

        return None, None

    # Plain model
    if hasattr(model, "feature_importances_"):
        feature_cols = _load_feature_columns()
        if feature_cols and len(feature_cols) == len(model.feature_importances_):
            return feature_cols, model.feature_importances_

        fallback_names = [f"Feature {i+1}" for i in range(len(model.feature_importances_))]
        return fallback_names, model.feature_importances_

    return None, None


def _format_feature_name(name: str) -> str:
    return (
        str(name)
        .replace("carrier_", "Carrier: ")
        .replace("facility_", "Facility: ")
        .replace("weight_lbs", "Weight (lbs)")
        .replace("miles", "Miles")
    )


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Cost & Risk Estimator")
st.caption("Predict total shipment cost and accessorial risk using machine learning.")
st.divider()

# ── Input form ────────────────────────────────────────────────────────────────
form_col, result_col = st.columns([2, 3], gap="large")

with form_col:
    with st.container(border=True):
        st.markdown("#### Shipment Details")

        carriers_list = sorted(df["carrier"].dropna().unique())
        facilities_list = sorted(df["facility"].dropna().unique())
        appt_types_list = sorted(df["AppointmentType"].dropna().unique())

        carrier = st.selectbox("Carrier", carriers_list)
        facility = st.selectbox("Facility", facilities_list)
        appt = st.selectbox("Appointment Type", appt_types_list)

        weight = st.number_input(
            "Weight (lbs)",
            min_value=100,
            max_value=44_000,
            value=10_000,
            step=500,
        )

        miles = st.number_input(
            "Miles",
            min_value=50,
            max_value=2_400,
            value=500,
            step=50,
        )

        estimate_clicked = st.button(
            "Estimate Cost & Risk →",
            type="primary",
            width="stretch",
        )

    with st.expander("ℹ️ Model Info", expanded=False):
        metadata = _load_model_metadata()
        model_type = metadata.get("model_type", type(_unwrap_model(cost_model)).__name__)

        st.markdown(
            f"""
**Cost model:** {model_type}  
**Risk model:** LightGBM Classifier  
**Training samples:** {len(df):,}  
**Cost features:** Carrier, Facility, Weight, Miles  
**Risk features:** Carrier, Facility, Appointment Type, Weight, Miles  
**Risk target:** Accessorial risk score (0 – 1)
            """
        )

# ── Run predictions ───────────────────────────────────────────────────────────
with result_col:
    avg_cpm = float(df["cost_per_mile"].mean()) if "cost_per_mile" in df.columns else 0.0
    avg_total = float(df["total_cost_usd"].mean()) if "total_cost_usd" in df.columns else 0.0

    if estimate_clicked:
        pred, lower, upper = _predict_cost_with_interval(
            cost_model, carrier, facility, weight, miles
        )

        risk = None
        if risk_model is not None:
            risk = predict_risk(risk_model, carrier, facility, appt, weight, miles, df)

        st.session_state["last_estimate"] = {
            "pred": pred,
            "lower": lower,
            "upper": upper,
            "simple_est": avg_cpm * miles,
            "avg_total": avg_total,
            "carrier": carrier,
            "facility": facility,
            "appt": appt,
            "weight": weight,
            "miles": miles,
            "risk": risk,
        }

    if "last_estimate" in st.session_state:
        e = st.session_state["last_estimate"]
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
                    gauge_fig = go.Figure(
                        go.Indicator(
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
                                "bar": {"color": risk["color"], "thickness": 0.28},
                                "bgcolor": "#0f0a1e",
                                "borderwidth": 0,
                                "steps": [
                                    {"range": [0, 34], "color": "rgba(5,150,105,0.15)"},
                                    {"range": [34, 67], "color": "rgba(217,119,6,0.15)"},
                                    {"range": [67, 100], "color": "rgba(220,38,38,0.15)"},
                                ],
                                "threshold": {
                                    "line": {"color": risk["color"], "width": 3},
                                    "thickness": 0.8,
                                    "value": risk["score"] * 100,
                                },
                            },
                        )
                    )

                    gauge_fig.update_layout(
                        height=220,
                        margin=dict(l=20, r=20, t=40, b=10),
                        paper_bgcolor="#0f0a1e",
                        font={"color": "#A78BFA"},
                    )
                    st.plotly_chart(gauge_fig, width="stretch")

                with factors_col:
                    st.markdown(
                        "<p style='color:#94A3B8;font-size:12px;margin:0 0 10px;'>"
                        "Key risk drivers</p>",
                        unsafe_allow_html=True,
                    )

                    sev_colors = {
                        "high": ("#F87171", "rgba(220,38,38,0.12)"),
                        "low": ("#34D399", "rgba(5,150,105,0.12)"),
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
                st.metric("ML Prediction", f"${pred:,.2f}")
            with c2:
                st.metric(
                    "Avg Cost/Mile Est.",
                    f"${simple_est:,.2f}",
                    delta=f"${pred - simple_est:+,.2f} vs ML",
                    delta_color="inverse",
                )
            with c3:
                st.metric(
                    "Fleet Avg Total",
                    f"${avg_total:,.2f}",
                    delta=f"${pred - avg_total:+,.2f} vs ML",
                    delta_color="inverse",
                )

            st.markdown("<br>", unsafe_allow_html=True)

            comp_fig = go.Figure(
                go.Bar(
                    x=[
                        "ML Prediction",
                        f"Avg Cost/Mile\n(${avg_cpm:.2f}/mi × {e['miles']} mi)",
                        "Fleet Avg Total",
                    ],
                    y=[pred, simple_est, avg_total],
                    marker_color=["#9333EA", "#6D28D9", "#4C1D95"],
                    text=[f"${v:,.0f}" for v in [pred, simple_est, avg_total]],
                    textposition="outside",
                    textfont={"color": "#E2E8F0"},
                )
            )

            comp_fig.update_layout(
                margin=dict(l=0, r=0, t=8, b=0),
                height=220,
                plot_bgcolor="#0f0a1e",
                paper_bgcolor="#0f0a1e",
                font=dict(color="#A78BFA"),
                yaxis=dict(
                    tickprefix="$",
                    gridcolor="rgba(150,50,200,0.15)",
                    color="#94A3B8",
                    linecolor="rgba(150,50,200,0.2)",
                ),
                xaxis=dict(
                    gridcolor="rgba(150,50,200,0.15)",
                    color="#94A3B8",
                    linecolor="rgba(150,50,200,0.2)",
                ),
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

    feature_names, importances = _get_feature_importance(cost_model)

    if feature_names is None or importances is None:
        st.info("Feature importance is not available for the currently loaded cost model.")
    else:
        importance = pd.DataFrame({
            "Feature": [_format_feature_name(x) for x in feature_names],
            "Importance": importances,
        }).sort_values("Importance", ascending=True).tail(12)

        fi_fig = go.Figure(
            go.Bar(
                x=importance["Importance"],
                y=importance["Feature"],
                orientation="h",
                marker_color="#9333EA",
                text=importance["Importance"].apply(lambda v: f"{v:.1%}"),
                textposition="outside",
                textfont={"color": "#E2E8F0"},
            )
        )

        fi_fig.update_layout(
            margin=dict(l=0, r=60, t=8, b=0),
            height=340,
            plot_bgcolor="#0f0a1e",
            paper_bgcolor="#0f0a1e",
            font=dict(color="#A78BFA"),
            xaxis=dict(
                tickformat=".0%",
                gridcolor="rgba(150,50,200,0.15)",
                color="#94A3B8",
                linecolor="rgba(150,50,200,0.2)",
            ),
            yaxis=dict(
                gridcolor="rgba(150,50,200,0.15)",
                color="#94A3B8",
                linecolor="rgba(150,50,200,0.2)",
            ),
        )

        st.plotly_chart(fi_fig, width="stretch")

# ── Historical distribution ───────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### Historical Total Cost Distribution")
    st.caption("Where your estimate falls relative to all past shipments")

    if "total_cost_usd" not in df.columns:
        st.info("Historical total cost distribution is unavailable for the current dataset.")
    else:
        hist_fig = go.Figure()
        hist_fig.add_trace(
            go.Histogram(
                x=df["total_cost_usd"],
                nbinsx=30,
                marker_color="#2D1B4E",
                marker_line_color=NAVY_500,
                marker_line_width=1,
                name="Historical",
            )
        )

        if "last_estimate" in st.session_state:
            v = st.session_state["last_estimate"]["pred"]
            hist_fig.add_vline(
                x=v,
                line_width=2,
                line_dash="dash",
                line_color="#DC2626",
                annotation_text=f"Your estimate: ${v:,.0f}",
                annotation_position="top right",
                annotation_font_color="#DC2626",
            )

        hist_fig.update_layout(
            margin=dict(l=0, r=0, t=8, b=0),
            height=220,
            plot_bgcolor="#0f0a1e",
            paper_bgcolor="#0f0a1e",
            font=dict(color="#A78BFA"),
            xaxis=dict(
                tickprefix="$",
                gridcolor="rgba(150,50,200,0.15)",
                color="#94A3B8",
                linecolor="rgba(150,50,200,0.2)",
            ),
            yaxis=dict(
                gridcolor="rgba(150,50,200,0.15)",
                color="#94A3B8",
                linecolor="rgba(150,50,200,0.2)",
            ),
        )

        st.plotly_chart(hist_fig, width="stretch")