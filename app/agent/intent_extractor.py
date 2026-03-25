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
    You are a STRICT intent extraction system for a Vehicle Monitoring System (VMS).

    Query: {query}

    Available telemetry metrics:
    {fields}

    Your job:
    - Extract telemetry intent if the query is about sensor data
    - Identify if the query is about vehicle details
    
    1. DOMAIN CHECK (MANDATORY):
    - The query MUST be related to vehicle telemetry or vehicle details.
    - If the query is NOT related to vehicles, telemetry, or IMEI:
    → Return ALL fields as null.

    2. METRIC EXTRACTION RULE:
    - Extract metric ONLY if explicitly mentioned or clearly implied.
    - DO NOT guess or infer unrelated metrics.

    Rules:
    - If query is about telemetry (battery, voltage, speed, etc.) → service = null
    - If query asks for vehicle details, or metadata → service = "vehicle_service"
    - Do NOT invent information

    Aggregation mapping:
    average, mean, avg → "average"
    max, highest → "maximum"
    min, lowest → "minimum"
    
    Return ONLY JSON.
    Do NOT include explanation.
    Do NOT include markdown.
    Do NOT include multiple JSON objects.

    {{
    "metric": "one of {fields}" | null,
    "aggregation": "string" | null,
    "analysis": "string" | null,
    "time_range": "string" | null,
    "service": "vehicle_service" | null
    }}
    """

    prompt_2 = f"""
You are a STRICT intent extraction system for a Vehicle Monitoring System (VMS).

Query: {query}

Available telemetry metrics:
{fields}

--------------------------------------------------
STRICT INSTRUCTIONS:

1. DOMAIN CHECK (MANDATORY):
- The query MUST be related to vehicle telemetry or vehicle details.
- If the query is NOT related to vehicles, telemetry, or IMEI:
  → Return ALL fields as null.

Examples of OUT-OF-SCOPE:
- mobile phones, prices, news, sports, general knowledge
- If unsure → return null for everything

--------------------------------------------------
2. METRIC EXTRACTION RULE:

- Extract metric ONLY if explicitly mentioned or clearly implied.
- DO NOT guess or infer unrelated metrics.

Valid mappings:
- "speed" → speed
- "battery", "voltage" → batteryLevel
- "rpm" → engineRpm
- "temperature" → engineTemperature

If metric is not clearly present:
→ metric = null

--------------------------------------------------
3. VEHICLE DETAILS RULE:

- If query asks about vehicle metadata or specifically vehicle details not telemetry or analysis
  → service = "vehicle_service"

- Otherwise:
  → service = null

--------------------------------------------------
4. AGGREGATION RULE:

- average, mean, avg → "average"
- max, highest → "maximum"
- min, lowest → "minimum"

If not present → null

--------------------------------------------------
5. OUTPUT RULE (CRITICAL):
- Return EXACTLY ONE JSON object
- NO explanation
- NO text before JSON
- NO text after JSON
- NO markdown
- NO comments

--------------------------------------------------

OUTPUT FORMAT:

{{
  "metric": "one of {fields}" | null,
  "aggregation": "string" | null,
  "analysis": "string" | null,
  "time_range": "string" | null,
  "service": "vehicle_service" | null
}}
"""

    response = llm.generate(prompt_2)

    logger.info(f"Raw LLM Response: {response}")

    # Extract JSON block
    # json_match = re.search(r"\{.*\}", response, re.DOTALL)
    # json_match = re.findall(r"\{.*?\}", response, re.DOTALL)
    json_match = re.search(r"\{.*\}", response, re.DOTALL)

    if not json_match:
        logger.error(f"No JSON found. Raw response: {response}")
        raise ValueError("No JSON found in LLM response")

    json_str = json_match.group()

    logger.info(f"Query: {query}")
    logger.info(f"JSON response: {json_str}")

    data = json.loads(json_str)
    logger.info(f"JSON data: {data}")

    return QueryIntent(**data)