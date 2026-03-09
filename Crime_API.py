import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
import sys
import re
import os
import json

BASE_URL = "https://data.cityofchicago.org/resource/crimes.json"

def run_query(params, timeout=5):
    APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")
    headers = {"X-App-Token": APP_TOKEN}

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        
        # Print the final URL for debugging
        print("Request URL:", response.url)
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

    if response.status_code == 200:
        try:
            data = response.json()
        except ValueError as e:
            print(f"JSON decode error: {e}")
            return None

        if not data:
            print("No data returned.")
            return None

        df = pd.DataFrame(data)
        print("Columns:", list(df.columns))
        print("Rows returned:", len(df))
        return df
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    
def pretty_print_rag_chunks(chunks, max_chunks=5):
    print("\nTop retrieved examples:\n" + "-" * 40)

    for i, chunk in enumerate(chunks[:max_chunks], 1):
        print(f"\nExample {i}")

        nl = re.search(r"nl_query\s+(.*)", chunk)
        soql = re.search(r"\{.*?\}", chunk, re.DOTALL)
        schema = re.search(r"schema\s+(.*)", chunk)

        if nl:
            print("NL Query:")
            print(" ", nl.group(1).strip())

        if soql:
            try:
                print("SoQL Params:")
                print(json.dumps(json.loads(soql.group()), indent=2))
            except Exception:
                print("SoQL Params:")
                print(" ", soql.group().strip())

        if schema:
            print("Schema:")
            print(" ", schema.group(1).strip())

        print("-" * 40)
    
if __name__ == "__main__":
    
    params = {
        "$select": "primary_type, count(primary_type) as type_count",
        "$group": "primary_type",
        "$order": "type_count DESC",
        "$limit": "5"
    }   
    
    df = run_query(params)
    if df is not None:
        print(df)