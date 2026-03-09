# SoQL Query Generation with RAG
## Overview
* This project implements a Retrieval-Augmented Generation (RAG) pipeline to generate SoQL queries based on natural language questions. 
* It leverages a dataset of Chicago crime data as retrieval context and uses a language model via the Openrouter API to formulate accurate queries which are the parameters for querying the Chicago Crimes API.
* The parameters that are in JSON format are extracted and used to query the API to fetch relevant data.
* **Group 5 Extension:** This repository also includes a systematic longitudinal analysis of violent crime across Chicago police districts (2015–2024), investigating whether the relationship between district-level socioeconomic factors and violent crime rates changed before and after 2020.

## Installation
1. Clone the repository:
```
git clone https://github.com/KhalidBargoti/NORP.git
cd NORP
```
2. Create and activate a virtual environment:
```
python3 -m venv venv
source venv/bin/activate
```
3. Install dependencies:
```
pip install -r requirements.txt
pip install matplotlib seaborn
```

## Environment Variables
Edit the `.env` file in the project root directory with the following contents:
```
OPENROUTER_API_KEY=your_openrouter_api_key
SOCRATA_APP_TOKEN=your_socrata_app_token
```

## LLM API
* This project utilizes the [Openrouter API](https://openrouter.ai/) for making queries to LLMs.
* You can make an account on the website to obtain an **API KEY** to store in your .env file and utilize several free models.
* The default model used is "mistralai/devstral-2512:free", but feel free to change it in the `main.py` file.

## Chicago Crimes API
* The project accesses the [Chicago Crimes Dataset](https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2/about_data) via the [Socrata API](https://dev.socrata.com/foundry/data.cityofchicago.org/ijzp-q8t2) (v2.0)
* To get started, first make an account on the [City of Chicago](https://data.cityofchicago.org/) website.
* Once you make a profile, head to [developer settings](https://data.cityofchicago.org/profile/edit/developer_settings) and create a new **APP TOKEN** and store it in your .env file. Note that you need the APP TOKEN not the SECRET TOKEN

## Dataset
The file `data/combined_dataset.csv` is used only as retrieval context.
Each row typically contains:
- A natural language query
- Corresponding SoQL parameters
- Schema information
- Optional IUCR context - Codes for Chicago crime types

## Running the Project
From the project root directory:
```
python main.py
```
You will be prompted to enter a natural language question.
The program will:
* Retrieve relevant context rows
* Print the retrieved examples
* Generate SoQL parameters using the language model
* Execute the query and display results

## Generating the Crime Data and Plots (Group 5 Analysis)

### Step 1 — Extract violent crime data by district and year
```
python cp2_extraction.py
```
This script queries the Chicago Crimes API for each year from 2015 to 2024, filtering for five violent crime types (HOMICIDE, ROBBERY, CRIMINAL SEXUAL ASSAULT, AGGRAVATED ASSAULT, AGGRAVATED BATTERY) and groups results by police district.

**Output:** `data/cp2_violent_crimes_by_district_year.csv`
- 220 rows — 22 districts × 10 years
- Columns: `year`, `district`, `violent_crime_count`

### Step 2 — Run exploratory data analysis
```
python cp2_eda.py
```
This script reads the CSV produced in Step 1 and generates the following outputs.

**Plots** saved to `plots/`:
| File | Description |
|------|-------------|
| `cp2_citywide_trend.png` | Citywide violent crime totals per year (2015–2024) |
| `cp2_district_heatmap.png` | District × year heatmap of crime counts |
| `cp2_pre_post_2020.png` | Average annual crimes per district, pre vs post 2020 |
| `cp2_pct_change.png` | % change in average crime by district, pre → post 2020 |

**Summary table** saved to `data/cp2_eda_summary.csv`:
- Per-district averages for pre-2020 and post-2020 periods
- Total crime count across the full study period
- Peak year and % change per district

> **Note:** Run `cp2_extraction.py` before `cp2_eda.py`. Both scripts read your `SOCRATA_APP_TOKEN` from the `.env` file automatically.

## Assignment Deliverables
Submit a short report describing your interaction with the system and the observations you made while using it.

### 1. Project Overview
Provide a brief overview of the project in your own words. Describe what the system does and how retrieval and the language model work together.

### 2. Natural Language Query Testing
Design and test a range of natural language queries of your own.
Your queries should vary in structure and complexity. For each query, briefly note whether:
- Relevant examples were retrieved
- The generated SoQL parameters were valid
- The final API query produced meaningful results

### 3. Observations and Failure Cases
Discuss cases where the system did not work as expected.
This may include certain types of queries that fail, inconsistencies between retrieval and generation, or cases where insufficient context is returned. Provide brief explanations based on your observations.

### 4. Directions for Improvement
Suggest directions for improving the system. Focus on high-level ideas related to retrieval, dataset design, prompting, or evaluation rather than implementation details.

## Contributing
This is a coursework project for CS 6365 Intro to Enterprise Computing. Please follow academic integrity guidelines when working on this assignment.

## License
Educational use only - CS 6365 coursework assignment.
