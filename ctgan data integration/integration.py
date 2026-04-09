"""
PACE Project — ctgan_input → Azure SQL ETL
==========================================
Reads the exported ctgan_input Excel file and loads data into:
  - Carrier_Safety_Profile   (one row per dot_number, latest snapshot)
  - Carrier_Inspections      (one row per dot_number + year + month)
  - Market_Conditions        (one row per year + month, deduplicated)
  - Weather_Conditions       (one row per county + year + month)
  - Reefer_Market_Rates      (one row per year + month, deduplicated)

Requirements:
    pip install pandas pymssql openpyxl sqlalchemy

Usage:
    python ctgan_to_azure_etl.py
"""
from dotenv import load_dotenv
load_dotenv()  
import os
import pandas as pd
import pymssql
from sqlalchemy import create_engine, text

# ── CONFIG ────────────────────────────────────────────────────────────────────
# Set these via environment variables or replace directly for local dev
AZURE_SERVER   = os.getenv("AZURE_SERVER",   "essql1.database.windows.net")
AZURE_DATABASE = os.getenv("AZURE_DATABASE", "ISYS43603_Spring2026_Sec02_Alice_db")
AZURE_USER     = os.getenv("AZURE_USER",     "Alice")
AZURE_PASSWORD = os.getenv("AZURE_PASSWORD", "PaceTeam2026!")

EXCEL_FILE = "ctgan_input_data_csv.xlsx"
CHUNK_SIZE = 10_000   # rows to read at a time — keeps memory manageable

# ── CONNECTION ────────────────────────────────────────────────────────────────
def get_engine():
    conn_str = (
        f"mssql+pymssql://{AZURE_USER}:{AZURE_PASSWORD}"
        f"@{AZURE_SERVER}/{AZURE_DATABASE}"
        f"?charset=utf8"
    )
    return create_engine(conn_str)


# ── CREATE TABLES IF MISSING ──────────────────────────────────────────────────
CREATE_TABLES_SQL = """
-- ── Carrier_Safety_Profile ───────────────────────────────────────────────────
IF OBJECT_ID('[dbo].[Carrier_Safety_Profile]', 'U') IS NULL
CREATE TABLE [dbo].[Carrier_Safety_Profile] (
    dot_number                      INT             NOT NULL,
    as_of_year                      SMALLINT        NOT NULL,
    as_of_month                     TINYINT         NOT NULL,
    carrier_operation               NVARCHAR(20)    NULL,
    power_units                     INT             NULL,
    truck_units                     INT             NULL,
    total_drivers                   INT             NULL,
    total_cdl                       SMALLINT        NULL,
    fleetsize_category              NVARCHAR(10)    NULL,
    recordable_crash_rate           DECIMAL(6,3)    NULL,
    hm_indicator                    NVARCHAR(5)     NULL,
    phy_state                       NCHAR(2)        NULL,
    status_code                     NVARCHAR(10)    NULL,
    mcs150_mileage                  BIGINT          NULL,
    interstate_beyond_100_miles     SMALLINT        NULL,
    intrastate_beyond_100_miles     SMALLINT        NULL,
    sms_nbr_power_unit              INT             NULL,
    sms_driver_total                INT             NULL,
    sms_authorized_for_hire         NVARCHAR(5)     NULL,
    sms_phy_state                   NCHAR(2)        NULL,
    CONSTRAINT PK_Carrier_Safety_Profile PRIMARY KEY (dot_number)
);

-- ── Carrier_Inspections ───────────────────────────────────────────────────────
IF OBJECT_ID('[dbo].[Carrier_Inspections]', 'U') IS NULL
CREATE TABLE [dbo].[Carrier_Inspections] (
    insp_id                         INT             IDENTITY(1,1) NOT NULL,
    dot_number                      INT             NOT NULL,
    insp_year                       SMALLINT        NOT NULL,
    insp_month                      TINYINT         NOT NULL,
    insp_day                        TINYINT         NULL,
    county_code_state               NVARCHAR(10)    NULL,
    insp_level_id                   TINYINT         NULL,
    driver_oos_total                SMALLINT        NULL,
    vehicle_oos_total               SMALLINT        NULL,
    oos_total                       SMALLINT        NULL,
    basic_viol                      SMALLINT        NULL,
    unsafe_viol                     SMALLINT        NULL,
    fatigued_viol                   SMALLINT        NULL,
    dr_fitness_viol                 SMALLINT        NULL,
    subt_alcohol_viol               SMALLINT        NULL,
    vh_maint_viol                   SMALLINT        NULL,
    hm_viol                         SMALLINT        NULL,
    hazmat_placard_req              NVARCHAR(10)    NULL,
    total_hazmat_sent               SMALLINT        NULL,
    hazmat_oos_total                SMALLINT        NULL,
    crash_count                     SMALLINT        NULL,
    crash_fatalities_total          TINYINT         NULL,
    crash_injuries_total            SMALLINT        NULL,
    crash_towaway_total             SMALLINT        NULL,
    crash_avg_severity              DECIMAL(8,7)    NULL,
    crash_hazmat_releases           TINYINT         NULL,
     CONSTRAINT PK_Carrier_Inspections PRIMARY KEY (insp_id)
);
-- ── Market_Conditions ─────────────────────────────────────────────────────────
IF OBJECT_ID('[dbo].[Market_Conditions]', 'U') IS NULL
CREATE TABLE [dbo].[Market_Conditions] (
    insp_year                       SMALLINT        NOT NULL,
    insp_month                      TINYINT         NOT NULL,
    eia_diesel_national             DECIMAL(4,3)    NULL,
    eia_diesel_padd1_east_coast     DECIMAL(4,3)    NULL,
    eia_diesel_padd2_midwest        DECIMAL(4,3)    NULL,
    eia_diesel_padd3_gulf_coast     DECIMAL(4,3)    NULL,
    eia_diesel_padd4_rocky_mountain DECIMAL(4,3)    NULL,
    eia_diesel_padd5_west_coast     DECIMAL(4,3)    NULL,
    eia_diesel_california           DECIMAL(4,3)    NULL,
    eia_diesel_no2_spot_ny          DECIMAL(4,3)    NULL,
    eia_steo_diesel_price_forecast  DECIMAL(8,5)    NULL,
    is_holiday                      TINYINT         NULL,
    is_near_holiday                 TINYINT         NULL,
    CONSTRAINT PK_Market_Conditions PRIMARY KEY (insp_year, insp_month)
);

-- ── Weather_Conditions ────────────────────────────────────────────────────────
IF OBJECT_ID('[dbo].[Weather_Conditions]', 'U') IS NULL
CREATE TABLE [dbo].[Weather_Conditions] (
    weather_id                      INT             IDENTITY(1,1) NOT NULL,
    county_code_state               NVARCHAR(10)    NOT NULL,
    insp_year                       SMALLINT        NOT NULL,
    insp_month                      TINYINT         NOT NULL,
    wx_avg_high_f                   DECIMAL(8,6)    NULL,
    wx_avg_low_f                    DECIMAL(8,6)    NULL,
    wx_total_precip_in              DECIMAL(4,2)    NULL,
    wx_total_snow_in                DECIMAL(3,1)    NULL,
    wx_avg_wind_mph                 DECIMAL(9,7)    NULL,
    CONSTRAINT PK_Weather_Conditions PRIMARY KEY (weather_id)
);

-- ── Reefer_Market_Rates ───────────────────────────────────────────────────────
IF OBJECT_ID('[dbo].[Reefer_Market_Rates]', 'U') IS NULL
CREATE TABLE [dbo].[Reefer_Market_Rates] (
    insp_year                       SMALLINT        NOT NULL,
    insp_month                      TINYINT         NOT NULL,
    usda_reefer_availability        DECIMAL(8,7)    NULL,
    fac_reefer_share                DECIMAL(4,3)    NULL,
    stb_avg_dwell_hours             DECIMAL(8,6)    NULL,
    fac_estab_warehousing_total     SMALLINT        NULL,
    fac_estab_493110                SMALLINT        NULL,
    fac_estab_493120                SMALLINT        NULL,
    fac_estab_484121                SMALLINT        NULL,
    fac_estab_484122                SMALLINT        NULL,
    CONSTRAINT PK_Reefer_Market_Rates PRIMARY KEY (insp_year, insp_month)
);
"""


def create_tables(engine):
    print("Creating tables if they don't exist...")
    with engine.connect() as conn:
        for stmt in CREATE_TABLES_SQL.strip().split("\n\n"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()
    print("  Tables ready.")


# ── LOAD HELPERS ──────────────────────────────────────────────────────────────
def safe_int(series):
    return pd.to_numeric(series, errors='coerce').astype('Int64')

def safe_float(series):
    return pd.to_numeric(series, errors='coerce')

def safe_str(series, length=None):
    s = series.astype(str).str.strip().replace('nan', None)
    if length:
        s = s.str[:length]
    return s


# ── LOAD CARRIER SAFETY PROFILE ───────────────────────────────────────────────
def load_carrier_safety(df, engine):
    """One row per dot_number — keep the most recent year/month snapshot."""
    cols = {
        'dot_number':                       safe_int,
        'insp_year':                        safe_int,
        'insp_month':                       safe_int,
        'carrier_carrier_operation':        lambda s: safe_str(s, 20),
        'carrier_power_units':              safe_int,
        'carrier_truck_units':              safe_int,
        'carrier_total_drivers':            safe_int,
        'carrier_total_cdl':                safe_int,
        'carrier_fleetsize':                lambda s: safe_str(s, 10),
        'carrier_recordable_crash_rate':    safe_float,
        'carrier_hm_ind':                   lambda s: safe_str(s, 5),
        'carrier_phy_state':                lambda s: safe_str(s, 2),
        'carrier_status_code':              lambda s: safe_str(s, 10),
        'carrier_mcs150_mileage':           safe_int,
        'carrier_interstate_beyond_100_miles': safe_int,
        'carrier_intrastate_beyond_100_miles': safe_int,
        'sms_nbr_power_unit':               safe_int,
        'sms_driver_total':                 safe_int,
        'sms_authorized_for_hire':          lambda s: safe_str(s, 5),
        'sms_phy_state':                    lambda s: safe_str(s, 2),
    }
    out = pd.DataFrame()
    for col, fn in cols.items():
        if col in df.columns:
            out[col] = fn(df[col])

    out = out.dropna(subset=['dot_number'])
    # Keep latest snapshot per carrier
    out = (out.sort_values(['insp_year','insp_month'], ascending=False)
              .drop_duplicates(subset=['dot_number'], keep='first'))

    out = out.rename(columns={
        'carrier_carrier_operation': 'carrier_operation',
        'carrier_power_units':       'power_units',
        'carrier_truck_units':       'truck_units',
        'carrier_total_drivers':     'total_drivers',
        'carrier_total_cdl':         'total_cdl',
        'carrier_fleetsize':         'fleetsize_category',
        'carrier_recordable_crash_rate': 'recordable_crash_rate',
        'carrier_hm_ind':            'hm_indicator',
        'carrier_phy_state':         'phy_state',
        'carrier_status_code':       'status_code',
        'carrier_mcs150_mileage':    'mcs150_mileage',
        'carrier_interstate_beyond_100_miles':  'interstate_beyond_100_miles',
        'carrier_intrastate_beyond_100_miles':  'intrastate_beyond_100_miles',
        'insp_year':                 'as_of_year',
        'insp_month':                'as_of_month',
    })
    return out


# ── LOAD CARRIER INSPECTIONS ──────────────────────────────────────────────────
def load_carrier_inspections(df):
    cols = [
        'dot_number','insp_year','insp_month','insp_day','county_code_state',
        'insp_level_id','driver_oos_total','vehicle_oos_total','oos_total',
        'basic_viol','unsafe_viol','fatigued_viol','dr_fitness_viol',
        'subt_alcohol_viol','vh_maint_viol','hm_viol','hazmat_placard_req',
        'total_hazmat_sent','hazmat_oos_total','crash_count',
        'crash_fatalities_total','crash_injuries_total','crash_towaway_total',
        'crash_avg_severity','crash_hazmat_releases',
    ]
    out = df[[c for c in cols if c in df.columns]].copy()
    int_cols = [c for c in out.columns if c not in
                ['county_code_state','hazmat_placard_req','crash_avg_severity']]
    for c in int_cols:
        out[c] = safe_int(out[c])
    out['crash_avg_severity'] = safe_float(out.get('crash_avg_severity', pd.Series()))
    out['county_code_state']  = safe_str(out.get('county_code_state', pd.Series()), 10)
    out['hazmat_placard_req'] = safe_str(out.get('hazmat_placard_req', pd.Series()), 10)
    return out.dropna(subset=['dot_number'])


# ── LOAD MARKET CONDITIONS ────────────────────────────────────────────────────
def load_market_conditions(df):
    cols = [
        'insp_year','insp_month',
        'eia_diesel_national','eia_diesel_padd1_east_coast',
        'eia_diesel_padd2_midwest','eia_diesel_padd3_gulf_coast',
        'eia_diesel_padd4_rocky_mountain','eia_diesel_padd5_west_coast',
        'eia_diesel_california','eia_diesel_no2_spot_ny',
        'eia_steo_diesel_price_forecast','is_holiday','is_near_holiday',
    ]
    out = df[[c for c in cols if c in df.columns]].copy()
    for c in out.columns:
        out[c] = pd.to_numeric(out[c], errors='coerce')
    out['insp_year']  = safe_int(out['insp_year'])
    out['insp_month'] = safe_int(out['insp_month'])
    out['is_holiday']      = safe_int(out.get('is_holiday', pd.Series()))
    out['is_near_holiday'] = safe_int(out.get('is_near_holiday', pd.Series()))
    return out.drop_duplicates(subset=['insp_year','insp_month'])


# ── LOAD WEATHER CONDITIONS ───────────────────────────────────────────────────
def load_weather_conditions(df):
    cols = [
        'county_code_state','insp_year','insp_month',
        'wx_avg_high_f','wx_avg_low_f','wx_total_precip_in',
        'wx_total_snow_in','wx_avg_wind_mph',
    ]
    out = df[[c for c in cols if c in df.columns]].copy()
    out['county_code_state'] = safe_str(out.get('county_code_state', pd.Series()), 10)
    for c in ['insp_year','insp_month']:
        out[c] = safe_int(out[c])
    for c in ['wx_avg_high_f','wx_avg_low_f','wx_total_precip_in',
              'wx_total_snow_in','wx_avg_wind_mph']:
        out[c] = safe_float(out.get(c, pd.Series()))
    return out.drop_duplicates(subset=['county_code_state','insp_year','insp_month'])


# ── LOAD REEFER MARKET RATES ──────────────────────────────────────────────────
def load_reefer_market_rates(df):
    cols = [
        'insp_year','insp_month','usda_reefer_availability','fac_reefer_share',
        'stb_avg_dwell_hours','fac_estab_warehousing_total',
        'fac_estab_493110','fac_estab_493120','fac_estab_484121','fac_estab_484122',
    ]
    out = df[[c for c in cols if c in df.columns]].copy()
    for c in out.columns:
        out[c] = pd.to_numeric(out[c], errors='coerce')
    out['insp_year']  = safe_int(out['insp_year'])
    out['insp_month'] = safe_int(out['insp_month'])
    return out.drop_duplicates(subset=['insp_year','insp_month'])


# ── UPSERT HELPER ─────────────────────────────────────────────────────────────
def upsert_table(df, table_name, pk_cols, engine, chunk_size=2000):
    """
    Write-if-not-exists upsert:
    Reads existing PKs from Azure, strips rows that already exist,
    then bulk-inserts only new rows.
    """
    if df.empty:
        print(f"  {table_name}: no data to insert.")
        return

    # Get existing PKs
    pk_select = ", ".join(pk_cols)
    existing = pd.read_sql(
        f"SELECT {pk_select} FROM [dbo].[{table_name}]", engine
    )
    if not existing.empty:
        merged = df.merge(existing, on=pk_cols, how='left', indicator=True)
        df = df[merged['_merge'] == 'left_only'].drop(columns=[], errors='ignore')

    if df.empty:
        print(f"  {table_name}: all rows already exist, skipping.")
        return

    print(f"  {table_name}: inserting {len(df):,} new rows...")
    df.to_sql(
            table_name, engine, schema='dbo',
            if_exists='append', index=False,
            chunksize=100
        )
    print(f"  {table_name}: done.")


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\nPACE ETL — ctgan_input → Azure SQL")
    print(f"File   : {EXCEL_FILE}")
    print(f"Server : {AZURE_SERVER}")
    print(f"DB     : {AZURE_DATABASE}\n")

    engine = get_engine()
    create_tables(engine)

    print(f"Reading {EXCEL_FILE} (this may take a minute)...")
    df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
    total_rows = len(df)
    print(f"  Loaded {total_rows:,} rows x {len(df.columns)} columns")

    if total_rows == 0:
        print("ERROR: File loaded but contains 0 rows. Check the Excel file.")
        return

    print(f"  Sample dot_numbers: {df['dot_number'].dropna().head(5).tolist()}\n")

    safety_frames     = []
    inspection_frames = []
    market_frames     = []
    weather_frames    = []
    reefer_frames     = []

    num_chunks = (total_rows // CHUNK_SIZE) + 1
    for i in range(num_chunks):
        chunk = df.iloc[i * CHUNK_SIZE : (i + 1) * CHUNK_SIZE]
        if chunk.empty:
            break
        print(f"  Processing chunk {i+1}/{num_chunks} ({len(chunk):,} rows)...")
        safety_frames.append(load_carrier_safety(chunk, engine))
        inspection_frames.append(load_carrier_inspections(chunk))
        market_frames.append(load_market_conditions(chunk))
        weather_frames.append(load_weather_conditions(chunk))
        reefer_frames.append(load_reefer_market_rates(chunk))

    print("\nConsolidating chunks...")

    safety_df = (pd.concat(safety_frames, ignore_index=True)
                   .sort_values(['as_of_year','as_of_month'], ascending=False)
                   .drop_duplicates(subset=['dot_number'], keep='first'))

    inspections_df = pd.concat(inspection_frames, ignore_index=True)

    market_df = (pd.concat(market_frames, ignore_index=True)
                   .drop_duplicates(subset=['insp_year','insp_month']))

    weather_df = (pd.concat(weather_frames, ignore_index=True)
                    .drop_duplicates(subset=['county_code_state','insp_year','insp_month']))

    reefer_df = (pd.concat(reefer_frames, ignore_index=True)
                   .drop_duplicates(subset=['insp_year','insp_month']))

    print(f"\nRow counts ready to load:")
    print(f"  Carrier_Safety_Profile : {len(safety_df):,}")
    print(f"  Carrier_Inspections    : {len(inspections_df):,}")
    print(f"  Market_Conditions      : {len(market_df):,}")
    print(f"  Weather_Conditions     : {len(weather_df):,}")
    print(f"  Reefer_Market_Rates    : {len(reefer_df):,}")

    print("\nWriting to Azure SQL...")
    upsert_table(safety_df,      "Carrier_Safety_Profile",  ["dot_number"],                                 engine)
    upsert_table(inspections_df, "Carrier_Inspections",     ["dot_number","insp_year","insp_month"],        engine)
    upsert_table(market_df,      "Market_Conditions",       ["insp_year","insp_month"],                     engine)
    upsert_table(weather_df,     "Weather_Conditions",      ["county_code_state","insp_year","insp_month"], engine)
    upsert_table(reefer_df,      "Reefer_Market_Rates",     ["insp_year","insp_month"],                     engine)

    print("\nETL complete.")


if __name__ == "__main__":
    main()