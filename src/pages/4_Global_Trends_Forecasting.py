import os
import tempfile

import country_converter as coco
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from fpdf import FPDF
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

# ---------------------------------------------------------
# 🌍 PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="📈 Global Trends Forecasting", layout="wide")

st.title("📈 Global Trends Forecasting — The Wealth of Nations")
st.markdown("""
Forecast the future of global prosperity and health.
Switch between **Linear** and **Polynomial Regression**, and forecast up to **2035**.
""")

# ---------------------------------------------------------
# 🌍 FULL 7-CONTINENT CUSTOM MAPPING
# ---------------------------------------------------------
continent_map = {
    "Asia": ["China", "India", "Japan", "Russia", "Saudi Arabia", "South Korea",
             "Indonesia", "Turkey", "Iran", "Pakistan", "Thailand", "Malaysia"],
    "Africa": ["Nigeria", "Egypt", "South Africa", "Kenya", "Ethiopia", "Ghana",
               "Algeria", "Morocco", "Tunisia"],
    "Europe": ["France", "Germany", "United Kingdom", "Italy", "Spain",
               "Netherlands", "Poland", "Sweden", "Belgium", "Norway",
               "Finland", "Denmark", "Switzerland"],
    "North America": ["United States", "Canada", "Mexico"],
    "South America": ["Brazil", "Argentina", "Chile", "Colombia", "Peru", "Uruguay"],
    "Australia": ["Australia", "New Zealand"],
    "Antarctica": []
}

def map_to_continent(country):
    for cont, clist in continent_map.items():
        if country in clist:
            return cont

    try:
        cc = coco.CountryConverter()
        r = cc.convert(country, to="continent")

        if r == "Oceania":
            return "Australia"

        if r == "Americas":
            if country in continent_map["North America"]:
                return "North America"
            else:
                return "South America"

        return r
    except:
        return None

# ---------------------------------------------------------
# 📁 LOAD DATA
# ---------------------------------------------------------
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.abspath(os.path.join(base_dir, "..", "..", "output", "final_dataset.csv"))

    if not os.path.exists(data_path):
        st.error("❌ final_dataset.csv not found. Run wealth_of_nations_analysis.py first.")
        st.stop()

    df = pd.read_csv(data_path)

    df["Region"] = df["Country"].apply(map_to_continent)
    df = df[df["Region"].notna()]

    numeric_cols = ["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

df = load_data()
st.success("✅ Dataset loaded successfully!")

# ---------------------------------------------------------
# ⚙️ SIDEBAR SETTINGS
# ---------------------------------------------------------
st.sidebar.header("⚙️ Forecast Settings")

region_list = ["Global"] + ["Asia", "Africa", "Europe",
                             "North America", "South America",
                             "Australia", "Antarctica"]

selected_region = st.sidebar.selectbox("🌍 Select Region", region_list)

metric = st.sidebar.selectbox(
    "📊 Select Indicator",
    ["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"]
)

forecast_years = st.sidebar.slider("🔮 Forecast up to Year", 2025, 2035, 2030)

regression_type = st.sidebar.radio(
    "📈 Regression Type",
    ["Linear", "Polynomial (Degree 2)"],
    index=1
)

# ---------------------------------------------------------
# 🔍 PREPARE DATA
# ---------------------------------------------------------
if selected_region == "Global":
    region_df = df.groupby("Year")[metric].mean().reset_index()
else:
    region_df = df[df["Region"] == selected_region].groupby("Year")[metric].mean().reset_index()

region_df = region_df.dropna()

if region_df.empty or len(region_df) < 2:
    st.error(f"No data found for {selected_region}. Cannot forecast.")
    st.stop()

X = region_df[["Year"]]
y = region_df[metric]

# ---------------------------------------------------------
# 🧠 MODEL TRAINING
# ---------------------------------------------------------
if regression_type.startswith("Polynomial"):
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(X)

    model = LinearRegression()
    model.fit(X_poly, y)

    future_years = np.arange(region_df["Year"].max() + 1, forecast_years + 1)
    future_poly = poly.transform(future_years.reshape(-1, 1))
    predictions = model.predict(future_poly)

else:
    model = LinearRegression()
    model.fit(X, y)

    future_years = np.arange(region_df["Year"].max() + 1, forecast_years + 1)
    predictions = model.predict(future_years.reshape(-1, 1))

# ---------------------------------------------------------
# 📊 FORECAST DF
# ---------------------------------------------------------
future_df = pd.DataFrame({"Year": future_years, metric: predictions})
future_df["Type"] = "Forecast"

region_df["Type"] = "Actual"

forecast_df = pd.concat([region_df, future_df])

# ---------------------------------------------------------
# 📈 PLOT GRAPH
# ---------------------------------------------------------
fig = px.line(
    forecast_df,
    x="Year",
    y=metric,
    color="Type",
    markers=True,
    line_dash="Type",
    title=f"{metric.replace('_',' ').title()} Forecast for {selected_region} ({regression_type})"
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# 🧠 INSIGHTS
# ---------------------------------------------------------
st.subheader("🧠 Forecast Insights")

latest_val = region_df.iloc[-1][metric]
predicted_val = future_df.iloc[-1][metric]

trend = "increase" if predicted_val > latest_val else "decrease"
change = ((predicted_val - latest_val) / latest_val) * 100 if latest_val else 0

st.markdown(f"""
**{selected_region}** is projected to see an **{trend}** in **{metric.replace('_',' ').title()}**.

- Last Actual ({region_df['Year'].max()}): **{latest_val:,.2f}**  
- Predicted ({forecast_years}): **{predicted_val:,.2f}**  
- Change: **{abs(change):.2f}%**  
""")

# ---------------------------------------------------------
# 📅 FORECAST TABLE
# ---------------------------------------------------------
st.subheader("📅 Forecast Data Table")
st.dataframe(forecast_df.style.format({metric: "{:,.2f}"}))

# ---------------------------------------------------------
# 📄 PDF REPORT GENERATION (WITH GRAPH)
# ---------------------------------------------------------
st.subheader("📄 Download Forecast Report")

def save_chart_png(fig):
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp.close()
        fig.write_image(tmp.name, format="png", width=1400, height=900)
        return tmp.name
    except Exception:
        st.error("❌ Missing kaleido. Install: pip install kaleido")
        return None

def generate_forecast_pdf():
    # Save chart
    chart_path = save_chart_png(fig)

    # Create PDF
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    # Cover Page
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 12, "Forecast Report", ln=True, align="C")
    pdf.ln(8)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Region: {selected_region}", ln=True)
    pdf.cell(0, 8, f"Metric: {metric}", ln=True)
    pdf.cell(0, 8, f"Model: {regression_type}", ln=True)
    pdf.cell(0, 8, f"Forecast up to: {forecast_years}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(
        0, 6,
        f"Last Actual Value ({region_df['Year'].max()}): {latest_val:,.2f}\n"
        f"Predicted Value ({forecast_years}): {predicted_val:,.2f}\n"
        f"Change: {change:.2f}%"
    )

    # Graph Page
    if chart_path and os.path.exists(chart_path):
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Forecast Graph", ln=True)
        pdf.ln(4)
        pdf.image(chart_path, x=10, w=190)

    # Generate PDF
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_pdf.close()
    pdf.output(tmp_pdf.name)

    # Remove temp chart
    if chart_path and os.path.exists(chart_path):
        os.remove(chart_path)

    return tmp_pdf.name

if st.button("Generate PDF"):
    pdf_path = generate_forecast_pdf()
    with open(pdf_path, "rb") as f:
        st.download_button(
            "⬇️ Download Forecast Report",
            data=f,
            file_name="forecast_report.pdf",
            mime="application/pdf"
        )

# ---------------------------------------------------------
# 🧭 FOOTER
# ---------------------------------------------------------
st.markdown("---")
st.markdown("<p style='text-align:center;'>👨‍💻 Developed by <b>Tushar Sinha</b> | MSc Data Science, University of Milan 🇮🇹</p>", unsafe_allow_html=True)
