"""
PACE ML Pipeline — Accessorial Risk Prediction (v3 — Complete)
================================================================
Connects to Azure SQL, extracts shipment data, trains a Random Forest
classifier to predict AccessorialFlag, evaluates model performance,
saves the trained model to disk, generates risk score predictions,
saves visualizations, and writes predictions back to the Shipments table.

Also includes a standalone inference function (predict_single_shipment)
that loads the saved model and scores a new shipment without retraining.

Three Pipelines Covered:
  1. DATA PIPELINE:     extract_data() + transform_data()
  2. ML PIPELINE:       train_model() + evaluate_model() + save_model()
  3. INFERENCE PIPELINE: generate_predictions() + predict_single_shipment()

Usage:
    # Full pipeline (train + predict all):
    python scripts/ml_pipeline.py

    # Score a single new shipment (after model is saved):
    python scripts/ml_pipeline.py --predict

Requirements:
    pip install -r scripts/requirements_pipeline.txt
"""

import os
import sys
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyodbc
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split, cross_val_score
from datetime import datetime

# ---------------------------------------------------------------------------
# Database credentials
# ---------------------------------------------------------------------------
DB_SERVER = "essql1.database.windows.net"
DB_NAME = "ISYS43603_Spring2026_Sec02_Alice_db"
DB_USERNAME = "Alice"
DB_PASSWORD = "ISYSPass12345678!"
DB_DRIVER = "ODBC Driver 18 for SQL Server"

# ---------------------------------------------------------------------------
# File paths for saved model artifacts
# ---------------------------------------------------------------------------
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "rf_accessorial_model.joblib")
FEATURES_PATH = os.path.join(MODEL_DIR, "feature_columns.json")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")

# ---------------------------------------------------------------------------
# SQL query — LEFT JOIN on both Carriers and Facilities
# ---------------------------------------------------------------------------
EXTRACT_QUERY = """
SELECT
    s.ShipmentId, s.ShipDate, s.OriginRegion, s.DestRegion,
    s.CarrierId, s.FacilityType, s.AppointmentType,
    s.DistanceMiles, s.weight_lbs, s.Revenue, s.LinehaulCost,
    s.AccessorialFlag, s.AccessorialCost, s.risk_score, s.risk_tier,
    c.carrier_name, c.safety_rating, c.fleet_size,
    f.facility_name, f.facility_type AS fac_type,
    f.avg_dwell_time_hrs, f.appointment_required,
    DATEPART(WEEKDAY, s.ShipDate) AS day_of_week,
    DATEPART(HOUR, s.ShipDate) AS hour_of_day
FROM Shipments s
LEFT JOIN Carriers c ON s.CarrierId = c.carrier_id
LEFT JOIN Facilities f ON s.facility_id = f.facility_id
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FACILITY_TYPES = [
    "Warehouse", "Cross-Dock", "Cold Storage",
    "Distribution Center", "Shipper", "Receiver",
]

TARGET = "AccessorialFlag"


# ============================================================================
# DATA PIPELINE
# ============================================================================

def get_connection():
    """Open and return a pyodbc connection to Azure SQL."""
    connection_string = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USERNAME};"
        f"PWD={DB_PASSWORD};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    print("[1/8] Connecting to Azure SQL...")
    conn = pyodbc.connect(connection_string)
    print("      Connected successfully.")
    return conn


def extract_data(conn):
    """
    DATA PIPELINE — Step 1: Extract
    Run the extraction query and return a raw DataFrame.
    Pulls from Shipments joined with Carriers and Facilities.
    """
    print("[2/8] Extracting data from database...")
    df = pd.read_sql(EXTRACT_QUERY, conn)
    print(f"      Extracted {len(df):,} rows, {df.shape[1]} columns.")

    # Show class balance
    flag_counts = df[TARGET].value_counts()
    total = len(df)
    n_zero = int(flag_counts.get(False, flag_counts.get(0, 0)))
    n_one = int(flag_counts.get(True, flag_counts.get(1, 0)))
    print(f"      Class balance:")
    print(f"        No accessorial (0): {n_zero:,} ({n_zero/total:.1%})")
    print(f"        Accessorial (1):    {n_one:,} ({n_one/total:.1%})")
    return df


def transform_data(df):
    """
    DATA PIPELINE — Step 2: Transform
    Clean nulls, encode categoricals, engineer features.
    Returns (transformed_df, feature_columns).
    """
    print("[3/8] Transforming data...")

    # --- Fill nulls ---
    df["weight_lbs"] = df["weight_lbs"].fillna(df["weight_lbs"].median())
    df["avg_dwell_time_hrs"] = df["avg_dwell_time_hrs"].fillna(0)
    df["fleet_size"] = df["fleet_size"].fillna(df["fleet_size"].median())
    df["DistanceMiles"] = df["DistanceMiles"].fillna(0)
    df["Revenue"] = df["Revenue"].fillna(0)
    df["LinehaulCost"] = df["LinehaulCost"].fillna(0)
    df["day_of_week"] = df["day_of_week"].fillna(4)
    df["hour_of_day"] = df["hour_of_day"].fillna(12)

    # --- Encode categorical columns ---
    df["appt_encoded"] = df["AppointmentType"].map(
        {"Live": 1, "Drop": 0}
    ).fillna(0).astype(int)

    df["safety_encoded"] = df["safety_rating"].map({
        "Satisfactory": 0, "Conditional": 1, "None": 2, "Unsatisfactory": 3
    }).fillna(2).astype(int)

    df["appt_required_encoded"] = df["appointment_required"].map(
        {"Yes": 1, "No": 0}
    ).fillna(0).astype(int)

    # --- One-hot encode FacilityType ---
    facility_dummies = pd.get_dummies(df["FacilityType"], prefix="fac")
    facility_cols = []
    for ftype in FACILITY_TYPES:
        col = f"fac_{ftype}"
        if col not in facility_dummies.columns:
            facility_dummies[col] = 0
        facility_cols.append(col)
    df = pd.concat([df, facility_dummies[facility_cols]], axis=1)

    # --- Engineered features ---
    safe_revenue = df["Revenue"].replace(0, float("nan"))
    df["cost_ratio"] = (df["LinehaulCost"] / safe_revenue).fillna(0)

    safe_miles = df["DistanceMiles"].replace(0, float("nan"))
    df["revenue_per_mile"] = (df["Revenue"] / safe_miles).fillna(0)
    df["cost_per_mile"] = (df["LinehaulCost"] / safe_miles).fillna(0)
    df["weight_per_mile"] = (df["weight_lbs"] / safe_miles).fillna(0)

    df["is_weekend"] = df["day_of_week"].isin([1, 7]).astype(int)
    df["is_afternoon"] = (df["hour_of_day"] >= 13).astype(int)
    df["high_dwell"] = (df["avg_dwell_time_hrs"] >= 4.0).astype(int)

    # --- Define final feature columns ---
    base_features = [
        "DistanceMiles", "weight_lbs", "LinehaulCost", "Revenue",
        "day_of_week", "hour_of_day",
        "appt_encoded", "safety_encoded", "fleet_size",
        "avg_dwell_time_hrs", "appt_required_encoded",
    ]

    engineered_features = [
        "cost_ratio", "revenue_per_mile", "cost_per_mile",
        "weight_per_mile", "is_weekend", "is_afternoon", "high_dwell",
    ]

    feature_columns = base_features + engineered_features + facility_cols

    # Verify no duplicate columns
    assert len(feature_columns) == len(set(feature_columns)), \
        f"Duplicate features: {[f for f in feature_columns if feature_columns.count(f) > 1]}"

    print(f"      Feature set: {len(feature_columns)} columns")
    print(f"        Base:        {len(base_features)}")
    print(f"        Engineered:  {len(engineered_features)}")
    print(f"        Facility OH: {len(facility_cols)}")
    return df, feature_columns


# ============================================================================
# ML PIPELINE
# ============================================================================

def train_model(df, feature_columns):
    """
    ML PIPELINE — Step 1: Train
    Split data 80/20, train Random Forest with balanced class weights.
    """
    print("[4/8] Training Random Forest model...")
    X = df[feature_columns].fillna(0)
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"      Train size: {len(X_train):,}  |  Test size: {len(X_test):,}")
    print(f"      Train class balance: "
          f"0={int((y_train == 0).sum()):,} / 1={int((y_train == 1).sum()):,}")

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced",
        max_depth=15,
        min_samples_leaf=10,
    )
    model.fit(X_train, y_train)
    print("      Model training complete.")

    # Cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="f1")
    print(f"      5-fold CV F1 score: {cv_scores.mean():.4f} "
          f"(±{cv_scores.std():.4f})")

    return model, X_train, X_test, y_train, y_test


def evaluate_model(model, X_test, y_test, feature_columns):
    """
    ML PIPELINE — Step 2: Evaluate
    Print accuracy, AUC-ROC, classification report, confusion matrix,
    and top-10 feature importances.
    """
    print("[5/8] Evaluating model...")
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)

    print(f"\n  Accuracy: {acc:.4f}")
    print(f"  AUC-ROC:  {auc:.4f}")
    print(f"\n  Classification Report:")
    print(classification_report(
        y_test, y_pred,
        target_names=["No Accessorial (0)", "Accessorial (1)"]
    ))

    cm = confusion_matrix(y_test, y_pred)
    print(f"  Confusion Matrix:")
    print(f"    True Negatives  (correct no-charge): {cm[0][0]:,}")
    print(f"    False Positives (false alarm):       {cm[0][1]:,}")
    print(f"    False Negatives (missed charge):     {cm[1][0]:,}")
    print(f"    True Positives  (caught charge):     {cm[1][1]:,}")

    # Feature importances
    importance_df = pd.DataFrame({
        "feature": feature_columns,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    print(f"\n  Top 10 Feature Importances:")
    for _, row in importance_df.head(10).iterrows():
        bar = "#" * int(row["importance"] * 80)
        print(f"    {row['feature']:<25} {row['importance']:.4f}  {bar}")

    return importance_df, acc, auc


def save_model(model, feature_columns, accuracy, auc_roc):
    """
    ML PIPELINE — Step 3: Save
    Saves the trained model, feature column list, and metadata to disk
    so the model can be loaded later for inference without retraining.

    Saves to models/ directory:
      - rf_accessorial_model.joblib  (the trained model)
      - feature_columns.json         (ordered list of feature names)
      - model_metadata.json          (accuracy, AUC, timestamp, etc.)
    """
    print("[6/8] Saving model to disk...")
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Save the trained model
    joblib.dump(model, MODEL_PATH)
    print(f"      Saved model: {MODEL_PATH}")

    # Save feature column names (needed to build input in correct order)
    with open(FEATURES_PATH, "w") as f:
        json.dump(feature_columns, f, indent=2)
    print(f"      Saved features: {FEATURES_PATH}")

    # Save metadata
    metadata = {
        "model_name": "RandomForest_v3",
        "n_estimators": model.n_estimators,
        "max_depth": model.max_depth,
        "class_weight": "balanced",
        "accuracy": round(accuracy, 4),
        "auc_roc": round(auc_roc, 4),
        "n_features": len(feature_columns),
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "trained_on_rows": model.n_features_in_,
    }
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"      Saved metadata: {METADATA_PATH}")
    print(f"      Model accuracy: {accuracy:.2%} | AUC-ROC: {auc_roc:.4f}")


# ============================================================================
# INFERENCE PIPELINE
# ============================================================================

def generate_predictions(model, df, feature_columns):
    """
    INFERENCE PIPELINE — Batch scoring
    Generate risk_score and risk_tier predictions for all rows in the
    DataFrame. Used during the full pipeline run.
    """
    print("[7/8] Generating predictions for all rows...")
    X_all = df[feature_columns].fillna(0)
    probas = model.predict_proba(X_all)
    risk_scores = probas[:, 1]

    tiers = pd.cut(
        risk_scores,
        bins=[0, 0.34, 0.67, 1.0],
        labels=["Low", "Medium", "High"],
        include_lowest=True,
    )

    predictions = pd.DataFrame({
        "ShipmentId": df["ShipmentId"].values,
        "ml_risk_score": risk_scores,
        "ml_risk_tier": tiers,
    })

    tier_counts = predictions["ml_risk_tier"].value_counts()
    print(f"      Predictions: {tier_counts.to_dict()}")
    return predictions


def predict_single_shipment(
    distance_miles,
    weight_lbs,
    linehaul_cost,
    revenue,
    appointment_type,      # "Live" or "Drop"
    facility_type,         # "Warehouse", "Cross-Dock", etc.
    safety_rating,         # "Satisfactory", "Conditional", "None", "Unsatisfactory"
    fleet_size,
    avg_dwell_time_hrs,
    appointment_required,  # "Yes" or "No"
    day_of_week=4,         # 1=Sunday, 7=Saturday (default Wednesday)
    hour_of_day=10,        # 0-23 (default 10 AM)
):
    """
    INFERENCE PIPELINE — Single shipment scoring
    Loads the saved model from disk, transforms one shipment's features,
    and returns a risk score + risk tier.

    This is what powers the live PACE application — a user enters shipment
    details and gets back a risk prediction without retraining the model.

    Parameters
    ----------
    distance_miles : float    Miles from origin to destination
    weight_lbs : int          Shipment weight in pounds
    linehaul_cost : float     Base freight cost in dollars
    revenue : float           Total revenue for the shipment
    appointment_type : str    "Live" or "Drop"
    facility_type : str       One of: Warehouse, Cross-Dock, Cold Storage,
                              Distribution Center, Shipper, Receiver
    safety_rating : str       Carrier safety rating
    fleet_size : int          Carrier fleet size (number of trucks)
    avg_dwell_time_hrs : float  Average facility dwell time in hours
    appointment_required : str  "Yes" or "No"
    day_of_week : int         1=Sunday through 7=Saturday
    hour_of_day : int         0-23 hour of shipment

    Returns
    -------
    dict with keys: risk_score (float), risk_tier (str), model_name (str)
    """
    # Load saved model and feature list
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"No saved model found at {MODEL_PATH}. "
            "Run the full pipeline first: python scripts/ml_pipeline.py"
        )

    model = joblib.load(MODEL_PATH)
    with open(FEATURES_PATH, "r") as f:
        feature_columns = json.load(f)
    with open(METADATA_PATH, "r") as f:
        metadata = json.load(f)

    # --- Apply same transformations as transform_data() ---
    appt_encoded = 1 if appointment_type == "Live" else 0

    safety_map = {"Satisfactory": 0, "Conditional": 1, "None": 2, "Unsatisfactory": 3}
    safety_encoded = safety_map.get(safety_rating, 2)

    appt_required_encoded = 1 if appointment_required == "Yes" else 0

    # Facility one-hot encoding
    facility_flags = {}
    for ftype in FACILITY_TYPES:
        facility_flags[f"fac_{ftype}"] = 1 if facility_type == ftype else 0

    # Engineered features
    safe_revenue = revenue if revenue > 0 else float("nan")
    safe_miles = distance_miles if distance_miles > 0 else float("nan")

    cost_ratio = (linehaul_cost / safe_revenue) if safe_revenue else 0
    revenue_per_mile = (revenue / safe_miles) if safe_miles else 0
    cost_per_mile = (linehaul_cost / safe_miles) if safe_miles else 0
    weight_per_mile = (weight_lbs / safe_miles) if safe_miles else 0
    is_weekend = 1 if day_of_week in [1, 7] else 0
    is_afternoon = 1 if hour_of_day >= 13 else 0
    high_dwell = 1 if avg_dwell_time_hrs >= 4.0 else 0

    # Build feature dict in the exact order the model expects
    feature_values = {
        "DistanceMiles": distance_miles,
        "weight_lbs": weight_lbs,
        "LinehaulCost": linehaul_cost,
        "Revenue": revenue,
        "day_of_week": day_of_week,
        "hour_of_day": hour_of_day,
        "appt_encoded": appt_encoded,
        "safety_encoded": safety_encoded,
        "fleet_size": fleet_size,
        "avg_dwell_time_hrs": avg_dwell_time_hrs,
        "appt_required_encoded": appt_required_encoded,
        "cost_ratio": cost_ratio,
        "revenue_per_mile": revenue_per_mile,
        "cost_per_mile": cost_per_mile,
        "weight_per_mile": weight_per_mile,
        "is_weekend": is_weekend,
        "is_afternoon": is_afternoon,
        "high_dwell": high_dwell,
    }
    feature_values.update(facility_flags)

    # Create single-row DataFrame in correct column order
    X = pd.DataFrame([feature_values])[feature_columns]

    # Predict
    risk_score = float(model.predict_proba(X)[0, 1])

    if risk_score < 0.34:
        risk_tier = "Low"
    elif risk_score <= 0.67:
        risk_tier = "Medium"
    else:
        risk_tier = "High"

    return {
        "risk_score": round(risk_score, 4),
        "risk_tier": risk_tier,
        "model_name": metadata.get("model_name", "Unknown"),
        "model_accuracy": metadata.get("accuracy", None),
        "model_auc_roc": metadata.get("auc_roc", None),
    }


# ============================================================================
# VISUALIZATIONS
# ============================================================================

def save_visualizations(importance_df, predictions):
    """Save feature importance and risk distribution charts."""
    os.makedirs("outputs", exist_ok=True)

    # --- Feature importance chart ---
    top10 = importance_df.head(10).sort_values("importance")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#2563EB" if imp > 0.05 else "#93C5FD"
              for imp in top10["importance"]]
    ax.barh(top10["feature"], top10["importance"], color=colors)
    ax.set_xlabel("Importance Score")
    ax.set_title("Top 10 Features — Random Forest Accessorial Risk Model")
    ax.axvline(x=0.05, color="#EF4444", linestyle="--", alpha=0.5,
               label="5% threshold")
    ax.legend()
    plt.tight_layout()
    fig.savefig("outputs/feature_importance.png", dpi=150)
    plt.close(fig)
    print("      Saved: outputs/feature_importance.png")

    # --- Risk score distribution histogram ---
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(predictions["ml_risk_score"], bins=50, color="#0F2B4A",
            edgecolor="white", alpha=0.85)
    ax.axvline(x=0.34, color="#10B981", linestyle="--", linewidth=2,
               label="Low/Medium (0.34)")
    ax.axvline(x=0.67, color="#F59E0B", linestyle="--", linewidth=2,
               label="Medium/High (0.67)")
    ax.set_xlabel("Predicted Risk Score")
    ax.set_ylabel("Number of Shipments")
    ax.set_title("Distribution of Predicted Accessorial Risk Scores")
    ax.legend()
    plt.tight_layout()
    fig.savefig("outputs/risk_distribution.png", dpi=150)
    plt.close(fig)
    print("      Saved: outputs/risk_distribution.png")


# ============================================================================
# EXPLANATION GENERATION
# ============================================================================

def generate_explanations(df, predictions, feature_columns):
    """
    INFERENCE PIPELINE — Generate human-readable risk explanations
    and recommended operational actions for each shipment.

    Uses rule-based logic driven by the actual feature values that the
    Random Forest found most predictive. No LLM needed — the patterns
    are deterministic and traceable back to real freight operations.

    Returns predictions DataFrame with two new columns:
      risk_reason         — plain-English explanation of top risk factors
      recommended_action  — suggested action for operations team
    """
    print("[7b/8] Generating risk explanations and recommendations...")

    reasons = []
    actions = []

    for idx, pred_row in predictions.iterrows():
        shipment_id = pred_row["ShipmentId"]
        tier        = str(pred_row["ml_risk_tier"])
        score       = float(pred_row["ml_risk_score"])

        # Look up the original shipment features
        match = df[df["ShipmentId"] == shipment_id]
        if match.empty:
            reasons.append("Insufficient data for explanation.")
            actions.append("Standard review recommended.")
            continue

        row = match.iloc[0]

        # ── Identify the top risk contributors ──────────────────────────────
        factors = []

        # Appointment type
        appt = str(row.get("AppointmentType", "")).strip()
        if appt == "Live":
            factors.append(("Live unload appointment — driver must wait at dock", 0.30))

        # Facility dwell time
        dwell = float(row.get("avg_dwell_time_hrs", 0) or 0)
        if dwell >= 5.0:
            factors.append((f"Facility avg dwell time is {dwell:.1f} hrs (very high)", 0.28))
        elif dwell >= 3.5:
            factors.append((f"Facility avg dwell time is {dwell:.1f} hrs (elevated)", 0.18))

        # Carrier safety
        safety = str(row.get("safety_rating", "") or row.get("safety_encoded", ""))
        if "Unsatisfactory" in safety or safety == "3":
            factors.append(("Carrier has Unsatisfactory safety rating", 0.25))
        elif "Conditional" in safety or safety == "1":
            factors.append(("Carrier has Conditional safety rating (at-risk)", 0.15))

        # Distance
        dist = float(row.get("DistanceMiles", 0) or 0)
        if dist > 1200:
            factors.append((f"Long-haul lane ({dist:.0f} mi) — layover risk elevated", 0.20))
        elif dist > 700:
            factors.append((f"Medium-long lane ({dist:.0f} mi) — potential overnight", 0.10))

        # Weight
        weight = float(row.get("weight_lbs", 0) or 0)
        if weight > 35000:
            factors.append((f"Heavy load ({weight:,.0f} lbs) — liftgate/lumper likely", 0.18))
        elif weight > 25000:
            factors.append((f"Above-average weight ({weight:,.0f} lbs)", 0.10))

        # Time of day
        hour = int(row.get("hour_of_day", 10) or 10)
        if hour >= 16:
            factors.append((f"Late dispatch ({hour}:00) — high overnight/weekend risk", 0.15))
        elif hour >= 14:
            factors.append((f"Afternoon dispatch ({hour}:00) — potential delay into evening", 0.08))

        # Fleet size (small carrier = less scheduling flexibility)
        fleet = float(row.get("fleet_size", 9999) or 9999)
        if fleet < 1000:
            factors.append((f"Small carrier fleet ({fleet:.0f} trucks) — limited scheduling buffer", 0.12))

        # Day of week
        dow = int(row.get("day_of_week", 3) or 3)
        if dow == 6:  # Saturday (1=Sun in SQL DATEPART, 6=Fri, 7=Sat)
            factors.append(("Weekend delivery — higher detention and delay risk", 0.15))
        elif dow == 5:  # Friday
            factors.append(("Friday dispatch — risk of weekend detention if delayed", 0.10))

        # Sort by weight and pick top 3
        factors.sort(key=lambda x: -x[1])
        top_factors = factors[:3] if factors else [("Standard shipment with no dominant risk flags", 0)]

        # ── Build reason string ──────────────────────────────────────────────
        if tier == "High":
            prefix = f"High risk score ({score:.2f}): "
        elif tier == "Medium":
            prefix = f"Moderate risk score ({score:.2f}): "
        else:
            prefix = f"Low risk score ({score:.2f}): "

        reason_parts = [f[0] for f in top_factors]
        reason = prefix + "; ".join(reason_parts) + "."
        reasons.append(reason[:500])  # cap at 500 chars for DB

        # ── Build recommended action ─────────────────────────────────────────
        if tier == "High":
            if appt == "Live" and dwell >= 4.0:
                action = (
                    "Request earliest available morning appointment window (before 10 AM). "
                    "Pre-confirm dock availability. Add detention buffer of $150-300 to freight budget."
                )
            elif dist > 1000 and appt == "Live":
                action = (
                    "Coordinate drop-and-hook if facility allows. If live required, "
                    "ensure driver departs by noon to avoid overnight layover ($250-450 charge)."
                )
            elif weight > 35000:
                action = (
                    "Confirm liftgate availability or lumper service at destination. "
                    "Pre-authorize driver assist. Budget $120-265 for unloading charges."
                )
            else:
                action = (
                    "Flag for proactive monitoring. Contact carrier day before for ETA confirmation. "
                    "Reserve $150-350 accessorial contingency in shipment budget."
                )
        elif tier == "Medium":
            if appt == "Live" and dwell >= 3.5:
                action = (
                    "Confirm appointment 24 hrs in advance. "
                    "Request dock availability update morning of delivery. "
                    "Reserve $75-150 contingency for potential detention."
                )
            else:
                action = (
                    "Standard monitoring. Verify carrier check-in protocol. "
                    "No immediate action required but watch for delays on day of delivery."
                )
        else:
            action = (
                "Low risk — standard operating procedure. "
                "No additional accessorial buffer required."
            )

        actions.append(action[:500])  # cap at 500 chars

    predictions = predictions.copy()
    predictions["risk_reason"]         = reasons
    predictions["recommended_action"]  = actions

    high_n   = (predictions["ml_risk_tier"].astype(str) == "High").sum()
    medium_n = (predictions["ml_risk_tier"].astype(str) == "Medium").sum()
    print(f"      Explanations generated: {len(predictions):,} total "
          f"({high_n} High, {medium_n} Medium, {len(predictions)-high_n-medium_n} Low)")
    return predictions


# ============================================================================
# WRITE-BACK
# ============================================================================

def _ensure_explanation_columns(conn):
    """
    Add risk_reason and recommended_action columns to the Shipments table
    if they don't already exist. Safe to run multiple times (no-op if present).
    """
    cursor = conn.cursor()
    for col, dtype in [("risk_reason", "NVARCHAR(500)"),
                       ("recommended_action", "NVARCHAR(500)")]:
        try:
            cursor.execute(f"""
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'Shipments' AND COLUMN_NAME = '{col}'
                )
                ALTER TABLE Shipments ADD {col} {dtype} NULL
            """)
            conn.commit()
        except Exception as e:
            print(f"      Warning: could not add column '{col}': {e}")
    cursor.close()
    print("      Schema check: risk_reason + recommended_action columns ready.")


def write_predictions_to_sql(conn, predictions):
    """
    UPDATE risk_score, risk_tier, risk_reason, and recommended_action
    on Shipments table in batches of 500.
    Falls back to updating only risk_score + risk_tier if the explanation
    columns don't exist in the schema yet.
    """
    print("[8/8] Writing predictions back to SQL...")

    has_explanation_cols = "risk_reason" in predictions.columns

    if has_explanation_cols:
        update_sql = """
            UPDATE Shipments
            SET risk_score = ?, risk_tier = ?,
                risk_reason = ?, recommended_action = ?
            WHERE ShipmentId = ?
        """
        records = list(zip(
            predictions["ml_risk_score"].round(4),
            predictions["ml_risk_tier"].astype(str),
            predictions["risk_reason"],
            predictions["recommended_action"],
            predictions["ShipmentId"],
        ))
    else:
        update_sql = """
            UPDATE Shipments
            SET risk_score = ?, risk_tier = ?
            WHERE ShipmentId = ?
        """
        records = list(zip(
            predictions["ml_risk_score"].round(4),
            predictions["ml_risk_tier"].astype(str),
            predictions["ShipmentId"],
        ))

    batch_size = 500
    cursor = conn.cursor()
    total = len(records)
    written = 0

    for i in range(0, total, batch_size):
        batch = records[i : i + batch_size]
        cursor.executemany(update_sql, batch)
        conn.commit()
        written += len(batch)
        print(f"      Updated {written:,}/{total:,} rows...", end="\r")

    cursor.close()
    print(f"\n      Write-back complete. {total:,} rows updated.")


# ============================================================================
# MAIN — FULL PIPELINE
# ============================================================================

def main():
    """
    Run the full ML pipeline end-to-end:
      1. Connect to Azure SQL
      2. Extract shipment data           (Data Pipeline)
      3. Transform / engineer features   (Data Pipeline)
      4. Train Random Forest             (ML Pipeline)
      5. Evaluate model                  (ML Pipeline)
      6. Save model to disk              (ML Pipeline)
      7. Generate predictions            (Inference Pipeline)
      8. Write predictions to SQL        (Inference Pipeline)
    """
    conn = None
    try:
        conn = get_connection()
        df = extract_data(conn)
        df, feature_columns = transform_data(df)
        model, X_train, X_test, y_train, y_test = train_model(df, feature_columns)
        importance_df, accuracy, auc = evaluate_model(
            model, X_test, y_test, feature_columns
        )
        save_model(model, feature_columns, accuracy, auc)
        predictions = generate_predictions(model, df, feature_columns)
        predictions = generate_explanations(df, predictions, feature_columns)
        save_visualizations(importance_df, predictions)
        _ensure_explanation_columns(conn)
        write_predictions_to_sql(conn, predictions)

        print("\n" + "=" * 60)
        print("  PIPELINE COMPLETE")
        print(f"  Model saved to: {MODEL_PATH}")
        print(f"  Accuracy: {accuracy:.2%} | AUC-ROC: {auc:.4f}")
        print(f"  Shipments scored: {len(predictions):,}")
        print("=" * 60)

    except Exception as exc:
        print(f"\nPipeline failed: {exc}")
        raise
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")


def demo_single_prediction():
    """
    Demo: score a single shipment using the saved model.
    Run with: python scripts/ml_pipeline.py --predict
    """
    print("\n" + "=" * 60)
    print("  SINGLE SHIPMENT PREDICTION (demo)")
    print("=" * 60)

    result = predict_single_shipment(
        distance_miles=1200,
        weight_lbs=35000,
        linehaul_cost=2800,
        revenue=3500,
        appointment_type="Live",
        facility_type="Cold Storage",
        safety_rating="Unsatisfactory",
        fleet_size=500,
        avg_dwell_time_hrs=6.5,
        appointment_required="No",
        day_of_week=3,       # Tuesday
        hour_of_day=15,      # 3 PM (afternoon)
    )

    print(f"\n  Input: 1,200 miles | 35,000 lbs | Live appt | Cold Storage")
    print(f"         Unsatisfactory carrier | 6.5hr avg dwell | 3 PM Tuesday")
    print(f"\n  Risk Score: {result['risk_score']:.4f}")
    print(f"  Risk Tier:  {result['risk_tier']}")
    print(f"  Model:      {result['model_name']} "
          f"(accuracy: {result['model_accuracy']:.2%}, "
          f"AUC: {result['model_auc_roc']:.4f})")
    print("=" * 60)


if __name__ == "__main__":
    if "--predict" in sys.argv:
        demo_single_prediction()
    else:
        main()