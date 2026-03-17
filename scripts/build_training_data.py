"""
scripts/build_training_data.py
─────────────────────────────
Builds a PACE-compatible training CSV by combining up to 3 public datasets.

Supported input sources (mix and match — you don't need all three):

  SOURCE A — Olist Brazilian E-Commerce (Kaggle)
    Files needed (place in data/olist/):
      olist_orders_dataset.csv
      olist_order_items_dataset.csv
      olist_customers_dataset.csv
      olist_sellers_dataset.csv

  SOURCE B — Global Supply Chain Shipment (Kaggle / USAID)
    File needed (place in data/):
      supply_chain_data.csv   (or any name — pass with --supply-chain)

  SOURCE C — US Zip Code lat/lng  (free, many sources)
    File needed (place in data/):
      uszips.csv   columns: zip, lat, lng, state_id

Usage:
  python scripts/build_training_data.py
  python scripts/build_training_data.py --olist data/olist --output data/training_data.csv
  python scripts/build_training_data.py --supply-chain data/supply_chain.csv
  python scripts/build_training_data.py --rows 50000   # generate pure synthetic if no files

Output:
  data/training_data.csv  — ready to upload via Admin panel → Full Retrain

Accessorial label logic (mimics real-world detention/surcharge triggers):
  • Late delivery > 2 hrs            → detention charge  $75–$175
  • Very late (> 8 hrs)              → lumper + detention $150–$300
  • Long haul (> 900 mi) + heavy     → redelivery risk   $50–$125
  • Friday dispatch                  → weekend detention premium
  • Q4 (Oct–Dec)                     → peak surcharge
  • 30% of remaining rows get $0     → realistic ~40% incidence rate
"""

import argparse
import math
import os
import random
import sys

import numpy as np
import pandas as pd

# ── Haversine distance ─────────────────────────────────────────────────────────
def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 3958.8  # Earth radius in miles
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)) * 1.25  # road factor


# ── Accessorial charge generator ──────────────────────────────────────────────
def _generate_accessorial(row: pd.Series, rng: np.random.Generator) -> float:
    """
    Rule-based accessorial charge simulation.
    Returns a dollar amount (0 = no charge incurred).
    """
    charge = 0.0
    late_hrs  = float(row.get("late_delivery_hours", 0) or 0)
    miles     = float(row.get("miles", 500) or 500)
    weight    = float(row.get("weight_lbs", 15000) or 15000)
    dow       = int(row.get("day_of_week", 2) or 2)   # 4 = Friday
    month     = int(row.get("month", 6) or 6)

    # Detention — driver waited too long at facility
    if late_hrs > 8:
        charge += rng.uniform(150, 300)
    elif late_hrs > 2:
        charge += rng.uniform(75, 175)

    # Long haul + heavy = redelivery / lumper exposure
    if miles > 900 and weight > 12_000 and charge == 0:
        if rng.random() < 0.35:
            charge += rng.uniform(50, 125)

    # Friday dispatch premium (weekend detention risk)
    if dow == 4 and rng.random() < 0.25:
        charge += rng.uniform(40, 90)

    # Q4 peak season surcharge
    if month in (10, 11, 12) and rng.random() < 0.20:
        charge += rng.uniform(25, 75)

    return round(charge, 2)


# ── Source A: Olist ────────────────────────────────────────────────────────────
def load_olist(olist_dir: str, zip_df: pd.DataFrame | None) -> pd.DataFrame:
    print(f"  Loading Olist from {olist_dir}/ ...")

    orders = pd.read_csv(os.path.join(olist_dir, "olist_orders_dataset.csv"),
                         parse_dates=["order_purchase_timestamp",
                                      "order_estimated_delivery_date",
                                      "order_delivered_customer_date"])
    items   = pd.read_csv(os.path.join(olist_dir, "olist_order_items_dataset.csv"))
    sellers = pd.read_csv(os.path.join(olist_dir, "olist_sellers_dataset.csv"))
    custs   = pd.read_csv(os.path.join(olist_dir, "olist_customers_dataset.csv"))

    # Aggregate items per order: total freight, total quantity
    items_agg = items.groupby("order_id").agg(
        base_freight_usd=("freight_value", "sum"),
        quantity=("order_item_id", "count"),
    ).reset_index()

    # Join seller to get origin state (use first seller per order)
    order_seller = items[["order_id", "seller_id"]].drop_duplicates("order_id")
    order_seller = order_seller.merge(
        sellers[["seller_id", "seller_state"]], on="seller_id", how="left"
    )

    df = (orders
          .merge(items_agg,    on="order_id",     how="inner")
          .merge(order_seller, on="order_id",     how="left")
          .merge(custs[["customer_id", "customer_state",
                         "customer_zip_code_prefix"]],
                 on="customer_id", how="left"))

    # Compute late delivery in hours
    df["late_delivery_hours"] = (
        (df["order_delivered_customer_date"] - df["order_estimated_delivery_date"])
        .dt.total_seconds() / 3600
    ).clip(lower=0).fillna(0)

    # Estimate weight from quantity (avg parcel ~8 lbs)
    df["weight_lbs"] = (df["quantity"] * 8).clip(upper=44_000)

    # Miles: Haversine if zip lat/lng available, else random lane
    if zip_df is not None:
        zip_map = zip_df.set_index("zip")[["lat", "lng"]].to_dict("index")

        def _miles(row):
            o = zip_map.get(str(row.get("seller_zip", "")).zfill(5))
            d = zip_map.get(str(row.get("customer_zip_code_prefix", "")).zfill(5))
            if o and d:
                return _haversine(o["lat"], o["lng"], d["lat"], d["lng"])
            return random.uniform(150, 1800)

        df["miles"] = df.apply(_miles, axis=1)
    else:
        df["miles"] = np.random.uniform(150, 1800, len(df))

    df["ship_date"]    = df["order_purchase_timestamp"].dt.date
    df["day_of_week"]  = df["order_purchase_timestamp"].dt.dayofweek
    df["month"]        = df["order_purchase_timestamp"].dt.month
    df["carrier"]      = "Carrier_" + df["seller_state"].fillna("XX")
    df["facility"]     = "DC_" + df["customer_state"].fillna("XX")
    df["origin_state"] = df["seller_state"].fillna("Unknown")
    df["dest_state"]   = df["customer_state"].fillna("Unknown")
    df["shipment_id"]  = df["order_id"]

    print(f"    → {len(df):,} orders loaded from Olist")
    return df[[
        "shipment_id", "ship_date", "carrier", "facility",
        "weight_lbs", "miles", "base_freight_usd",
        "origin_state", "dest_state", "day_of_week", "month",
        "late_delivery_hours",
    ]]


# ── Source B: Supply chain / generic CSV ──────────────────────────────────────
def load_supply_chain(path: str) -> pd.DataFrame:
    print(f"  Loading supply chain data from {path} ...")
    raw = pd.read_csv(path)
    raw.columns = [c.strip().lower().replace(" ", "_").replace("-", "_")
                   for c in raw.columns]

    # Try to map columns
    col_map = {
        "carrier_name": "carrier", "carrier": "carrier",
        "shipping_mode": "appointment_type",
        "order_item_quantity": "quantity",
        "order_item_total": "base_freight_usd",
        "order_date": "ship_date",
        "order_country": "dest_state",
        "market": "origin_state",
    }
    raw = raw.rename(columns={k: v for k, v in col_map.items() if k in raw.columns})

    if "quantity" in raw.columns and "weight_lbs" not in raw.columns:
        raw["weight_lbs"] = pd.to_numeric(raw["quantity"], errors="coerce").fillna(10) * 12

    if "miles" not in raw.columns:
        raw["miles"] = np.random.uniform(200, 1500, len(raw))

    if "base_freight_usd" not in raw.columns:
        raw["base_freight_usd"] = np.random.uniform(400, 2500, len(raw))

    raw["ship_date"]   = pd.to_datetime(raw.get("ship_date", pd.Timestamp.now()), errors="coerce")
    raw["day_of_week"] = raw["ship_date"].dt.dayofweek
    raw["month"]       = raw["ship_date"].dt.month
    raw["ship_date"]   = raw["ship_date"].dt.date

    if "shipment_id" not in raw.columns:
        raw["shipment_id"] = ["SC_" + str(i) for i in range(len(raw))]
    if "facility" not in raw.columns:
        raw["facility"] = "DC_" + raw.get("dest_state", pd.Series(["Unknown"] * len(raw))).astype(str)
    if "carrier" not in raw.columns:
        raw["carrier"] = "UnknownCarrier"
    if "late_delivery_hours" not in raw.columns:
        raw["late_delivery_hours"] = 0.0

    print(f"    → {len(raw):,} rows loaded from supply chain CSV")
    return raw[[c for c in [
        "shipment_id", "ship_date", "carrier", "facility",
        "weight_lbs", "miles", "base_freight_usd",
        "origin_state", "dest_state", "day_of_week", "month",
        "late_delivery_hours",
    ] if c in raw.columns]]


# ── Synthetic fallback ─────────────────────────────────────────────────────────
_CARRIERS   = ["JB Hunt", "Werner", "Swift", "Schneider", "XPO", "Old Dominion",
               "Estes", "Saia", "ABF Freight", "Yellow", "TForce", "Ryder"]
_FACILITIES = ["Dallas DC", "Atlanta Hub", "Chicago RDC", "LA Gateway",
               "Memphis XDock", "Nashville DC", "Denver Hub", "Phoenix DC",
               "Seattle WH", "Miami DC", "Columbus RDC", "Charlotte Hub"]
_STATES     = ["TX", "CA", "IL", "FL", "OH", "GA", "NC", "AZ", "WA",
               "CO", "TN", "MN", "MO", "PA", "NY"]

def generate_synthetic(n: int, rng: np.random.Generator) -> pd.DataFrame:
    print(f"  Generating {n:,} synthetic rows ...")
    dates = pd.date_range("2022-01-01", "2024-12-31", periods=n)
    df = pd.DataFrame({
        "shipment_id":       ["SYN_" + str(i) for i in range(n)],
        "ship_date":         dates.date,
        "carrier":           rng.choice(_CARRIERS,   n),
        "facility":          rng.choice(_FACILITIES, n),
        "weight_lbs":        rng.uniform(500, 44_000, n).round(0),
        "miles":             rng.uniform(50, 2_500, n).round(0),
        "base_freight_usd":  rng.uniform(200, 4_000, n).round(2),
        "origin_state":      rng.choice(_STATES, n),
        "dest_state":        rng.choice(_STATES, n),
        "day_of_week":       pd.DatetimeIndex(dates).dayofweek,
        "month":             pd.DatetimeIndex(dates).month,
        "late_delivery_hours": np.where(
            rng.random(n) < 0.35,
            rng.exponential(scale=3.5, size=n).clip(0, 48),
            0.0
        ).round(1),
    })
    return df


# ── Main ──────────────────────────────────────────────────────────────────────
def build(olist_dir=None, supply_chain_path=None, zip_path=None,
          n_synthetic=10_000, output_path="data/training_data.csv",
          seed=42):

    rng = np.random.default_rng(seed)
    random.seed(seed)
    frames = []

    # Load zip codes for distance calc
    zip_df = None
    if zip_path and os.path.exists(zip_path):
        zip_df = pd.read_csv(zip_path, usecols=["zip", "lat", "lng"],
                             dtype={"zip": str})
        print(f"  Zip lat/lng loaded: {len(zip_df):,} zips")

    # Source A
    if olist_dir and os.path.exists(olist_dir):
        frames.append(load_olist(olist_dir, zip_df))

    # Source B
    if supply_chain_path and os.path.exists(supply_chain_path):
        frames.append(load_supply_chain(supply_chain_path))

    # Synthetic fill
    if not frames or n_synthetic > 0:
        frames.append(generate_synthetic(n_synthetic, rng))

    df = pd.concat(frames, ignore_index=True)

    # Fill missing columns
    for col, default in [("origin_state", "Unknown"), ("dest_state", "Unknown"),
                          ("late_delivery_hours", 0.0), ("day_of_week", 2),
                          ("month", 6)]:
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].fillna(default)

    df["weight_lbs"]       = pd.to_numeric(df["weight_lbs"],       errors="coerce").fillna(15_000)
    df["miles"]            = pd.to_numeric(df["miles"],            errors="coerce").fillna(500)
    df["base_freight_usd"] = pd.to_numeric(df["base_freight_usd"], errors="coerce").fillna(800)

    # Generate accessorial charges
    print(f"  Generating accessorial labels for {len(df):,} rows ...")
    df["accessorial_charge_usd"] = df.apply(
        lambda row: _generate_accessorial(row, rng), axis=1
    )

    # Stats
    incidence = (df["accessorial_charge_usd"] > 0).mean()
    avg_charge = df.loc[df["accessorial_charge_usd"] > 0, "accessorial_charge_usd"].mean()
    print(f"  Accessorial incidence: {incidence:.1%}  |  Avg charge (when > 0): ${avg_charge:.0f}")

    # Final schema
    out = df[[
        "shipment_id", "ship_date", "carrier", "facility",
        "weight_lbs", "miles", "base_freight_usd", "accessorial_charge_usd",
    ]].copy()

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    out.to_csv(output_path, index=False)
    print(f"\n  Saved {len(out):,} rows → {output_path}")
    print(f"  Ready to upload via Admin panel → Full Retrain (from CSV)")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build PACE training data from public datasets")
    parser.add_argument("--olist",        default=None,  help="Path to folder containing Olist CSV files")
    parser.add_argument("--supply-chain", default=None,  help="Path to supply chain CSV file")
    parser.add_argument("--zips",         default=None,  help="Path to US zip code lat/lng CSV (zip,lat,lng)")
    parser.add_argument("--rows",         type=int, default=10_000, help="Synthetic rows to generate (default 10000)")
    parser.add_argument("--output",       default="data/training_data.csv", help="Output CSV path")
    args = parser.parse_args()

    print("Building PACE training dataset...")
    print(f"  Olist dir:      {args.olist or '(not provided)'}")
    print(f"  Supply chain:   {args.supply_chain or '(not provided)'}")
    print(f"  Zip lat/lng:    {args.zips or '(not provided)'}")
    print(f"  Synthetic rows: {args.rows:,}")
    print()

    df = build(
        olist_dir=args.olist,
        supply_chain_path=args.supply_chain,
        zip_path=args.zips,
        n_synthetic=args.rows,
        output_path=args.output,
    )
    print("\nDone.")
