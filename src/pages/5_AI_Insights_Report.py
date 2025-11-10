import os

import country_converter as coco
import numpy as np
import pandas as pd
import plotly.express as px
import speech_recognition as sr
import streamlit as st

# ---------------------------------------------------------
# 🌍 PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="🎤 AI Insight Assistant — The Wealth of Nations", layout="wide")

st.title("🎤 AI Insight Assistant — The Wealth of Nations")
st.markdown("""
Chat with your data — explore global prosperity trends through **natural-language or voice input**.  
Just click the 🎙️ button and ask your question aloud!

**Examples:**
- “How has life expectancy changed in Europe?”
- “Compare GDP between Asia and Africa.”
- “Which region spends more on health?”
""")

# ---------------------------------------------------------
# 📁 LOAD DATA
# ---------------------------------------------------------
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.abspath(os.path.join(base_dir, "..", "..", "output", "final_dataset.csv"))
    if not os.path.exists(data_path):
        st.error("❌ Data file not found. Please run 'wealth_of_nations_analysis.py' first.")
        st.stop()

    df = pd.read_csv(data_path)
    cc = coco.CountryConverter()

    if "Region" not in df.columns:
        def get_region(c):
            try:
                region = cc.convert(c, to='continent')
                if region == "Oceania": return "Australia"
                if c in ["Russia", "Russian Federation"]: return "Asia"
                return region
            except:
                return None
        df["Region"] = df["Country"].apply(get_region)

    df["Region"] = df["Region"].apply(lambda x: x[0] if isinstance(x, list) else x)
    df = df[df["Region"].notna()]
    df = df[~df["Region"].isin(["America", "Not Found", "Other"])]

    for col in ["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

df = load_data()

# ---------------------------------------------------------
# 🧠 SIDEBAR INPUTS
# ---------------------------------------------------------
st.sidebar.header("⚙️ Assistant Controls")
metrics = ["GDP_per_capita", "Life_Expectancy", "Health_Exp_per_Capita", "Child_Mortality"]
selected_metric = st.sidebar.selectbox("📊 Choose a Metric", metrics)

# ---------------------------------------------------------
# 🎤 VOICE INPUT
# ---------------------------------------------------------
st.sidebar.markdown("### 🎤 Voice Input")
if st.sidebar.button("🎙️ Speak"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.sidebar.info("🎧 Listening... please speak clearly.")
        audio = recognizer.listen(source, phrase_time_limit=8)

    try:
        spoken_query = recognizer.recognize_google(audio)
        st.session_state["query_text"] = spoken_query
        st.sidebar.success(f"You said: {spoken_query}")
    except sr.UnknownValueError:
        st.sidebar.warning("⚠️ Couldn’t understand your speech, please try again.")
    except sr.RequestError:
        st.sidebar.error("⚠️ Speech recognition service unavailable.")

# ---------------------------------------------------------
# 💬 TEXT QUERY
# ---------------------------------------------------------
query = st.sidebar.text_area(
    "💬 Type or edit your question:",
    value=st.session_state.get("query_text", ""),
    height=120,
)

# ---------------------------------------------------------
# 🔍 PROCESS QUERY
# ---------------------------------------------------------
regions = sorted(df["Region"].astype(str).unique())

def get_latest_value(region, metric):
    temp = df[df["Region"] == region]
    if temp.empty:
        return None
    return temp.loc[temp["Year"].idxmax(), metric]

if query:
    query_lower = query.lower()
    found_regions = [r for r in regions if r.lower() in query_lower]

    # --- Compare two regions ---
    if len(found_regions) >= 2:
        r1, r2 = found_regions[:2]
        v1 = get_latest_value(r1, selected_metric)
        v2 = get_latest_value(r2, selected_metric)

        if v1 is None or v2 is None:
            st.error(f"⚠️ Data not available for {r1} or {r2}.")
        else:
            diff = v2 - v1
            pct = (diff / v1) * 100 if v1 else 0
            better = r2 if v2 > v1 else r1

            st.markdown(f"### 🧭 {selected_metric.replace('_', ' ')} Comparison: {r1} vs {r2}")
            st.write(f"**{better}** has higher {selected_metric.replace('_', ' ')} by **{abs(pct):.2f}%**")

            comp_df = pd.DataFrame({"Region": [r1, r2], selected_metric: [v1, v2]})
            fig = px.bar(comp_df, x="Region", y=selected_metric, color="Region",
                         text=selected_metric, title=f"{r1} vs {r2}")
            fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    # --- Single region query ---
    elif len(found_regions) == 1:
        region = found_regions[0]
        region_df = df[df["Region"] == region].groupby("Year")[metrics].mean().reset_index()

        if "life" in query_lower:
            metric = "Life_Expectancy"
        elif "gdp" in query_lower:
            metric = "GDP_per_capita"
        elif "health" in query_lower:
            metric = "Health_Exp_per_Capita"
        elif "child" in query_lower or "mortality" in query_lower:
            metric = "Child_Mortality"
        else:
            metric = selected_metric

        latest = region_df.iloc[-1][metric]
        first = region_df.iloc[0][metric]
        trend = "increased 📈" if latest > first else "decreased 📉"

        st.markdown(f"### 🧠 Insight for {region}")
        st.write(f"{metric.replace('_', ' ')} has {trend} from {first:.2f} to {latest:.2f}.")
        fig = px.line(region_df, x="Year", y=metric, markers=True,
                      title=f"{metric.replace('_', ' ')} Trend in {region}")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("🤖 Please mention at least one region in your question!")
else:
    st.info("💬 Type or speak your question to explore insights.")

# ---------------------------------------------------------
# 🧭 FOOTER
# ---------------------------------------------------------
st.markdown("---")
st.markdown("<p style='text-align:center;'>🎤 Developed by <b>Tushar Sinha</b> | Vishwakarma Enterprises 🇮🇹</p>", unsafe_allow_html=True)
