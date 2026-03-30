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
You are a STRICT deterministic intent extraction system for a Vehicle Monitoring System (VMS).

Your output MUST be a valid JSON object.

--------------------------------------------------
INPUT:
Query: {query}

Available Metrics (STRICT LIST):
{fields}

--------------------------------------------------
CORE DEFINITIONS:

- IMEI → 15-digit identifier (NOT a metric)
- Metric → telemetry field from provided list ONLY
- Aggregation → operation on metric
- Service → vehicle metadata request
- Action → user operation

--------------------------------------------------
FIELD EXTRACTION ORDER (STRICT):

1. ACTION
2. IMEI
3. AGGREGATION
4. METRIC
5. SERVICE
6. TIME RANGE
7. ANALYSIS

--------------------------------------------------
1. ACTION (STRICT – NO GUESSING)

Determine action ONLY using explicit keywords from the query.

DELETE:
- Trigger ONLY if query contains EXACT words:
  "delete", "remove", "erase"

UPDATE:
- Trigger ONLY if query contains EXACT words:
  "update", "modify", "change"

FETCH:
- Trigger if query contains:
  "get", "fetch", "show", "retrieve", "what", "list"

  
DEFAULT:
- If NONE of the above keywords are present:
  → action = "fetch"


CRITICAL RULES:
- DO NOT infer action
- DO NOT assume intent
- DO NOT use context outside the query
- If "delete" keyword is NOT present → action MUST NOT be "delete"
- If "update" keyword is NOT present → action MUST NOT be "update"

If action != "fetch":
→ metric = null
→ aggregation = null
→ service = null

--------------------------------------------------
2. IMEI

- Extract ONLY 15-digit number
- If multiple → take FIRST
- Else → null

--------------------------------------------------
3. AGGREGATION (HIGH PRIORITY)

Mappings:

- average, avg, mean → "average"
- maximum, max, highest → "maximum"
- minimum, min, lowest → "minimum"

RULES:
- If keyword exists → MUST extract
- Case insensitive
- Else → null

--------------------------------------------------
4. METRIC

- Must be EXACT match from:
{fields}

RULES:
- Extract ONLY if explicitly mentioned
- DO NOT infer
- DO NOT guess
- DO NOT map IMEI

STRICT:
- "imei" is NOT a metric
- "device" only if explicitly present

--------------------------------------------------
5. SERVICE

Apply ONLY IF:
- action = "fetch"
- metric = null
- aggregation = null

AND query asks for:
- vehicle details
- vehicle information
- metadata

Then:
→ "vehicle_service"

Else → null

--------------------------------------------------
6. TIME RANGE

- today, yesterday, last week
Else → null

--------------------------------------------------
7. ANALYSIS

- Only if explicitly present
Else → null

--------------------------------------------------
FINAL VALIDATION (STRICT):

- If aggregation != null → metric MUST NOT be null
- If metric != null → service MUST be null
- If service != null → metric = null AND aggregation = null
- IMEI must NOT affect metric
- NO guessing

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