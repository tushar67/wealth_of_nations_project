import os
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
    except:
        return None

if "Region" not in df.columns:
    df["Region"] = df["Country"].apply(get_region)

df["Region"] = df["Region"].apply(lambda x: x[0] if isinstance(x, list) else x)
df["Region"] = df["Region"].astype(str)
df = df[df["Region"].notna()]
df = df[~df["Region"].isin(["America", "Other", "Not Found", "None", "nan"])]

df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
df = df.sort_values(["Country", "Year"]).reset_index(drop=True)

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
    default_compare = next((c for c in all_countries if c != selected_country), all_countries[0])
    compare_country = st.sidebar.selectbox("🏁 Select Comparison Country", all_countries,
                                           index=all_countries.index(default_compare))

country_data = df[df["Country"] == selected_country]
if compare_mode:
    country2_data = df[df["Country"] == compare_country]
else:
    country2_data = None

# ---------------------------------------------------------
# 🧭 FIXED PROGRESS SCORE + BREAKDOWN
# ---------------------------------------------------------
def progress_score_with_breakdown(country_df, global_df):
    weights = {
        "GDP_per_capita": 0.4,
        "Life_Expectancy": 0.3,
        "Health_Exp_per_Capita": 0.2,
        "Child_Mortality": 0.1
    }
    cols = list(weights.keys())

    global_clean = global_df[["Country", "Year"] + cols].dropna(subset=cols, how="all")

    scaler = MinMaxScaler((0, 100))
    fit_df = global_clean.dropna(subset=cols)

    if fit_df.empty:
        return None, None, None

    scaler.fit(fit_df[cols])
    scaled_values = scaler.transform(global_clean[cols].fillna(fit_df[cols].median()))
    scaled_df = pd.DataFrame(scaled_values, columns=cols)
    scaled_df["Country"] = global_clean["Country"].values
    scaled_df["Year"] = global_clean["Year"].values

    if country_df.empty:
        return None, None, None

    latest_year = int(country_df["Year"].max())

    row = scaled_df[
        (scaled_df["Country"] == country_df["Country"].iloc[0]) &
        (scaled_df["Year"] == latest_year)
    ]

    if row.empty:
        row = scaled_df[scaled_df["Country"] == country_df["Country"].iloc[0]]
        if row.empty:
            return None, None, None
        row = row.iloc[[-1]]

    v = row.iloc[0]

    breakdown = {}
    score = 0.0

    for m in cols:
        scaled_val = float(v[m])

        if m == "Child_Mortality":
            contrib = (100 - scaled_val) * weights[m]
        else:
            contrib = scaled_val * weights[m]

        breakdown[m] = {
            "scaled": scaled_val,
            "weight": weights[m],
            "contribution": contrib
        }

        score += contrib

    return float(score), breakdown, v[cols]

# ---------------------------------------------------------
# 🪄 ANIMATED GAUGE
# ---------------------------------------------------------
def animated_gauge(title, score):
    placeholder = st.empty()
    score = max(0, min(100, float(score)))
    steps = 40

    for val in np.linspace(0, score, steps):
        color = "mediumseagreen" if val > 70 else "gold" if val > 50 else "lightcoral"
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=val,
            number={'suffix': " / 100"},
            title={'text': title},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 40], 'color': 'mistyrose'},
                    {'range': [40, 70], 'color': 'lightyellow'},
                    {'range': [70, 100], 'color': 'honeydew'},
                ],
            }
        ))
        fig.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10))
        placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(0.01)

# ---------------------------------------------------------
# 🎯 DISPLAY GAUGE
# ---------------------------------------------------------
st.markdown("### 🧭 National Progress Score")

if not compare_mode:
    score, breakdown, scaled_series = progress_score_with_breakdown(country_data, df)

    if score is None:
        st.error("⚠️ Unable to compute score due to missing data.")
    else:
        animated_gauge(f"{selected_country} — National Progress", score)

        # ---------------------------------------------------------
        # 📌 SCORE COMPONENTS BREAKDOWN
        # ---------------------------------------------------------
        st.markdown("### 📌 Score Components Breakdown")

        label_map = {
            "GDP_per_capita": "GDP per Capita (scaled)",
            "Life_Expectancy": "Life Expectancy (scaled)",
            "Health_Exp_per_Capita": "Health Expenditure (scaled)",
            "Child_Mortality": "Child Mortality (inverted)"
        }

        breakdown_rows = []
        for m, info in breakdown.items():
            breakdown_rows.append({
                "Metric": label_map[m],
                "Scaled Value (0-100)": info["scaled"],
                "Weight": info["weight"],
                "Contribution": info["contribution"]
            })

        breakdown_df = pd.DataFrame(breakdown_rows)

        st.dataframe(
            breakdown_df.style.format({
                "Scaled Value (0-100)": "{:.2f}",
                "Weight": "{:.2f}",
                "Contribution": "{:.2f}"
            })
        )

        # ---------------------------------------------------------
        # 🕸️ RADIAL CHART
        # ---------------------------------------------------------
        st.markdown("### 🕸️ Component Radar Chart")

        metrics_labels = [
            "GDP per Capita", "Life Expectancy", "Health Expenditure", "Child Mortality (inv)"
        ]

        r = [
            breakdown["GDP_per_capita"]["scaled"],
            breakdown["Life_Expectancy"]["scaled"],
            breakdown["Health_Exp_per_Capita"]["scaled"],
            100 - breakdown["Child_Mortality"]["scaled"]
        ]

        fig_rad = go.Figure()
        fig_rad.add_trace(go.Scatterpolar(
            r=r + [r[0]],
            theta=metrics_labels + [metrics_labels[0]],
            fill="toself",
            name=selected_country
        ))
        fig_rad.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            title=f"{selected_country} — Score Component Radar"
        )
        st.plotly_chart(fig_rad, use_container_width=True)

else:
    # ---------------------------------------------------------
    # COMPARISON MODE (GAUGES)
    # ---------------------------------------------------------
    score1, breakdown1, _ = progress_score_with_breakdown(country_data, df)
    score2, breakdown2, _ = progress_score_with_breakdown(country2_data, df)

    col1, col2 = st.columns(2)
    with col1:
        animated_gauge(f"{selected_country} — National Progress", score1)
    with col2:
        animated_gauge(f"{compare_country} — National Progress", score2)

    diff = score1 - score2
    better = selected_country if diff > 0 else compare_country
    st.info(f"🏁 **{better}** has a higher national progress score ({abs(diff):.1f}).")

    # ---------------------------------------------------------
    # 📌 BREAKDOWN TABLES
    # ---------------------------------------------------------
    st.markdown("### 📌 Score Component Breakdown (Comparison)")

    def build_df(br):
        rows = []
        for m, info in br.items():
            rows.append({
                "Metric": m,
                "Scaled": info["scaled"],
                "Weight": info["weight"],
                "Contribution": info["contribution"]
            })
        return pd.DataFrame(rows)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(selected_country)
        st.dataframe(build_df(breakdown1))
    with col2:
        st.subheader(compare_country)
        st.dataframe(build_df(breakdown2))

    # ---------------------------------------------------------
    # 🕸️ RADIAL COMPARISON
    # ---------------------------------------------------------
    st.markdown("### 🕸️ Radar Comparison")

    metrics = ["GDP", "Life Expect", "Health Exp", "Child Mort (inv)"]

    r1 = [
        breakdown1["GDP_per_capita"]["scaled"],
        breakdown1["Life_Expectancy"]["scaled"],
        breakdown1["Health_Exp_per_Capita"]["scaled"],
        100 - breakdown1["Child_Mortality"]["scaled"]
    ]
    r2 = [
        breakdown2["GDP_per_capita"]["scaled"],
        breakdown2["Life_Expectancy"]["scaled"],
        breakdown2["Health_Exp_per_Capita"]["scaled"],
        100 - breakdown2["Child_Mortality"]["scaled"]
    ]

    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Scatterpolar(
        r=r1 + [r1[0]],
        theta=metrics + [metrics[0]],
        fill='toself',
        name=selected_country
    ))
    fig_cmp.add_trace(go.Scatterpolar(
        r=r2 + [r2[0]],
        theta=metrics + [metrics[0]],
        fill='toself',
        name=compare_country
    ))
    fig_cmp.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title=f"{selected_country} vs {compare_country} — Radar Chart"
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

# ---------------------------------------------------------
# 🧭 FOOTER
# ---------------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center;'>👨‍💻 Developed by <b>Tushar Sinha</b> | MSc Data Science, University of Milan 🇮🇹</p>",
    unsafe_allow_html=True
)
