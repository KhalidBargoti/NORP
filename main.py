import os
from ingest import load_documents
from rag_pipeline import RAGPipeline
import requests
import json
from Crime_API import run_query
import re
from dotenv import load_dotenv

# API Information
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "mistralai/devstral-2512:free"

def print_chunk_as_row(chunk):
    lines = [ln for ln in chunk.splitlines() if ln.strip()]
    if not lines:
        return

    row_line = lines[-1]

    row_num = None
    m_row = re.match(r"^(\d+)\s+", row_line)
    if m_row:
        row_num = m_row.group(1)
        row_line = row_line[m_row.end():]

    m = re.search(r"\{.*\}", row_line)
    if not m:
        print("Row:")
        print("  (unparseable chunk)")
        return

    nl_query = row_line[:m.start()].strip()
    soql_str = m.group(0).strip()
    tail = row_line[m.end():].strip()

    parts = [p.strip() for p in re.split(r"\s{2,}", tail) if p.strip()]
    schema = parts[0] if len(parts) >= 1 else ""
    iucr_context = parts[1] if len(parts) >= 2 else ""

    if iucr_context.lower() == "nan":
        iucr_context = ""

    try:
        soql_pretty = json.dumps(json.loads(soql_str), indent=2)
    except json.JSONDecodeError:
        soql_pretty = soql_str

    print(f"Row: {row_num if row_num is not None else ''}")
    print(f"NL_QUERY:\n  {nl_query}")
    print("SOQL_PARAMS:")
    print(soql_pretty)
    print(f"SCHEMA:\n  {schema}")
    print(f"IUCR_CONTEXT:\n  {iucr_context}")

def test_llm_api():
    question = "What is the capital of France?"
    context = "France is a country in Europe. Its capital is Paris."
    response = query_llm_api(question, context)
    print("LLM API Test Response:\n", response)

def query_llm_api(question, context):
    API_KEY = os.getenv("OPENROUTER_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {   
                "role": "system", 
                "content": 
                    "You are a SoQL query generator for a Socrata dataset. \
                    You must generate SoQL parameters for the question ONLY using the provided context examples. \
                    Do NOT invent fields, filters, or functions. \
                    If the context does not contain enough information to answer the question, \
                    output exactly: NOT_ENOUGH_CONTEXT. \
                    Your output must be a single valid JSON object containing ONLY SoQL parameters \
                    (e.g., $select, $where, $group, $order, $limit). \
                    Do not include explanations, comments, or extra text."
            },
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
        ],
    }
    
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code}, {response.text}"
    

def main():
    print("Entering Main")
    
    print("Loading environment variables from .env file")
    load_dotenv()
    
    docs_dir = "data"
    texts = load_documents(docs_dir)
    if not texts:
        print("No documents found. Please add files to data/")
        return

    rag = RAGPipeline(texts)
    question = input("\nEnter your question: ")
    answer = rag.query(question)
    
    print("\nRetrived "+ str(len(answer)) + " relevant chunks from RAG Pipeline.")
    
    for i, chunk in enumerate(answer, 1):
        
        print(f"\nChunk {i}:")
        print_chunk_as_row(chunk)
    
    # Append Question to the answer for context
    llm_answer = query_llm_api(question, "\n\n".join(answer))
    print("\nLLM Response:\n", llm_answer)
        
    output_df = None
    
    json_str = re.search(r"\{.*\}", llm_answer, re.DOTALL)
    if json_str:
        soql_params = json.loads(json_str.group())
        output_df = run_query(soql_params, 10)
        
        if output_df is not None:
            print("\nQuery Result (top 5 rows):\n", output_df.head())
        else:
            print("No data returned from the query.")
            
    else:
        print("No valid JSON found in LLM response.")
    
if __name__ == "__main__":
    # test_llm_api()
    main()