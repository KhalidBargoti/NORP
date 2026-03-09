from unstructured.partition.auto import partition
import pandas as pd
import os

# Define the chunk size here
CHUNK_SIZE = 1

def load_documents(directory):
    docs = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                # Handle Excel files - read ALL sheets but chunk them
                print(f"Processing Excel file: {filename}")
                excel_file = pd.ExcelFile(filepath)
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(filepath, sheet_name=sheet_name)
                    
                    # Chunk large dataframes
                    chunk_size = CHUNK_SIZE
                    for i in range(0, len(df), chunk_size):
                        chunk = df.iloc[i:i+chunk_size]
                        text_content = f"Sheet: {sheet_name} (rows {i+1}-{min(i+chunk_size, len(df))})\n{chunk.to_string()}"
                        docs.append(text_content)
            
            if filename.endswith('.csv'):
                # Handle CSV files - read and chunk them
                print(f"Processing CSV file: {filename}")
                df = pd.read_csv(filepath)
                
                # Chunk large dataframes
                chunk_size = CHUNK_SIZE
                for i in range(0, len(df), chunk_size):
                    chunk = df.iloc[i:i+chunk_size]
                    text_content = f"CSV rows {i+1}-{min(i+chunk_size, len(df))}\n{chunk.to_string()}"
                    docs.append(text_content)
            
            else:
                # Ignore other file types for now
                print(f"Skipping unsupported file type: {filename}")
    return docs