
import streamlit as st
import pandas as pd
import joblib
import plotly.graph_objects as go

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Twin-Screw Pyrolysis Digital Twin",
    page_icon="🔥",
    layout="wide"
)

# =========================================================
# LOAD MODELS
# =========================================================

oil_model = joblib.load("oil_model.pkl")
char_model = joblib.load("char_model.pkl")
gas_model = joblib.load("gas_model.pkl")


# =========================================================
# FUNCTIONS
# =========================================================

def predict_yields(temperature, residence_time, moisture, feed_rate):

    X = pd.DataFrame({
        "Temperature_C": [temperature],
        "Residence_Time_s": [residence_time],
        "Moisture_pct": [moisture],
        "Feed_Rate_kg_h": [feed_rate]
    })

    oil_raw = oil_model.predict(X)[0]
    char_raw = char_model.predict(X)[0]
    gas_raw = gas_model.predict(X)[0]

    total = oil_raw + char_raw + gas_raw

    oil = oil_raw / total * 100
    char = char_raw / total * 100
    gas = gas_raw / total * 100

    dry_feed = feed_rate * (1 - moisture / 100)

    oil_flow = oil / 100 * dry_feed
    char_flow = char / 100 * dry_feed
    gas_flow = gas / 100 * dry_feed

    total_product = oil_flow + char_flow + gas_flow

    mass_error = dry_feed - total_product

    return {
        "oil_yield": oil,
        "char_yield": char,
        "gas_yield": gas,
        "oil_flow": oil_flow,
        "char_flow": char_flow,
        "gas_flow": gas_flow,
        "dry_feed": dry_feed,
        "total_product": total_product,
        "mass_error": mass_error
    }


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <h1 style="margin-bottom:0;">
    Twin-Screw Pyrolysis Digital Twin
    </h1>
    <p style="color:#777;">
    AI-based prediction of bio-oil, biochar and gas yields
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()


# =========================================================
# SIDEBAR INPUTS
# =========================================================

st.sidebar.header("Reactor & Feed")

temperature = st.sidebar.slider(
    "Reactor Temperature (°C)",
    400, 700, 520, 5
)

residence_time = st.sidebar.slider(
    "Residence Time (s)",
    20, 120, 60, 5
)

moisture = st.sidebar.slider(
    "Moisture Content (%)",
    0, 30, 10, 1
)

feed_rate = st.sidebar.slider(
    "Biomass Feed Rate (kg/h)",
    5, 50, 20, 1
)

predict_button = st.sidebar.button(
    "RUN PREDICTION",
    type="primary",
    use_container_width=True
)


# =========================================================
# RUN PREDICTION
# =========================================================

result = predict_yields(
    temperature,
    residence_time,
    moisture,
    feed_rate
)


# =========================================================
# STATUS
# =========================================================

if abs(result["mass_error"]) < 1e-6:
    st.success("● Stable calculation | Mass balance closed")
else:
    st.warning("● Check mass balance")


# =========================================================
# KPI CARDS
# =========================================================

st.subheader("Current Prediction")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Bio-oil",
    f"{result['oil_flow']:.2f} kg/h",
    f"{result['oil_yield']:.2f}%"
)

c2.metric(
    "Biochar",
    f"{result['char_flow']:.2f} kg/h",
    f"{result['char_yield']:.2f}%"
)

c3.metric(
    "Gas",
    f"{result['gas_flow']:.2f} kg/h",
    f"{result['gas_yield']:.2f}%"
)

c4.metric(
    "Dry Biomass",
    f"{result['dry_feed']:.2f} kg/h",
    f"Feed = {feed_rate:.0f} kg/h"
)


# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "Process Overview",
    "Live Trends",
    "Model Insight",
    "Operating Envelope"
])


# =========================================================
# TAB 1 — PROCESS OVERVIEW
# =========================================================

with tab1:

    st.subheader("Product Distribution")

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Bio-oil", "Biochar", "Gas"],
                values=[
                    result["oil_yield"],
                    result["char_yield"],
                    result["gas_yield"]
                ],
                hole=0.45
            )
        ]
    )

    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=30, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Mass Balance")

    m1, m2, m3 = st.columns(3)

    m1.metric(
        "Dry Biomass",
        f"{result['dry_feed']:.2f} kg/h"
    )

    m2.metric(
        "Total Products",
        f"{result['total_product']:.2f} kg/h"
    )

    m3.metric(
        "Mass Balance Error",
        f"{result['mass_error']:.6f} kg/h"
    )


# =========================================================
# TAB 2 — LIVE TRENDS
# =========================================================

with tab2:

    st.subheader("Predicted Yield vs Temperature")

    temperatures = list(range(400, 701, 10))

    oil_values = []
    char_values = []
    gas_values = []

    for T in temperatures:

        r = predict_yields(
            T,
            residence_time,
            moisture,
            feed_rate
        )

        oil_values.append(r["oil_yield"])
        char_values.append(r["char_yield"])
        gas_values.append(r["gas_yield"])

    fig_temp = go.Figure()

    fig_temp.add_trace(
        go.Scatter(
            x=temperatures,
            y=oil_values,
            mode="lines",
            name="Bio-oil"
        )
    )

    fig_temp.add_trace(
        go.Scatter(
            x=temperatures,
            y=char_values,
            mode="lines",
            name="Biochar"
        )
    )

    fig_temp.add_trace(
        go.Scatter(
            x=temperatures,
            y=gas_values,
            mode="lines",
            name="Gas"
        )
    )

    fig_temp.update_layout(
        xaxis_title="Temperature (°C)",
        yaxis_title="Yield (%)",
        height=450
    )

    st.plotly_chart(
        fig_temp,
        use_container_width=True
    )


    st.subheader("Predicted Yield vs Residence Time")

    times = list(range(20, 121, 5))

    oil_values = []
    char_values = []
    gas_values = []

    for t in times:

        r = predict_yields(
            temperature,
            t,
            moisture,
            feed_rate
        )

        oil_values.append(r["oil_yield"])
        char_values.append(r["char_yield"])
        gas_values.append(r["gas_yield"])

    fig_time = go.Figure()

    fig_time.add_trace(
        go.Scatter(
            x=times,
            y=oil_values,
            mode="lines",
            name="Bio-oil"
        )
    )

    fig_time.add_trace(
        go.Scatter(
            x=times,
            y=char_values,
            mode="lines",
            name="Biochar"
        )
    )

    fig_time.add_trace(
        go.Scatter(
            x=times,
            y=gas_values,
            mode="lines",
            name="Gas"
        )
    )

    fig_time.update_layout(
        xaxis_title="Residence Time (s)",
        yaxis_title="Yield (%)",
        height=450
    )

    st.plotly_chart(
        fig_time,
        use_container_width=True
    )


# =========================================================
# TAB 3 — MODEL INSIGHT
# =========================================================

with tab3:

    st.subheader("Model Feature Importance")

    features = [
        "Temperature",
        "Residence Time",
        "Moisture",
        "Feed Rate"
    ]

    importance_df = pd.DataFrame({
        "Input": features,
        "Importance": (
            oil_model.feature_importances_
            + char_model.feature_importances_
            + gas_model.feature_importances_
        ) / 3
    })

    importance_df = importance_df.sort_values(
        "Importance",
        ascending=True
    )

    fig_imp = go.Figure(
        go.Bar(
            x=importance_df["Importance"],
            y=importance_df["Input"],
            orientation="h"
        )
    )

    fig_imp.update_layout(
        xaxis_title="Average Feature Importance",
        yaxis_title="",
        height=400
    )

    st.plotly_chart(
        fig_imp,
        use_container_width=True
    )

    st.info(
        "Feature importance indicates how strongly each input "
        "contributed to the predictions of the trained Random Forest models. "
        "It does not by itself establish physical causality."
    )


# =========================================================
# TAB 4 — OPERATING ENVELOPE
# =========================================================

with tab4:

    st.subheader("Bio-oil Yield Operating Envelope")

    envelope_temperatures = list(range(400, 701, 20))
    envelope_times = list(range(20, 121, 10))

    z = []

    for t in envelope_times:

        row = []

        for T in envelope_temperatures:

            r = predict_yields(
                T,
                t,
                moisture,
                feed_rate
            )

            row.append(r["oil_yield"])

        z.append(row)

    fig_heat = go.Figure(
        data=go.Heatmap(
            x=envelope_temperatures,
            y=envelope_times,
            z=z,
            colorbar=dict(
                title="Oil Yield (%)"
            )
        )
    )

    fig_heat.update_layout(
        xaxis_title="Temperature (°C)",
        yaxis_title="Residence Time (s)",
        height=500
    )

    st.plotly_chart(
        fig_heat,
        use_container_width=True
    )

    st.caption(
        "Envelope is generated from the trained model while "
        "moisture and feed rate are held at the selected values."
    )
