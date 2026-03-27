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

    if sample is None:
        logger.warning("No documents found in collection")
        return []

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
- Service → vehicle metadata requests (READ ONLY)
- Action → operation requested by user

--------------------------------------------------
CRITICAL RULE:

ACTION detection OVERRIDES everything.

--------------------------------------------------
FIELD EXTRACTION:

--------------------------------------------------
1. ACTION (HIGHEST PRIORITY)

Detect user intent:

- delete, remove → "delete"
- update, modify, change → "update"
- fetch, get, show, retrieve → "fetch"

If none → "fetch" (default safe read)

IMPORTANT:
- If action = delete or update:
  → service MUST be null
  → metric MUST be null

--------------------------------------------------
2. IMEI

- Extract ONLY 15-digit number
- If multiple → take FIRST
- Else → null

--------------------------------------------------
3. SERVICE (ONLY FOR READ QUERIES)

Apply ONLY if:
- action = "fetch"

AND query asks for:
- vehicle details
- vehicle information
- vehicle data
- metadata
- company, model, plate, make

Then:
→ service = "vehicle_service"

Else:
→ null

IMPORTANT:
- If action != fetch → service MUST be null

--------------------------------------------------
4. METRIC (STRICT)

- Must be EXACTLY from:
{fields}

Rules:
- ONLY extract if explicitly mentioned
- DO NOT infer
- DO NOT map IMEI
- DO NOT guess

STRICT NEGATIVE:
- "imei" is NOT a metric
- "device" is NOT a metric UNLESS explicitly mentioned in query

OVERRIDE:
- If service = "vehicle_service" → metric = null
- If action != "fetch" → metric = null

--------------------------------------------------
5. AGGREGATION

- avg → "average"
- max → "maximum"
- min → "minimum"

Else → null

Only if metric exists

--------------------------------------------------
6. ANALYSIS

- Extract ONLY if explicitly mentioned
Else → null

--------------------------------------------------
7. TIME RANGE

- today, yesterday, last week

Else → null

--------------------------------------------------
FINAL VALIDATION (STRICT):

- If action != "fetch":
    metric = null
    service = null

- metric must be from {fields} or null
- metric MUST NOT be "imei"
- metric MUST NOT be inferred

--------------------------------------------------
OUTPUT RULES:

- ONLY JSON
- NO explanation
- NO extra text

--------------------------------------------------

OUTPUT FORMAT:

{{
  "action": "fetch | delete | update",
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