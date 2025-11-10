import os
import subprocess

import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import streamlit as st

# ---------------------------------------------------------
# 🌍 PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="🌍 The Wealth of Nations", layout="wide")

st.title("🌍 The Wealth of Nations — Global Prosperity Dashboard")
st.markdown("""
Welcome to the global overview of **The Wealth of Nations** —  
an interactive dashboard visualizing worldwide economic and social progress using **World Bank data (2010–2020)**.
""")

# ---------------------------------------------------------
# 📁 LOAD DATA
# ---------------------------------------------------------
@st.cache_data
def load_data():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    data_path = os.path.join(project_root, "output", "final_dataset.csv")
    analysis_script = os.path.join(project_root, "src", "wealth_of_nations_analysis.py")

    if not os.path.exists(data_path):
        st.warning("⚠️ Dataset not found. Running analysis script to generate it...")
        try:
            subprocess.run(["python3", analysis_script], check=True)
        except subprocess.CalledProcessError as e:
            st.error("❌ Failed to generate dataset. Please run wealth_of_nations_analysis.py manually.")
            st.text(e.stderr)
            st.stop()

    if not os.path.exists(data_path):
        st.error("❌ Dataset still not found after running the script.")
        st.stop()

    df = pd.read_csv(data_path)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.dropna(subset=["Year"])
    return df

df = load_data()

# ---------------------------------------------------------
# 🎛️ SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.header("🔎 Filters")

years = sorted(df["Year"].unique())
year = st.sidebar.slider("Select Year", int(min(years)), int(max(years)), int(max(years)))

countries = ["All"] + sorted(df["Country"].unique().tolist())
country = st.sidebar.selectbox("Select Country", countries)

filtered = df[df["Year"] == year]
if country != "All":
    filtered = filtered[filtered["Country"] == country]

# ---------------------------------------------------------
# 🌐 CHOROPLETH MAP
# ---------------------------------------------------------
st.subheader(f"🌐 Global GDP per Capita — {year}")
if filtered.empty:
    st.warning("⚠️ No data available for this selection.")
else:
    fig_map = px.choropleth(
        filtered,
        locations="Country",
        locationmode="country names",
        color="GDP_per_capita",
        hover_name="Country",
        color_continuous_scale="Viridis",
        title=f"GDP per Capita in {year}",
    )
    fig_map.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

# ---------------------------------------------------------
# 💡 GDP vs LIFE EXPECTANCY
# ---------------------------------------------------------
st.subheader("💡 GDP vs Life Expectancy")

scatter_df = filtered.dropna(subset=["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita"])
if scatter_df.empty:
    st.warning("⚠️ No valid data available for this year.")
else:
    fig_scatter = px.scatter(
        scatter_df,
        x="GDP_per_capita",
        y="Life_Expectancy",
        color="Country",
        size="Health_Exp_per_Capita",
        hover_name="Country",
        size_max=20,
        title="Health and Prosperity (Bubble size = Health Expenditure)",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ---------------------------------------------------------
# 📈 TREND OVER TIME
# ---------------------------------------------------------
st.subheader("📈 Trend Over Time (2010–2020)")
if country == "All":
    st.info("Select a specific country in the sidebar to see its trend over time.")
else:
    country_data = df[df["Country"] == country]
    fig_line = px.line(
        country_data,
        x="Year",
        y=["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita"],
        title=f"Trends in {country} (2010–2020)",
        markers=True
    )
    fig_line.update_layout(legend_title_text="Indicator")
    st.plotly_chart(fig_line, use_container_width=True)

# ---------------------------------------------------------
# 📊 CORRELATION HEATMAP
# ---------------------------------------------------------
st.subheader("📊 Correlation Heatmap (Global)")
numeric_df = df[["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"]].dropna()
if numeric_df.empty:
    st.warning("⚠️ Not enough data for correlation analysis.")
else:
    corr = numeric_df.corr()
    fig_heat = ff.create_annotated_heatmap(
        z=corr.values,
        x=list(corr.columns),
        y=list(corr.index),
        colorscale="Viridis",
        showscale=True
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ---------------------------------------------------------
# 🧠 SUMMARY METRICS
# ---------------------------------------------------------
st.subheader("📋 Summary Statistics")

if not filtered.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Avg GDP per Capita", f"${filtered['GDP_per_capita'].mean():,.0f}")
    col2.metric("❤️ Avg Life Expectancy", f"{filtered['Life_Expectancy'].mean():.1f} yrs")
    col3.metric("👶 Avg Child Mortality", f"{filtered['Child_Mortality'].mean():.1f}")

st.markdown("💬 *Data Source: World Bank Open Data (2010–2020)*")

# ---------------------------------------------------------
# 🧭 FOOTER
# ---------------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center;'>🌍 Built with ❤️ by <b>Tushar Sinha</b> | MSc Data Science, University of Milan 🇮🇹</p>",
    unsafe_allow_html=True,
)
