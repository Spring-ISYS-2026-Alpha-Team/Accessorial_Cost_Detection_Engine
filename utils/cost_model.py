"""

utils/cost_model.py

Load pre-trained cost model from disk instead of training in-app.

"""



import streamlit as st

import joblib

import os



# Path to trained model

MODEL_PATH = os.path.join(

    os.path.dirname(os.path.dirname(__file__)),

    "models",

    "rf_accessorial_model.joblib"

)



@st.cache_resource(show_spinner=False)

def get_cost_model():

    """

    Load and cache the pre-trained cost model.

    """

    if not os.path.exists(MODEL_PATH):

        raise FileNotFoundError(f"Cost model not found at {MODEL_PATH}")



    model = joblib.load(MODEL_PATH)

    return model