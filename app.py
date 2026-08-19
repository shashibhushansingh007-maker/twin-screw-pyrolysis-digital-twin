
import streamlit as st
import pandas as pd
import joblib

# Load trained models
oil_model = joblib.load("oil_model.pkl")
char_model = joblib.load("char_model.pkl")
gas_model = joblib.load("gas_model.pkl")

# Page title
st.title("Twin-Screw Pyrolysis Digital Twin")

st.subheader("Reactor Operating Conditions")

# Inputs
temperature = st.slider(
    "Reactor Temperature (°C)",
    400, 700, 520, 5
)

residence_time = st.slider(
    "Residence Time (s)",
    20, 120, 60, 5
)

moisture = st.slider(
    "Moisture Content (%)",
    0, 30, 10, 1
)

feed_rate = st.slider(
    "Biomass Feed Rate (kg/h)",
    5, 50, 20, 1
)

# Prediction button
if st.button("PREDICT"):

    # Prepare input in the same order used for model training
    X_new = pd.DataFrame({
        "Temperature_C": [temperature],
        "Residence_Time_s": [residence_time],
        "Moisture_pct": [moisture],
        "Feed_Rate_kg_h": [feed_rate]
    })

    # Predict yields
    oil_pred = oil_model.predict(X_new)[0]
    char_pred = char_model.predict(X_new)[0]
    gas_pred = gas_model.predict(X_new)[0]

    # Normalize to 100%
    total = oil_pred + char_pred + gas_pred

    oil_yield = oil_pred / total * 100
    char_yield = char_pred / total * 100
    gas_yield = gas_pred / total * 100

    # Dry biomass flow
    dry_biomass = feed_rate * (1 - moisture / 100)

    # Product flow rates
    oil_flow = oil_yield / 100 * dry_biomass
    char_flow = char_yield / 100 * dry_biomass
    gas_flow = gas_yield / 100 * dry_biomass

    # Display results
    st.subheader("Predicted Product Yields")

    col1, col2, col3 = st.columns(3)

    col1.metric("Bio-oil", f"{oil_yield:.2f} %")
    col2.metric("Biochar", f"{char_yield:.2f} %")
    col3.metric("Gas", f"{gas_yield:.2f} %")

    st.subheader("Product Flow Rates")

    col1, col2, col3 = st.columns(3)

    col1.metric("Bio-oil", f"{oil_flow:.2f} kg/h")
    col2.metric("Biochar", f"{char_flow:.2f} kg/h")
    col3.metric("Gas", f"{gas_flow:.2f} kg/h")

    # Mass balance
    total_product = oil_flow + char_flow + gas_flow
    mass_balance_error = dry_biomass - total_product

    st.subheader("Mass Balance")

    st.write(f"Dry biomass feed: **{dry_biomass:.2f} kg/h**")
    st.write(f"Total predicted products: **{total_product:.2f} kg/h**")
    st.write(f"Mass balance error: **{mass_balance_error:.6f} kg/h**")
