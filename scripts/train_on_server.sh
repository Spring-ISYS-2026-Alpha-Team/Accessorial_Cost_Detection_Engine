#!/usr/bin/env bash
# =============================================================
# PACE: Full training pipeline — run this on the university server
#
# Steps:
#   1. Pull latest code from git
#   2. Install / verify dependencies
#   3. Run CTGAN (trains on Teradata, writes ctgan_synthetic)
#   4. Create the pace_training_v view
#   5. Run FT-Transformer (trains on the view, saves weights)
#
# Usage (from repo root on aimlsrv):
#   chmod +x scripts/train_on_server.sh
#   nohup bash scripts/train_on_server.sh > ctgan_log.txt 2>&1 &
#
# Prerequisites:
#   - .env file in repo root with TD_HOST, TD_USERNAME, TD_PASSWORD
#   - Python 3.10+ with requirements installed
#   - teradatasql, ctgan, torch installed (see scripts/requirements_pipeline.txt)
# =============================================================

set -e  # Exit immediately on any error

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "============================================================"
echo "PACE Training Pipeline — $(date)"
echo "Working directory: $REPO_DIR"
echo "============================================================"

# ── 1. Pull latest code ──────────────────────────────────────
echo ""
echo "[1/5] Pulling latest code..."
git pull origin main

# ── 2. Verify dependencies ──────────────────────────────────
echo ""
echo "[2/5] Checking dependencies..."
python3 -c "import ctgan; import torch; import teradatasql; import pandas; print('  All dependencies OK')"

# ── 3. CTGAN training ────────────────────────────────────────
echo ""
echo "[3/5] Running CTGAN training pipeline..."
echo "  This trains on Teradata and writes 3M synthetic rows back."
echo "  Expected time: 4-8 hours depending on GPU availability."
echo ""
python3 -m pipeline.ctgan_train

# ── 4. Create Teradata view ──────────────────────────────────
echo ""
echo "[4/5] Creating pace_training_v view in Teradata..."

# Load credentials from .env
export $(grep -v '^#' .env | grep -E '^TD_' | xargs)

python3 - <<'PYEOF'
import os
import teradatasql

host     = os.environ["TD_HOST"]
user     = os.environ["TD_USERNAME"]
password = os.environ["TD_PASSWORD"]
database = os.environ["TD_DATABASE"]

with open("scripts/create_teradata_view.sql") as f:
    sql = f.read()

conn   = teradatasql.connect(host=host, user=user, password=password, database=database)
cursor = conn.cursor()

# Execute each statement separately (BTEQ-style split on semicolons)
statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
for stmt in statements:
    try:
        cursor.execute(stmt)
        print(f"  OK: {stmt[:60]}...")
    except Exception as e:
        # DROP VIEW errors are expected if view doesn't exist yet
        if "not found" in str(e).lower() or "does not exist" in str(e).lower():
            print(f"  Skipped (not found): {stmt[:60]}")
        else:
            raise

conn.close()
print("  pace_training_v view created successfully.")
PYEOF

# ── 5. Transformer training ──────────────────────────────────
echo ""
echo "[5/5] Running FT-Transformer training pipeline..."
echo "  Reads from pace_training_v, trains model, saves weights."
echo "  Expected time: 2-6 hours depending on GPU."
echo ""
python3 -m pipeline.pace_transformer

echo ""
echo "============================================================"
echo "Training complete! — $(date)"
echo ""
echo "Output files:"
echo "  models/pace_transformer_weights.pt"
echo "  models/artifacts.pkl"
echo "  outputs/predictions.csv"
echo "  outputs/confusion_matrix.png"
echo ""
echo "Next step: run scripts/deploy_weights.py to transfer"
echo "the weights to your Streamlit environment."
echo "============================================================"
