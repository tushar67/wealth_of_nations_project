🌍 The Wealth of Nations — Global Data Analytics & Forecasting Platform

A professional, multi-page Streamlit analytics application built using World Bank data (2010–2020).
This platform brings together interactive dashboards, AI-powered insights, machine learning forecasting, and PDF report generation — all in one seamless experience.

<p align="center"> <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python"> <img src="https://img.shields.io/badge/Streamlit-App-red?logo=streamlit"> <img src="https://img.shields.io/badge/Plotly-Interactive%20Charts-00c7ff?logo=plotly"> <img src="https://img.shields.io/badge/ML-Forecasting-green?logo=scikitlearn"> </p>
📌 Features Overview
🟦 1. Global Dashboard

The main page that visualizes worldwide prosperity trends.

🌐 Choropleth world map

📊 GDP vs Life Expectancy bubble chart

⏳ Country trends (2010–2020)

🔥 Correlation heatmap

📋 Summary metrics

📝 PDF Report Generator (with charts embedded)

🟩 2. Global Correlations

Analyze relationships between economics & health indicators.

📉 Pearson Correlation

🟢 2D scatter with OLS regression

🤖 AI-generated correlation insights

🔊 Text-to-speech summary (gTTS)

🧮 Clean continent mapping (7-continent system)

🟧 3. Global Trends Forecasting

Forecast future prosperity trends up to 2035 using Machine Learning.

📈 Linear Regression

📈 Polynomial Regression (Degree 2)

🔮 Forecast graphs

📄 PDF Forecast Report (with graph included)

📅 Forecast Data Table

🧠 Forecast insights (direction + % change)

⚙️ Tech Stack
Category	Tools
Frontend	Streamlit
Data Handling	Pandas, NumPy
ML / Forecasting	scikit-learn
Charts	Plotly (PNG export via kaleido)
Audio	gTTS (Google Text-to-Speech)
PDF Reports	FPDF
Country to Continent Mapping	country_converter
📦 Project Structure
wealth_of_nations_project/
│
├── src/
│   ├── wealth_of_nations_analysis.py
│   ├── wealth_dashboard.py
│   ├── pages/
│   │   ├── 0_Global_Dashboard.py
│   │   ├── 1_Global_Correlations.py
│   │   ├── 3_Global_Trends_Forecasting.py
│   │   └── 4_Global_Trends_Forecasting.py
│   │   └── 5_AI_Insights_Report.py
│   └── utils/
│       └── continent_mapper.py
│
├── output/
│   └── final_dataset.csv
│
├── assets/
│   └── (optional: logos, background images)
│
├── requirements.txt
└── README.md

🚀 Setup & Installation
1️⃣ Clone the repo
git clone https://github.com/yourusername/wealth_of_nations_project.git
cd wealth_of_nations_project

2️⃣ Create a virtual environment
python3 -m venv venv
source venv/bin/activate

3️⃣ Install dependencies
pip install -r requirements.txt

▶️ Run the App

Launch the Streamlit dashboard:

streamlit run src/pages/0_Global_Dashboard.py


Now open your browser at:

http://localhost:8501


Use the sidebar navigation to explore all pages.

📄 PDF Report Generation

Two pages offer downloadable PDF reports:

✔ Global Dashboard

Summary metrics

Choropleth map

Bubble chart

Trend graph

All graphs embedded as PNG via kaleido

✔ Forecasting Page

Forecast summary

% change analysis

Forecast graph embedded

Trend reporting

Reports use FPDF, ensuring:

Lightweight PDFs

No Unicode dependency

Works on local + Streamlit Cloud

🤖 Machine Learning Forecasting

The app supports:

🔹 Linear Regression

Best for stable, linear growth patterns.

🔹 Polynomial Regression (Degree 2)

Captures acceleration or deceleration trends.

Output includes:

Forecasted values

Confidence-style separation (Actual vs Forecast color-coded)

Insights on upward/downward trends

Forecast data table

🧪 requirements.txt
streamlit
pandas
numpy
plotly
country_converter
scikit-learn
scipy
gtts
fpdf==1.7.2
kaleido==0.2.1

📘 Data Source

World Bank Open Data (2010–2020)
Collected & aggregated via custom analysis script.

👨‍💻 Developer

Tushar Sinha
MSc Data Science, University of Milan 🇮🇹
Fabrication, analytics & global research enthusiast