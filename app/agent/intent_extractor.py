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

Do NOT invent information that is not present in the query.

Map synonyms to the correct aggregation:

average, mean, avg → "average"  
max, highest → "maximum"  
min, lowest → "minimum"  

Return ONLY valid JSON.

{{
 "metric": "one of {fields} or null",
 "aggregation": "string | null",
 "analysis": "string | null",
 "time_range": "string | null",
 "service": "string | null"
}}
"""

    prompt_1 = f"""
    You are an intent extraction system.

    Query: {query}

    Available telemetry metrics:
    {fields}

    Your job:
    - Extract telemetry intent if the query is about sensor data
    - Identify if the query is about vehicle details

    Rules:
    - If query is about telemetry (battery, voltage, speed, etc.) → service = null
    - If query asks for vehicle details, or metadata → service = "vehicle_service"
    - Do NOT invent information

    Aggregation mapping:
    average, mean, avg → "average"
    max, highest → "maximum"
    min, lowest → "minimum"

    Return ONLY valid JSON:

    {{
    "metric": "one of {fields} or null",
    "aggregation": "string | null",
    "analysis": "string | null",
    "time_range": "string | null",
    "service": "vehicle_service | null"
    }}
    """

    response = llm.generate(prompt_1)

    # Extract JSON block
    json_match = re.search(r"\{.*\}", response, re.DOTALL)
    # json_match = re.search(r"\{.*?\}", response, re.DOTALL)

    if not json_match:
        raise ValueError("No JSON found in LLM response")

    json_str = json_match.group()

    logger.info(f"Query: {query}")
    logger.info(f"JSON response: {json_str}")

    data = json.loads(json_str)
    logger.info(f"JSON data: {data}")

    return QueryIntent(**data)