# INSTRUCTIONS.md — AI Workflow Guide

## Project Identity
- **Course:** CS 4365/6365: Intro to Enterprise Computing — Spring 2026, Georgia Tech
- **Group:** 5
- **Members:** Khoa Bui, Khalid A Bargoti
- **Project:** Analysis of Socioeconomic Determinants of Violent Crime Using Retrieval-Augmented Query Generation

---

## Research Question
Has the relationship between district-level socioeconomic factors and violent crime rates changed before and after 2020?

---

## Repository Structure

```
NORP/
├── .env                                          # API keys (not committed — see Setup)
├── main.py                                       # Interactive NORP pipeline (RAG → LLM → SoQL → API)
├── rag_pipeline.py                               # RAG retrieval using sentence-transformers + cosine similarity
├── ingest.py                                     # Loads CSV/Excel knowledge base into RAG chunks
├── Crime_API.py                                  # Executes SoQL queries against Chicago Crimes API
├── cp2_extraction.py                             # CP2: Systematic district-by-year violent crime extraction
├── cp2_eda.py                                    # CP2: EDA — plots and summary statistics
├── cp3_socioeco.py                               # CP3: Loads hardship index, derives crosswalk, aggregates to district
├── cp3_merge.py                                  # CP3: Merges crime panel with socioeconomic data
├── cp3_analysis.py                               # CP3: Correlations, scatter plots, OLS regression models
├── data/
│   ├── combined_dataset.csv                      # RAG knowledge base (NL → SoQL examples)
│   ├── cp2_violent_crimes_by_district_year.csv   # 220 rows, 22 districts x 10 years
│   ├── cp2_eda_summary.csv                       # District-level pre/post summary stats
│   ├── cp3_community_socioeco.csv                # Raw hardship index by community area
│   ├── cp3_community_to_district.csv             # Community area → police district crosswalk
│   ├── cp3_district_socioeco.csv                 # Socioeconomic indicators aggregated to district
│   ├── cp3_panel.csv                             # Final panel: 140 rows, 14 districts x 10 years
│   ├── cp3_correlation_table.csv                 # Pre/post correlations and delta per variable
│   └── cp3_regression_results.txt               # OLS model coefficients and R-squared
├── plots/
│   ├── cp2_citywide_trend.png
│   ├── cp2_district_heatmap.png
│   ├── cp2_pre_post_2020.png
│   ├── cp2_pct_change.png
│   ├── cp3_correlation_matrix.png
│   ├── cp3_income_vs_crime.png
│   ├── cp3_poverty_vs_crime.png
│   └── cp3_hardship_vs_crime.png
├── INSTRUCTIONS.md
└── requirements.txt
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
pip install matplotlib seaborn scikit-learn
```

### 2. Configure environment
Create a `.env` file in the project root:
```
SOCRATA_APP_TOKEN=your_token_here
OPENROUTER_API_KEY=your_key_here
```
- **SOCRATA_APP_TOKEN**: Free token from https://data.cityofchicago.org (raises API rate limits)
- **OPENROUTER_API_KEY**: From https://openrouter.ai (used by the interactive NORP pipeline)

---

## How to Run

### Interactive NORP pipeline (original system)
```bash
python main.py
```
Prompts for a natural language question → retrieves RAG examples → sends to LLM → generates SoQL → queries Chicago API.

### CP2: Systematic extraction (district x year violent crime counts)
```bash
python cp2_extraction.py
```
- Queries Chicago Crimes API for years 2015–2024
- Filters for: HOMICIDE, ROBBERY, CRIMINAL SEXUAL ASSAULT, AGGRAVATED ASSAULT, AGGRAVATED BATTERY
- Groups by police district
- Output: `data/cp2_violent_crimes_by_district_year.csv`

### CP2: Exploratory data analysis
```bash
python cp2_eda.py
```
- Reads `data/cp2_violent_crimes_by_district_year.csv`
- Produces 4 plots in `plots/` and `data/cp2_eda_summary.csv`
- Run AFTER cp2_extraction.py

### CP3: Socioeconomic dataset
```bash
python cp3_socioeco.py
```
- Loads Chicago Hardship Index (2008-2012 ACS) for 77 community areas
- Derives community-area → police-district crosswalk from the Chicago Crimes API
- Aggregates indicators to district level
- Outputs: `data/cp3_community_socioeco.csv`, `data/cp3_community_to_district.csv`, `data/cp3_district_socioeco.csv`

### CP3: Merge panel dataset
```bash
python cp3_merge.py
```
- Merges CP2 crime data with district-level socioeconomic indicators
- Adds `post2020` dummy variable
- Output: `data/cp3_panel.csv` — 140 rows (14 districts x 10 years)
- Run AFTER cp2_extraction.py and cp3_socioeco.py

### CP3: Statistical analysis
```bash
python cp3_analysis.py
```
- Pearson correlations split by pre/post-2020 period
- 4 scatter plots with trend lines saved to `plots/`
- Three OLS regression models: socioeconomic only, + post2020 dummy, + interaction term
- Outputs: `data/cp3_correlation_table.csv`, `data/cp3_regression_results.txt`
- Run AFTER cp3_merge.py

---

## Data Sources

| Dataset | Source | Notes |
|---------|--------|-------|
| Chicago Crimes | https://data.cityofchicago.org/resource/crimes.json | SoQL API, filtered to violent types |
| RAG knowledge base | `data/combined_dataset.csv` | NL→SoQL examples for the RAG pipeline |
| Chicago Hardship Index | Chicago Data Portal (q3ty-n64b) | 2008-2012 ACS, 77 community areas, hardcoded in cp3_socioeco.py |

---

## Key Schema Fields (Chicago Crimes API)

| Field | Type | Description |
|-------|------|-------------|
| `primary_type` | text | Crime category (e.g., HOMICIDE, ROBBERY) |
| `district` | number | Chicago Police Department district (1–25) |
| `year` | number | Year of incident |
| `date` | timestamp | Full incident datetime |
| `arrest` | boolean | Whether an arrest was made |
| `iucr` | text | Illinois Uniform Crime Reporting code |
| `community_area` | number | Chicago community area number (used for crosswalk) |

---

## Violent Crime Definition
This project uses the FBI Uniform Crime Reporting definition of violent crime:
- `HOMICIDE`
- `ROBBERY`
- `CRIMINAL SEXUAL ASSAULT`
- `AGGRAVATED ASSAULT`
- `AGGRAVATED BATTERY`

SoQL filter used:
```
primary_type IN ('HOMICIDE','ROBBERY','CRIMINAL SEXUAL ASSAULT','AGGRAVATED ASSAULT','AGGRAVATED BATTERY')
```

---

## Key Findings (as of CP3)
- Socioeconomic variables explain ~42% of violent crime variance across districts (Model 1 R² = 0.42)
- All five socioeconomic variables show weakened or reversed correlations with crime post-2020
- Hardship index correlation dropped from +0.349 (pre-2020) to +0.072 (post-2020), delta = -0.277
- Per capita income correlation flipped from -0.241 to +0.120, driven largely by District 12's post-2020 surge
- Interaction model confirms structural change: hardship × post2020 coefficient = -2.32

---

## Current Progress
- [x] NORP pipeline verified and running
- [x] District-by-year violent crime extraction (2015–2024)
- [x] EDA: citywide trend, district heatmap, pre/post-2020 comparison, % change chart
- [x] Socioeconomic dataset integration (Chicago Hardship Index)
- [x] Community area → police district crosswalk (derived from crimes API)
- [x] Merged panel dataset (district x year)
- [x] Correlation analysis split by pre/post-2020 period
- [x] OLS regression with structural break interaction test
- [ ] Robustness improvements: population normalization, fixed effects, outlier analysis (CP4)
- [ ] Final reproducibility package

---

## For LLM Context Injection
If you are an LLM ingesting this file to assist with the project, here is the essential state:

- All CP2 and CP3 scripts are **complete**. Do not rebuild them unless asked.
- The panel dataset `data/cp3_panel.csv` contains 140 rows covering 14 matched districts x 10 years with crime counts and 5 socioeconomic variables.
- The key finding is that socioeconomic relationships with violent crime **weakened post-2020** across all variables. The structural break is confirmed by the interaction model.
- The next task is **CP4**: improve robustness by normalizing crime by population, investigating District 12 as an outlier, and potentially running a fixed-effects panel regression.
- All code is self-contained, reads credentials from `.env`, and writes outputs to `data/` or `plots/`.
- Do not change the existing script logic unless explicitly asked — extend only.