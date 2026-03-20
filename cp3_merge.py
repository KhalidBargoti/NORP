"""
cp3_merge.py
Checkpoint 3 — Merge crime panel with socioeconomic indicators.

Inputs:
  data/cp2_violent_crimes_by_district_year.csv   (from CP2)
  data/cp3_district_socioeco.csv                 (from cp3_socioeco.py)

Output:
  data/cp3_panel.csv   district × year panel with crime + socioeconomic columns
"""

import os
import pandas as pd

os.makedirs("data", exist_ok=True)

# ── Load ──────────────────────────────────────────────────────────────────────
print("=== CP3 Panel Dataset Construction ===\n")

crime = pd.read_csv("data/cp2_violent_crimes_by_district_year.csv")
crime["district"] = crime["district"].astype(int)
crime["year"]     = crime["year"].astype(int)

soceco = pd.read_csv("data/cp3_district_socioeco.csv")
soceco["district"] = soceco["district"].astype(int)

print(f"Crime data  : {len(crime)} rows, {crime['district'].nunique()} districts, "
      f"years {crime['year'].min()}–{crime['year'].max()}")
print(f"Soceco data : {len(soceco)} rows, {soceco['district'].nunique()} districts")

# ── Merge ─────────────────────────────────────────────────────────────────────
# Socioeconomic data is a single cross-section (2008-2012 ACS) — it serves as
# a fixed structural baseline for each district, not a time-varying measure.
# This is standard in crime research when longitudinal socioeconomic panel data
# is unavailable at the sub-city level.

panel = crime.merge(soceco, on="district", how="left")

missing = panel[soceco.columns.difference(["district"])].isna().any(axis=1).sum()
if missing:
    print(f"\nWarning: {missing} rows could not be matched to socioeconomic data.")
    print("Unmatched districts:", sorted(panel[panel["per_capita_income"].isna()]["district"].unique().tolist()))

panel = panel.dropna(subset=["per_capita_income"])

# ── Derived variables ─────────────────────────────────────────────────────────
panel["post2020"] = (panel["year"] >= 2020).astype(int)
panel["log_crime"] = panel["violent_crime_count"].apply(lambda x: __import__("math").log(x + 1))

panel = panel.sort_values(["district", "year"]).reset_index(drop=True)

panel.to_csv("data/cp3_panel.csv", index=False)

print(f"\n✓ Saved data/cp3_panel.csv")
print(f"  Rows    : {len(panel)}")
print(f"  Columns : {list(panel.columns)}")
print(f"\nSample (first 10 rows):")
print(panel.head(10).to_string(index=False))

print(f"\nPre-2020 rows  : {(panel['post2020'] == 0).sum()}")
print(f"Post-2020 rows : {(panel['post2020'] == 1).sum()}")
