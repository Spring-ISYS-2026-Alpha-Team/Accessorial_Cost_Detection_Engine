"""
pipeline/config.py
Shared constants for PACE model training and inference.
Imported by pipeline/inference.py and pace_transformer.py.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Targets ───────────────────────────────────────────────────────────────────
N_CLASSES = 6
CHARGE_TYPE_LABELS = [
    "No Charge",
    "Detention",
    "Safety Surcharge",
    "Compliance Fee",
    "Hazmat Fee",
    "High Risk / Multiple",
]

# ── Column identifiers ────────────────────────────────────────────────────────
DOT_COLUMN = "dot_number"

# ── Model paths ───────────────────────────────────────────────────────────────
MODEL_WEIGHTS_PATH  = os.path.join("models", "pace_transformer.pt")
ARTIFACTS_PATH      = os.path.join("models", "artifacts.pkl")

# ── Teradata credentials ──────────────────────────────────────────────────────
TD_HOST     = os.environ.get("TD_HOST",     "")
TD_USERNAME = os.environ.get("TD_USERNAME", "")
TD_PASSWORD = os.environ.get("TD_PASSWORD", "")
TD_DATABASE = os.environ.get("TD_DATABASE", "")

# ── Feature columns (must match pace_transformer.py exactly) ──────────────────
CATEGORICAL_COLUMNS = [
    "report_state", "county_code_state", "insp_level_id",
    "carrier_status_code", "carrier_carrier_operation", "carrier_fleetsize",
    "carrier_hm_ind", "carrier_phy_country", "carrier_phy_state",
    "carrier_safety_rating",
    "carrier_crgo_genfreight", "carrier_crgo_household", "carrier_crgo_produce",
    "carrier_crgo_intermodal", "carrier_crgo_oilfield", "carrier_crgo_meat",
    "carrier_crgo_chem", "carrier_crgo_drybulk", "carrier_crgo_coldfood",
    "carrier_crgo_beverages", "carrier_crgo_construct",
    "sms_carrier_operation", "sms_hm_flag", "sms_pc_flag",
    "sms_phy_state", "sms_phy_country",
    "sms_private_only", "sms_authorized_for_hire",
    "sms_exempt_for_hire", "sms_private_property",
    "hazmat_placard_req", "unit_type_desc", "unit_make", "unit_license_state",
]

CONTINUOUS_COLUMNS = [
    "insp_year", "insp_month", "insp_dow", "insp_day",
    "is_holiday", "is_near_holiday", "time_weight", "carrier_add_date",
    "carrier_mcs150_mileage", "carrier_mcs150_mileage_year",
    "carrier_truck_units", "carrier_power_units",
    "carrier_recordable_crash_rate", "carrier_total_intrastate_drivers",
    "carrier_interstate_beyond_100_miles", "carrier_interstate_within_100_miles",
    "carrier_intrastate_beyond_100_miles", "carrier_intrastate_within_100_miles",
    "carrier_total_cdl", "carrier_total_drivers",
    "sms_nbr_power_unit", "sms_driver_total",
    "sms_recent_mileage", "sms_recent_mileage_year",
    "oos_total", "driver_oos_total", "vehicle_oos_total",
    "hazmat_oos_total", "total_hazmat_sent",
    "basic_viol", "unsafe_viol", "fatigued_viol", "dr_fitness_viol",
    "subt_alcohol_viol", "vh_maint_viol", "hm_viol",
    "crash_count", "crash_fatalities_total", "crash_injuries_total",
    "crash_towaway_total", "crash_avg_severity", "crash_hazmat_releases",
    "eia_diesel_national", "eia_diesel_padd1_east_coast",
    "eia_diesel_padd2_midwest", "eia_diesel_padd3_gulf_coast",
    "eia_diesel_padd4_rocky_mountain", "eia_diesel_padd5_west_coast",
    "eia_diesel_california", "eia_gasoline_national",
    "eia_crude_wti_spot", "eia_crude_brent_spot",
    "eia_diesel_no2_spot_ny", "eia_jet_fuel_spot_ny",
    "eia_heating_oil_spot_ny", "eia_distillate_stocks_us",
    "eia_distillate_supplied_us", "eia_distillate_stocks_padd1",
    "eia_distillate_stocks_padd2", "eia_distillate_stocks_padd3",
    "eia_refinery_utilization_us", "eia_crude_inputs_to_refineries",
    "eia_steo_diesel_price_forecast", "eia_steo_wti_price_forecast",
    "eia_steo_gasoline_retail_forecast", "eia_steo_liquid_fuels_consumption",
    "eia_natgas_henry_hub_spot", "eia_natgas_industrial_price",
    "eia_natgas_commercial_price",
    "fred_TSIFRGHT", "fred_PCU484121484121", "fred_PCU4841248412",
    "fred_AMTMVS", "fred_INDPRO", "fred_GASDESW",
    "fred_FRGEXPUSM649NCIS", "fred_FRGSHPUSM649NCIS",
    "fred_PCU4841224841221", "fred_TRUCKD11",
    "fred_CES4348400001", "fred_CES4349300001",
    "fred_RAILFRTINTERMODAL", "fred_WPU057303", "fred_WPU3012",
    "fred_CES4300000001", "fred_CES4348100001",
    "wx_avg_high_f", "wx_avg_low_f", "wx_total_precip_in",
    "wx_total_snow_in", "wx_avg_wind_mph",
    "fac_estab_311612", "fac_estab_311991", "fac_estab_311999",
    "fac_estab_312111", "fac_estab_312120",
    "fac_estab_424410", "fac_estab_424420", "fac_estab_424430",
    "fac_estab_424450", "fac_estab_424460",
    "fac_estab_424480", "fac_estab_424490",
    "fac_estab_484110", "fac_estab_484121", "fac_estab_484122",
    "fac_estab_484220", "fac_estab_484230",
    "fac_estab_493110", "fac_estab_493120",
    "fac_estab_493130", "fac_estab_493190",
    "fac_estab_warehousing_total",
    "fac_reefer_share", "usda_reefer_availability", "stb_avg_dwell_hours",
]
