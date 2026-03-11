"""
utils/risk_model.py
PACE accessorial risk model — LightGBM binary classifier.

Target variable: had_accessorial (1 = shipment incurred any accessorial charge)
Output:          risk_score (0–1 probability), risk_tier (Low/Medium/High)

Feature set (all available without map data):
  Categorical : carrier, facility, appointment_type, origin_state, dest_state
  Numeric     : weight_lbs, miles, day_of_week, month, avg_dwell_hrs

Persistence:
  The trained model is saved to utils/pace_risk_model.joblib so it survives
  app restarts and can be retrained on demand from new data.

Adaptability:
  Call retrain(df) whenever new shipment data arrives — the model will
  update itself and save the new version to disk automatically.
"""
import os
import hashlib

import joblib
import numpy as np
import pandas as pd
import streamlit as st

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "pace_risk_model.joblib")

# ── Feature definitions ───────────────────────────────────────────────────────
_CAT_COLS = ["carrier", "facility", "appointment_type", "origin_state", "dest_state"]
_NUM_COLS = ["weight_lbs", "miles", "day_of_week", "month", "avg_dwell_hrs"]
_ALL_COLS = _CAT_COLS + _NUM_COLS
_TARGET   = "had_accessorial"

# Columns that can be derived if missing (fallback logic)
_DERIVABLE = {"day_of_week", "month", "had_accessorial"}


# ── Tier thresholds ───────────────────────────────────────────────────────────
def score_to_tier(score: float) -> str:
    if score >= 0.67:
        return "High"
    if score >= 0.34:
        return "Medium"
    return "Low"


# ── Feature preparation ───────────────────────────────────────────────────────
def _prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize and fill feature columns. Derives missing columns where possible.
    Returns a copy with all _ALL_COLS present.
    """
    df = df.copy()

    # Derive temporal features from ship_date if missing
    if "day_of_week" not in df.columns and "ship_date" in df.columns:
        df["day_of_week"] = pd.to_datetime(df["ship_date"], errors="coerce").dt.dayofweek
    if "month" not in df.columns and "ship_date" in df.columns:
        df["month"] = pd.to_datetime(df["ship_date"], errors="coerce").dt.month

    # Derive had_accessorial from accessorial_charge_usd if missing
    if "had_accessorial" not in df.columns and "accessorial_charge_usd" in df.columns:
        df["had_accessorial"] = (df["accessorial_charge_usd"] > 0).astype(int)

    # Fill optional columns with sensible defaults if absent
    if "appointment_type" not in df.columns:
        df["appointment_type"] = "Live"
    if "origin_state" not in df.columns:
        df["origin_state"] = "Unknown"
    if "dest_state" not in df.columns:
        df["dest_state"] = "Unknown"
    if "avg_dwell_hrs" not in df.columns:
        df["avg_dwell_hrs"] = 3.0   # fleet average fallback

    # Fill nulls
    for col in _CAT_COLS:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown").astype(str)
    for col in _NUM_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


# ── Model persistence ─────────────────────────────────────────────────────────
def save_model(model, metrics: dict):
    joblib.dump({"model": model, "metrics": metrics}, _MODEL_PATH)


def load_model_from_disk():
    """Returns (model, metrics) or (None, None) if no saved model exists."""
    if not os.path.exists(_MODEL_PATH):
        return None, None
    try:
        data = joblib.load(_MODEL_PATH)
        return data["model"], data["metrics"]
    except Exception:
        return None, None


# ── Training ──────────────────────────────────────────────────────────────────
def _train_model(df: pd.DataFrame):
    """
    Internal: train LightGBM classifier on df, return (pipeline, metrics).
    Requires LightGBM and scikit-learn.
    """
    from lightgbm import LGBMClassifier
    from sklearn.compose import ColumnTransformer
    from sklearn.metrics import roc_auc_score, f1_score, accuracy_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OrdinalEncoder

    df = _prepare_features(df)

    needed = _ALL_COLS + [_TARGET]
    df = df[[c for c in needed if c in df.columns]].dropna(subset=[_TARGET])

    if len(df) < 40:
        raise ValueError(
            f"Need at least 40 rows to train — only {len(df)} rows available."
        )

    X = df[_ALL_COLS]
    y = df[_TARGET].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    preprocessor = ColumnTransformer([
        ("cat", OrdinalEncoder(
            handle_unknown="use_encoded_value", unknown_value=-1
        ), _CAT_COLS),
        ("num", "passthrough", _NUM_COLS),
    ])

    model = Pipeline([
        ("pre", preprocessor),
        ("lgbm", LGBMClassifier(
            n_estimators=400,
            learning_rate=0.05,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_samples=10,
            class_weight="balanced",   # handles imbalanced had_accessorial
            random_state=42,
            n_jobs=-1,
            verbose=-1,
        )),
    ])
    model.fit(X_train, y_train)

    y_pred      = model.predict(X_test)
    y_prob      = model.predict_proba(X_test)[:, 1]

    metrics = {
        "auc":          round(float(roc_auc_score(y_test, y_prob)),  3),
        "f1":           round(float(f1_score(y_test, y_pred)),       3),
        "accuracy":     round(float(accuracy_score(y_test, y_pred)), 3),
        "n_train":      int(len(X_train)),
        "n_test":       int(len(X_test)),
        "pos_rate":     round(float(y.mean()), 3),
        "features":     _ALL_COLS,
    }

    return model, metrics


# ── Cached loader / trainer ───────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_risk_model(data_hash: int, _df: pd.DataFrame):
    """
    Returns (model, metrics).
    Load from disk if available, otherwise train fresh and save.
    data_hash is used as the Streamlit cache key.
    """
    model, metrics = load_model_from_disk()
    if model is not None:
        return model, metrics

    try:
        model, metrics = _train_model(_df)
        save_model(model, metrics)
        return model, metrics
    except Exception as e:
        return None, {"error": str(e)}


def retrain(df: pd.DataFrame) -> dict:
    """
    Retrain on new data, save to disk, clear Streamlit cache so the app
    picks up the new model on the next run.
    Returns metrics dict.
    """
    model, metrics = _train_model(df)
    save_model(model, metrics)
    # Clear cache so get_risk_model reloads from disk next call
    get_risk_model.clear()
    return metrics


def data_hash(df: pd.DataFrame) -> int:
    """Stable hash of a DataFrame for use as Streamlit cache key."""
    h = hashlib.md5(pd.util.hash_pandas_object(df, index=False).values).hexdigest()
    return int(h, 16) % (2 ** 31)


# ── Inference ─────────────────────────────────────────────────────────────────
def predict_risk(
    model,
    carrier: str,
    facility: str,
    appt_type: str,
    weight: float,
    miles: float,
    df_ref: pd.DataFrame,
    origin_state: str = "Unknown",
    dest_state: str = "Unknown",
    day_of_week: int | None = None,
    month: int | None = None,
    avg_dwell_hrs: float = 3.0,
) -> dict | None:
    """
    Predict accessorial risk for a single shipment.

    Returns dict with:
        score   — float 0–1 (probability of accessorial charge)
        tier    — "Low" | "Medium" | "High"
        color   — hex color matching tier
        factors — list of (label, detail, severity) tuples
    Returns None if model is unavailable.
    """
    if model is None:
        return None

    import datetime
    if day_of_week is None:
        day_of_week = datetime.date.today().weekday()
    if month is None:
        month = datetime.date.today().month

    X = pd.DataFrame([{
        "carrier":          carrier,
        "facility":         facility,
        "appointment_type": appt_type,
        "origin_state":     origin_state,
        "dest_state":       dest_state,
        "weight_lbs":       float(weight),
        "miles":            float(miles),
        "day_of_week":      int(day_of_week),
        "month":            int(month),
        "avg_dwell_hrs":    float(avg_dwell_hrs),
    }])

    try:
        score = float(np.clip(model.predict_proba(X)[0][1], 0.02, 0.97))
    except Exception:
        return None

    tier  = score_to_tier(score)
    color = {"Low": "#34D399", "Medium": "#FCD34D", "High": "#F87171"}[tier]

    # ── Explanation factors ───────────────────────────────────────────────────
    factors = []
    fleet_avg = df_ref["risk_score"].mean() if "risk_score" in df_ref.columns else 0.45

    # Carrier risk vs fleet
    if "risk_score" in df_ref.columns and "carrier" in df_ref.columns:
        c_avg = df_ref.groupby("carrier")["risk_score"].mean().get(carrier)
        if c_avg is not None:
            if c_avg > fleet_avg * 1.15:
                factors.append(("Carrier history",
                    f"{carrier} averages {c_avg:.0%} risk vs fleet avg {fleet_avg:.0%}", "high"))
            elif c_avg < fleet_avg * 0.85:
                factors.append(("Carrier history",
                    f"{carrier} averages {c_avg:.0%} risk — below fleet avg {fleet_avg:.0%}", "low"))

    # Appointment type
    if appt_type == "Live":
        factors.append(("Live appointment",
            "Live unloads have significantly higher detention risk than drop trailers", "high"))
    else:
        factors.append(("Drop trailer",
            "Drop trailers reduce on-site wait time and lower detention risk", "low"))

    # Weight
    avg_wt = df_ref["weight_lbs"].mean() if "weight_lbs" in df_ref.columns else 20_000
    if weight > avg_wt * 1.35:
        factors.append(("Heavy load",
            f"{weight:,.0f} lbs is well above fleet avg of {avg_wt:,.0f} lbs", "high"))
    elif weight < avg_wt * 0.55:
        factors.append(("Light load",
            f"{weight:,.0f} lbs is well below fleet avg of {avg_wt:,.0f} lbs", "low"))

    # Miles
    avg_mi = df_ref["miles"].mean() if "miles" in df_ref.columns else 500
    if miles > avg_mi * 1.5:
        factors.append(("Long haul",
            f"{miles:,.0f} mi exceeds fleet avg of {avg_mi:,.0f} mi — more layover exposure", "high"))
    elif miles < avg_mi * 0.4:
        factors.append(("Short haul",
            f"{miles:,.0f} mi is well below fleet avg of {avg_mi:,.0f} mi", "low"))

    # Day of week
    if day_of_week == 4:
        factors.append(("Friday dispatch",
            "Friday shipments have 2× higher weekend detention risk", "high"))

    # Month / peak season
    if month in (10, 11, 12):
        factors.append(("Peak season (Q4)",
            "Oct–Dec capacity crunch raises accessorial incidence by 15–25%", "high"))

    # Facility
    if "risk_score" in df_ref.columns and "facility" in df_ref.columns:
        f_avg = df_ref.groupby("facility")["risk_score"].mean().get(facility)
        if f_avg is not None and f_avg > fleet_avg * 1.2:
            factors.append(("High-risk facility",
                f"{facility} averages {f_avg:.0%} risk — above fleet avg", "high"))

    if not factors:
        factors.append(("Balanced profile",
            "Carrier, route, and load are all near fleet averages", "neutral"))

    return {"score": score, "tier": tier, "color": color, "factors": factors[:3]}
