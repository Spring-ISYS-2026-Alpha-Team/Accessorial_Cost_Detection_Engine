"""
PACE ML Pipeline — Accessorial Risk Prediction (v4 — Explainable)
=================================================================
Connects to Azure SQL, extracts shipment data, trains a Random Forest
classifier to predict AccessorialFlag, evaluates model performance,
saves the trained model to disk, generates risk score predictions,
creates user-friendly explanations and recommended actions,
saves visualizations, and writes predictions back to the Shipments table.

Also includes a standalone inference function (predict_single_shipment)
that loads the saved model and scores a new shipment without retraining.

Three Pipelines Covered:
  1. DATA PIPELINE:      extract_data() + transform_data()
  2. ML PIPELINE:        train_model() + evaluate_model() + save_model()
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
from datetime import datetime

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
    s.ShipmentId,
    s.ShipDate,
    s.OriginRegion,
    s.DestRegion,
    s.CarrierId,
    s.FacilityType,
    s.AppointmentType,
    s.DistanceMiles,
    s.weight_lbs,
    s.Revenue,
    s.LinehaulCost,
    s.AccessorialFlag,
    s.AccessorialCost,
    s.risk_score,
    s.risk_tier,
    c.carrier_name,
    c.safety_rating,
    c.fleet_size,
    f.facility_name,
    f.facility_type AS fac_type,
    f.avg_dwell_time_hrs,
    f.appointment_required,
    DATEPART(WEEKDAY, s.ShipDate) AS day_of_week,
    DATEPART(HOUR, s.ShipDate) AS hour_of_day
FROM Shipments s
LEFT JOIN Carriers c
    ON s.CarrierId = c.carrier_id
LEFT JOIN Facilities f
    ON s.facility_id = f.facility_id
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FACILITY_TYPES = [
    "Warehouse",
    "Cross-Dock",
    "Cold Storage",
    "Distribution Center",
    "Shipper",
    "Receiver",
]
TARGET = "AccessorialFlag"

# ============================================================================
# DATA PIPELINE
# ============================================================================

def get_connection():
    """Open and return a pyodbc connection to Azure SQL."""
    connection_string = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER=tcp:{DB_SERVER},1433;"
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

    flag_counts = df[TARGET].value_counts()
    total = len(df)
    n_zero = int(flag_counts.get(False, flag_counts.get(0, 0)))
    n_one = int(flag_counts.get(True, flag_counts.get(1, 0)))

    print("      Class balance:")
    print(f"        No accessorial (0): {n_zero:,} ({n_zero / total:.1%})")
    print(f"        Accessorial (1):    {n_one:,} ({n_one / total:.1%})")
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
    df["OriginRegion"] = df["OriginRegion"].fillna("")
    df["DestRegion"] = df["DestRegion"].fillna("")
    df["FacilityType"] = df["FacilityType"].fillna("Unknown")
    df["AppointmentType"] = df["AppointmentType"].fillna("Drop")
    df["safety_rating"] = df["safety_rating"].fillna("None")
    df["appointment_required"] = df["appointment_required"].fillna("No")

    # --- Encode categorical columns ---
    df["appt_encoded"] = df["AppointmentType"].map({
        "Live": 1,
        "Drop": 0
    }).fillna(0).astype(int)

    df["safety_encoded"] = df["safety_rating"].map({
        "Satisfactory": 0,
        "Conditional": 1,
        "None": 2,
        "Unsatisfactory": 3
    }).fillna(2).astype(int)

    df["appt_required_encoded"] = df["appointment_required"].map({
        "Yes": 1,
        "No": 0
    }).fillna(0).astype(int)

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
    safe_revenue = df["Revenue"].replace(0, np.nan)
    safe_miles = df["DistanceMiles"].replace(0, np.nan)

    df["cost_ratio"] = (df["LinehaulCost"] / safe_revenue).fillna(0)
    df["revenue_per_mile"] = (df["Revenue"] / safe_miles).fillna(0)
    df["cost_per_mile"] = (df["LinehaulCost"] / safe_miles).fillna(0)
    df["weight_per_mile"] = (df["weight_lbs"] / safe_miles).fillna(0)
    df["is_weekend"] = df["day_of_week"].isin([1, 7]).astype(int)
    df["is_afternoon"] = (df["hour_of_day"] >= 13).astype(int)
    df["high_dwell"] = (df["avg_dwell_time_hrs"] >= 4.0).astype(int)

    # --- Demo operational risk features ---
    # Placeholder logic for explainability / decision support
    # Can later be replaced by real API data
    df["weather_risk"] = np.where(df["is_weekend"] == 1, 0.35, 0.15)

    df["traffic_risk"] = np.where(
        df["hour_of_day"].between(7, 9) | df["hour_of_day"].between(16, 18),
        0.40,
        0.15,
    )

    df["storm_flag"] = np.where(
        (
            df["DestRegion"].str.contains("South", case=False, na=False)
            | df["DestRegion"].str.contains("Gulf", case=False, na=False)
            | df["OriginRegion"].str.contains("South", case=False, na=False)
        ) & (df["is_afternoon"] == 1),
        1,
        0,
    )

    df["holiday_flag"] = df["is_weekend"].astype(int)

    # --- Define final feature columns ---
    base_features = [
        "DistanceMiles",
        "weight_lbs",
        "LinehaulCost",
        "Revenue",
        "day_of_week",
        "hour_of_day",
        "appt_encoded",
        "safety_encoded",
        "fleet_size",
        "avg_dwell_time_hrs",
        "appt_required_encoded",
    ]

    engineered_features = [
        "cost_ratio",
        "revenue_per_mile",
        "cost_per_mile",
        "weight_per_mile",
        "is_weekend",
        "is_afternoon",
        "high_dwell",
        "weather_risk",
        "traffic_risk",
        "storm_flag",
        "holiday_flag",
    ]

    feature_columns = base_features + engineered_features + facility_cols

    assert len(feature_columns) == len(set(feature_columns)), (
        f"Duplicate features: "
        f"{[f for f in feature_columns if feature_columns.count(f) > 1]}"
    )

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
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print(f"      Train size: {len(X_train):,}  |  Test size: {len(X_test):,}")
    print(
        "      Train class balance: "
        f"0={int((y_train == 0).sum()):,} / 1={int((y_train == 1).sum()):,}"
    )

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

    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="f1")
    print(f"      5-fold CV F1 score: {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")

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

    print("\n  Classification Report:")
    print(classification_report(
        y_test,
        y_pred,
        target_names=["No Accessorial (0)", "Accessorial (1)"]
    ))

    cm = confusion_matrix(y_test, y_pred)
    print("  Confusion Matrix:")
    print(f"    True Negatives  (correct no-charge): {cm[0][0]:,}")
    print(f"    False Positives (false alarm):       {cm[0][1]:,}")
    print(f"    False Negatives (missed charge):     {cm[1][0]:,}")
    print(f"    True Positives  (caught charge):     {cm[1][1]:,}")

    importance_df = pd.DataFrame({
        "feature": feature_columns,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    print("\n  Top 10 Feature Importances:")
    for _, row in importance_df.head(10).iterrows():
        bar = "█" * int(row["importance"] * 80)
        print(f"    {row['feature']:<25} {row['importance']:.4f}  {bar}")

    return importance_df, acc, auc


def save_model(model, feature_columns, accuracy, auc_roc, train_rows):
    """
    ML PIPELINE — Step 3: Save
    Saves model, feature columns, and metadata.
    """
    print("[6/8] Saving model to disk...")
    os.makedirs(MODEL_DIR, exist_ok=True)

    joblib.dump(model, MODEL_PATH)
    print(f"      Saved model: {MODEL_PATH}")

    with open(FEATURES_PATH, "w") as f:
        json.dump(feature_columns, f, indent=2)
    print(f"      Saved features: {FEATURES_PATH}")

    metadata = {
        "model_name": "RandomForest_v4_explainable",
        "n_estimators": model.n_estimators,
        "max_depth": model.max_depth,
        "class_weight": "balanced",
        "accuracy": round(accuracy, 4),
        "auc_roc": round(auc_roc, 4),
        "n_features": len(feature_columns),
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "trained_on_rows": int(train_rows),
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"      Saved metadata: {METADATA_PATH}")
    print(f"      Model accuracy: {accuracy:.2%} | AUC-ROC: {auc_roc:.4f}")

# ============================================================================
# INFERENCE PIPELINE
# ============================================================================

def generate_shipment_explanations(df, predictions):
    """
    Build user-friendly explanations and recommendations for each shipment.
    Returns DataFrame with ShipmentId, risk_reason, recommended_action.
    """
    results = []
    merged = df.merge(predictions, on="ShipmentId", how="left")

    for _, row in merged.iterrows():
        reasons = []
        actions = []

        if row.get("AppointmentType") == "Live":
            reasons.append("Live appointment increases detention risk.")
            actions.append("Confirm dock readiness before dispatch.")

        if row.get("hour_of_day", 0) >= 13:
            reasons.append("Afternoon shipment timing may increase delays.")
            actions.append("Move the appointment to the morning if possible.")

        if row.get("avg_dwell_time_hrs", 0) >= 4:
            reasons.append("This facility has historically high dwell time.")
            actions.append("Add unload buffer time and alert operations.")

        if row.get("safety_rating") in ["Conditional", "Unsatisfactory"]:
            reasons.append("Carrier safety profile indicates higher operational risk.")
            actions.append("Consider a more reliable carrier if available.")

        if row.get("DistanceMiles", 0) >= 800:
            reasons.append("Long-haul distance increases layover exposure.")
            actions.append("Build additional time buffer into the delivery plan.")

        if row.get("weight_lbs", 0) >= 25000:
            reasons.append("Heavy load may increase lumper or unloading charges.")
            actions.append("Confirm unloading requirements in advance.")

        if row.get("appointment_required") == "No":
            reasons.append("Facilities without strict appointments may create unpredictable wait times.")
            actions.append("Call ahead to verify loading and unloading readiness.")

        if row.get("traffic_risk", 0) >= 0.35:
            reasons.append("Traffic conditions around the delivery window may increase delay risk.")
            actions.append("Avoid peak traffic windows or adjust dispatch timing.")

        if row.get("weather_risk", 0) >= 0.30:
            reasons.append("Weather conditions may increase transit variability.")
            actions.append("Add schedule flexibility and monitor route conditions.")

        if row.get("storm_flag", 0) == 1:
            reasons.append("Storm-related disruption risk is elevated for this shipment.")
            actions.append("Prepare a backup route or contingency plan.")

        if row.get("holiday_flag", 0) == 1:
            reasons.append("Weekend or holiday timing may reduce facility efficiency.")
            actions.append("Confirm staffing and appointment availability in advance.")

        if not reasons:
            reasons.append("This shipment shows relatively stable operating conditions.")
            actions.append("Proceed with normal planning and monitoring.")

        results.append({
            "ShipmentId": row["ShipmentId"],
            "risk_reason": " ".join(reasons[:3]),
            "recommended_action": " ".join(actions[:3]),
        })

    return pd.DataFrame(results)


def generate_predictions(model, df, feature_columns):
    """
    INFERENCE PIPELINE — Batch scoring
    Generate risk_score and risk_tier predictions for all rows in the DataFrame.
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

    explanations = generate_shipment_explanations(df, predictions)
    predictions = predictions.merge(explanations, on="ShipmentId", how="left")

    tier_counts = predictions["ml_risk_tier"].value_counts()
    print(f"      Predictions: {tier_counts.to_dict()}")

    return predictions


def predict_single_shipment(
    distance_miles,
    weight_lbs,
    linehaul_cost,
    revenue,
    appointment_type,
    facility_type,
    safety_rating,
    fleet_size,
    avg_dwell_time_hrs,
    appointment_required,
    day_of_week=4,
    hour_of_day=10,
    weather_risk=0.15,
    traffic_risk=0.15,
    storm_flag=0,
    holiday_flag=0,
):
    """
    INFERENCE PIPELINE — Single shipment scoring
    Loads the saved model from disk, transforms one shipment's features,
    and returns a risk score + risk tier.
    """
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

    appt_encoded = 1 if appointment_type == "Live" else 0

    safety_map = {
        "Satisfactory": 0,
        "Conditional": 1,
        "None": 2,
        "Unsatisfactory": 3
    }
    safety_encoded = safety_map.get(safety_rating, 2)

    appt_required_encoded = 1 if appointment_required == "Yes" else 0

    facility_flags = {}
    for ftype in FACILITY_TYPES:
        facility_flags[f"fac_{ftype}"] = 1 if facility_type == ftype else 0

    safe_revenue = revenue if revenue > 0 else np.nan
    safe_miles = distance_miles if distance_miles > 0 else np.nan

    cost_ratio = (linehaul_cost / safe_revenue) if pd.notna(safe_revenue) else 0
    revenue_per_mile = (revenue / safe_miles) if pd.notna(safe_miles) else 0
    cost_per_mile = (linehaul_cost / safe_miles) if pd.notna(safe_miles) else 0
    weight_per_mile = (weight_lbs / safe_miles) if pd.notna(safe_miles) else 0
    is_weekend = 1 if day_of_week in [1, 7] else 0
    is_afternoon = 1 if hour_of_day >= 13 else 0
    high_dwell = 1 if avg_dwell_time_hrs >= 4.0 else 0

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
        "weather_risk": weather_risk,
        "traffic_risk": traffic_risk,
        "storm_flag": storm_flag,
        "holiday_flag": holiday_flag,
    }
    feature_values.update(facility_flags)

    X = pd.DataFrame([feature_values])[feature_columns]

    risk_score = float(model.predict_proba(X)[0, 1])

    if risk_score < 0.34:
        risk_tier = "Low"
    elif risk_score <= 0.67:
        risk_tier = "Medium"
    else:
        risk_tier = "High"

    reason_parts = []
    action_parts = []

    if appointment_type == "Live":
        reason_parts.append("Live appointment increases detention risk.")
        action_parts.append("Confirm dock readiness before dispatch.")

    if hour_of_day >= 13:
        reason_parts.append("Afternoon timing may increase delays.")
        action_parts.append("Move the appointment to the morning if possible.")

    if avg_dwell_time_hrs >= 4:
        reason_parts.append("Facility dwell time is historically elevated.")
        action_parts.append("Add unload buffer time.")

    if safety_rating in ["Conditional", "Unsatisfactory"]:
        reason_parts.append("Carrier profile indicates elevated operational risk.")
        action_parts.append("Consider a stronger carrier option.")

    if traffic_risk >= 0.35:
        reason_parts.append("Traffic exposure is elevated for this delivery window.")
        action_parts.append("Avoid peak congestion windows.")

    if weather_risk >= 0.30 or storm_flag == 1:
        reason_parts.append("Weather or storm conditions may increase variability.")
        action_parts.append("Monitor route conditions and prepare contingency plans.")

    if holiday_flag == 1:
        reason_parts.append("Holiday or weekend timing may reduce facility efficiency.")
        action_parts.append("Confirm staffing and appointment availability.")

    if not reason_parts:
        reason_parts.append("This shipment shows relatively stable operating conditions.")
        action_parts.append("Proceed with standard planning.")

    return {
        "risk_score": round(risk_score, 4),
        "risk_tier": risk_tier,
        "model_name": metadata.get("model_name", "Unknown"),
        "model_accuracy": metadata.get("accuracy", None),
        "model_auc_roc": metadata.get("auc_roc", None),
        "risk_reason": " ".join(reason_parts[:3]),
        "recommended_action": " ".join(action_parts[:3]),
    }

# ============================================================================
# VISUALIZATIONS
# ============================================================================

def save_visualizations(importance_df, predictions):
    """Save feature importance and risk distribution charts."""
    os.makedirs("outputs", exist_ok=True)

    top10 = importance_df.head(10).sort_values("importance")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [
        "#2563EB" if imp > 0.05 else "#93C5FD"
        for imp in top10["importance"]
    ]
    ax.barh(top10["feature"], top10["importance"], color=colors)
    ax.set_xlabel("Importance Score")
    ax.set_title("Top 10 Features — Random Forest Accessorial Risk Model")
    ax.axvline(
        x=0.05,
        color="#EF4444",
        linestyle="--",
        alpha=0.5,
        label="5% threshold"
    )
    ax.legend()
    plt.tight_layout()
    fig.savefig("outputs/feature_importance.png", dpi=150)
    plt.close(fig)
    print("      Saved: outputs/feature_importance.png")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(
        predictions["ml_risk_score"],
        bins=50,
        color="#0F2B4A",
        edgecolor="white",
        alpha=0.85
    )
    ax.axvline(
        x=0.34,
        color="#10B981",
        linestyle="--",
        linewidth=2,
        label="Low/Medium (0.34)"
    )
    ax.axvline(
        x=0.67,
        color="#F59E0B",
        linestyle="--",
        linewidth=2,
        label="Medium/High (0.67)"
    )
    ax.set_xlabel("Predicted Risk Score")
    ax.set_ylabel("Number of Shipments")
    ax.set_title("Distribution of Predicted Accessorial Risk Scores")
    ax.legend()
    plt.tight_layout()
    fig.savefig("outputs/risk_distribution.png", dpi=150)
    plt.close(fig)
    print("      Saved: outputs/risk_distribution.png")

# ============================================================================
# WRITE-BACK
# ============================================================================

def write_predictions_to_sql(conn, predictions):
    """UPDATE risk_score, risk_tier, risk_reason, recommended_action."""
    print("[8/8] Writing predictions back to SQL...")

    update_sql = """
        UPDATE Shipments
        SET risk_score = ?, risk_tier = ?, risk_reason = ?, recommended_action = ?
        WHERE ShipmentId = ?
    """

    records = list(zip(
        predictions["ml_risk_score"].round(4),
        predictions["ml_risk_tier"].astype(str),
        predictions["risk_reason"].fillna(""),
        predictions["recommended_action"].fillna(""),
        predictions["ShipmentId"],
    ))

    batch_size = 500
    cursor = conn.cursor()
    total = len(records)
    written = 0

    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
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
    Run the full ML pipeline end-to-end.
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

        save_model(model, feature_columns, accuracy, auc, len(X_train))

        predictions = generate_predictions(model, df, feature_columns)
        save_visualizations(importance_df, predictions)
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
        day_of_week=3,
        hour_of_day=15,
        weather_risk=0.35,
        traffic_risk=0.40,
        storm_flag=1,
        holiday_flag=0,
    )

    print("\n  Input: 1,200 miles | 35,000 lbs | Live appt | Cold Storage")
    print("         Unsatisfactory carrier | 6.5hr avg dwell | 3 PM Tuesday")
    print(f"\n  Risk Score: {result['risk_score']:.4f}")
    print(f"  Risk Tier:  {result['risk_tier']}")
    print(
        f"  Model:      {result['model_name']} "
        f"(accuracy: {result['model_accuracy']:.2%}, "
        f"AUC: {result['model_auc_roc']:.4f})"
    )
    print(f"  Reason:     {result['risk_reason']}")
    print(f"  Action:     {result['recommended_action']}")
    print("=" * 60)


if __name__ == "__main__":
    if "--predict" in sys.argv:
        demo_single_prediction()
    else:
        main()