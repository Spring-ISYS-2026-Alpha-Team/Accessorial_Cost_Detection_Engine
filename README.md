# PACE — Predictive Accessorial Cost Engine

![CI](https://github.com/Spring-ISYS-2026-Alpha-Team/Accessorial_Cost_Detection_Engine/actions/workflows/ci.yml/badge.svg)

**PACE** is a decision-support tool for freight logistics teams. It ingests historical shipment data, validates it, assigns ML-based risk scores, and surfaces actionable recommendations to help prevent unexpected accessorial charges — detention fees, lumper fees, layovers — before they occur.

---

## Features

### Risk Dashboard
- KPI summary cards: total shipments, average risk score, high-risk count, estimated accessorial exposure
- Interactive charts: risk score distribution histogram and average risk by carrier
- Filterable by date range, carrier, and risk tier
- Searchable shipment table with real-time updates

### CSV Upload & Validation
- Drag-and-drop CSV ingestion with a built-in sample dataset option
- Row-level validation: required fields, date formats, numeric ranges, non-negative constraints
- Detailed error and warning reports before committing data
- One-click risk scoring on clean uploads

### Shipments Explorer
- Paginated, filterable list of all shipments (carrier, facility, risk tier)
- Per-shipment detail view with:
  - Risk score gauge and tier badge
  - Factor breakdown (carrier history, facility profile, distance, weight, freight rate)
  - Recommended actions tailored to risk tier
  - Historical comparison table for the same carrier

### Authentication
- Session-based login with auth guard on every page
- Secure logout clears all session state

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io) |
| Data Processing | pandas, NumPy |
| Visualization | Plotly |
| Database | Azure SQL (via pyodbc) |
| Config | python-dotenv |

---

## Project Structure

```
Accessorial_Cost_Detection_Engine/
├── app.py                  # Entry point — login page
├── auth_utils.py           # Session auth helpers
├── requirements.txt
├── pages/
│   ├── 1_Dashboard.py      # Risk dashboard
│   ├── 2_Upload.py         # CSV upload & scoring
│   └── 3_Shipments.py      # Shipment list + detail view
└── utils/
    ├── database.py         # Azure SQL connection utility
    ├── mock_data.py        # Synthetic data generator
    └── styling.py          # Shared CSS and theme tokens
```

---

## Setup

### Prerequisites
- Python 3.10+
- An Azure SQL (or compatible SQL Server) database
- ODBC Driver 17+ for SQL Server

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment

Create a `.env` file in the project root:

```env
DB_SERVER=your-server.database.windows.net
DB_NAME=your-database
DB_USER=your-username
DB_PASSWORD=your-password
```

### Run the app

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

---

## CSV Format

Upload historical shipment data using the following schema:

| Column | Type | Constraints |
|---|---|---|
| `shipment_id` | string | Required, unique |
| `ship_date` | date | Required, `YYYY-MM-DD` |
| `carrier` | string | Required |
| `facility` | string | Required |
| `weight_lbs` | float | Required, 0 – 200,000 |
| `miles` | float | Required, 0 – 5,000 |
| `base_freight_usd` | float | Required, ≥ 0 |
| `accessorial_charge_usd` | float | Required, ≥ 0 |

Maximum file size: **10 MB**. Only `.csv` format is accepted.

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
