import io

import pandas as pd

import pytest



from app import (

    validate_shipments_df,

    CFG,

    add_target,

    score_shipments,

    train_baseline_on_synthetic,

)





def test_validate_good_df():

    df = pd.DataFrame({

        "shipment_id": ["S1"],

        "ship_date": ["2025-01-01"],

        "carrier": ["UPS"],

        "facility": ["DAL1"],

        "risk_tier": ["Low"],

        "weight_lbs": [1000],

        "miles": [100],

        "base_freight_usd": [200.0],

        "accessorial_charge_usd": [0.0],

    })



    ok, errors, _ = validate_shipments_df(df, CFG)

    assert ok

    assert errors == []





def test_validate_missing_column():

    df = pd.DataFrame({"a": [1]})

    ok, errors, _ = validate_shipments_df(df, CFG)

    assert not ok

    assert any("Missing required columns" in e for e in errors)





def test_malformed_csv_raises_parsererror():

    bad = io.StringIO('bad,csv\n"unclosed')

    with pytest.raises(Exception):

        pd.read_csv(bad)





def test_scoring_pipeline_runs():

    model = train_baseline_on_synthetic()



    df = pd.DataFrame({

        "shipment_id": ["S1"],

        "ship_date": [pd.to_datetime("2025-01-01")],

        "carrier": ["UPS"],

        "facility": ["DAL1"],

        "risk_tier": ["Low"],

        "weight_lbs": [1000],

        "miles": [100],

        "base_freight_usd": [200.0],

        "accessorial_charge_usd": [0.0],

    })



    df = add_target(df)

    scored = score_shipments(df, model)



    assert "risk_score" in scored.columns

    assert 0.0 <= float(scored["risk_score"].iloc[0]) <= 1.0