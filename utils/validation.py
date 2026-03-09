import pandas as pd


def validate_data(df: pd.DataFrame) -> list[str]:
    """
    Validate a shipment DataFrame before upload or processing.
    Returns a list of error strings (empty list = valid).
    """
    errors = []

    required_cols = [
        "ship_date",
        "carrier",
        "facility",
        "risk_tier",
        "total_cost",
    ]

    # Missing columns
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing column: {col}")

    # Null values
    for col in required_cols:
        if col in df.columns and df[col].isnull().any():
            errors.append(f"Column '{col}' contains NULL values")

    # Numeric type check
    if "total_cost" in df.columns:
        if not pd.api.types.is_numeric_dtype(df["total_cost"]):
            errors.append("'total_cost' must be numeric")
        elif (df["total_cost"] < 0).any():
            errors.append("'total_cost' cannot be negative")

    return errors
