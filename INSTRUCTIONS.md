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
NORP_Reproducibility_Exercise_IEC_Sp26/
├── .env                         # API keys (not committed — see Setup)
├── main.py                      # Interactive NORP pipeline (RAG → LLM → SoQL → API)
├── rag_pipeline.py              # RAG retrieval using sentence-transformers + cosine similarity
├── ingest.py                    # Loads CSV/Excel knowledge base into RAG chunks
├── Crime_API.py                 # Executes SoQL queries against Chicago Crimes API
├── cp2_extraction.py            # CP2: Systematic district-by-year violent crime extraction
├── cp2_eda.py                   # CP2: EDA — plots and summary statistics
├── data/
│   ├── combined_dataset.csv                        # RAG knowledge base (NL → SoQL examples)
│   └── cp2_violent_crimes_by_district_year.csv     # Output: 220 rows, 22 districts x 10 years
├── plots/                       # Output plots from cp2_eda.py
│   ├── cp2_citywide_trend.png
│   ├── cp2_district_heatmap.png
│   ├── cp2_pre_post_2020.png
│   └── cp2_pct_change.png
└── requirements.txt
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
pip install matplotlib seaborn
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

---

## Data Sources

| Dataset | Source | Notes |
|---------|--------|-------|
| Chicago Crimes | https://data.cityofchicago.org/resource/crimes.json | SoQL API, filtered to violent types |
| RAG knowledge base | `data/combined_dataset.csv` | NL→SoQL examples for the RAG pipeline |
| Socioeconomic indicators | U.S. Census ACS / Chicago Data Portal | Planned for CP3 |

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

## Current Progress (Checkpoint 2)
- [x] NORP pipeline verified and running
- [x] District-by-year violent crime extraction (2015–2024)
- [x] EDA: citywide trend, district heatmap, pre/post-2020 comparison, % change chart
- [ ] Socioeconomic dataset integration (CP3)
- [ ] Regression / statistical analysis (CP3–CP4)
- [ ] Final reproducibility package

---

## For LLM Context Injection
If you are an LLM ingesting this file to assist with the project, here is the essential state:

- The crime data extraction is **complete**. Do not rebuild cp2_extraction.py unless asked.
- The next task is **CP3**: source district-level socioeconomic indicators and merge with the crime panel.
- The panel structure is `district x year` — 22 districts, years 2015–2024.
- The key analytical goal is a **pre/post-2020 structural break test** using regression with interaction terms.
- Spatial alignment between Chicago police districts and Census geographies (community areas or tracts) is a known challenge to address in CP3.
- All code should remain self-contained, read credentials from `.env`, and write outputs to `data/` or `plots/`.
