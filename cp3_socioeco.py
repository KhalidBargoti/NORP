"""
cp3_socioeco.py
Checkpoint 3 — Build socioeconomic indicators dataset for Chicago community areas.

Source: Chicago Data Portal - Selected Socioeconomic Indicators (2008-2012 ACS)
        Dataset: q3ty-n64b
        Hardcoded here since the API and CSV download endpoints are unreliable.

Community area → police district crosswalk is derived from the Chicago
Crimes API to match the exact geography used in CP2.

Outputs:
  data/cp3_community_socioeco.csv     raw community-area indicators
  data/cp3_community_to_district.csv  derived crosswalk
  data/cp3_district_socioeco.csv      indicators aggregated to district level
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

APP_TOKEN  = os.getenv("SOCRATA_APP_TOKEN", "")
HEADERS    = {"X-App-Token": APP_TOKEN} if APP_TOKEN else {}
CRIMES_URL = "https://data.cityofchicago.org/resource/crimes.json"

os.makedirs("data", exist_ok=True)

# ── Step 1: Hardcoded socioeconomic data (Chicago Data Portal q3ty-n64b) ──────
# Source: Selected Socioeconomic Indicators in Chicago Neighborhoods, 2008-2012
# Columns: community_area, community_area_name, per_capita_income,
#          pct_poverty, pct_unemployed, pct_no_hs, pct_crowded, hardship_index
print("=== Step 1: Loading socioeconomic indicators (2008-2012 ACS) ===")

data = [
    (1,"Rogers Park",23961,23.6,8.7,18.2,7.7,39),
    (2,"West Ridge",23088,17.2,8.8,20.8,7.8,46),
    (3,"Uptown",35787,24.0,8.9,11.8,3.8,20),
    (4,"Lincoln Square",37524,10.9,8.2,13.4,3.4,17),
    (5,"North Center",57123,7.5,5.2,4.5,0.3,6),
    (6,"Lake View",60058,11.4,4.7,2.6,1.1,5),
    (7,"Lincoln Park",71551,12.3,3.9,3.0,1.0,2),
    (8,"Near North Side",88669,12.9,4.4,2.5,0.9,1),
    (9,"Edison Park",40959,4.2,5.5,9.9,1.2,8),
    (10,"Norwood Park",38991,7.0,6.3,12.9,1.5,10),
    (11,"Jefferson Park",35640,9.1,9.1,14.2,2.5,13),
    (12,"Forest Glen",42583,5.2,5.8,9.6,1.3,7),
    (13,"North Park",34315,11.3,8.7,17.4,3.0,15),
    (14,"Albany Park",21323,22.4,10.5,27.3,9.3,41),
    (15,"Portage Park",32803,11.4,8.0,17.4,3.9,26),
    (16,"Irving Park",28385,15.8,8.1,20.3,6.9,34),
    (17,"Dunning",35508,8.2,7.0,15.9,2.5,14),
    (18,"Montclare",26772,14.4,8.3,26.3,5.5,31),
    (19,"Belmont Cragin",22419,21.2,9.3,30.0,8.9,48),
    (20,"Hermosa",20996,25.3,10.8,33.2,10.5,56),
    (21,"Avondale",25777,18.0,8.8,22.4,6.7,37),
    (22,"Logan Square",29488,19.5,7.4,13.7,5.1,28),
    (23,"Humboldt Park",15461,37.0,13.7,33.7,12.2,73),
    (24,"West Town",40113,17.1,6.6,8.5,3.3,16),
    (25,"Austin",15089,36.4,18.8,32.4,9.4,73),
    (26,"West Garfield Park",12961,46.6,20.4,36.3,11.2,83),
    (27,"East Garfield Park",14234,44.4,16.5,36.2,14.2,81),
    (28,"Near West Side",30161,26.3,12.7,15.8,6.3,45),
    (29,"North Lawndale",12541,47.3,20.6,41.9,11.5,87),
    (30,"South Lawndale",15089,32.2,11.5,44.7,12.3,72),
    (31,"Lower West Side",16444,35.8,10.4,36.6,12.5,67),
    (32,"Loop",65526,11.8,3.3,2.8,1.3,3),
    (33,"Near South Side",42534,12.8,6.9,4.5,2.2,9),
    (34,"Armour Square",16148,39.3,11.5,28.6,8.4,68),
    (35,"Douglas",22655,34.4,16.4,22.6,5.5,60),
    (36,"Oakland",19252,39.7,16.1,28.6,7.4,78),
    (37,"Fuller Park",10432,55.8,23.6,36.2,9.0,97),
    (38,"Grand Boulevard",16209,38.7,18.2,29.2,6.9,76),
    (39,"Kenwood",24426,23.8,12.0,20.5,3.7,43),
    (40,"Washington Park",13785,44.3,21.7,33.0,7.3,88),
    (41,"Hyde Park",32952,18.0,8.1,9.6,2.1,22),
    (42,"Woodlawn",17916,39.0,17.8,31.3,6.1,74),
    (43,"South Shore",18881,31.2,14.0,24.6,6.0,59),
    (44,"Chatham",18881,27.4,14.8,22.2,4.1,56),
    (45,"Avalon Park",20702,17.6,12.6,20.6,3.1,42),
    (46,"South Chicago",18770,30.7,14.7,28.4,7.3,64),
    (47,"Burnside",17013,33.0,17.3,27.7,5.8,71),
    (48,"Calumet Heights",25282,16.1,11.1,18.1,3.6,32),
    (49,"Roseland",16681,30.5,17.5,25.5,4.5,69),
    (50,"Pullman",16191,30.9,16.6,24.7,5.2,66),
    (51,"South Deering",16495,30.1,14.8,27.6,6.1,65),
    (52,"East Side",19600,22.3,11.6,27.6,7.4,49),
    (53,"West Pullman",15127,36.7,18.1,31.0,6.5,75),
    (54,"Riverdale",8201,56.5,21.8,41.8,8.1,98),
    (55,"Hegewisch",21672,14.8,9.9,22.3,4.0,29),
    (56,"Garfield Ridge",33080,9.0,7.7,17.5,4.8,22),
    (57,"Archer Heights",22781,21.4,10.1,34.4,9.2,52),
    (58,"Brighton Park",20282,24.2,9.4,36.8,12.7,57),
    (59,"McKinley Park",21454,20.5,9.0,28.3,8.1,47),
    (60,"Bridgeport",24435,16.0,8.2,20.7,5.1,33),
    (61,"New City",15698,40.3,15.8,37.8,10.9,77),
    (62,"West Elsdon",22570,16.8,9.8,29.2,8.4,44),
    (63,"Gage Park",18993,30.4,9.6,38.4,12.5,63),
    (64,"Clearing",29137,9.5,7.0,18.8,4.9,19),
    (65,"West Lawn",19252,26.3,10.7,33.3,11.2,55),
    (66,"Chicago Lawn",16398,34.3,12.3,36.1,10.9,70),
    (67,"West Englewood",12961,41.0,20.3,35.4,9.5,82),
    (68,"Englewood",11888,48.0,21.3,35.8,8.7,90),
    (69,"Greater Grand Crossing",16146,36.8,17.8,30.9,6.6,74),
    (70,"Ashburn",22744,15.6,10.3,22.9,5.8,36),
    (71,"Auburn Gresham",15757,35.0,17.7,28.2,5.7,75),
    (72,"Beverly",44585,7.6,6.2,7.9,1.4,11),
    (73,"Washington Heights",17249,31.6,16.0,25.9,4.9,69),
    (74,"Mount Greenwood",42737,5.8,5.5,10.7,1.9,9),
    (75,"Morgan Park",26145,19.6,11.3,17.9,3.3,35),
    (76,"O'Hare",21345,14.0,10.5,17.9,4.6,30),
    (77,"Edgewater",34044,21.7,7.0,8.1,3.2,18),
]

cols = ["community_area","community_area_name","per_capita_income",
        "pct_poverty","pct_unemployed","pct_no_hs","pct_crowded","hardship_index"]
soceco = pd.DataFrame(data, columns=cols)

soceco.to_csv("data/cp3_community_socioeco.csv", index=False)
print(f"  Community areas : {len(soceco)}")
print(f"  ✓ Saved data/cp3_community_socioeco.csv")
print(soceco.head(5).to_string(index=False))

# ── Step 2: Derive community area → district crosswalk ────────────────────────
print("\n=== Step 2: Deriving community area → district crosswalk ===")

xwalk_params = {
    "$select": "community_area, district",
    "$where":  "community_area IS NOT NULL AND district IS NOT NULL",
    "$group":  "community_area, district",
    "$limit":  "500",
}
r2 = requests.get(CRIMES_URL, params=xwalk_params, headers=HEADERS, timeout=30)
xwalk_raw = pd.DataFrame(r2.json())
xwalk_raw["community_area"] = pd.to_numeric(xwalk_raw["community_area"], errors="coerce").astype("Int64")
xwalk_raw["district"]       = pd.to_numeric(xwalk_raw["district"],       errors="coerce").astype("Int64")
xwalk_raw = xwalk_raw.dropna()

xwalk = (
    xwalk_raw.groupby("community_area")["district"]
    .agg(lambda x: x.value_counts().index[0])
    .reset_index()
)
xwalk.to_csv("data/cp3_community_to_district.csv", index=False)
print(f"  ✓ Saved data/cp3_community_to_district.csv ({len(xwalk)} community areas mapped)")
print(f"  Districts covered: {sorted(xwalk['district'].unique().tolist())}")

# ── Step 3: Aggregate to district level ───────────────────────────────────────
print("\n=== Step 3: Aggregating to district level ===")

merged = soceco.merge(xwalk, on="community_area", how="left")
missing = merged["district"].isna().sum()
if missing:
    print(f"  Warning: {missing} community areas could not be mapped to a district.")
merged = merged.dropna(subset=["district"])
merged["district"] = merged["district"].astype(int)

numeric_cols = [c for c in merged.columns if c not in ("community_area","community_area_name","district")]
district_soceco = merged.groupby("district")[numeric_cols].mean().reset_index().round(2)

district_soceco.to_csv("data/cp3_district_socioeco.csv", index=False)
print(f"  ✓ Saved data/cp3_district_socioeco.csv ({len(district_soceco)} districts)")
print(district_soceco.to_string(index=False))
