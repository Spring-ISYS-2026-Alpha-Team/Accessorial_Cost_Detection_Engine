"""
utils/risk_model.py
LightGBM risk score predictor — pre-warmed on the loading screen.
Predicts accessorial risk (0–1) from carrier, facility, route, and load features.
"""
import streamlit as st
import pandas as pd
import numpy as np

_CAT_COLS = ["carrier", "facility", "AppointmentType"]
_NUM_COLS = ["weight_lbs", "miles"]
_ALL_COLS  = _CAT_COLS + _NUM_COLS


def score_to_tier(score: float) -> str:
    if score >= 0.67:
        return "High"
    if score >= 0.34:
        return "Medium"
    return "Low"


@st.cache_resource(show_spinner=False)
def get_risk_model(data_hash: int, _df: pd.DataFrame):
    """
    Train (or return cached) LightGBM risk score regressor.
    Returns (pipeline, col_list) or (None, []) if data is insufficient.
    _df uses underscore prefix so Streamlit skips hashing it;
    data_hash is the cache key.
    """
    try:
        from lightgbm import LGBMRegressor
        from sklearn.compose import ColumnTransformer
        from sklearn.preprocessing import OrdinalEncoder
        from sklearn.pipeline import Pipeline
    except ImportError:
        return None, []

    df = _df.copy()
    if "AppointmentType" not in df.columns:
        df["AppointmentType"] = "Drop"
    df["AppointmentType"] = df["AppointmentType"].fillna("Drop")

    needed = _ALL_COLS + ["risk_score"]
    df = df[needed].dropna()
    if len(df) < 20:
        return None, []

    X = df[_ALL_COLS]
    y = df["risk_score"].clip(0, 1)

    preprocessor = ColumnTransformer([
        ("cat", OrdinalEncoder(
            handle_unknown="use_encoded_value", unknown_value=-1
        ), _CAT_COLS),
        ("num", "passthrough", _NUM_COLS),
    ])

    model = Pipeline([
        ("pre", preprocessor),
        ("lgbm", LGBMRegressor(
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_samples=5,
            random_state=42,
            n_jobs=-1,
            verbose=-1,
        )),
    ])
    model.fit(X, y)
    return model, _ALL_COLS


def predict_risk(
    model,
    carrier: str,
    facility: str,
    appt_type: str,
    weight: float,
    miles: float,
    df_ref: pd.DataFrame,
) -> dict | None:
    """
    Predict risk score and return a plain-English explanation.

    Returns a dict with:
        score   — float 0–1
        tier    — "Low" | "Medium" | "High"
        color   — hex color matching tier
        factors — list of (label, detail, severity) tuples, up to 3
    Returns None if the model is unavailable.
    """
    if model is None:
        return None

    X = pd.DataFrame([{
        "carrier":         carrier,
        "facility":        facility,
        "AppointmentType": appt_type,
        "weight_lbs":      weight,
        "miles":           miles,
    }])

    score = float(np.clip(model.predict(X)[0], 0.02, 0.97))
    tier  = score_to_tier(score)

    color_map = {"Low": "#34D399", "Medium": "#FCD34D", "High": "#F87171"}
    color = color_map[tier]

    # ── Build explanation factors ────────────────────────────────────────────
    factors = []

    fleet_avg = df_ref["risk_score"].mean() if "risk_score" in df_ref.columns else 0.45

    # Carrier risk vs fleet
    if "risk_score" in df_ref.columns and "carrier" in df_ref.columns:
        c_avg = df_ref.groupby("carrier")["risk_score"].mean().get(carrier)
        if c_avg is not None:
            if c_avg > fleet_avg * 1.15:
                factors.append((
                    "Carrier history",
                    f"{carrier} averages {c_avg:.0%} risk vs fleet avg {fleet_avg:.0%}",
                    "high",
                ))
            elif c_avg < fleet_avg * 0.85:
                factors.append((
                    "Carrier history",
                    f"{carrier} averages {c_avg:.0%} risk — below fleet avg {fleet_avg:.0%}",
                    "low",
                ))

    # Appointment type
    if appt_type == "Live":
        factors.append((
            "Live appointment",
            "Live unloads have significantly higher detention risk than drop trailers",
            "high",
        ))
    else:
        factors.append((
            "Drop trailer",
            "Drop trailers reduce on-site wait time and lower detention risk",
            "low",
        ))

    # Weight vs fleet avg
    avg_wt = df_ref["weight_lbs"].mean() if "weight_lbs" in df_ref.columns else 15_000
    if weight > avg_wt * 1.35:
        factors.append((
            "Heavy load",
            f"{weight:,.0f} lbs is well above the fleet avg of {avg_wt:,.0f} lbs",
            "high",
        ))
    elif weight < avg_wt * 0.55:
        factors.append((
            "Light load",
            f"{weight:,.0f} lbs is well below the fleet avg of {avg_wt:,.0f} lbs",
            "low",
        ))

    # Miles vs fleet avg
    avg_mi = df_ref["miles"].mean() if "miles" in df_ref.columns else 500
    if miles > avg_mi * 1.5:
        factors.append((
            "Long haul",
            f"{miles:,.0f} mi exceeds fleet avg of {avg_mi:,.0f} mi — more layover exposure",
            "high",
        ))
    elif miles < avg_mi * 0.4:
        factors.append((
            "Short haul",
            f"{miles:,.0f} mi is well below fleet avg of {avg_mi:,.0f} mi",
            "low",
        ))

    # Facility type
    if "risk_score" in df_ref.columns and "facility" in df_ref.columns:
        f_avg = df_ref.groupby("facility")["risk_score"].mean().get(facility)
        if f_avg is not None and f_avg > fleet_avg * 1.2:
            factors.append((
                "Facility type",
                f"{facility} facilities average {f_avg:.0%} risk — above fleet avg",
                "high",
            ))

    # Fallback if nothing triggered
    if not factors:
        factors.append((
            "Balanced profile",
            "Carrier, route, and load are all near fleet averages",
            "neutral",
        ))

    return {
        "score":   score,
        "tier":    tier,
        "color":   color,
        "factors": factors[:3],
    }
