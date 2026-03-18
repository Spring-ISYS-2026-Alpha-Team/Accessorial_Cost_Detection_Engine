-- =============================================================
-- PACE: Create pace_training_v on Teradata
-- Run this once on the university server after ctgan_train.py
-- has populated the ctgan_synthetic table.
--
-- Usage:
--   bteq < scripts/create_teradata_view.sql
--   OR paste into Teradata Studio / TDGSS
-- =============================================================

-- Drop existing view if present
DROP VIEW CTGAN.pace_training_v;

-- Create the training view on the synthetic table.
-- pace_transformer.py reads from this view.
--
-- accessorial_risk_score: weighted sum of OOS + violation counts.
--   Normalisation (/ 100.0) keeps values in [0, ~100] range.
-- accessorial_type: maps the dominant violation class to an integer
--   0 = No Charge
--   1 = Detention        (driver OOS dominant)
--   2 = Safety Surcharge (unsafe / basic viol dominant)
--   3 = Compliance Fee   (dr_fitness / fatigued dominant)
--   4 = Hazmat Fee       (hm_viol / hazmat_placard_req dominant)
--   5 = High Risk / Multiple (high overall OOS or multiple types)

CREATE VIEW CTGAN.pace_training_v AS
SELECT
    -- ── Identity ──────────────────────────────────────────────────
    unique_id,
    dot_number,
    insp_year,

    -- ── All feature columns (pass-through) ────────────────────────
    report_state,
    county_code_state,
    insp_level_id,
    time_weight,
    oos_total,
    driver_oos_total,
    vehicle_oos_total,
    hazmat_oos_total,
    total_hazmat_sent,
    basic_viol,
    unsafe_viol,
    fatigued_viol,
    dr_fitness_viol,
    subt_alcohol_viol,
    vh_maint_viol,
    hm_viol,
    hazmat_placard_req,
    unit_type_desc,
    unit_make,
    unit_license_state,
    insp_month,
    insp_dow,
    insp_day,
    is_holiday,
    is_near_holiday,

    -- Carrier profile
    carrier_carrier_operation,
    carrier_total_drivers,
    carrier_power_units,
    carrier_truck_units,
    carrier_fleetsize,
    carrier_mcs150_mileage,
    carrier_mcs150_mileage_year,
    carrier_hm_ind,
    carrier_phy_state,
    carrier_phy_country,
    carrier_interstate_beyond_100_miles,
    carrier_interstate_within_100_miles,
    carrier_intrastate_beyond_100_miles,
    carrier_intrastate_within_100_miles,
    carrier_total_cdl,
    carrier_total_intrastate_drivers,
    carrier_crgo_genfreight,
    carrier_crgo_household,
    carrier_crgo_produce,
    carrier_crgo_coldfood,
    carrier_crgo_beverages,
    carrier_crgo_meat,
    carrier_crgo_chem,
    carrier_crgo_drybulk,
    carrier_crgo_construct,
    carrier_crgo_intermodal,
    carrier_crgo_oilfield,
    carrier_recordable_crash_rate,
    carrier_safety_rating,
    carrier_status_code,
    carrier_add_date,

    -- SMS
    sms_carrier_operation,
    sms_hm_flag,
    sms_pc_flag,
    sms_phy_state,
    sms_phy_country,
    sms_nbr_power_unit,
    sms_driver_total,
    sms_recent_mileage,
    sms_recent_mileage_year,
    sms_private_only,
    sms_authorized_for_hire,
    sms_exempt_for_hire,
    sms_private_property,

    -- Crash history
    crash_count,
    crash_fatalities_total,
    crash_injuries_total,
    crash_towaway_total,
    crash_avg_severity,
    crash_hazmat_releases,

    -- EIA energy
    eia_diesel_national,
    eia_diesel_padd1_east_coast,
    eia_diesel_padd2_midwest,
    eia_diesel_padd3_gulf_coast,
    eia_diesel_padd4_rocky_mountain,
    eia_diesel_padd5_west_coast,
    eia_diesel_california,
    eia_gasoline_national,
    eia_crude_wti_spot,
    eia_crude_brent_spot,
    eia_diesel_no2_spot_ny,
    eia_jet_fuel_spot_ny,
    eia_heating_oil_spot_ny,
    eia_distillate_stocks_us,
    eia_distillate_supplied_us,
    eia_distillate_stocks_padd1,
    eia_distillate_stocks_padd2,
    eia_distillate_stocks_padd3,
    eia_refinery_utilization_us,
    eia_crude_inputs_to_refineries,
    eia_steo_diesel_price_forecast,
    eia_steo_wti_price_forecast,
    eia_steo_gasoline_retail_forecast,
    eia_steo_liquid_fuels_consumption,
    eia_natgas_henry_hub_spot,
    eia_natgas_industrial_price,
    eia_natgas_commercial_price,

    -- FRED economic
    fred_TSIFRGHT,
    fred_PCU484121484121,
    fred_PCU4841248412,
    fred_AMTMVS,
    fred_INDPRO,
    fred_GASDESW,
    fred_FRGEXPUSM649NCIS,
    fred_FRGSHPUSM649NCIS,
    fred_PCU4841224841221,
    fred_TRUCKD11,
    fred_CES4348400001,
    fred_CES4349300001,
    fred_RAILFRTINTERMODAL,
    fred_WPU057303,
    fred_WPU3012,
    fred_CES4300000001,
    fred_CES4348100001,

    -- Weather
    wx_avg_high_f,
    wx_avg_low_f,
    wx_total_precip_in,
    wx_total_snow_in,
    wx_avg_wind_mph,

    -- Facility density
    fac_estab_311612,
    fac_estab_311991,
    fac_estab_311999,
    fac_estab_312111,
    fac_estab_312120,
    fac_estab_424410,
    fac_estab_424420,
    fac_estab_424430,
    fac_estab_424450,
    fac_estab_424460,
    fac_estab_424480,
    fac_estab_424490,
    fac_estab_484110,
    fac_estab_484121,
    fac_estab_484122,
    fac_estab_484220,
    fac_estab_484230,
    fac_estab_493110,
    fac_estab_493120,
    fac_estab_493130,
    fac_estab_493190,
    fac_estab_warehousing_total,
    fac_reefer_share,

    -- Market/logistics
    usda_reefer_availability,
    stb_avg_dwell_hours,

    -- ── Computed target: regression ───────────────────────────────
    -- Weighted sum of risk-relevant violations, scaled 0-100
    CAST(
        LEAST(100.0,
            (oos_total            * 15.0) +
            (driver_oos_total     * 10.0) +
            (vehicle_oos_total    * 10.0) +
            (basic_viol           *  8.0) +
            (unsafe_viol          *  8.0) +
            (vh_maint_viol        *  7.0) +
            (fatigued_viol        *  7.0) +
            (dr_fitness_viol      *  6.0) +
            (subt_alcohol_viol    *  6.0) +
            (hm_viol              *  5.0) +
            (crash_count          *  8.0) +
            (crash_avg_severity   *  6.0) +
            (crash_fatalities_total * 4.0) +
            (crash_injuries_total *  3.0) +
            (crash_towaway_total  *  2.0)
        ) AS FLOAT
    ) AS accessorial_risk_score,

    -- ── Computed target: multiclass ───────────────────────────────
    -- 0=No Charge, 1=Detention, 2=Safety Surcharge,
    -- 3=Compliance Fee, 4=Hazmat Fee, 5=High Risk/Multiple
    CASE
        WHEN (oos_total * 15.0 + driver_oos_total * 10.0 +
              vehicle_oos_total * 10.0 + basic_viol * 8.0 +
              unsafe_viol * 8.0 + vh_maint_viol * 7.0 +
              fatigued_viol * 7.0 + dr_fitness_viol * 6.0 +
              subt_alcohol_viol * 6.0 + hm_viol * 5.0 +
              crash_count * 8.0) >= 80
            THEN 5  -- High Risk / Multiple
        WHEN hm_viol > 0 OR CAST(hazmat_placard_req AS INTEGER) > 0
            THEN 4  -- Hazmat Fee
        WHEN dr_fitness_viol > 0 OR fatigued_viol > 0
            THEN 3  -- Compliance Fee
        WHEN unsafe_viol > 0 OR basic_viol > 0 OR vh_maint_viol > 0
            THEN 2  -- Safety Surcharge
        WHEN driver_oos_total > 0
            THEN 1  -- Detention
        ELSE 0      -- No Charge
    END AS accessorial_type

FROM CTGAN.ctgan_synthetic;
