import os

import country_converter as coco
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

# ---------------------------------------------------------
# 🌍 PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="📈 Global Trends Forecasting", layout="wide")

st.title("📈 Global Trends Forecasting — The Wealth of Nations")
st.markdown("""
Forecast the future of global prosperity and health with **Machine Learning**.  
Switch between **Linear** and **Polynomial Regression** to see how different models predict up to **2035**.
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
        st.error("❌ Dataset not found. Please run 'wealth_of_nations_analysis.py' first.")
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

    for col in ["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


df = load_data()
st.success("✅ Dataset loaded successfully!")

# ---------------------------------------------------------
# ⚙️ SIDEBAR SETTINGS
# ---------------------------------------------------------
st.sidebar.header("⚙️ Forecast Settings")

region_list = ["Global"] + sorted(df["Region"].astype(str).unique())
selected_region = st.sidebar.selectbox("🌍 Select Region", region_list)

metric = st.sidebar.selectbox(
    "📊 Select Indicator to Forecast",
    ["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"],
    index=0,
)

forecast_years = st.sidebar.slider("🔮 Forecast up to Year", 2025, 2035, 2030)

regression_type = st.sidebar.radio("📈 Regression Type", ["Linear", "Polynomial (Degree 2)"], index=1)

# ---------------------------------------------------------
# 🔍 DATA PREPARATION
# ---------------------------------------------------------
if selected_region == "Global":
    region_df = df.groupby("Year")[metric].mean().reset_index()
else:
    region_df = df[df["Region"] == selected_region].groupby("Year")[metric].mean().reset_index()

region_df = region_df.dropna()
X = region_df[["Year"]]
y = region_df[metric]

# ---------------------------------------------------------
# 🧠 MODEL TRAINING & FORECAST
# ---------------------------------------------------------
if regression_type.startswith("Polynomial"):
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(X)
    model = LinearRegression()
    model.fit(X_poly, y)
    future_years = np.arange(region_df["Year"].max() + 1, forecast_years + 1)
    X_future_poly = poly.transform(future_years.reshape(-1, 1))
    predictions = model.predict(X_future_poly)
else:
    model = LinearRegression()
    model.fit(X, y)
    future_years = np.arange(region_df["Year"].max() + 1, forecast_years + 1)
    predictions = model.predict(future_years.reshape(-1, 1))

future_df = pd.DataFrame({"Year": future_years, metric: predictions})
forecast_df = pd.concat([region_df, future_df], ignore_index=True)
forecast_df["Type"] = ["Actual"] * len(region_df) + ["Forecast"] * len(future_df)

# ---------------------------------------------------------
# 📊 VISUALIZATION
# ---------------------------------------------------------
fig = px.line(
    forecast_df,
    x="Year",
    y=metric,
    color="Type",
    markers=True,
    line_dash="Type",
    title=f"{metric.replace('_', ' ')} Forecast for {selected_region} ({regression_type})",
)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# 🧭 INSIGHTS & AI FORECAST SUMMARY
# ---------------------------------------------------------
st.subheader("🧠 Forecast Insights")

latest_val = region_df.iloc[-1][metric]
predicted_val = future_df.iloc[-1][metric]
trend = "increase 📈" if predicted_val > latest_val else "decrease 📉"
change = ((predicted_val - latest_val) / latest_val) * 100 if latest_val else 0

st.markdown(f"""
**{selected_region}** is projected to see a **{trend}** in **{metric.replace('_', ' ')}**  
from **{region_df['Year'].max()} ({latest_val:,.2f})** to **{forecast_years} ({predicted_val:,.2f})**  
using a **{regression_type} model**, representing a **{abs(change):.2f}%** change overall.
""")

# --- AI Narrative Insight Generator ---
def generate_forecast_summary(region, metric, change, trend, regression_type):
    metric_name = metric.replace("_", " ").title()
    direction = "growth" if "increase" in trend else "decline"

    if abs(change) < 5:
        tone = "a stable trend with minor fluctuations"
    elif abs(change) < 20:
        tone = f"a moderate {direction} trajectory"
    else:
        tone = f"a strong {direction} pattern"

    if regression_type.startswith("Polynomial"):
        model_comment = "a nonlinear pattern suggesting accelerating or slowing change"
    else:
        model_comment = "a steady, linear trend over time"

    emoji = "🌱" if "increase" in trend else "⚠️"
    summary = (
        f"{emoji} Between {int(region_df['Year'].min())} and {forecast_years}, "
        f"{region} exhibits {tone} in **{metric_name}**. "
        f"The model detects {model_comment}, with projected values reaching approximately "
        f"**{predicted_val:,.2f}** by {forecast_years}. "
        f"This implies sustained {direction} in long-term {metric_name.lower()} performance."
    )
    return summary

summary_text = generate_forecast_summary(selected_region, metric, change, trend, regression_type)
st.info(summary_text)

# ---------------------------------------------------------
# 🧾 FORECAST DATA TABLE
# ---------------------------------------------------------
st.subheader("📅 Forecast Data Table")
st.dataframe(forecast_df.style.format({metric: "{:,.2f}"}))

# ---------------------------------------------------------
# 🧭 FOOTER
# ---------------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center;'>🌍 Developed by <b>Tushar Sinha</b> | University of Milan 🇮🇹</p>",
    unsafe_allow_html=True,
)
