import json
import re

from app.llm.ollama_client import OllamaClient
from app.schemas.intent_schema import QueryIntent

llm = OllamaClient()


def get_db_fields():

    collection = get_collection()

    sample = collection.find_one()

    excluded = {"_id", "imei", "date", "sensor"}

    fields = [k for k in sample.keys() if k not in excluded]

    return fields
    

def extract_intent(query: str) -> QueryIntent:

    prompt = f"""
You are an AI that extracts telemetry query intent. Extract telemetry query intent.

Query: {query}

Return ONLY valid JSON.

{{
 "metric": "string | null",
 "aggregation": "string | null",
 "analysis": "string | null",
 "time_range": "string | null",
 "service": "string | null"
}}
"""

    response = llm.generate(prompt)

    # Extract JSON block
    json_match = re.search(r"\{.*\}", response, re.DOTALL)

    if not json_match:
        raise ValueError("No JSON found in LLM response")

    json_str = json_match.group()
    print("JSON response: ", json_str)

    data = json.loads(json_str)
    print("JSON data: ", data)

    return QueryIntent(**data)