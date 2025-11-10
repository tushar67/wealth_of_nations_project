import os
import time
from urllib.request import urlopen

import country_converter as coco
import pandas as pd
import plotly.express as px
import streamlit as st
from fpdf import FPDF

# ---------------------------------------------------------
# 🌍 STREAMLIT PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="🌍 Wealth of Nations Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 🏷️ TITLE & INTRO
# ---------------------------------------------------------
st.markdown(
    """
    <div style="text-align:center; padding:20px 0;">
        <h1 style="font-size:42px;">🌍 The Wealth of Nations Dashboard</h1>
        <p style="font-size:18px; color:gray;">
            An interactive global prosperity explorer using World Bank data.<br>
            Compare nations, visualize economic and social progress, and uncover trends.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# 📊 LOAD DATA (correct relative path for your structure)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    time.sleep(1)

    # One directory up (..), then go to output/final_dataset.csv
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(BASE_DIR, "..", "output", "final_dataset.csv")

    if not os.path.exists(DATA_PATH):
        st.error("❌ Data file not found. Please run 'wealth_of_nations_analysis.py' first.")
        st.stop()

    try:
        df = pd.read_csv(DATA_PATH)
        return df
    except Exception as e:
        st.error(f"⚠️ Error loading data: {e}")
        st.stop()

with st.spinner("📡 Fetching and preparing global data..."):
    df = load_data()
st.success("✅ Data loaded successfully and ready to explore!")

# ---------------------------------------------------------
# 🌐 REGION FIX USING country_converter
# ---------------------------------------------------------
cc = coco.CountryConverter()

def get_region(country_name):
    try:
        region = cc.convert(country_name, to='continent')
        if isinstance(region, list):
            region = region[0] if region else "Other"
        if region == "Oceania": return "Australia"
        if country_name in ["Russia", "Russian Federation"]: return "Asia"
        if country_name in ["Turkey", "Georgia", "Kazakhstan"]: return "Europe"
        if country_name in ["United States", "Canada", "Mexico"]: return "North America"
        if country_name in [
            "Brazil", "Argentina", "Chile", "Colombia", "Peru", "Ecuador",
            "Venezuela", "Paraguay", "Uruguay", "Bolivia"
        ]: return "South America"
        if country_name in ["Egypt", "Morocco", "Tunisia"]: return "Africa"
        return region
    except:
        return None

if "Region" not in df.columns or df["Region"].isnull().all():
    df["Region"] = df["Country"].apply(get_region)

df = df[df["Region"].notna()]
df = df[~df["Region"].str.lower().isin(["america", "other", "none", "not found", "nan"])]

region_colors = {
    "Africa": "#2ca02c",
    "Asia": "#ff7f0e",
    "Europe": "#1f77b4",
    "North America": "#9467bd",
    "South America": "#d62728",
    "Australia": "#17becf",
}

# ---------------------------------------------------------
# 🧭 SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.markdown("### 🌍 Global Dashboard Filters")

years = sorted(df["Year"].unique())
regions = sorted(df["Region"].dropna().unique())
selected_year = st.sidebar.selectbox("Select Year", years, index=len(years) - 1)
selected_region = st.sidebar.selectbox("Select Region", ["All"] + list(regions))

x_axis = st.sidebar.selectbox("Select X-Axis Metric", ["GDP_per_capita", "Health_Exp_per_Capita", "Child_Mortality"])
y_axis = st.sidebar.selectbox("Select Y-Axis Metric", ["Life_Expectancy", "Child_Mortality", "Health_Exp_per_Capita"])

min_gdp, max_gdp = st.sidebar.slider(
    "Select GDP per Capita Range ($)",
    min_value=int(df["GDP_per_capita"].min()),
    max_value=int(df["GDP_per_capita"].max()),
    value=(int(df["GDP_per_capita"].min()), int(df["GDP_per_capita"].max()))
)

top_n = st.sidebar.slider("Show Top N Countries (by GDP)", 5, 50, 20)

filtered = df[df["Year"] == selected_year]
if selected_region != "All":
    filtered = filtered[filtered["Region"] == selected_region]
filtered = filtered[
    (filtered["GDP_per_capita"] >= min_gdp) &
    (filtered["GDP_per_capita"] <= max_gdp)
]
filtered = filtered.nlargest(top_n, "GDP_per_capita")

# ---------------------------------------------------------
# 🏁 COUNTRY COMPARISON SECTION
# ---------------------------------------------------------
st.markdown("---")
st.markdown("## 🏁 Compare Two Countries")

col1, col2 = st.columns(2)
with col1:
    country1 = st.selectbox("Select First Country", sorted(df["Country"].unique()), index=sorted(df["Country"].unique()).index("India"))
with col2:
    country2 = st.selectbox("Select Second Country", sorted(df["Country"].unique()), index=sorted(df["Country"].unique()).index("Italy"))

def get_flag_url(country):
    base = "https://flagsapi.com"
    try:
        code = cc.convert(country, to='ISO2')
        return f"{base}/{code}/flat/64.png"
    except:
        return None

if country1 and country2:
    c1_data = df[df["Country"] == country1].sort_values("Year")
    c2_data = df[df["Country"] == country2].sort_values("Year")

    flag1 = get_flag_url(country1)
    flag2 = get_flag_url(country2)

    st.markdown("### 🌐 Country Overview")

    ccol1, ccol2 = st.columns(2)
    with ccol1:
        if flag1:
            st.image(flag1, width=70)
        st.markdown(f"### 🇮🇳 **{country1}**")
        st.metric("💰 GDP per Capita", f"${c1_data.iloc[-1]['GDP_per_capita']:,.0f}")
        st.metric("❤️ Life Expectancy", f"{c1_data.iloc[-1]['Life_Expectancy']:.1f} yrs")
        st.metric("💊 Health Exp.", f"${c1_data.iloc[-1]['Health_Exp_per_Capita']:,.0f}")
        st.metric("👶 Child Mortality", f"{c1_data.iloc[-1]['Child_Mortality']:.1f} / 1k")

    with ccol2:
        if flag2:
            st.image(flag2, width=70)
        st.markdown(f"### 🇮🇹 **{country2}**")
        st.metric("💰 GDP per Capita", f"${c2_data.iloc[-1]['GDP_per_capita']:,.0f}")
        st.metric("❤️ Life Expectancy", f"{c2_data.iloc[-1]['Life_Expectancy']:.1f} yrs")
        st.metric("💊 Health Exp.", f"${c2_data.iloc[-1]['Health_Exp_per_Capita']:,.0f}")
        st.metric("👶 Child Mortality", f"{c2_data.iloc[-1]['Child_Mortality']:.1f} / 1k")

    # -----------------------------------------------------
    # 📈 Animated Life Expectancy vs GDP
    # -----------------------------------------------------
    st.markdown("### 📈 Animated Life Expectancy vs GDP")
    comp_data = pd.concat([c1_data, c2_data])
    fig_anim = px.scatter(
        comp_data,
        x="GDP_per_capita",
        y="Life_Expectancy",
        color="Country",
        animation_frame="Year",
        size="Health_Exp_per_Capita",
        hover_name="Country",
        range_x=[0, df["GDP_per_capita"].max()],
        range_y=[40, 90],
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    st.plotly_chart(fig_anim, use_container_width=True)

# ---------------------------------------------------------
# 🧾 FOOTER
# ---------------------------------------------------------
st.markdown("---")
st.markdown("<p style='text-align:center;'>👨‍💻 Developed by <b>Tushar Sinha</b> | MSc Data Science, University of Milan 🇮🇹</p>", unsafe_allow_html=True)
