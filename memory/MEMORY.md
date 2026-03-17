# PACE Project Memory

## Project Overview
Streamlit analytics app for shipping companies (PACE — Predictive Accessorial Cost Engine).
University of Arkansas ISYS 43603 Spring 2026 project.
Branch: TConn

## Tech Stack
- Streamlit frontend (multi-page app, pages/ folder)
- Azure SQL database via pyodbc
- pandas, plotly, scikit-learn
- python-dotenv for local credentials

## Azure Database
- Server: essql1.database.windows.net
- Database: ISYS43603_Spring2026_Sec02_Alice_db
- Credentials stored in .env (git-ignored)
- DB open to all IPs (school setup)

## Key Tables & Real Column Names
- **Shipments**: ShipmentId, ShipDate, OriginRegion, DestRegion, CarrierId, FacilityType, AppointmentType, DistanceMiles, Revenue, LinehaulCost, AccessorialFlag, AccessorialCost, weight_lbs, risk_score, risk_tier
- **Accessorial_Charges**: charge_id, shipment_id, charge_type, amount, risk_flag, invoice_date, disputed, dispute_resolved, notes
- **Carriers**: carrier_id, carrier_name, dot_number, mc_number, safety_rating, fleet_size, home_state
- **Facilities**: facility_id, facility_name, city, state, zip_code, avg_dwell_time_hrs, appointment_required, facility_type, dock_hours_open, dock_hours_close

## Database Layer (utils/database.py)
Functions:
- `get_connection()` — cached pyodbc connection, reads from .env or st.secrets
- `get_shipments(_conn)` — returns shipments joined with carrier_name, plus computed columns
- `get_accessorial_charges(_conn)` — raw accessorial charge rows
- `get_shipments_with_charges(_conn)` — Accessorial_Charges joined to Shipments+Carriers (for Accessorial Tracker page)
- `get_carriers(_conn)`, `get_facilities(_conn)`

### Computed columns added in get_shipments():
- total_cost_usd = base_freight_usd + accessorial_charge_usd
- cost_per_mile = base_freight_usd / miles
- lane = OriginRegion + " → " + DestRegion
- origin_city = OriginRegion, destination_city = DestRegion

### Column aliases in get_shipments() SQL:
- ShipmentId → shipment_id, ShipDate → ship_date, FacilityType → facility
- DistanceMiles → miles, LinehaulCost → base_freight_usd, AccessorialCost → accessorial_charge_usd

## Data Pattern (all pages)
All pages use live DB with mock fallback:
```python
conn = get_connection()
df = get_shipments(conn) if conn is not None else pd.DataFrame()
if df.empty:
    df = generate_mock_shipments(300)
    st.info("Live database unavailable — showing demo data.", icon="ℹ️")
```

## Pages
- app.py — login (no auth backend, just sets session_state)
- 0_Home.py — operations overview KPIs
- 1_Dashboard.py — risk dashboard with charts
- 2_Upload.py — CSV upload page
- 3_Shipments.py — shipment list + detail view
- 4_Cost_Estimate.py — ML cost prediction (Random Forest)
- 5_Route_Analysis.py — lane/route analysis
- 6_Carrier_Comparison.py — carrier metrics comparison
- 7_Accessorial_Tracker.py — accessorial charge breakdown (uses get_shipments_with_charges)

## Team Setup
- Each teammate creates their own .env from .env.example (git-ignored)
- For Streamlit Cloud: paste secrets into share.streamlit.io → Settings → Secrets
- .streamlit/secrets.toml.example shows the format

## Mock Data
- utils/mock_data.py — generate_mock_shipments(n) for fallback
- Has columns: accessorial_type (not in real DB Shipments table — only in Accessorial_Charges)
