
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
# CUSTOM STYLE
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #f5f1eb;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

h1, h2, h3 {
    color: #4a2919;
}

.dashboard-header {
    background: linear-gradient(
        90deg,
        #4a2919,
        #713b21
    );
    padding: 22px 28px;
    border-radius: 12px;
    color: white;
    margin-bottom: 20px;
}

.dashboard-title {
    font-size: 30px;
    font-weight: 700;
}

.dashboard-subtitle {
    font-size: 15px;
    opacity: 0.85;
}

.status-box {
    background-color: #e7f1df;
    color: #355d2a;
    padding: 10px 16px;
    border-radius: 10px;
    font-weight: 600;
    margin-bottom: 18px;
}

.kpi-card {
    background-color: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e5ddd4;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.kpi-title {
    color: #806b5d;
    font-size: 14px;
}

.kpi-value {
    color: #4a2919;
    font-size: 27px;
    font-weight: 700;
}

.kpi-sub {
    color: #8a6b55;
    font-size: 14px;
}

.section-title {
    color: #4a2919;
    font-size: 20px;
    font-weight: 700;
    border-left: 5px solid #c66b2c;
    padding-left: 10px;
    margin-top: 20px;
    margin-bottom: 12px;
}

.flow-box {
    background-color: #fffaf5;
    border: 1px solid #e3d7ca;
    border-radius: 12px;
    padding: 18px;
    text-align: center;
    font-weight: 600;
    color: #4a2919;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# LOAD MODELS
# =========================================================

oil_model = joblib.load("oil_model.pkl")
char_model = joblib.load("char_model.pkl")
gas_model = joblib.load("gas_model.pkl")


# =========================================================
# PREDICTION FUNCTION
# =========================================================

def predict_yields(
    temperature,
    residence_time,
    moisture,
    feed_rate
):

    X = pd.DataFrame({
        "Temperature_C": [temperature],
        "Residence_Time_s": [residence_time],
        "Moisture_pct": [moisture],
        "Feed_Rate_kg_h": [feed_rate]
    })

    oil_raw = oil_model.predict(X)[0]
    char_raw = char_model.predict(X)[0]
    gas_raw = gas_model.predict(X)[0]

    # Normalize predicted yields
    total = oil_raw + char_raw + gas_raw

    oil_yield = oil_raw / total * 100
    char_yield = char_raw / total * 100
    gas_yield = gas_raw / total * 100

    # Dry biomass
    dry_feed = feed_rate * (1 - moisture / 100)

    # Product flows
    oil_flow = dry_feed * oil_yield / 100
    char_flow = dry_feed * char_yield / 100
    gas_flow = dry_feed * gas_yield / 100

    total_products = oil_flow + char_flow + gas_flow

    mass_error = dry_feed - total_products

    return {
        "oil_yield": oil_yield,
        "char_yield": char_yield,
        "gas_yield": gas_yield,
        "oil_flow": oil_flow,
        "char_flow": char_flow,
        "gas_flow": gas_flow,
        "dry_feed": dry_feed,
        "total_products": total_products,
        "mass_error": mass_error
    }


# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="dashboard-header">

<div class="dashboard-title">
Twin-Screw Auger Pyrolysis Digital Twin
</div>

<div class="dashboard-subtitle">
AI-based prediction of bio-oil, biochar and gas production
</div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown("## Reactor & Feed")

st.sidebar.markdown("### Feed")

feed_rate = st.sidebar.slider(
    "Biomass Feed Rate (kg/h)",
    min_value=5,
    max_value=50,
    value=20,
    step=1
)

moisture = st.sidebar.slider(
    "Moisture Content (%)",
    min_value=0,
    max_value=30,
    value=10,
    step=1
)

st.sidebar.markdown("### Reactor")

temperature = st.sidebar.slider(
    "Reactor Temperature (°C)",
    min_value=400,
    max_value=700,
    value=520,
    step=5
)

residence_time = st.sidebar.slider(
    "Residence Time (s)",
    min_value=20,
    max_value=120,
    value=60,
    step=5
)

st.sidebar.markdown("---")

run_prediction = st.sidebar.button(
    "RUN PREDICTION",
    type="primary",
    use_container_width=True
)


# =========================================================
# SESSION STATE
# =========================================================

if "prediction" not in st.session_state:

    st.session_state.prediction = predict_yields(
        temperature,
        residence_time,
        moisture,
        feed_rate
    )

    st.session_state.inputs = {
        "temperature": temperature,
        "residence_time": residence_time,
        "moisture": moisture,
        "feed_rate": feed_rate
    }


if run_prediction:

    st.session_state.prediction = predict_yields(
        temperature,
        residence_time,
        moisture,
        feed_rate
    )

    st.session_state.inputs = {
        "temperature": temperature,
        "residence_time": residence_time,
        "moisture": moisture,
        "feed_rate": feed_rate
    }


result = st.session_state.prediction
inputs = st.session_state.inputs


# =========================================================
# STATUS
# =========================================================

if abs(result["mass_error"]) < 1e-6:

    st.markdown(
        """
        <div class="status-box">
        ● Stable operating calculation &nbsp; | &nbsp;
        Mass balance closed
        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.warning("Mass balance requires attention.")


# =========================================================
# CURRENT OPERATING CONDITION
# =========================================================

st.markdown(
    '<div class="section-title">Current Operating Condition</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Temperature",
    f"{inputs['temperature']} °C"
)

c2.metric(
    "Residence Time",
    f"{inputs['residence_time']} s"
)

c3.metric(
    "Moisture",
    f"{inputs['moisture']} %"
)

c4.metric(
    "Biomass Feed",
    f"{inputs['feed_rate']} kg/h"
)


# =========================================================
# PRODUCT KPI CARDS
# =========================================================

st.markdown(
    '<div class="section-title">Predicted Product Performance</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)


with c1:

    st.markdown(
        f"""
        <div class="kpi-card">
        <div class="kpi-title">BIO-OIL</div>
        <div class="kpi-value">{result['oil_flow']:.2f} kg/h</div>
        <div class="kpi-sub">
        Yield: {result['oil_yield']:.2f} %
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with c2:

    st.markdown(
        f"""
        <div class="kpi-card">
        <div class="kpi-title">BIOCHAR</div>
        <div class="kpi-value">{result['char_flow']:.2f} kg/h</div>
        <div class="kpi-sub">
        Yield: {result['char_yield']:.2f} %
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with c3:

    st.markdown(
        f"""
        <div class="kpi-card">
        <div class="kpi-title">GAS</div>
        <div class="kpi-value">{result['gas_flow']:.2f} kg/h</div>
        <div class="kpi-sub">
        Yield: {result['gas_yield']:.2f} %
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with c4:

    st.markdown(
        f"""
        <div class="kpi-card">
        <div class="kpi-title">DRY BIOMASS</div>
        <div class="kpi-value">{result['dry_feed']:.2f} kg/h</div>
        <div class="kpi-sub">
        Wet feed: {inputs['feed_rate']:.0f} kg/h
        </div>
        </div>
        """,
        unsafe_allow_html=True
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

    st.markdown(
        '<div class="section-title">Process Flow</div>',
        unsafe_allow_html=True
    )

    f1, f2, f3, f4, f5 = st.columns([1, 0.3, 1.2, 0.3, 1])

    with f1:
        st.markdown(
            '<div class="flow-box">BIOMASS<br>FEED</div>',
            unsafe_allow_html=True
        )

    with f2:
        st.markdown("### →")

    with f3:
        st.markdown(
            '<div class="flow-box">TWIN-SCREW<br>PYROLYSIS REACTOR</div>',
            unsafe_allow_html=True
        )

    with f4:
        st.markdown("### →")

    with f5:
        st.markdown(
            '<div class="flow-box">PRODUCT<br>SEPARATION</div>',
            unsafe_allow_html=True
        )


    st.markdown(
        '<div class="section-title">Product Distribution</div>',
        unsafe_allow_html=True
    )

    fig = go.Figure(
        data=[
            go.Pie(
                labels=[
                    "Bio-oil",
                    "Biochar",
                    "Gas"
                ],
                values=[
                    result["oil_yield"],
                    result["char_yield"],
                    result["gas_yield"]
                ],
                hole=0.50
            )
        ]
    )

    fig.update_layout(
        height=430,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


    st.markdown(
        '<div class="section-title">Mass Balance</div>',
        unsafe_allow_html=True
    )

    m1, m2, m3 = st.columns(3)

    m1.metric(
        "Dry Biomass Input",
        f"{result['dry_feed']:.2f} kg/h"
    )

    m2.metric(
        "Total Products",
        f"{result['total_products']:.2f} kg/h"
    )

    m3.metric(
        "Mass Balance Error",
        f"{result['mass_error']:.6f} kg/h"
    )


# =========================================================
# TAB 2 — LIVE TRENDS
# =========================================================

with tab2:

    st.markdown(
        '<div class="section-title">Yield vs Temperature</div>',
        unsafe_allow_html=True
    )

    temperatures = list(range(400, 701, 10))

    oil_values = []
    char_values = []
    gas_values = []

    for T in temperatures:

        r = predict_yields(
            T,
            inputs["residence_time"],
            inputs["moisture"],
            inputs["feed_rate"]
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

    # Current operating point

    fig_temp.add_trace(
        go.Scatter(
            x=[inputs["temperature"]],
            y=[result["oil_yield"]],
            mode="markers",
            name="Current condition",
            marker=dict(size=12)
        )
    )

    fig_temp.update_layout(
        xaxis_title="Temperature (°C)",
        yaxis_title="Yield (%)",
        height=450,
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_temp,
        use_container_width=True
    )


    st.markdown(
        '<div class="section-title">Yield vs Residence Time</div>',
        unsafe_allow_html=True
    )

    times = list(range(20, 121, 5))

    oil_values = []
    char_values = []
    gas_values = []

    for t in times:

        r = predict_yields(
            inputs["temperature"],
            t,
            inputs["moisture"],
            inputs["feed_rate"]
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

    fig_time.add_trace(
        go.Scatter(
            x=[inputs["residence_time"]],
            y=[result["oil_yield"]],
            mode="markers",
            name="Current condition",
            marker=dict(size=12)
        )
    )

    fig_time.update_layout(
        xaxis_title="Residence Time (s)",
        yaxis_title="Yield (%)",
        height=450,
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_time,
        use_container_width=True
    )


# =========================================================
# TAB 3 — MODEL INSIGHT
# =========================================================

with tab3:

    st.markdown(
        '<div class="section-title">Model Feature Importance</div>',
        unsafe_allow_html=True
    )

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
        "Feature importance describes how strongly each input "
        "contributed to the trained Random Forest predictions. "
        "It should not be interpreted as proof of physical causality."
    )


# =========================================================
# TAB 4 — OPERATING ENVELOPE
# =========================================================

with tab4:

    st.markdown(
        '<div class="section-title">Bio-oil Yield Operating Envelope</div>',
        unsafe_allow_html=True
    )

    envelope_temperatures = list(
        range(400, 701, 20)
    )

    envelope_times = list(
        range(20, 121, 10)
    )

    z = []

    for t in envelope_times:

        row = []

        for T in envelope_temperatures:

            r = predict_yields(
                T,
                t,
                inputs["moisture"],
                inputs["feed_rate"]
            )

            row.append(
                r["oil_yield"]
            )

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


    # Current operating point

    fig_heat.add_trace(

        go.Scatter(

            x=[inputs["temperature"]],

            y=[inputs["residence_time"]],

            mode="markers",

            marker=dict(
                size=14,
                symbol="x"
            ),

            name="Current condition"
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
        "Moisture and biomass feed rate are held at the "
        "currently selected values."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Twin-Screw Auger Pyrolysis Digital Twin | V0.6.1 | "
    "Engineering prototype"
)
