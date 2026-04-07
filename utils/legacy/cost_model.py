# DEPRECATED — moved to utils/legacy/ on 2026-04-02.
# No active pages import this file. Superseded by pipeline/inference.py
# (PACE FT-Transformer). Retained for reference only — do not use.
"""
utils/cost_model.py
Shared cost-estimation model loader.
Pre-warmed on the login page so page 4 loads instantly.
"""
import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline


_CAT_COLS = ["carrier", "facility"]
_NUM_COLS = ["weight_lbs", "miles"]


@st.cache_resource(show_spinner=False)
def get_cost_model(data_hash: int, _df: pd.DataFrame):
    """
    Train (or return cached) RandomForest cost estimator.
    _df is passed with underscore prefix so Streamlit skips hashing it;
    data_hash is used as the cache key instead.
    """
    X = _df[_CAT_COLS + _NUM_COLS]
    y = _df["total_cost_usd"]

    preprocessor = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), _CAT_COLS),
        ("num", "passthrough", _NUM_COLS),
    ])
    model = Pipeline([
        ("pre", preprocessor),
        ("rf",  RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)),
    ])
    model.fit(X, y)
    return model
