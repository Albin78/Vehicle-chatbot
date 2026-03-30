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
You are a STRICT rule-based intent extraction engine for a Vehicle Monitoring System (VMS).

You MUST behave like a deterministic system. DO NOT infer, guess, or complete missing information.

--------------------------------------------------
INPUT:
Query: {query}

Available Metrics (STRICT LIST):
{fields}

--------------------------------------------------
STEP 0 — QUERY CLASSIFICATION (MANDATORY FIRST STEP)

Classify the query into ONE of the following:

1. TELEMETRY_QUERY
   → Requires IMEI + metric
   Example:
   "What is speed of imei 123456789012345"

2. SERVICE_QUERY
   → Explicit request for vehicle metadata
   Example:
   "Get vehicle details for imei 123456789012345"

3. INVALID_QUERY
   → Missing IMEI OR ambiguous OR generic question
   Examples:
   ❌ "What is speed of Land Cruiser"
   ❌ "Average speed of vehicle"
   ❌ "Tell me about cars"

--------------------------------------------------
CRITICAL RULE:

IF query is INVALID_QUERY:
→ RETURN all fields as null (except action)

DO NOT attempt extraction

--------------------------------------------------
STEP 1 — ACTION

- "delete", "remove", "erase" → delete
- "update", "modify", "change" → update
- "get", "fetch", "show", "retrieve", "what", "list" → fetch
- Default → fetch

--------------------------------------------------
STEP 2 — IMEI

- Extract ONLY 15-digit number
- Else → null

--------------------------------------------------
STEP 3 — TELEMETRY GATING (CRITICAL)

IF IMEI is null:
→ metric = null
→ aggregation = null

DO NOT extract metric or aggregation without IMEI

--------------------------------------------------
STEP 4 — AGGREGATION

- average, avg, mean → "average"
- maximum, max, highest → "maximum"
- minimum, min, lowest → "minimum"
- Else → null

--------------------------------------------------
STEP 5 — METRIC

- Extract ONLY if:
    1. IMEI exists
    2. Exact match from list

- DO NOT infer
- DO NOT guess

--------------------------------------------------
STEP 6 — SERVICE (STRICT)

SERVICE = "vehicle_service" ONLY IF:

ALL conditions TRUE:
1. action = fetch
2. metric = null
3. aggregation = null
4. IMEI exists
5. Query contains EXACT phrases:
   - "vehicle details"
   - "vehicle info"
   - "vehicle information"
   - "vehicle metadata"

ELSE:
→ service = null

--------------------------------------------------
STRICT PROHIBITIONS:

❌ DO NOT assign service for:
- "vehicle", "car", "truck"
- vehicle names (e.g., Land Cruiser)
- generic queries

--------------------------------------------------
STEP 7 — TIME RANGE

- today, yesterday, last week
Else → null

--------------------------------------------------
STEP 8 — ANALYSIS

- Only if explicitly present
Else → null

--------------------------------------------------
FINAL HARD VALIDATION (MANDATORY)

1. If IMEI is null:
   → metric = null
   → aggregation = null

2. If metric != null:
   → service = null

3. If aggregation != null:
   → service = null

4. If service != null:
   → metric = null
   → aggregation = null

5. If query classified as INVALID_QUERY:
   → metric = null
   → aggregation = null
   → service = null

DO NOT output invalid combinations

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