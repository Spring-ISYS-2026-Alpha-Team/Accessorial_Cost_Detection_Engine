# File: pages/4_Cost_Estimate.py



import os

import sys

import numpy as np

import pandas as pd

import plotly.graph_objects as go

import streamlit as st



sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



from auth_utils import require_auth

from utils.styling import inject_css, top_nav

from utils.database import get_connection, get_shipments

from utils.cost_model import get_cost_model



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





def _safe_float(value, default=0.0):

    try:

        if value is None or (isinstance(value, float) and np.isnan(value)):

            return default

        return float(value)

    except Exception:

        return default





def _compute_data_hash(df: pd.DataFrame) -> int:

    """

    Stable-ish hash for Streamlit cache key.

    """

    if df.empty:

        return 0

    cols = ["carrier", "facility", "weight_lbs", "miles", "total_cost_usd"]

    base = df[cols].copy()

    for col in base.columns:

        base[col] = base[col].astype(str)

    return int(pd.util.hash_pandas_object(base, index=True).sum())





def _get_tree_interval(model, X_pred: pd.DataFrame):

    """

    Compute mean + approximate 95% interval from individual RF trees.

    """

    try:

        pre = model.named_steps["pre"]

        rf = model.named_steps["rf"]

        X_t = pre.transform(X_pred)

        preds = np.array([tree.predict(X_t)[0] for tree in rf.estimators_], dtype=float)

        mean_pred = float(preds.mean())

        lower = float(np.percentile(preds, 2.5))

        upper = float(np.percentile(preds, 97.5))

        return mean_pred, lower, upper

    except Exception:

        pred = float(model.predict(X_pred)[0])

        return pred, pred, pred





def _get_feature_importance(model) -> pd.DataFrame:

    """

    Extract feature importances from the RF pipeline.

    """

    try:

        pre = model.named_steps["pre"]

        rf = model.named_steps["rf"]

        feature_names = pre.get_feature_names_out()

        importances = rf.feature_importances_



        fi = pd.DataFrame(

            {

                "feature": feature_names,

                "importance": importances,

            }

        ).sort_values("importance", ascending=False)



        fi["feature"] = (

            fi["feature"]

            .str.replace("cat__", "", regex=False)

            .str.replace("num__", "", regex=False)

        )

        return fi

    except Exception:

        return pd.DataFrame(columns=["feature", "importance"])





def _get_history_subset(df: pd.DataFrame, carrier: str, facility: str) -> pd.DataFrame:

    """

    Prefer exact carrier+facility match; otherwise fall back to carrier; otherwise whole df.

    """

    exact = df[(df["carrier"] == carrier) & (df["facility"] == facility)].copy()

    if len(exact) >= 5:

        return exact



    carrier_only = df[df["carrier"] == carrier].copy()

    if len(carrier_only) >= 5:

        return carrier_only



    facility_only = df[df["facility"] == facility].copy()

    if len(facility_only) >= 5:

        return facility_only



    return df.copy()





# -------------------------------------------------------------------

# Load data + model

# -------------------------------------------------------------------

conn = get_connection()

shipments_df = get_shipments(conn)



st.markdown("## Cost Estimator")

st.caption(

    "Estimate total shipment cost using the Random Forest cost model trained on "

    "historical shipment data."

)

st.divider()



required_cols = ["carrier", "facility", "weight_lbs", "miles", "total_cost_usd"]

data_ready = (

    shipments_df is not None

    and not shipments_df.empty

    and all(col in shipments_df.columns for col in required_cols)

)



if not data_ready:

    st.error(

        "Cost model cannot run because shipment training data is unavailable. "

        "Make sure the database is connected and `get_shipments()` returns valid rows."

    )

    st.stop()



model_df = shipments_df[required_cols].copy()

model_df["carrier"] = model_df["carrier"].fillna("UNKNOWN").astype(str).str.strip()

model_df["facility"] = model_df["facility"].fillna("UNKNOWN").astype(str).str.strip()

model_df["weight_lbs"] = pd.to_numeric(model_df["weight_lbs"], errors="coerce").fillna(0.0)

model_df["miles"] = pd.to_numeric(model_df["miles"], errors="coerce").fillna(0.0)

model_df["total_cost_usd"] = pd.to_numeric(model_df["total_cost_usd"], errors="coerce").fillna(0.0)



model_df = model_df[

    (model_df["carrier"] != "")

    & (model_df["facility"] != "")

    & (model_df["weight_lbs"] >= 0)

    & (model_df["miles"] >= 0)

].copy()



if model_df.empty:

    st.error("No valid shipment rows are available to train the cost model.")

    st.stop()



data_hash = _compute_data_hash(model_df)

cost_model = get_cost_model(data_hash, model_df)



carrier_options = sorted(model_df["carrier"].dropna().astype(str).unique().tolist())

facility_options = sorted(model_df["facility"].dropna().astype(str).unique().tolist())



# -------------------------------------------------------------------

# UI Layout

# -------------------------------------------------------------------

form_col, result_col = st.columns([2, 3], gap="large")



with form_col:

    with st.container(border=True):

        st.markdown("#### Shipment Inputs")



        default_carrier = carrier_options.index(carrier_options[0]) if carrier_options else 0

        default_facility = facility_options.index(facility_options[0]) if facility_options else 0



        carrier = st.selectbox(

            "Carrier",

            carrier_options,

            index=default_carrier if carrier_options else None,

            help="Carrier is a direct model input feature.",

        )



        facility = st.selectbox(

            "Facility",

            facility_options,

            index=default_facility if facility_options else None,

            help="Facility is a direct model input feature.",

        )



        weight_lbs = st.number_input(

            "Weight (lbs)",

            min_value=0.0,

            max_value=200000.0,

            value=42000.0,

            step=500.0,

        )



        miles = st.number_input(

            "Miles",

            min_value=0.0,

            max_value=5000.0,

            value=850.0,

            step=25.0,

        )



        estimate_clicked = st.button(

            "Estimate Total Shipment Cost →",

            type="primary",

            use_container_width=True,

        )



        with st.expander("ℹ️ Model Info", expanded=False):

            st.markdown(

                f"""

**Model:** Random Forest Regressor  

**Target:** `total_cost_usd`  

**Input features:** `carrier`, `facility`, `weight_lbs`, `miles`  

**Training rows:** {len(model_df):,}  

**Unique carriers:** {model_df['carrier'].nunique():,}  

**Unique facilities:** {model_df['facility'].nunique():,}

"""

            )



# -------------------------------------------------------------------

# Run cost prediction

# -------------------------------------------------------------------

if estimate_clicked:

    X_pred = pd.DataFrame(

        [

            {

                "carrier": carrier,

                "facility": facility,

                "weight_lbs": float(weight_lbs),

                "miles": float(miles),

            }

        ]

    )



    try:

        pred_cost, ci_low, ci_high = _get_tree_interval(cost_model, X_pred)



        est_cpm = pred_cost / miles if miles > 0 else 0.0



        hist_subset = _get_history_subset(model_df, carrier, facility)

        hist_avg_cost = float(hist_subset["total_cost_usd"].mean()) if not hist_subset.empty else 0.0

        hist_avg_cpm = (

            float((hist_subset["total_cost_usd"] / hist_subset["miles"].replace(0, np.nan)).mean())

            if not hist_subset.empty

            else 0.0

        )

        fleet_avg_cpm = float(

            (model_df["total_cost_usd"] / model_df["miles"].replace(0, np.nan)).mean()

        )



        st.session_state["ce_cost_result"] = {

            "carrier": carrier,

            "facility": facility,

            "weight_lbs": float(weight_lbs),

            "miles": float(miles),

            "pred_cost": pred_cost,

            "ci_low": ci_low,

            "ci_high": ci_high,

            "est_cpm": est_cpm,

            "hist_avg_cost": hist_avg_cost,

            "hist_avg_cpm": hist_avg_cpm,

            "fleet_avg_cpm": fleet_avg_cpm,

            "history_rows": len(hist_subset),

            "history_df": hist_subset,

            "feature_importance": _get_feature_importance(cost_model),

        }

    except Exception as e:

        st.error(f"Cost prediction failed: {e}")



# -------------------------------------------------------------------

# Results

# -------------------------------------------------------------------

with result_col:

    if "ce_cost_result" not in st.session_state:

        with st.container(border=True):

            st.markdown(

                "<div style='text-align:center;padding:100px 20px;color:#9CA3AF;'>"

                "<div style='font-size:48px;'>💰</div>"

                "<div style='font-size:15px;font-weight:600;margin-top:16px;color:#E2E8F0;'>"

                "Enter shipment inputs to estimate cost</div>"

                "<div style='font-size:13px;margin-top:8px;'>"

                "This page now uses the Random Forest cost model trained on historical shipments."

                "</div></div>",

                unsafe_allow_html=True,

            )

    else:

        r = st.session_state["ce_cost_result"]



        pred_cost = _safe_float(r["pred_cost"])

        ci_low = _safe_float(r["ci_low"])

        ci_high = _safe_float(r["ci_high"])

        est_cpm = _safe_float(r["est_cpm"])

        hist_avg_cost = _safe_float(r["hist_avg_cost"])

        hist_avg_cpm = _safe_float(r["hist_avg_cpm"])

        fleet_avg_cpm = _safe_float(r["fleet_avg_cpm"])

        history_rows = int(r["history_rows"])

        history_df = r["history_df"]

        feature_importance = r["feature_importance"]



        with st.container(border=True):

            st.markdown("#### Estimated Total Shipment Cost")



            m1, m2, m3 = st.columns(3)

            m1.metric("Predicted Total Cost", f"${pred_cost:,.2f}")

            m2.metric("Estimated Cost / Mile", f"${est_cpm:,.2f}")

            m3.metric("Historical Rows Used", f"{history_rows:,}")



            st.markdown("<br>", unsafe_allow_html=True)



            ci_fig = go.Figure(

                go.Indicator(

                    mode="number+delta",

                    value=pred_cost,

                    number={"prefix": "$", "valueformat": ",.2f"},

                    delta={

                        "reference": hist_avg_cost if hist_avg_cost > 0 else pred_cost,

                        "relative": False,

                        "valueformat": ",.2f",

                    },

                    title={"text": f"<b>95% Interval: ${ci_low:,.2f} — ${ci_high:,.2f}</b>"},

                )

            )

            ci_fig.update_layout(

                height=180,

                margin=dict(l=20, r=20, t=40, b=10),

                paper_bgcolor="#0f0a1e",

                font={"color": "#E2E8F0"},

            )

            st.plotly_chart(ci_fig, use_container_width=True)



        st.markdown("<br>", unsafe_allow_html=True)



        with st.container(border=True):

            st.markdown("#### Benchmark Comparison")



            b1, b2, b3 = st.columns(3)

            b1.metric("Historical Avg Cost", f"${hist_avg_cost:,.2f}")

            b2.metric("Historical Avg Cost / Mile", f"${hist_avg_cpm:,.2f}")

            b3.metric("Fleet Avg Cost / Mile", f"${fleet_avg_cpm:,.2f}")



        st.markdown("<br>", unsafe_allow_html=True)



        with st.container(border=True):

            st.markdown("#### Historical Cost Distribution")



            hist_plot_df = history_df.copy()

            hist_plot_df = hist_plot_df[np.isfinite(hist_plot_df["total_cost_usd"])]



            if hist_plot_df.empty:

                st.info("No historical shipment distribution available for this selection.")

            else:

                hist_fig = go.Figure()

                hist_fig.add_histogram(

                    x=hist_plot_df["total_cost_usd"],

                    nbinsx=25,

                    name="Historical Shipments",

                    opacity=0.8,

                )

                hist_fig.add_vline(

                    x=pred_cost,

                    line_width=3,

                    annotation_text=f"Prediction: ${pred_cost:,.0f}",

                    annotation_position="top",

                )

                hist_fig.update_layout(

                    height=300,

                    margin=dict(l=10, r=10, t=20, b=10),

                    paper_bgcolor="#0f0a1e",

                    plot_bgcolor="#0f0a1e",

                    font={"color": "#E2E8F0"},

                    xaxis_title="Total Cost (USD)",

                    yaxis_title="Count",

                )

                st.plotly_chart(hist_fig, use_container_width=True)



        st.markdown("<br>", unsafe_allow_html=True)



        with st.container(border=True):

            st.markdown("#### Feature Importance")



            if feature_importance.empty:

                st.info("Feature importance is not available.")

            else:

                top_fi = feature_importance.head(12).sort_values("importance", ascending=True)



                fi_fig = go.Figure(

                    go.Bar(

                        x=top_fi["importance"],

                        y=top_fi["feature"],

                        orientation="h",

                        text=[f"{v:.3f}" for v in top_fi["importance"]],

                        textposition="outside",

                    )

                )

                fi_fig.update_layout(

                    height=380,

                    margin=dict(l=10, r=70, t=10, b=10),

                    paper_bgcolor="#0f0a1e",

                    plot_bgcolor="#0f0a1e",

                    font={"color": "#E2E8F0"},

                    xaxis_title="Importance",

                    yaxis_title="Feature",

                )

                st.plotly_chart(fi_fig, use_container_width=True)