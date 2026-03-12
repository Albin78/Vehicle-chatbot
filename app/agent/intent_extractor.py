import json
import re

from app.db.mongoclient import get_collection
from app.llm.ollama_client import OllamaClient
from app.schemas.intent_schema import QueryIntent
from app.utils.logger import logger

llm = OllamaClient()


def get_db_fields():

    collection = get_collection()

    sample = collection.find_one()

    excluded = {"_id", "imei", "date", "sensor"}

    fields = [k for k in sample.keys() if k not in excluded]

    return fields


def extract_intent(query: str) -> QueryIntent:

    fields = get_db_fields()

    prompt = f"""
Extract telemetry query intent.

Query: {query}

Available telemetry metrics:
{fields}

Return ONLY valid JSON.

{{
 "metric": "one of {fields} or null",
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
    # logger.info("JSON response: ", json_str)
    print("JSON response: ", json_str)

    data = json.loads(json_str)
    # print("JSON data: ", data)

    return QueryIntent(**data)