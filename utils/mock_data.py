"""
utils/mock_data.py
Generates synthetic shipment data for PACE demo/development use.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

CARRIERS = [
    "XPO Logistics",
    "J.B. Hunt",
    "Werner Enterprises",
    "Schneider National",
    "Old Dominion",
    "FedEx Freight",
]

FACILITIES = [
    "Warehouse A - Dallas",
    "Warehouse B - Memphis",
    "Distribution Center C - Atlanta",
    "Warehouse D - Chicago",
    "Cold Storage E - Houston",
]

ORIGIN_CITIES = [
    "Dallas, TX", "Chicago, IL", "Los Angeles, CA",
    "New York, NY", "Atlanta, GA", "Denver, CO",
    "Phoenix, AZ", "Seattle, WA",
]

DESTINATION_CITIES = [
    "Memphis, TN", "Houston, TX", "Nashville, TN",
    "Louisville, KY", "Charlotte, NC", "Indianapolis, IN",
    "Columbus, OH", "Kansas City, MO",
]

ACCESSORIAL_TYPES = ["Detention", "Lumper Fee", "Layover", "Re-delivery"]

# Risk bias per carrier (positive = higher risk)
CARRIER_BIAS = {
    "XPO Logistics":      0.10,
    "J.B. Hunt":         -0.05,
    "Werner Enterprises":  0.15,
    "Schneider National": -0.10,
    "Old Dominion":       -0.20,
    "FedEx Freight":       0.05,
}

# Risk bias per facility
FACILITY_BIAS = {
    "Warehouse A - Dallas":            0.05,
    "Warehouse B - Memphis":           0.20,
    "Distribution Center C - Atlanta": -0.10,
    "Warehouse D - Chicago":            0.15,
    "Cold Storage E - Houston":        -0.05,
}


def generate_mock_shipments(n: int = 300, seed: int = 42) -> pd.DataFrame:
    """Return a DataFrame of n synthetic shipments with risk scores."""
    rng = np.random.default_rng(seed)

    base_date = datetime.today()
    ship_dates = [
        base_date - timedelta(days=int(rng.integers(0, 90))) for _ in range(n)
    ]

    carriers     = rng.choice(CARRIERS,          n)
    facilities   = rng.choice(FACILITIES,        n)
    origins      = rng.choice(ORIGIN_CITIES,     n)
    destinations = rng.choice(DESTINATION_CITIES, n)

    c_bias = np.array([CARRIER_BIAS[c]  for c in carriers])
    f_bias = np.array([FACILITY_BIAS[f] for f in facilities])
    base_risk = rng.uniform(0.10, 0.90, n)
    risk_scores = np.clip(base_risk + c_bias + f_bias, 0.05, 0.98).round(3)

    weight_lbs   = rng.uniform(500,   44_000, n).round(0).astype(int)
    miles        = rng.uniform(50,     2_400, n).round(0).astype(int)
    base_freight = (weight_lbs * 0.04 + miles * 0.80 + rng.uniform(100, 500, n)).round(2)

    accessorial_charges = np.array([
        round(float(rng.uniform(200, 850)), 2) if rs >= 0.67
        else round(float(rng.uniform(50, 350)), 2) if rs >= 0.34
        else 0.0
        for rs in risk_scores
    ])

    risk_tiers = [
        "High" if rs >= 0.67 else "Medium" if rs >= 0.34 else "Low"
        for rs in risk_scores
    ]

    accessorial_types = [
        str(rng.choice(ACCESSORIAL_TYPES)) if rs >= 0.34 else "None"
        for rs in risk_scores
    ]

    total_costs   = (base_freight + accessorial_charges).round(2)
    cost_per_mile = np.where(miles > 0, total_costs / miles, 0).round(4)

    df = pd.DataFrame({
        "shipment_id":            [f"SHP-{str(i).zfill(5)}" for i in range(1, n + 1)],
        "ship_date":              [d.strftime("%Y-%m-%d") for d in ship_dates],
        "carrier":                carriers,
        "facility":               facilities,
        "origin_city":            origins,
        "destination_city":       destinations,
        "lane":                   [f"{o} → {d}" for o, d in zip(origins, destinations)],
        "weight_lbs":             weight_lbs,
        "miles":                  miles,
        "base_freight_usd":       base_freight,
        "accessorial_charge_usd": accessorial_charges,
        "total_cost_usd":         total_costs,
        "cost_per_mile":          cost_per_mile,
        "risk_score":             risk_scores,
        "risk_tier":              risk_tiers,
        "accessorial_type":       accessorial_types,
    })

    return df.sort_values("ship_date", ascending=False).reset_index(drop=True)
