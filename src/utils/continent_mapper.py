# ---------------------------------------------------------
# 🌍 Continent Mapper Module (Shared Across Project)
# ---------------------------------------------------------

import country_converter as coco

# 7-Continent Custom Mapping (Highest Priority)
CONTINENT_MAP = {
    "Asia": [
        "China", "India", "Japan", "Russia", "Saudi Arabia", "South Korea",
        "Indonesia", "Turkey", "Iran", "Pakistan", "Thailand", "Malaysia"
    ],
    "Africa": [
        "Nigeria", "Egypt", "South Africa", "Kenya", "Ethiopia", "Ghana",
        "Algeria", "Morocco", "Tunisia"
    ],
    "Europe": [
        "France", "Germany", "United Kingdom", "Italy", "Spain", "Netherlands",
        "Poland", "Sweden", "Belgium", "Norway", "Finland", "Denmark", "Switzerland"
    ],
    "North America": [
        "United States", "Canada", "Mexico"
    ],
    "South America": [
        "Brazil", "Argentina", "Chile", "Colombia", "Peru", "Uruguay"
    ],
    "Australia": [
        "Australia", "New Zealand"
    ],
    "Antarctica": []
}


def map_to_continent(country: str):
    """
    Universal continent mapper for your entire project.
    Priority:
    1. Manual 7-continent mapping
    2. coco fallback (UN M49)
    3. Re-mapping Americas -> NA/SA
    """

    if not isinstance(country, str):
        return None

    # 1️⃣ Manual mapping
    for continent, countries in CONTINENT_MAP.items():
        if country in countries:
            return continent

    # 2️⃣ Fallback to coco
    try:
        cc = coco.CountryConverter()
        cont = cc.convert(country, to="continent")

        # coco sometimes returns ["Europe"], fix it
        if isinstance(cont, list):
            cont = cont[0]

        # Convert Oceania -> Australia
        if cont == "Oceania":
            return "Australia"

        # Convert Americas -> NA / SA
        if cont == "Americas":
            if country in CONTINENT_MAP["North America"]:
                return "North America"
            return "South America"

        return cont
    except:
        return None


def apply_continent_mapping(df):
    """
    Apply continent mapping to DataFrame.
    Ensures:
    - All regions become valid 7 continents
    - No 'America', 'Not Found', 'Other', None
    - No list types from coco
    """
    # Apply mapping
    df["Region"] = df["Country"].apply(map_to_continent)

    # Fix lists returned by coco
    df["Region"] = df["Region"].apply(lambda x: x[0] if isinstance(x, list) else x)

    # Convert to string
    df["Region"] = df["Region"].astype(str)

    # Remove missing and invalid mappings
    df = df[df["Region"].notna() & (df["Region"] != "None")].copy()

    # Keep ONLY valid 7 continents
    valid_continents = {
        "Asia", "Africa", "Europe",
        "North America", "South America",
        "Australia", "Antarctica"
    }
    df = df[df["Region"].isin(valid_continents)].copy()

    return df
