"""
cp2_extraction.py
Checkpoint 2 — Systematic violent crime extraction by district and year (2015–2024)
Builds on the NORP Crime_API infrastructure but runs a fixed, research-grade aggregation
instead of the interactive RAG loop.
"""

import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────

BASE_URL   = "https://data.cityofchicago.org/resource/crimes.json"
YEARS      = list(range(2015, 2025))   # 2015 through 2024 inclusive
OUTPUT_CSV = "data/cp2_violent_crimes_by_district_year.csv"

# Chicago PD violent crime primary_type categories
VIOLENT_TYPES = (
    "HOMICIDE",
    "CRIMINAL SEXUAL ASSAULT",
    "ROBBERY",
    "AGGRAVATED ASSAULT",
    "AGGRAVATED BATTERY",
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def build_type_filter(types):
    """Return a SoQL IN(...) clause for a tuple of primary_types."""
    quoted = ", ".join(f"'{t}'" for t in types)
    return f"primary_type IN ({quoted})"


def fetch_year(year: int, app_token: str) -> pd.DataFrame | None:
    """
    Fetch violent crime counts grouped by district for a single year.
    Returns a DataFrame with columns [district, year, violent_crime_count].
    """
    params = {
        "$select": "district, count(*) as violent_crime_count",
        "$where":  f"year = {year} AND {build_type_filter(VIOLENT_TYPES)}",
        "$group":  "district",
        "$order":  "district ASC",
        "$limit":  "50",   # only 25 Chicago police districts — 50 is safe headroom
    }

    headers = {"X-App-Token": app_token} if app_token else {}

    try:
        r = requests.get(BASE_URL, params=params, headers=headers, timeout=15)
        print(f"  [{year}] URL: {r.url}")
    except requests.exceptions.RequestException as e:
        print(f"  [{year}] Request error: {e}")
        return None

    if r.status_code != 200:
        print(f"  [{year}] HTTP {r.status_code}: {r.text[:200]}")
        return None

    data = r.json()
    if not data:
        print(f"  [{year}] No data returned.")
        return None

    df = pd.DataFrame(data)
    df["year"] = year
    df["violent_crime_count"] = pd.to_numeric(df["violent_crime_count"], errors="coerce")
    return df


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    load_dotenv()
    app_token = os.getenv("SOCRATA_APP_TOKEN", "")
    if not app_token:
        print("Warning: SOCRATA_APP_TOKEN not set — requests will be rate-limited.")

    os.makedirs("data", exist_ok=True)

    all_frames = []

    print("=== CP2 Violent Crime Extraction ===")
    print(f"Years   : {YEARS[0]}–{YEARS[-1]}")
    print(f"Types   : {', '.join(VIOLENT_TYPES)}")
    print()

    for year in YEARS:
        print(f"Fetching {year}...")
        df = fetch_year(year, app_token)
        if df is not None:
            print(f"  → {len(df)} districts returned for {year}")
            all_frames.append(df)
        else:
            print(f"  → Skipping {year} due to error.")
        time.sleep(0.3)   # be polite to the API

    if not all_frames:
        print("\nNo data retrieved. Check your API token and network connection.")
        return

    # ── Combine & clean ────────────────────────────────────────────────────────
    combined = pd.concat(all_frames, ignore_index=True)

    # Drop rows where district is null/empty (can appear in raw API results)
    combined = combined[combined["district"].notna()]
    combined = combined[combined["district"].str.strip() != ""]

    # Cast district to integer for clean joining later
    combined["district"] = pd.to_numeric(combined["district"], errors="coerce").astype("Int64")
    combined = combined.dropna(subset=["district"])

    # Reorder columns
    combined = combined[["year", "district", "violent_crime_count"]].sort_values(
        ["year", "district"]
    )

    # ── Save ──────────────────────────────────────────────────────────────────
    combined.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✓ Saved {len(combined)} rows to {OUTPUT_CSV}")

    # ── Quick summary ─────────────────────────────────────────────────────────
    print("\n── Summary ──────────────────────────────────")
    print(f"Years covered  : {combined['year'].min()} – {combined['year'].max()}")
    print(f"Districts found: {sorted(combined['district'].dropna().unique().tolist())}")
    print(f"Total rows     : {len(combined)}")
    print("\nSample (first 10 rows):")
    print(combined.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
