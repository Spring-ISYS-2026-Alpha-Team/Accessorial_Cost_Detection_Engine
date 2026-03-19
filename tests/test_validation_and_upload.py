import io
import pandas as pd
import pytest

from pipeline.data_pipeline import (
    normalize_column_names,
    validate_dataframe,
    detect_schema,
)
from utils.column_mapper import find_unrecognized_columns, PACE_TARGET_COLS


# ── normalize_column_names ────────────────────────────────────────────────────

def test_normalize_alias_mapping():
    df = pd.DataFrame({"DOT": [12345], "crashes": [1], "oos": [0]})
    df_norm, mapping = normalize_column_names(df)
    assert "dot_number" in df_norm.columns
    assert "crash_count" in df_norm.columns
    assert "oos_total" in df_norm.columns


def test_normalize_preserves_already_canonical():
    df = pd.DataFrame({"dot_number": [123], "crash_count": [0]})
    df_norm, mapping = normalize_column_names(df)
    assert list(df_norm.columns) == ["dot_number", "crash_count"]
    assert mapping == {}


# ── detect_schema ─────────────────────────────────────────────────────────────

def test_detect_schema_pace():
    df = pd.DataFrame({
        "dot_number": [123],
        "carrier_status_code": ["A"],
        "carrier_carrier_operation": ["H"],
        "carrier_power_units": [10],
        "carrier_total_drivers": [5],
        "oos_total": [0],
        "driver_oos_total": [0],
        "vehicle_oos_total": [0],
        "basic_viol": [0],
        "unsafe_viol": [0],
        "vh_maint_viol": [0],
        "crash_count": [0],
        "crash_avg_severity": [0.0],
    })
    assert detect_schema(df) in ("pace", "pace_aliased")


def test_detect_schema_legacy():
    df = pd.DataFrame({
        "carrier": ["UPS"],
        "weight_lbs": [1000],
        "miles": [100],
    })
    assert detect_schema(df) == "legacy"


def test_detect_schema_unknown():
    df = pd.DataFrame({"col_a": [1], "col_b": [2]})
    assert detect_schema(df) == "unknown"


# ── validate_dataframe ────────────────────────────────────────────────────────

def test_validate_empty_df():
    errors, warnings, mask = validate_dataframe(pd.DataFrame(), schema="pace")
    assert len(errors) > 0
    assert "no data" in errors[0].lower()


def test_validate_invalid_dot_number():
    df = pd.DataFrame({
        "dot_number": ["not_a_number"],
        "carrier_status_code": ["A"],
        "carrier_carrier_operation": ["H"],
        "carrier_power_units": [10],
        "carrier_total_drivers": [5],
        "oos_total": [0],
        "driver_oos_total": [0],
        "vehicle_oos_total": [0],
        "basic_viol": [0],
        "unsafe_viol": [0],
        "vh_maint_viol": [0],
        "crash_count": [0],
        "crash_avg_severity": [0.0],
    })
    errors, warnings, mask = validate_dataframe(df, schema="pace")
    assert any("dot" in e.lower() for e in errors)


# ── find_unrecognized_columns ─────────────────────────────────────────────────

def test_find_unrecognized_returns_unknown_cols():
    df = pd.DataFrame({"dot_number": [123], "invoice_ref": ["INV001"]})
    unrecognized = find_unrecognized_columns(df)
    assert "invoice_ref" in unrecognized
    assert "dot_number" not in unrecognized


def test_find_unrecognized_alias_cols_not_returned():
    # "crashes" aliases to crash_count — should not appear as unrecognized
    df = pd.DataFrame({"crashes": [1], "oos": [0]})
    unrecognized = find_unrecognized_columns(df)
    assert "crashes" not in unrecognized
    assert "oos" not in unrecognized


def test_find_unrecognized_all_known():
    df = pd.DataFrame({"dot_number": [123], "crash_count": [0], "oos_total": [1]})
    assert find_unrecognized_columns(df) == []


# ── PACE_TARGET_COLS ──────────────────────────────────────────────────────────

def test_pace_target_cols_not_empty():
    assert len(PACE_TARGET_COLS) > 100


def test_pace_target_cols_no_duplicates():
    assert len(PACE_TARGET_COLS) == len(set(PACE_TARGET_COLS))


def test_pace_target_cols_contains_key_fields():
    for col in ("dot_number", "crash_count", "oos_total", "carrier_power_units"):
        assert col in PACE_TARGET_COLS


# ── malformed CSV ─────────────────────────────────────────────────────────────

def test_malformed_csv_raises():
    bad = io.StringIO('bad,csv\n"unclosed')
    with pytest.raises(Exception):
        pd.read_csv(bad)
