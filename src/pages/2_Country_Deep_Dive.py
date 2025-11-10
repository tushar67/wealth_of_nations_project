import os
import subprocess
import time

import country_converter as coco
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.preprocessing import MinMaxScaler

# ---------------------------------------------------------
# 🌍 PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="🏳️ Country Deep Dive", layout="wide")

st.title("🏳️ Country Deep Dive — The Wealth of Nations")
st.markdown("Explore detailed insights about a single country's economic and health trends.")

# ---------------------------------------------------------
# 📁 LOAD DATA
# ---------------------------------------------------------
@st.cache_data
def load_data():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    data_path = os.path.join(project_root, "output", "final_dataset.csv")
    if not os.path.exists(data_path):
        st.error("❌ Data file missing. Please run wealth_of_nations_analysis.py first.")
        st.stop()
    return pd.read_csv(data_path)

df = load_data()

# ---------------------------------------------------------
# 🧹 CLEAN DATA
# ---------------------------------------------------------
cc = coco.CountryConverter()

def get_region(c):
    try:
        r = cc.convert(c, to="continent")
        if r == "Oceania": return "Australia"
        if c in ["Russia", "Russian Federation"]: return "Asia"
        return r
    except: return None

if "Region" not in df.columns:
    df["Region"] = df["Country"].apply(get_region)

df["Region"] = df["Region"].apply(lambda x: x[0] if isinstance(x, list) else x)
df["Region"] = df["Region"].astype(str)
df = df[df["Region"].notna()]
df = df[~df["Region"].isin(["America", "Other", "Not Found", "None", "nan"])]

# ---------------------------------------------------------
# ⚙️ SIDEBAR
# ---------------------------------------------------------
regions = sorted(df["Region"].unique().tolist())
selected_region = st.sidebar.selectbox("🌍 Select Region", regions)
countries = sorted(df[df["Region"] == selected_region]["Country"].unique().tolist())
selected_country = st.sidebar.selectbox("🏳️ Select Country", countries)

compare_mode = st.sidebar.checkbox("🔁 Compare with another country", value=False)
compare_country = None
if compare_mode:
    all_countries = sorted(df["Country"].unique().tolist())
    compare_country = st.sidebar.selectbox("🏁 Select Comparison Country", all_countries)

country_data = df[df["Country"] == selected_country]

# ---------------------------------------------------------
# 🧭 PROGRESS SCORE FUNCTION
# ---------------------------------------------------------
def progress_score(df, global_df):
    weights = {"GDP_per_capita":0.4,"Life_Expectancy":0.3,"Health_Exp_per_Capita":0.2,"Child_Mortality":0.1}
    cols = list(weights.keys())
    scaled = MinMaxScaler((0,100)).fit_transform(global_df[cols].dropna())
    scaled_df = pd.DataFrame(scaled, columns=cols)
    v = scaled_df.iloc[-1].to_dict()
    score = (v["GDP_per_capita"]*weights["GDP_per_capita"] +
             v["Life_Expectancy"]*weights["Life_Expectancy"] +
             v["Health_Exp_per_Capita"]*weights["Health_Exp_per_Capita"] +
             (100-v["Child_Mortality"])*weights["Child_Mortality"])
    return float(score)

# ---------------------------------------------------------
# 🪄 ANIMATED GAUGE
# ---------------------------------------------------------
def animated_gauge(title, score):
    placeholder = st.empty()
    steps = 40
    for val in np.linspace(0, score, steps):
        color = "mediumseagreen" if val > 70 else "gold" if val > 50 else "lightcoral"
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=val,
            number={'suffix': " / 100"},
            title={'text': title},
            gauge={
                'axis': {'range':[0,100]},
                'bar': {'color': color},
                'steps': [
                    {'range':[0,40],'color':'mistyrose'},
                    {'range':[40,70],'color':'lightyellow'},
                    {'range':[70,100],'color':'honeydew'},
                ],
            }
        ))
        fig.update_layout(height=250, margin=dict(t=10,b=10,l=10,r=10))
        placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(0.02)

# ---------------------------------------------------------
# 🎯 DISPLAY GAUGES (Single or Compare Mode)
# ---------------------------------------------------------
st.markdown("### 🧭 National Progress Score")

if not compare_mode:
    score = progress_score(country_data, df)
    animated_gauge(f"{selected_country} — National Progress", score)

else:
    col1, col2 = st.columns(2)
    country2_data = df[df["Country"] == compare_country]

    score1 = progress_score(country_data, df)
    score2 = progress_score(country2_data, df)

    with col1:
        animated_gauge(f"{selected_country} — National Progress", score1)
    with col2:
        animated_gauge(f"{compare_country} — National Progress", score2)

    diff = score1 - score2
    better = selected_country if diff > 0 else compare_country
    st.info(f"🏁 **{better}** has a higher national progress score ({abs(diff):.1f} points difference).")

# ---------------------------------------------------------
# 📈 GDP vs Life Expectancy (Comparison Aware)
# ---------------------------------------------------------
st.markdown("### 📈 GDP vs Life Expectancy Trends")

fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=country_data["Year"], y=country_data["GDP_per_capita"],
    name=f"{selected_country} — GDP", mode="lines+markers"
))
fig2.add_trace(go.Scatter(
    x=country_data["Year"], y=country_data["Life_Expectancy"],
    name=f"{selected_country} — Life Expectancy", mode="lines+markers", yaxis="y2"
))

if compare_mode:
    country2_data = df[df["Country"] == compare_country]
    fig2.add_trace(go.Scatter(
        x=country2_data["Year"], y=country2_data["GDP_per_capita"],
        name=f"{compare_country} — GDP", mode="lines+markers"
    ))
    fig2.add_trace(go.Scatter(
        x=country2_data["Year"], y=country2_data["Life_Expectancy"],
        name=f"{compare_country} — Life Expectancy", mode="lines+markers", yaxis="y2"
    ))

fig2.update_layout(
    title=f"GDP & Life Expectancy — {selected_country}" + (f" vs {compare_country}" if compare_mode else ""),
    yaxis=dict(title="GDP per Capita"),
    yaxis2=dict(title="Life Expectancy", overlaying="y", side="right"),
)
st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# 📋 SUMMARY TABLE
# ---------------------------------------------------------
st.markdown("### 📋 Summary Data")

if not compare_mode:
    num_cols = country_data.select_dtypes(include=["int64","float64"]).columns
    st.dataframe(country_data.style.format({c:"{:,.2f}" for c in num_cols}))
else:
    latest1 = country_data.iloc[-1]
    latest2 = df[df["Country"] == compare_country].iloc[-1]
    comparison = pd.DataFrame({
        "Metric": ["GDP per Capita", "Life Expectancy", "Health Expenditure", "Child Mortality"],
        selected_country: [
            latest1["GDP_per_capita"], latest1["Life_Expectancy"], latest1["Health_Exp_per_Capita"], latest1["Child_Mortality"]
        ],
        compare_country: [
            latest2["GDP_per_capita"], latest2["Life_Expectancy"], latest2["Health_Exp_per_Capita"], latest2["Child_Mortality"]
        ],
    })
    st.dataframe(comparison.style.format("{:,.2f}"))

# ---------------------------------------------------------
# 🧭 FOOTER
# ---------------------------------------------------------
st.markdown("---")
st.markdown("<p style='text-align:center;'>🌍 Developed by <b>Tushar Sinha</b> | University of Milan 🇮🇹</p>", unsafe_allow_html=True)
