# PACE — Predictive Accessorial Cost Engine

![CI](https://github.com/Spring-ISYS-2026-Alpha-Team/Accessorial_Cost_Detection_Engine/actions/workflows/ci.yml/badge.svg)

**PACE** PACE is a decision-support tool for freight logistics teams. It ingests historical shipment data, validates it, assigns ML-based risk scores, and surfaces actionable recommendations to help prevent unexpected accessorial charges — detention fees, lumper fees, layovers — before they occur.
Accessorial charges are not random. They are the downstream result of identifiable, repeatable operational patterns — carriers that consistently run late, facilities that routinely cause delays, or lane combinations that carry elevated risk. The problem is that without a system to surface these patterns at the right time, logistics teams are forced to operate reactively, absorbing costs that were, in hindsight, entirely predictable. PACE shifts that point of insight from invoice reconciliation to pre-dispatch decision-making.
The system ingests and validates historical shipment records, engineers the features necessary for machine learning, and trains a classification model that outputs calibrated probability scores — not binary flags, but a quantified likelihood that a given shipment will incur a specific charge. Those scores are surfaced through an operational dashboard alongside actionable recommendations: swap carriers, adjust appointment windows, apply pricing buffers, or flag loads for additional attention before they're executed.
The goal of PACE is not to eliminate accessorial charges entirely — some are unavoidable. The goal is to give logistics teams the right information at the moment they can still act on it, so that avoidable costs are avoided and unavoidable ones are anticipated and priced correctly.

---

## Changelog — TConn Branch (March 2026)

### Bug Fixes
- **Resolved all merge conflicts** across `app.py`, `utils/database.py`, `utils/styling.py`, `pages/1_Dashboard.py`, `pages/4_Cost_Estimate.py`, `pages/5_Route_Analysis.py`, `pages/6_Carrier_Comparison.py`, `pages/7_Accessorial_Tracker.py` — conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) baked into committed files caused `SyntaxError` on startup
- **Fixed `ImportError`** — `verify_pace_user` was referenced in `app.py` but missing from `utils/database.py`; function added with SHA-256 password hashing against the `PaceUsers` Azure SQL table
- **Fixed admin routing crash** — `pages/8_Admin.py` was missing after the merge conflict cleanup; page recreated and admin routing restored in `app.py`
- **Fixed login Enter key** — moved `if submitted:` inside the `st.form()` block so pressing Enter in the password field correctly submits
- **Fixed ship date display** — detail view was showing `2026-02-17 00:00:00`; now trimmed to `2026-02-17`

### UI / Theme Fixes
- **Metric cards** — were using light-theme CSS (`background: #FFFFFF`, text `#111827`); updated to dark glass style matching the rest of the app (`rgba(12,6,30,0.82)` background, purple border, lavender labels, white values)
- **Shipment detail view** — multiple hardcoded near-black text colors (`#374151`, `#1F2937`, `#111827`) were invisible on the dark background; fixed throughout: breadcrumb, factor names, factor percentages, recommended action text, accessorial exposure label
- **`utils/styling.py` full rewrite** — 8 merge conflict zones removed; dark glass theme consolidated with color tokens (`ACCENT_PURPLE`, `ACCENT_SOFT`, `TEXT_PRIMARY`, `TEXT_SECONDARY`, `CHART_BG`), `chart_theme()` helper function, and correct dark CSS for all components

### Performance
- **Loading screen speed** — removed unnecessary `time.sleep(0.3)` before progress completion; reduced post-load pause from `0.7s → 0.15s` and error-path pause from `1.0s → 0.3s`; eliminates the 6–7 second wait on "Everything ready"
- **Loading screen errors** — exception handler now surfaces the actual error message (`⚠ Loaded with warnings — {e}`) instead of silently swallowing it

### New Features
- **Admin panel (`pages/8_Admin.py`)** — recreated with full dark glass theme; connected to live `PaceUsers` Azure SQL table; supports creating users (SHA-256 hashed passwords), viewing all current users, and deleting users (cannot delete yourself)
- **DB admin helpers** — added `get_pace_users()`, `create_pace_user()`, `delete_pace_user()` to `utils/database.py`
- **Sort buttons on Accessorial Tracker charts** — `_popup_carrier_acc` and `_popup_facility` expand dialogs now have Value ↑ / Value ↓ / A-Z sort controls; `_popup_trend` retains time-range buttons (1M/3M/6M/1Y/All)

---

## Features

### Home
- KPI summary cards: total shipments, average risk score, high-risk count, estimated accessorial exposure
- 4 interactive charts with expand-to-full-screen dialogs: weekly shipment trend, cost per mile by carrier, risk distribution, accessorial exposure over time
- Filterable by date range and carrier

### Risk Dashboard
- KPI row with delta comparisons against the full unfiltered dataset
- Risk score distribution histogram and average risk score by carrier (sortable)
- Risk tier breakdown with per-tier accessorial exposure totals
- Searchable shipment table

### Multi-Format Upload & Validation
- Accepts `.csv`, `.xlsx`, `.xls`, `.pdf`, `.png`, `.jpg`, `.jpeg` — max 10 MB
- Flexible column normalization: 20+ common column name aliases auto-mapped to PACE schema
- AI-assisted extraction for PDFs and images via Ollama (local LLM, no cloud required)
- Row-level validation: required fields, date formats, numeric ranges, non-negative constraints
- Detailed error and warning reports before committing data
- One-click risk scoring on clean uploads
- Built-in sample dataset for demo/testing

### Shipments Explorer
- Paginated, filterable list of all shipments (carrier, facility, risk tier)
- Click any row for a per-shipment detail view with:
  - Risk score gauge and tier badge
  - Factor breakdown (carrier history, facility profile, distance, weight, freight rate)
  - Recommended actions tailored to risk tier
  - Historical comparison table for the same carrier

### Cost Estimator
- Random Forest ML model trained on historical shipment data
- Predicts total shipment cost from carrier, facility, weight, and miles
- 95% confidence interval using tree ensemble spread
- Comparison against average cost/mile estimate and fleet average
- Feature importance chart and historical cost distribution

### Route Analysis
- Lane-level cost and risk metrics
- Charts: cost per mile by lane, risk by route, mileage distribution, scatter of miles vs cost

### Carrier Comparison
- Side-by-side carrier performance: cost per mile, high-risk shipment count, accessorial rate, radar chart
- Expand dialogs with sort controls

### Accessorial Tracker
- Accessorial charge trends over time (time-range filterable)
- Donut chart by charge type, carrier breakdown, facility breakdown
- All expand dialogs include sort or range controls

### Admin Panel
- Role-gated (admin only)
- **User management:** view, create (SHA-256 hashed passwords), and delete users from Azure SQL
- **Model management:** live AUC/F1/Accuracy cards, mode toggle (demo vs. production)
- **Risk tier thresholds:** adjustable sliders with data-suggested recommendations (Youden's J)
- **Manual training:** incremental update (continues from current model) or full retrain from scratch
- **Version history:** last 3 model versions with metrics, one-click rollback
- **Auto-update:** configurable threshold — model updates automatically as new shipment records accumulate

### Authentication
- Session-based login with auth guard on every page
- SHA-256 password hashing against Azure SQL `PaceUsers` table
- Fallback hardcoded accounts if DB is unreachable
- Secure logout clears all session state
- Loading screen pre-warms all DB caches and ML model after login

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io) 1.5+ |
| Data Processing | pandas, NumPy |
| Visualization | Plotly |
| ML | LightGBM (risk classifier), scikit-learn (cost estimator) |
| Document Parsing | pdfplumber, pytesseract, Pillow, Ollama (optional AI enrichment) |
| Database | Azure SQL (via pyodbc) |
| Auth | SHA-256 hashing, Streamlit session state |
| Config | python-dotenv / Streamlit secrets |

---

## Project Structure

```
Accessorial_Cost_Detection_Engine/
├── app.py                      # Entry point — login page
├── auth_utils.py               # Session auth helpers
├── requirements.txt
├── assets/
│   ├── background.png          # Network globe background image
│   └── logo.png                # PACE truck-on-globe logo
├── pages/
│   ├── loading.py              # Post-login cache pre-warm screen
│   ├── 0_Home.py               # Home KPIs + 4 charts
│   ├── 1_Dashboard.py          # Risk dashboard
│   ├── 2_Upload.py             # Multi-format upload & scoring
│   ├── 3_Shipments.py          # Shipment list + detail view
│   ├── 4_Cost_Estimate.py      # ML cost predictor
│   ├── 5_Route_Analysis.py     # Lane/route metrics
│   ├── 6_Carrier_Comparison.py # Carrier benchmarking
│   ├── 7_Accessorial_Tracker.py# Accessorial charge analysis
│   └── 8_Admin.py              # Admin panel (role-gated)
└── utils/
    ├── database.py             # Azure SQL connection + all query functions
    ├── mock_data.py            # Synthetic data generator (fallback)
    ├── cost_model.py           # Random Forest cost estimator
    ├── risk_model.py           # LightGBM risk classifier + versioning
    ├── model_config.py         # Model metadata, thresholds, auto-update settings
    ├── doc_parser.py           # Multi-format document parser (CSV/Excel/PDF/image)
    ├── geo.py                  # Geospatial routing (driving distance)
    └── styling.py              # Dark glass theme CSS, color tokens, nav
```

---

## Setup

### 1. Prerequisites

- **Python 3.10+**
- **Git**
- An **Azure SQL** (or compatible SQL Server) database with ODBC Driver 17+
  - *The app runs in demo mode with mock data if no DB is configured — no Azure account required to explore the app*

### 2. Clone the repo

```bash
git clone https://github.com/Spring-ISYS-2026-Alpha-Team/Accessorial_Cost_Detection_Engine.git
cd Accessorial_Cost_Detection_Engine
```

### 3. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment

Create a `.env` file in the project root (copy the example below):

```env
DB_SERVER=your-server.database.windows.net
DB_NAME=your-database
DB_USER=your-username
DB_PASSWORD=your-password
```

> **No database?** Leave the `.env` file empty or skip this step entirely. PACE will run in demo mode using generated mock data — all pages are fully functional.

### 6. Run the app

```bash
streamlit run app.py
```

If `streamlit` is not on your PATH (common on Windows), use:

```bash
python -m streamlit run app.py
```

The app opens at **http://localhost:8501**.

**Default login credentials:**
| Username | Password | Role |
|---|---|---|
| `admin` | `admin` | Admin |
| `user` | `user` | User |

---

## Optional: PDF & Image Upload Support

PDF and image uploads require two additional installs:

### pdfplumber (PDF text extraction)

```bash
pip install pdfplumber
```

### Tesseract OCR (image text extraction)

1. Download and install Tesseract:
   - **Windows:** [UB-Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki) — install to `C:\Program Files\Tesseract-OCR`
   - **macOS:** `brew install tesseract`
   - **Linux:** `sudo apt install tesseract-ocr`

2. Add Tesseract to your PATH (Windows only):
   ```
   setx PATH "%PATH%;C:\Program Files\Tesseract-OCR"
   ```
   Then restart your terminal.

### Ollama (AI field extraction for unstructured PDFs/images)

Ollama enables PACE to extract shipment fields from freeform documents using a local LLM — no cloud API key required.

1. Download and install Ollama: https://ollama.com/download
2. Start the Ollama server:
   ```bash
   ollama serve
   ```
3. Pull the model (one-time, ~2 GB):
   ```bash
   ollama pull llama3.2
   ```

> **Without Ollama:** CSV and standard Excel uploads work fully. PDFs and images with non-standard layouts will show a clear error message explaining what's needed.

---

## Upload Format

PACE accepts **`.csv`, `.xlsx`, `.xls`, `.pdf`, `.png`, `.jpg`, `.jpeg`** — max **10 MB**.

Column names are **automatically normalized** — you don't need to match the exact schema. Common variations are recognized:

| PACE Column | Also recognized as |
|---|---|
| `shipment_id` | `load_id`, `order_id`, `shipment_number`, `id` |
| `ship_date` | `date`, `pickup_date`, `shipment_date` |
| `carrier` | `carrier_name`, `trucking_company`, `provider` |
| `facility` | `warehouse`, `location`, `dc`, `distribution_center` |
| `weight_lbs` | `weight`, `lbs`, `shipment_weight` |
| `miles` | `distance`, `distance_miles`, `route_miles` |
| `base_freight_usd` | `freight_cost`, `base_rate`, `freight`, `base_cost` |
| `accessorial_charge_usd` | `accessorial_cost`, `extra_charges`, `accessorials` |

**Required columns** (must be present, non-empty): `shipment_id`, `carrier`, `facility`

**Constraints:**
- `weight_lbs`: 0 – 200,000
- `miles`: 0 – 5,000
- `base_freight_usd`, `accessorial_charge_usd`: ≥ 0
- `ship_date`: any recognizable date format (normalized to `YYYY-MM-DD`)

---

## Edge Cases & Known Limitations

See [EDGE_CASES.md](EDGE_CASES.md) for a full catalog of handled edge cases, validation rules, and known system limitations.

---

## Contributing

1. Branch from `main`: `git checkout -b feature/your-description`
2. Make changes and test locally with `streamlit run app.py`
3. Open a pull request — use the PR template and link any relevant issues

---

## Team

**Team Alpha — University of Arkansas, ISYS 43603**

| Name | Role |
|---|---|
| Clayton Josef | Scrum Master |
| Tyler Connolly | Product Owner |
| Bui Vu | Developer |
| Anna Diggs | Developer |
| Kirsten Capangpangan | Developer |

---

*Academic project — Spring 2026*
