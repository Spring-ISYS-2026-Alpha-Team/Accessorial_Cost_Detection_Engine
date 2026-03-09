"""
PACE — Fix Seed Data Patterns
==============================
The current AccessorialFlag values in the database were generated randomly,
so no ML model can learn to predict them. This script updates AccessorialFlag
and AccessorialCost to correlate with shipment features the way they would
in real freight operations:

  - Live appointments → higher accessorial risk
  - Afternoon shipments → higher detention risk  
  - High dwell time facilities → higher risk
  - Unsatisfactory carriers → higher risk
  - Longer distances → more layover risk
  - Heavier loads → more lumper/liftgate risk

After running this, re-run ml_pipeline.py and the model should achieve
AUC-ROC > 0.70 because there are now real patterns to learn.

Usage:
    python scripts/fix_seed_data.py

WARNING: This updates AccessorialFlag and AccessorialCost on ALL 22,000
shipments. Run this ONCE, then re-run the ML pipeline.
"""

import pyodbc
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Database credentials (same as ml_pipeline.py)
# ---------------------------------------------------------------------------
DB_SERVER = "essql1.database.windows.net"
DB_NAME = "ISYS43603_Spring2026_Sec02_Alice_db"
DB_USERNAME = "Alice"
DB_PASSWORD = "ISYSPass12345678!"
DB_DRIVER = "ODBC Driver 18 for SQL Server"


def main():
    print("Connecting to Azure SQL...")
    conn = pyodbc.connect(
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USERNAME};"
        f"PWD={DB_PASSWORD};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    print("Connected.\n")

    # Pull all shipments with carrier + facility info
    print("Loading shipment data...")
    df = pd.read_sql("""
        SELECT 
            s.ShipmentId, s.AppointmentType, s.DistanceMiles, 
            s.weight_lbs, s.Revenue, s.LinehaulCost,
            s.ShipDate,
            c.safety_rating, c.fleet_size,
            f.avg_dwell_time_hrs, f.appointment_required
        FROM Shipments s
        LEFT JOIN Carriers c ON s.CarrierId = c.carrier_id
        LEFT JOIN Facilities f ON s.facility_id = f.facility_id
    """, conn)
    print(f"Loaded {len(df):,} shipments.\n")

    # Set random seed for reproducibility
    np.random.seed(42)

    # -----------------------------------------------------------------------
    # Build a risk score from 0-100 based on real freight risk factors
    # Each factor adds points. More points = higher accessorial probability.
    # -----------------------------------------------------------------------
    print("Calculating risk-based AccessorialFlag...")

    risk_points = np.zeros(len(df))

    # Factor 1: Live appointments are riskier (detention, waiting)
    risk_points += np.where(df["AppointmentType"] == "Live", 15, 0)

    # Factor 2: Afternoon shipments (hour >= 13) have more delays
    hour = pd.to_datetime(df["ShipDate"]).dt.hour
    risk_points += np.where(hour >= 13, 12, 0)
    risk_points += np.where(hour >= 16, 8, 0)  # Late afternoon even worse

    # Factor 3: High dwell time facilities cause detention
    dwell = df["avg_dwell_time_hrs"].fillna(0)
    risk_points += np.where(dwell >= 6, 20, 0)
    risk_points += np.where((dwell >= 4) & (dwell < 6), 10, 0)
    risk_points += np.where((dwell >= 2) & (dwell < 4), 5, 0)

    # Factor 4: Carrier safety rating
    risk_points += np.where(df["safety_rating"] == "Unsatisfactory", 18, 0)
    risk_points += np.where(df["safety_rating"] == "Conditional", 8, 0)
    risk_points += np.where(df["safety_rating"] == "None", 5, 0)
    # Satisfactory adds 0

    # Factor 5: Long distances = more layover risk
    miles = df["DistanceMiles"].fillna(0)
    risk_points += np.where(miles > 1500, 12, 0)
    risk_points += np.where((miles > 800) & (miles <= 1500), 5, 0)

    # Factor 6: Heavy loads = more lumper/liftgate charges
    weight = df["weight_lbs"].fillna(0)
    risk_points += np.where(weight > 35000, 10, 0)
    risk_points += np.where((weight > 25000) & (weight <= 35000), 5, 0)

    # Factor 7: Small carriers (fewer trucks) = less reliable
    fleet = df["fleet_size"].fillna(0)
    risk_points += np.where(fleet < 500, 8, 0)
    risk_points += np.where((fleet >= 500) & (fleet < 1500), 3, 0)

    # Factor 8: Facility doesn't require appointments = chaotic, more delays
    risk_points += np.where(df["appointment_required"] == "No", 7, 0)

    # -----------------------------------------------------------------------
    # Convert risk points to probability, then flip the coin
    # Max possible points is ~110, normalize to 0-1 range
    # Add randomness so it's not perfectly deterministic (realistic)
    # -----------------------------------------------------------------------
    max_points = 110.0
    base_probability = risk_points / max_points

    # Add noise: +/- 15% randomness
    noise = np.random.uniform(-0.15, 0.15, len(df))
    probability = np.clip(base_probability + noise, 0.02, 0.95)

    # Flip the coin for each shipment based on its probability
    random_draw = np.random.uniform(0, 1, len(df))
    new_flag = (random_draw < probability).astype(int)

    # -----------------------------------------------------------------------
    # Generate accessorial costs for flagged shipments
    # Cost varies by type of charge (implied by risk factors)
    # -----------------------------------------------------------------------
    base_cost = np.where(new_flag == 1,
        np.random.uniform(75, 250, len(df))  # base accessorial cost
        + np.where(df["AppointmentType"] == "Live", 
                   np.random.uniform(50, 200, len(df)), 0)  # detention premium
        + np.where(dwell >= 5, 
                   np.random.uniform(100, 300, len(df)), 0)  # high-dwell premium  
        + np.where(weight > 35000, 
                   np.random.uniform(50, 150, len(df)), 0),  # heavy load premium
        0.0
    )
    new_cost = np.round(base_cost, 2)

    # -----------------------------------------------------------------------
    # Summary before updating
    # -----------------------------------------------------------------------
    total = len(df)
    flagged = int(new_flag.sum())
    print(f"\n  Results:")
    print(f"    Total shipments:     {total:,}")
    print(f"    Accessorial flagged: {flagged:,} ({flagged/total:.1%})")
    print(f"    Clean shipments:     {total - flagged:,} ({(total-flagged)/total:.1%})")
    print(f"    Avg cost (flagged):  ${new_cost[new_flag == 1].mean():.2f}")
    print(f"    Max cost:            ${new_cost.max():.2f}")

    # Show which factors drive risk
    print(f"\n  Risk factor breakdown (avg risk points):")
    print(f"    Live appointments:     {risk_points[df['AppointmentType'] == 'Live'].mean():.1f} pts")
    print(f"    Drop appointments:     {risk_points[df['AppointmentType'] == 'Drop'].mean():.1f} pts")
    print(f"    Unsatisfactory carrier: {risk_points[df['safety_rating'] == 'Unsatisfactory'].mean():.1f} pts")
    print(f"    Satisfactory carrier:   {risk_points[df['safety_rating'] == 'Satisfactory'].mean():.1f} pts")

    # -----------------------------------------------------------------------
    # Write updates to database
    # -----------------------------------------------------------------------
    print(f"\nUpdating {total:,} shipments in database...")

    cursor = conn.cursor()
    update_sql = """
        UPDATE Shipments 
        SET AccessorialFlag = ?, AccessorialCost = ?
        WHERE ShipmentId = ?
    """

    records = list(zip(
        new_flag.tolist(),
        new_cost.tolist(),
        df["ShipmentId"].tolist()
    ))

    batch_size = 500
    written = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        cursor.executemany(update_sql, batch)
        conn.commit()
        written += len(batch)
        print(f"  Updated {written:,}/{total:,}...", end="\r")

    cursor.close()
    conn.close()

    print(f"\n\nDone! Updated {total:,} shipments.")
    print("Now re-run: python scripts/ml_pipeline.py")
    print("Expected result: AUC-ROC > 0.70, recall on class 1 > 0.50")


if __name__ == "__main__":
    main()