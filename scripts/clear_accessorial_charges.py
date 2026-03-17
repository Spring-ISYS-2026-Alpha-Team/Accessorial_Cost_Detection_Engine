"""
scripts/clear_accessorial_charges.py

Sets accessorial_charge_usd to 0 for 34% of shipments, removing their
entries from Accessorial_Charges and zeroing AccessorialCost in Shipments.

Selection logic (smart-first):
  1. All Low risk shipments are candidates first — they are least likely
     to generate accessorial charges in the real world.
  2. If Low risk doesn't cover 34%, fill the remainder randomly from Medium risk.
  3. High risk shipments are never zeroed out (high risk → high accessorial exposure).

Run from the project root:
    python scripts/clear_accessorial_charges.py
"""

import os
import sys
import random

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import pyodbc

# ── Connection ────────────────────────────────────────────────────────────────
server   = os.getenv("DB_SERVER",   "essql1.database.windows.net")
database = os.getenv("DB_DATABASE", "ISYS43603_Spring2026_Sec02_Alice_db")
username = os.getenv("DB_USERNAME", "Alice")
password = os.getenv("DB_PASSWORD", "ISYSPass12345678!")
driver   = os.getenv("DB_DRIVER",   "ODBC Driver 18 for SQL Server")

conn_str = (
    f"DRIVER={{{driver}}};"
    f"SERVER=tcp:{server},1433;"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
)

print("Connecting to Azure SQL...")
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
print("Connected.\n")

# ── Fetch all shipment IDs with risk tier ─────────────────────────────────────
print("Fetching shipments...")
cursor.execute("""
    SELECT ShipmentId, risk_tier
    FROM Shipments
    ORDER BY ShipmentId
""")
rows = cursor.fetchall()
all_ids = [(r[0], r[1]) for r in rows]
total = len(all_ids)
target_count = round(total * 0.34)

print(f"  Total shipments : {total:,}")
print(f"  Target to zero  : {target_count:,} (34%)\n")

# ── Smart selection ───────────────────────────────────────────────────────────
random.seed(42)  # reproducible

low_ids    = [sid for sid, tier in all_ids if str(tier).strip().lower() == "low"]
medium_ids = [sid for sid, tier in all_ids if str(tier).strip().lower() == "medium"]

random.shuffle(low_ids)
random.shuffle(medium_ids)

selected = []

if len(low_ids) >= target_count:
    # Low risk alone covers the quota — take a random subset of Low
    selected = low_ids[:target_count]
    print(f"  Strategy: {len(selected):,} Low-risk shipments selected (Low pool had {len(low_ids):,})")
else:
    # Use all Low, fill remainder from Medium
    selected = low_ids[:]
    remaining = target_count - len(selected)
    medium_fill = medium_ids[:remaining]
    selected += medium_fill
    print(f"  Strategy: {len(low_ids):,} Low-risk + {len(medium_fill):,} Medium-risk selected")

print(f"  Final selection : {len(selected):,} shipments\n")

# ── Apply updates ─────────────────────────────────────────────────────────────
# Use batches of 500 to avoid parameter limits
def chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

print("Deleting rows from Accessorial_Charges...")
deleted_total = 0
for batch in chunked(selected, 500):
    placeholders = ",".join("?" * len(batch))
    cursor.execute(
        f"DELETE FROM Accessorial_Charges WHERE shipment_id IN ({placeholders})",
        batch,
    )
    deleted_total += cursor.rowcount

print(f"  Deleted {deleted_total:,} charge rows\n")

print("Zeroing AccessorialCost in Shipments...")
zeroed_total = 0
for batch in chunked(selected, 500):
    placeholders = ",".join("?" * len(batch))
    cursor.execute(
        f"UPDATE Shipments SET AccessorialCost = 0 WHERE ShipmentId IN ({placeholders})",
        batch,
    )
    zeroed_total += cursor.rowcount

print(f"  Zeroed {zeroed_total:,} shipment rows\n")

conn.commit()
conn.close()

print("Done. Reload the PACE app to see updated totals.")
print(f"  ~{100 - 34}% of shipments still have accessorial charges")
print(f"  ~34% now have $0 accessorial charges")
