import os
import subprocess

import country_converter as coco
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------
# 🌍 PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="🌎 Global Insights", layout="wide")

st.title("🌎 Global Insights — The Wealth of Nations")
st.markdown("""
This page summarizes global prosperity indicators by continent using World Bank data.  
Analyze GDP, life expectancy, health expenditure, and child mortality over time.
""")

# ---------------------------------------------------------
# 📁 LOAD DATA
# ---------------------------------------------------------
@st.cache_data
def load_data():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    data_path = os.path.join(project_root, "output", "final_dataset.csv")
    analysis_script = os.path.join(project_root, "src", "wealth_of_nations_analysis.py")

    # Auto-generate dataset if missing
    if not os.path.exists(data_path):
        st.warning("⚠️ Dataset not found. Running analysis script to generate it...")
        try:
            subprocess.run(["python3", analysis_script], check=True)
        except subprocess.CalledProcessError as e:
            st.error("❌ Failed to generate dataset. Please run wealth_of_nations_analysis.py manually.")
            st.text(e.stderr)
            st.stop()

    if not os.path.exists(data_path):
        st.error("❌ Still no dataset found after running the script.")
        st.stop()

    df = pd.read_csv(data_path)

    # 🧹 Clean and fix Region column
    cc = coco.CountryConverter()

    def get_region(country):
        try:
            region = cc.convert(country, to="continent")
            if region == "Oceania": return "Australia"
            if country in ["Russia", "Russian Federation"]: return "Asia"
            return region
        except Exception:
            return None

    if "Region" not in df.columns:
        df["Region"] = df["Country"].apply(get_region)

    # Flatten list-like regions and force to string
    df["Region"] = df["Region"].apply(lambda x: x[0] if isinstance(x, list) else x)
    df["Region"] = df["Region"].astype(str)

    # Filter invalid
    df = df[df["Region"].notna()]
    df = df[~df["Region"].isin(["Other", "America", "Not Found", "nan", "None"])]

    # Convert numerics
    num_cols = ["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    st.success("✅ Dataset loaded and cleaned successfully!")
    return df


df = load_data()

# ---------------------------------------------------------
# 🎛️ SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.header("🌍 Filters")

years = sorted(df["Year"].unique())
selected_year = st.sidebar.selectbox("Select Year", years, index=len(years) - 1)
metric = st.sidebar.selectbox(
    "Select Metric",
    ["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"],
    index=0,
)

# ---------------------------------------------------------
# 🧮 CONTINENT SUMMARY
# ---------------------------------------------------------
latest_data = df[df["Year"] == selected_year]
continent_summary = (
    latest_data.groupby("Region")[["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"]]
    .mean(numeric_only=True)
    .reset_index()
)

st.subheader(f"🌎 Continental Summary ({selected_year})")

# Format numbers for display
styled_df = continent_summary.copy()
for col in ["GDP_per_capita", "Health_Exp_per_Capita"]:
    styled_df[col] = styled_df[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "-")
for col in ["Life_Expectancy", "Child_Mortality"]:
    styled_df[col] = styled_df[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")

st.dataframe(styled_df, use_container_width=True)

# ---------------------------------------------------------
# 📊 VISUALIZATION
# ---------------------------------------------------------
st.markdown(f"### 📈 {metric.replace('_', ' ')} by Continent — {selected_year}")

fig = px.bar(
    continent_summary,
    x="Region",
    y=metric,
    color="Region",
    title=f"{metric.replace('_', ' ')} by Continent ({selected_year})",
    text_auto=".2s",
)
fig.update_traces(textfont_size=12)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# 🌍 ANIMATED TREND
# ---------------------------------------------------------
st.markdown(f"### 🎬 Animated Trend of {metric.replace('_', ' ')} Over Time")

fig_anim = px.bar(
    df,
    x="Region",
    y=metric,
    color="Region",
    animation_frame="Year",
    title=f"Animated Trend of {metric.replace('_', ' ')} by Continent (2000–{max(years)})",
)
st.plotly_chart(fig_anim, use_container_width=True)

# ---------------------------------------------------------
# 🧭 FOOTER
# ---------------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center;'>👨‍💻 Developed by <b>Tushar Sinha</b> | MSc Data Science, University of Milan 🇮🇹</p>",
    unsafe_allow_html=True,
)
