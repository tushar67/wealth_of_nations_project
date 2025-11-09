import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import streamlit as st

# --------------------------------------
# PAGE CONFIG
# --------------------------------------
st.set_page_config(page_title="🌍 The Wealth of Nations", layout="wide")
st.title("🌍 The Wealth of Nations — Global Prosperity Dashboard")

# Load Data
@st.cache_data
def load_data():
    df = pd.read_csv("../output/final_dataset.csv")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    return df.dropna(subset=["Year"])

df = load_data()

# --------------------------------------
# SIDEBAR FILTERS
# --------------------------------------
st.sidebar.header("🔎 Filters")
years = sorted(df["Year"].unique())
year = st.sidebar.slider("Select Year", int(min(years)), int(max(years)), int(max(years)))

countries = ["All"] + sorted(df["Country"].unique().tolist())
country = st.sidebar.selectbox("Select Country", countries)

filtered = df[df["Year"] == year]
if country != "All":
    filtered = filtered[filtered["Country"] == country]

# --------------------------------------
# CHOROPLETH MAP
# --------------------------------------
st.subheader(f"🌐 Global GDP per Capita — {year}")
fig_map = px.choropleth(
    filtered,
    locations="Country",
    locationmode="country names",
    color="GDP_per_capita",
    hover_name="Country",
    color_continuous_scale="Viridis",
    title=f"GDP per Capita in {year}",
)
st.plotly_chart(fig_map, use_container_width=True)

# --------------------------------------
# GDP vs LIFE EXPECTANCY
# --------------------------------------
st.subheader("💡 GDP vs Life Expectancy")
fig_scatter = px.scatter(
    filtered,
    x="GDP_per_capita",
    y="Life_Expectancy",
    color="Country",
    size="Health_Exp_per_Capita",
    hover_name="Country",
    size_max=20,
    title="Health and Prosperity",
)
st.plotly_chart(fig_scatter, use_container_width=True)

# --------------------------------------
# TREND OVER TIME
# --------------------------------------
st.subheader("📈 Trend Over Time (2010–2020)")
if country == "All":
    st.info("Select a specific country to see its trends over time.")
else:
    country_data = df[df["Country"] == country]
    fig_line = px.line(
        country_data,
        x="Year",
        y=["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita"],
        title=f"Trends in {country} (2010–2020)",
        markers=True
    )
    st.plotly_chart(fig_line, use_container_width=True)

# --------------------------------------
# CORRELATION HEATMAP
# --------------------------------------
st.subheader("📊 Correlation Heatmap (Global)")
numeric_df = df[["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"]].dropna()
corr = numeric_df.corr()
fig_heat = ff.create_annotated_heatmap(
    z=corr.values,
    x=list(corr.columns),
    y=list(corr.index),
    colorscale="Viridis",
    showscale=True
)
st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("💬 *Data Source: World Bank Open Data (2010–2020)*")
