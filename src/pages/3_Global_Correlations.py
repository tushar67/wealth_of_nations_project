import os
import tempfile

import country_converter as coco
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from gtts import gTTS  # 🎤 Text-to-Speech
from scipy.stats import pearsonr

# ---------------------------------------------------------
# 🌍 PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="📊 Global Correlations", layout="wide")

st.title("📊 Global Correlations — The Wealth of Nations")
st.markdown("""
Explore the relationships between key economic and health indicators across the world.  
Use filters to analyze trends by region, year, or globally.  
Now featuring **🎤 AI Narration** for insights!
""")

# ---------------------------------------------------------
# 📁 LOAD DATA
# ---------------------------------------------------------
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.abspath(os.path.join(base_dir, "..", "..", "output", "final_dataset.csv"))
    st.caption(f"📂 Looking for data at: {data_path}")

    if not os.path.exists(data_path):
        st.error("❌ Data file not found. Please run 'wealth_of_nations_analysis.py' first.")
        st.stop()

    df = pd.read_csv(data_path)
    cc = coco.CountryConverter()

    def get_region(country):
        try:
            region = cc.convert(country, to='continent')
            if region == "Oceania": return "Australia"
            if country in ["Russia", "Russian Federation"]: return "Asia"
            return region
        except:
            return None

    if "Region" not in df.columns:
        df["Region"] = df["Country"].apply(get_region)

    df["Region"] = df["Region"].apply(lambda x: x[0] if isinstance(x, list) else x)
    df = df[df["Region"].notna()]
    df = df[~df["Region"].isin(["America", "Not Found", "Other"])]

    num_cols = ["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


df = load_data()
st.success("✅ Data loaded successfully!")

# ---------------------------------------------------------
# ⚙️ SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.header("🔍 Filters")

years = sorted(df["Year"].unique())
selected_year = st.sidebar.selectbox("📅 Select Year", years, index=len(years) - 1)

df["Region"] = df["Region"].astype(str)
regions = ["All"] + sorted(df["Region"].unique())
selected_region = st.sidebar.selectbox("🌍 Select Region", regions)

x_metric = st.sidebar.selectbox(
    "X-axis Metric",
    ["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"],
    index=0,
)
y_metric = st.sidebar.selectbox(
    "Y-axis Metric",
    ["Life_Expectancy", "Child_Mortality", "Health_Exp_per_Capita", "GDP_per_capita"],
    index=1,
)

# ---------------------------------------------------------
# 🔎 FILTER & CLEAN DATA
# ---------------------------------------------------------
filtered = df[df["Year"] == selected_year]
if selected_region != "All":
    filtered = filtered[filtered["Region"] == selected_region]

filtered = filtered.dropna(subset=[x_metric, y_metric])
filtered["Health_Exp_per_Capita"] = filtered["Health_Exp_per_Capita"].fillna(1)

# ---------------------------------------------------------
# 📈 CORRELATION ANALYSIS
# ---------------------------------------------------------
if not filtered.empty:
    corr, _ = pearsonr(filtered[x_metric], filtered[y_metric])
    st.metric(label="📈 Pearson Correlation", value=f"{corr:.2f}")
else:
    st.warning("⚠️ No data available for the selected filters.")
    st.stop()

# ---------------------------------------------------------
# 🟢 SCATTER PLOT
# ---------------------------------------------------------
fig = px.scatter(
    filtered,
    x=x_metric,
    y=y_metric,
    color="Region",
    hover_name="Country",
    size=filtered["Health_Exp_per_Capita"].replace({0: np.nan}).fillna(1),
    size_max=25,
    trendline="ols",
    title=f"{x_metric.replace('_', ' ')} vs {y_metric.replace('_', ' ')} ({selected_year})",
)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# 📋 DATA SUMMARY
# ---------------------------------------------------------
st.subheader("📋 Data Summary")
st.dataframe(
    filtered[["Country", "Region", "Year", x_metric, y_metric]]
    .sort_values(by=x_metric, ascending=False)
    .style.format({x_metric: "{:,.2f}", y_metric: "{:,.2f}"})
)

# ---------------------------------------------------------
# 🧠 AI NARRATIVE INSIGHT
# ---------------------------------------------------------
st.subheader("🧠 AI Correlation Insight")

def generate_ai_insight(region, year, x_metric, y_metric, corr):
    x_name = x_metric.replace("_", " ").title()
    y_name = y_metric.replace("_", " ").title()
    abs_corr = abs(corr)

    # Correlation strength
    if abs_corr >= 0.7:
        strength = "a strong relationship"
    elif abs_corr >= 0.4:
        strength = "a moderate connection"
    else:
        strength = "a weak correlation"

    # Direction
    if corr > 0:
        direction = f"As {x_name} increases, {y_name} tends to rise."
    else:
        direction = f"As {x_name} increases, {y_name} tends to decrease."

    # Context
    if "Child_Mortality" in [x_metric, y_metric] and corr < 0:
        context = "This typically reflects how rising income and better healthcare reduce child mortality rates."
    elif "Life_Expectancy" in [x_metric, y_metric] and corr > 0:
        context = "This indicates that wealthier nations tend to enjoy longer, healthier lives."
    elif "Health_Exp_per_Capita" in [x_metric, y_metric]:
        context = "It highlights the close link between healthcare investment and economic strength."
    else:
        context = "This reflects broader social and economic patterns."

    emoji = "📈" if corr > 0 else "📉"

    summary = (
        f"{emoji} In {region} during {year}, there is {strength} between {x_name} and {y_name} "
        f"(correlation = {corr:.2f}). {direction} {context}"
    )
    return summary

ai_text = generate_ai_insight(selected_region, selected_year, x_metric, y_metric, corr)
st.info(ai_text)

# ---------------------------------------------------------
# 🔊 VOICE OUTPUT (Text-to-Speech)
# ---------------------------------------------------------
if st.button("🔊 Speak Insight"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tts = gTTS(ai_text, lang="en")
        tts.save(tmp_file.name)
        st.audio(tmp_file.name, format="audio/mp3")

# ---------------------------------------------------------
# 🧭 FOOTER
# ---------------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center;'>🌍 Developed by <b>Tushar Sinha</b> | University of Milan 🇮🇹</p>",
    unsafe_allow_html=True,
)
