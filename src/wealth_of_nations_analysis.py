import pandas as pd
import requests
import datetime
import os

# ------------------------------------------
# CONFIGURATION
# ------------------------------------------
output_dir = "../output"
os.makedirs(output_dir, exist_ok=True)

# Indicators (World Bank codes)
indicators = {
    "NY.GDP.PCAP.CD": "GDP_per_capita",
    "SP.DYN.LE00.IN": "Life_Expectancy",
    "SH.XPD.CHEX.PC.CD": "Health_Exp_per_Capita",
    "SH.DYN.MORT": "Child_Mortality"
}

countries = ["IN", "IT", "DE", "US", "CN", "BR", "ZA", "FR", "JP", "GB"]  # example list
years = list(range(2010, 2021))

def fetch_data(indicator):
    print(f"📡 Fetching {indicator} data...")
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=20000"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Error fetching {indicator}: {response.status_code}")
        return pd.DataFrame()

    data = response.json()[1]  # The second element contains the actual data
    df = pd.DataFrame(data)
    df = df[['country', 'countryiso3code', 'date', 'value']]
    df.rename(columns={
        'country': 'Country',
        'countryiso3code': 'Country_Code',
        'date': 'Year',
        'value': indicators[indicator]
    }, inplace=True)
    df['Country'] = df['Country'].apply(lambda x: x['value'] if isinstance(x, dict) else x)
    return df

# Fetch all indicators
data_frames = []
for ind in indicators:
    df_ind = fetch_data(ind)
    data_frames.append(df_ind)

# Merge all indicators on Country + Year
print("🔄 Merging data...")
final_df = data_frames[0]
for df in data_frames[1:]:
    final_df = pd.merge(final_df, df, on=["Country", "Country_Code", "Year"], how="outer")

# Filter by years
final_df = final_df[final_df["Year"].astype(int).between(2010, 2020)]

# Save the data
output_path = os.path.join(output_dir, "final_dataset.csv")
final_df.to_csv(output_path, index=False)

print(f"✅ Data successfully saved at: {output_path}")
print(final_df.head())
