"""
PACE ML Pipeline — Accessorial Risk Prediction
===============================================
Connects to Azure SQL, extracts shipment data, trains a Random Forest
classifier to predict AccessorialFlag, evaluates model performance,
generates risk score predictions, saves visualizations, and writes
predictions back to the Shipments table.

Usage:
    python scripts/ml_pipeline.py

Requirements:
    pip install -r scripts/requirements_pipeline.txt
"""

import os
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — must be set before pyplot import
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyodbc
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Database credentials — fill these in before running
# ---------------------------------------------------------------------------
DB_SERVER = "essql1.database.windows.net"
DB_NAME = "ISYS43603_Spring2026_Sec02_Alice_db"
DB_USERNAME = "YOUR_USERNAME_HERE"
DB_PASSWORD = "YOUR_PASSWORD_HERE"
DB_DRIVER = "ODBC Driver 18 for SQL Server"

# ---------------------------------------------------------------------------
# SQL query
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
JOIN Carriers c ON s.CarrierId = c.carrier_id
LEFT JOIN Facilities f ON s.facility_id = f.facility_id
"""

# ---------------------------------------------------------------------------
# Feature columns (after encoding)
# ---------------------------------------------------------------------------
NUMERIC_FEATURES = [
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

FACILITY_TYPES = [
    "Warehouse",
    "Cross-Dock",
    "Cold Storage",
    "Distribution Center",
    "Shipper",
    "Receiver",
]

TARGET = "AccessorialFlag"


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def get_connection():
    """
    Open and return a pyodbc connection to the Azure SQL database.

    Uses the module-level credential constants (DB_SERVER, DB_NAME,
    DB_USERNAME, DB_PASSWORD, DB_DRIVER).  The caller is responsible for
    closing the connection when finished.

    Returns
    -------
    pyodbc.Connection
    """
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
    print("[1/7] Connecting to Azure SQL...")
    conn = pyodbc.connect(connection_string)
    print("      Connected successfully.")
    return conn


def extract_data(conn):
    """
    Run the extraction SQL query and return a DataFrame.

    Reads from Shipments joined with Carriers and Facilities.  Expects
    approximately 22,000 rows.

    Parameters
    ----------
    conn : pyodbc.Connection
        An open database connection.

    Returns
    -------
    pd.DataFrame
        Raw DataFrame with all columns from EXTRACT_QUERY.
    """
    print("[2/7] Extracting data from database...")
    df = pd.read_sql(EXTRACT_QUERY, conn)
    print(f"      Extracted {len(df):,} rows, {df.shape[1]} columns.")
    return df


def transform_data(df):
    """
    Clean, encode, and engineer features from the raw DataFrame.

    Steps:
    - Fill nulls: weight_lbs → median, avg_dwell_time_hrs → 0,
      fleet_size → median
    - Encode AppointmentType: Live=1, Drop=0
    - Encode safety_rating: Satisfactory=0, Conditional=1, None=2,
      Unsatisfactory=3
    - Encode appointment_required: Yes=1, No=0
    - One-hot encode FacilityType for FACILITY_TYPES categories

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame from extract_data().

    Returns
    -------
    tuple[pd.DataFrame, list[str]]
        (transformed_df, feature_columns) where feature_columns is the
        final ordered list of column names used as model input.
    """
    print("[3/7] Transforming data...")

    # --- Null filling ---
    df["weight_lbs"] = df["weight_lbs"].fillna(df["weight_lbs"].median())
    df["avg_dwell_time_hrs"] = df["avg_dwell_time_hrs"].fillna(0)
    df["fleet_size"] = df["fleet_size"].fillna(df["fleet_size"].median())

    # --- Encode AppointmentType ---
    appt_map = {"Live": 1, "Drop": 0}
    df["appt_encoded"] = df["AppointmentType"].map(appt_map).fillna(0).astype(int)

    # --- Encode safety_rating ---
    safety_map = {
        "Satisfactory": 0,
        "Conditional": 1,
        "None": 2,
        "Unsatisfactory": 3,
    }
    df["safety_encoded"] = df["safety_rating"].map(safety_map).fillna(2).astype(int)

    # --- Encode appointment_required ---
    appt_req_map = {"Yes": 1, "No": 0}
    df["appt_required_encoded"] = (
        df["appointment_required"].map(appt_req_map).fillna(0).astype(int)
    )

    # --- One-hot encode FacilityType ---
    facility_dummies = pd.get_dummies(df["FacilityType"], prefix="fac")
    # Ensure all expected facility type columns are present
    for ftype in FACILITY_TYPES:
        col = f"fac_{ftype}"
        if col not in facility_dummies.columns:
            facility_dummies[col] = 0
    facility_cols = [f"fac_{t}" for t in FACILITY_TYPES]
    df = pd.concat([df, facility_dummies[facility_cols]], axis=1)

    feature_columns = NUMERIC_FEATURES + facility_cols
    print(f"      Feature set: {len(feature_columns)} columns.")
    return df, feature_columns


def train_model(df, feature_columns):
    """
    Split data and train a RandomForestClassifier.

    Uses an 80/20 train-test split (random_state=42).  The classifier
    uses 200 estimators with all available CPU cores (n_jobs=-1).

    Parameters
    ----------
    df : pd.DataFrame
        Transformed DataFrame containing both feature and target columns.
    feature_columns : list[str]
        Ordered list of feature column names to pass to the model.

    Returns
    -------
    tuple
        (model, X_train, X_test, y_train, y_test) where model is the
        fitted RandomForestClassifier.
    """
    print("[4/7] Training Random Forest model...")
    X = df[feature_columns]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"      Train size: {len(X_train):,}  |  Test size: {len(X_test):,}")

    model = RandomForestClassifier(
        n_estimators=200, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)
    print("      Model training complete.")
    return model, X_train, X_test, y_train, y_test


def evaluate_model(model, X_test, y_test, feature_columns):
    """
    Print accuracy, classification report, confusion matrix, and top-10
    feature importances.

    Parameters
    ----------
    model : RandomForestClassifier
        A fitted classifier.
    X_test : pd.DataFrame
        Held-out feature data.
    y_test : pd.Series
        Held-out target labels.
    feature_columns : list[str]
        Feature names (same order as model was trained on).

    Returns
    -------
    pd.DataFrame
        Feature importance DataFrame sorted descending, columns
        ['feature', 'importance'].
    """
    print("[5/7] Evaluating model...")
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    print(f"\n  Accuracy: {acc:.4f}")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred))
    print("  Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Feature importances
    importance_df = pd.DataFrame(
        {"feature": feature_columns, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=False)

    print("\n  Top 10 Feature Importances:")
    print(importance_df.head(10).to_string(index=False))
    return importance_df


def generate_predictions(model, df, feature_columns):
    """
    Generate risk_score and risk_tier predictions for all rows.

    Runs predict_proba on the full dataset to obtain the probability of
    AccessorialFlag == 1.  Assigns tiers:
    - Low    : risk_score < 0.34
    - Medium : 0.34 <= risk_score <= 0.67
    - High   : risk_score > 0.67

    Parameters
    ----------
    model : RandomForestClassifier
        A fitted classifier.
    df : pd.DataFrame
        Full transformed DataFrame.
    feature_columns : list[str]
        Feature column names.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['ShipmentId', 'ml_risk_score', 'ml_risk_tier'].
    """
    print("[6/7] Generating predictions for all rows...")
    probas = model.predict_proba(df[feature_columns])
    # Column index 1 = probability of AccessorialFlag == 1
    risk_scores = probas[:, 1]

    def assign_tier(score):
        if score < 0.34:
            return "Low"
        elif score <= 0.67:
            return "Medium"
        else:
            return "High"

    tiers = [assign_tier(s) for s in risk_scores]

    predictions = pd.DataFrame(
        {
            "ShipmentId": df["ShipmentId"].values,
            "ml_risk_score": risk_scores,
            "ml_risk_tier": tiers,
        }
    )
    tier_counts = predictions["ml_risk_tier"].value_counts()
    print(f"      Predictions: {tier_counts.to_dict()}")
    return predictions


def save_visualizations(importance_df, predictions):
    """
    Save two charts to the outputs/ directory.

    1. Feature importance horizontal bar chart (top 10 features).
    2. Risk score distribution histogram.

    Creates the outputs/ directory if it does not exist.

    Parameters
    ----------
    importance_df : pd.DataFrame
        Output of evaluate_model(), with columns ['feature', 'importance'].
    predictions : pd.DataFrame
        Output of generate_predictions(), with column 'ml_risk_score'.
    """
    os.makedirs("outputs", exist_ok=True)

    # --- Feature importance chart ---
    top10 = importance_df.head(10).sort_values("importance")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top10["feature"], top10["importance"], color="#2563EB")
    ax.set_xlabel("Importance")
    ax.set_title("Top 10 Feature Importances — Random Forest")
    plt.tight_layout()
    fig.savefig("outputs/feature_importance.png", dpi=150)
    plt.close(fig)
    print("      Saved: outputs/feature_importance.png")

    # --- Risk score distribution histogram ---
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(predictions["ml_risk_score"], bins=40, color="#16A34A", edgecolor="white")
    ax.set_xlabel("Risk Score")
    ax.set_ylabel("Count")
    ax.set_title("ML Risk Score Distribution")
    plt.tight_layout()
    fig.savefig("outputs/risk_distribution.png", dpi=150)
    plt.close(fig)
    print("      Saved: outputs/risk_distribution.png")


def write_predictions_to_sql(conn, predictions):
    """
    UPDATE risk_score and risk_tier on the Shipments table using
    predicted values.  Rows are processed in batches of 500 using
    executemany for performance.

    Only the two columns risk_score and risk_tier are modified.  The
    database schema is not altered.

    Parameters
    ----------
    conn : pyodbc.Connection
        An open, autocommit-disabled connection.
    predictions : pd.DataFrame
        DataFrame with columns ['ShipmentId', 'ml_risk_score', 'ml_risk_tier'].

    Notes
    -----
    Commented-out code below shows how to INSERT into a separate
    Predictions table instead of updating Shipments.
    """
    print("[7/7] Writing predictions back to SQL...")

    update_sql = """
        UPDATE Shipments
        SET risk_score = ?,
            risk_tier  = ?
        WHERE ShipmentId = ?
    """

    # Build list of (risk_score, risk_tier, ShipmentId) tuples
    records = list(
        zip(
            predictions["ml_risk_score"].round(4),
            predictions["ml_risk_tier"],
            predictions["ShipmentId"],
        )
    )

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

    # ---------------------------------------------------------------------------
    # ALTERNATIVE: Write to a separate Predictions table instead of updating
    # Shipments.  Uncomment the block below and comment out the UPDATE block
    # above if you prefer to keep predictions in their own table.
    # ---------------------------------------------------------------------------
    # insert_sql = """
    #     INSERT INTO Predictions (ShipmentId, ml_risk_score, ml_risk_tier, predicted_at)
    #     VALUES (?, ?, ?, GETDATE())
    # """
    # records_insert = list(
    #     zip(
    #         predictions["ShipmentId"],
    #         predictions["ml_risk_score"].round(4),
    #         predictions["ml_risk_tier"],
    #     )
    # )
    # for i in range(0, total, batch_size):
    #     batch = records_insert[i : i + batch_size]
    #     cursor.executemany(insert_sql, batch)
    #     conn.commit()
    # ---------------------------------------------------------------------------


def main():
    """
    Orchestrate the full ML pipeline end-to-end.

    Steps:
    1. Open database connection
    2. Extract shipment data
    3. Transform / engineer features
    4. Train Random Forest classifier
    5. Evaluate model on held-out test set
    6. Generate predictions for all rows
    7. Save visualizations
    8. Write predictions back to Shipments table

    The database connection is always closed in the finally block,
    even if an error occurs mid-pipeline.
    """
    conn = None
    try:
        conn = get_connection()
        df = extract_data(conn)
        df, feature_columns = transform_data(df)
        model, X_train, X_test, y_train, y_test = train_model(df, feature_columns)
        importance_df = evaluate_model(model, X_test, y_test, feature_columns)
        predictions = generate_predictions(model, df, feature_columns)
        save_visualizations(importance_df, predictions)
        write_predictions_to_sql(conn, predictions)
        print("\nPipeline complete.")
    except Exception as exc:
        print(f"\nPipeline failed: {exc}")
        raise
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    main()
