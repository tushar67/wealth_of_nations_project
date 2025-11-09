# 🌍 The Wealth of Nations — Global Prosperity Dashboard

![Dashboard Preview](dashboard_preview.png)

## 🎯 Overview
This project analyzes the relationship between a country's **economic prosperity** and the **well-being of its population**, using official **World Bank data**.  
It explores how **GDP per capita**, **life expectancy**, **healthcare spending**, and **child mortality** have evolved globally.

The project includes:
- Data fetching directly from the **World Bank API**
- Data cleaning and merging into a unified dataset
- Interactive visualizations with **Streamlit** and **Plotly**
- A dashboard to explore countries and global trends

---

## 📊 Indicators Used
| Indicator | Description | World Bank Code |
|------------|--------------|-----------------|
| GDP per capita | Economic output per person | NY.GDP.PCAP.CD |
| Life expectancy | Average life span | SP.DYN.LE00.IN |
| Health expenditure per capita | Health spending per person | SH.XPD.CHEX.PC.CD |
| Child mortality rate | Deaths under 5 years per 1,000 births | SH.DYN.MORT |

---

## ⚙️ Project Structure
wealth_of_nations_project/
│
├── src/
│   ├── wealth_of_nations_analysis.py
│   └── wealth_dashboard.py
│
├── output/
│   └── final_dataset.csv
│
├── requirements.txt
├── README.md
└── LICENSE

## 🚀 How to Run the Project

### 1️⃣ Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
 
 2️⃣ Install dependencies
pip install -r requirements.txt

Run the data analysis
cd src
python wealth_of_nations_analysis.py


This script fetches and merges data from the World Bank API
and saves the cleaned dataset to:

output/final_dataset.csv

4️⃣ Launch the dashboard
streamlit run src/wealth_dashboard.py

Then open the URL shown in the terminal (usually http://localhost:8501).

🧰 Tech Stack

Python 3.11
pandas
numpy
plotly
streamlit
wbdata
requests

📈 Features

Interactive year and region filters
Dynamic scatter plots showing GDP vs Life Expectancy
Choropleth map of Life Expectancy across the world
Time-series plots for selected countries
Automatic data cleaning to handle missing values
Modular, reproducible, and extendable code

📊 Example Insights

Higher GDP per capita generally correlates with longer life expectancy.
Regions with higher healthcare spending tend to have lower child mortality.
The gap between developed and developing countries is narrowing over time.

🧑‍💻 Author

Tushar Randhir Sinha
Master’s in Data Science for Economics and Health — University of Milan
📧 tusharrandhir.sinha@studenti.unimi.it

Data Source: World Bank Open Data

License

This project is open-source and distributed under the GPL-3.0 License.

