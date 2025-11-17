import os
import subprocess
import tempfile

import country_converter as coco
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import streamlit as st
from fpdf import FPDF

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="The Wealth of Nations", layout="wide")

st.title("The Wealth of Nations — Global Prosperity Dashboard")
st.markdown(
    "Welcome to the global overview of The Wealth of Nations — "
    "an interactive dashboard visualizing worldwide economic and social progress."
)

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
@st.cache_data
def load_data():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    data_path = os.path.join(project_root, "output", "final_dataset.csv")
    analysis_script = os.path.join(project_root, "src", "wealth_of_nations_analysis.py")

    if not os.path.exists(data_path):
        st.warning("Dataset not found. Running analysis script...")
        try:
            subprocess.run(["python3", analysis_script], check=True)
        except subprocess.CalledProcessError:
            st.error("Failed to generate dataset. Please run analysis script manually.")
            st.stop()

    if not os.path.exists(data_path):
        st.error("Dataset still not found.")
        st.stop()

    df = pd.read_csv(data_path)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.dropna(subset=["Year"])
    return df

df = load_data()

# ---------------------------------------------------------
# MAP: country -> continent
# ---------------------------------------------------------
cc = coco.CountryConverter()
df["Continent"] = cc.convert(names=df["Country"], to="continent", not_found=None)
df["Continent"] = df["Continent"].apply(lambda x: x[0] if isinstance(x, list) else x)
df["Continent"] = df["Continent"].replace({"Oceania": "Australia", "Americas": "North America"})

ALL_CONTINENTS = [
    "All", "Africa", "Asia", "Europe",
    "North America", "South America", "Australia", "Antarctica"
]

# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.header("Filters")

years = sorted(df["Year"].unique())
year = st.sidebar.slider("Select Year", int(min(years)), int(max(years)), int(max(years)))

continent = st.sidebar.selectbox("Select Continent", ALL_CONTINENTS)
if continent == "All":
    country_options = ["All"] + sorted(df["Country"].unique())
else:
    country_options = ["All"] + sorted(df[df["Continent"] == continent]["Country"].unique())

country = st.sidebar.selectbox("Select Country", country_options)

# ---------------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------------
filtered = df[df["Year"] == year].copy()
if continent != "All":
    filtered = filtered[filtered["Continent"] == continent]
if country != "All":
    filtered = filtered[filtered["Country"] == country]

# ---------------------------------------------------------
# CHOROPLETH MAP
# ---------------------------------------------------------
st.subheader(f"Global GDP per Capita — {year}")
if filtered.empty:
    st.warning("No data available for this selection.")
    fig_map = None
else:
    fig_map = px.choropleth(
        filtered,
        locations="Country",
        locationmode="country names",
        color="GDP_per_capita",
        hover_name="Country",
        color_continuous_scale="Viridis",
        title=f"GDP per Capita in {year}"
    )
    st.plotly_chart(fig_map, use_container_width=True)

# ---------------------------------------------------------
# GDP vs Life Expectancy scatter
# ---------------------------------------------------------
st.subheader("GDP vs Life Expectancy")
scatter_df = filtered.dropna(subset=["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita"])
if scatter_df.empty:
    st.warning("No valid data available for scatter.")
    fig_scatter = None
else:
    fig_scatter = px.scatter(
        scatter_df,
        x="GDP_per_capita",
        y="Life_Expectancy",
        color="Country",
        size="Health_Exp_per_Capita",
        hover_name="Country",
        title="Health and Prosperity (Bubble size = Health Expenditure)"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ---------------------------------------------------------
# Trend over time
# ---------------------------------------------------------
st.subheader("Trend Over Time (2010–2020)")
if country == "All":
    st.info("Select a specific country to see trend.")
    fig_line = None
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

# ---------------------------------------------------------
# Correlation heatmap
# ---------------------------------------------------------
st.subheader("Correlation Heatmap (Global)")
numeric_df = df[["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"]].dropna()
if numeric_df.empty:
    st.warning("Not enough data for heatmap.")
    fig_heat = None
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
# Summary metrics
# ---------------------------------------------------------
st.subheader("Summary Statistics")
if not filtered.empty:
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg GDP per Capita", f"${filtered['GDP_per_capita'].mean():,.0f}")
    c2.metric("Avg Life Expectancy", f"{filtered['Life_Expectancy'].mean():.1f} yrs")
    c3.metric("Avg Child Mortality", f"{filtered['Child_Mortality'].mean():.1f}")
st.markdown("*Source: World Bank Data (2010–2020)*")

# ---------------------------------------------------------
# REPORT WITH CHARTS EMBEDDED (requires kaleido)
# ---------------------------------------------------------
st.subheader("Download Report (with charts)")

def save_figure_png(fig, prefix="chart", width=1200, height=800):
    """
    Save a Plotly figure to a temporary PNG file using kaleido.
    Returns the file path or None if fig is None.
    """
    if fig is None:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.close()
    img_path = tmp.name
    try:
        # use write_image which requires kaleido
        fig.write_image(img_path, format="png", width=width, height=height, scale=1)
        return img_path
    except Exception as e:
        # cleanup and return None
        if os.path.exists(img_path):
            os.remove(img_path)
        st.error("Failed to export figure image. Ensure 'kaleido' is installed.")
        return None

def generate_pdf_with_charts():
    # render images
    map_img = save_figure_png(fig_map, prefix="map", width=1200, height=700)
    scatter_img = save_figure_png(fig_scatter, prefix="scatter", width=1200, height=800)
    line_img = save_figure_png(fig_line, prefix="line", width=1200, height=700)
    heat_img = save_figure_png(fig_heat, prefix="heat", width=900, height=700)

    # create pdf
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    # Cover page
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Wealth of Nations Report", ln=True, align="C")
    pdf.ln(6)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Year: {year}", ln=True)
    pdf.cell(0, 8, f"Continent: {continent}", ln=True)
    pdf.cell(0, 8, f"Country: {country}", ln=True)
    pdf.ln(6)
    pdf.multi_cell(0, 6, "This report contains visual snapshots (map, scatter, trend, heatmap) based on the selected filters.")

    # Insert map page if available
    if map_img and os.path.exists(map_img):
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "GDP per Capita Map", ln=True)
        pdf.ln(4)
        # center image with width ~180 mm (A4 width minus margins)
        pdf.image(map_img, x=15, y=None, w=180)
    
    # Insert scatter page
    if scatter_img and os.path.exists(scatter_img):
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "GDP vs Life Expectancy (Scatter)", ln=True)
        pdf.ln(4)
        pdf.image(scatter_img, x=15, y=None, w=180)

    # Insert line (trend) page
    if line_img and os.path.exists(line_img):
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Trend Over Time", ln=True)
        pdf.ln(4)
        pdf.image(line_img, x=15, y=None, w=180)

    # Insert heatmap page
    if heat_img and os.path.exists(heat_img):
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Correlation Heatmap", ln=True)
        pdf.ln(4)
        # Use smaller width for heatmap
        pdf.image(heat_img, x=20, y=None, w=170)

    # Summary / Insights page
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Summary Statistics", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", "", 12)
    if not filtered.empty:
        pdf.cell(0, 6, f"Avg GDP per Capita: ${filtered['GDP_per_capita'].mean():,.0f}", ln=True)
        pdf.cell(0, 6, f"Avg Life Expectancy: {filtered['Life_Expectancy'].mean():.1f} years", ln=True)
        pdf.cell(0, 6, f"Avg Child Mortality: {filtered['Child_Mortality'].mean():.1f}", ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Insights", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 6,
        "- Higher GDP per capita tends to be associated with longer life expectancy.\n"
        "- Health expenditure is an important factor in national wellbeing.\n"
        "- Patterns differ across countries and regions.\n"
    )

    # Save PDF to temp file
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_pdf.close()
    pdf.output(tmp_pdf.name)

    # cleanup images
    for p in [map_img, scatter_img, line_img, heat_img]:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    return tmp_pdf.name

if st.button("Generate PDF (with charts)"):
    pdf_path = generate_pdf_with_charts()
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                "Download Report (PDF)",
                data=f,
                file_name="wealth_of_nations_report_with_charts.pdf",
                mime="application/pdf"
            )
        try:
            os.remove(pdf_path)
        except Exception:
            pass

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.markdown("---")
st.markdown("<p style='text-align:center;'>👨‍💻 Developed by <b>Tushar Sinha</b> | MSc Data Science, University of Milan 🇮🇹</p>", unsafe_allow_html=True)
