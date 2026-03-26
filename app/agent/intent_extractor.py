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

    prompt_final = f"""
You are a STRICT and deterministic intent extraction system for a Vehicle Monitoring System (VMS).

Your output MUST be a valid JSON object.

--------------------------------------------------
INPUT:
Query: {query}

Available Metrics (STRICT LIST):
{fields}

--------------------------------------------------
CORE DEFINITIONS:

- IMEI → a 15-digit IDENTIFIER (NOT a metric)
- Metrics → telemetry fields ONLY from the provided list
- Service → vehicle metadata or vehicle information requests

--------------------------------------------------
CRITICAL GLOBAL RULES:

- NEVER guess metric
- NEVER hallucinate values
- If unsure about a field → return null
- Fields must be extracted independently

IMPORTANT:
- LIMITED semantic understanding is allowed ONLY for SERVICE detection

--------------------------------------------------
FIELD EXTRACTION RULES:

--------------------------------------------------
1. IMEI (HIGHEST PRIORITY)

- Extract ONLY a 15-digit number
- If multiple → take FIRST
- If none → null

IMPORTANT:
- IMEI MUST NOT influence metric

--------------------------------------------------
2. SERVICE (INTENT DETECTION - ALLOWED SEMANTIC MATCHING)

Set service = "vehicle_service" IF query contains intent like:

- vehicle details
- vehicle information
- fetch vehicle
- vehicle data
- details of vehicle
- vehicle info
- metadata
- company, model, plate, make

IMPORTANT:
- This does NOT require exact keyword match
- Semantic meaning is enough

Examples:
- "Fetch vehicle details" → vehicle_service
- "Get details for imei" → vehicle_service
- "Show vehicle info" → vehicle_service

Otherwise:
→ service = null

--------------------------------------------------
3. METRIC (STRICT CONTROL)

- Metric MUST be EXACTLY one of:
{fields}

STRICT RULES:
- ONLY extract if explicitly mentioned
- DO NOT infer
- DO NOT use IMEI
- DO NOT guess

STRICT NEGATIVE:
- "imei" is NOT a metric
- If not clearly present → metric = null

OVERRIDE RULE:
- If service = "vehicle_service"
  → metric MUST be null

--------------------------------------------------
4. AGGREGATION

- avg, mean → "average"
- max → "maximum"
- min → "minimum"

STRICT:
- ONLY if explicitly present
- Else → null

--------------------------------------------------
5. ANALYSIS

- Extract ONLY if explicitly mentioned
- Else → null

--------------------------------------------------
6. TIME RANGE

- today → "today"
- yesterday → "yesterday"
- last week → "last_week"

STRICT:
- ONLY if explicitly mentioned
- Else → null

--------------------------------------------------
FINAL VALIDATION (MANDATORY):

Before output:

- metric must be from {fields} or null
- metric must NOT be "imei"
- if service = "vehicle_service" → metric = null
- no field should contain guessed values

--------------------------------------------------
OUTPUT RULES:

- Return EXACTLY ONE JSON object
- NO explanation
- NO extra text
- NO markdown

--------------------------------------------------

OUTPUT FORMAT:

{{
  "imei": "15-digit string | null",
  "metric": "one of {fields} or null",
  "aggregation": "average | maximum | minimum | null",
  "analysis": "string | null",
  "time_range": "today | yesterday | last_week | null",
  "service": "vehicle_service | null"
}}
"""

    response = llm.generate(prompt_final)

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