import joblib

model = joblib.load("models/rf_accessorial_model.joblib")
print("TYPE:", type(model))

if isinstance(model, dict):
    print("DICT KEYS:", model.keys())
    if "model" in model:
        model = model["model"]
        print("INNER TYPE:", type(model))

if hasattr(model, "feature_names_in_"):
    print("feature_names_in_ =", list(model.feature_names_in_))

if hasattr(model, "n_features_in_"):
    print("n_features_in_ =", model.n_features_in_)