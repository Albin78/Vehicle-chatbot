import json
import re

from app.db.mongoclient import get_collection
from app.llm.ollama_client import OllamaClient
from app.schemas.intent_schema import QueryIntent
from app.tools.vehicle_cache import resolve_intent
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




def extract_intent(query: str) -> QueryIntent :  

    fields = get_db_fields()

    prompt_final = f"""
You are an intent extraction engine for a Vehicle Monitoring System (VMS).

Your task is to understand the user query and extract structured intent.

Return ONLY a valid JSON object.
No explanation.
No extra text.
No markdown.

----------------------------------------
INPUT:
Query: {query}

Available Metrics (REFERENCE ONLY):
{fields}

----------------------------------------

TASK:

Extract the following fields based ONLY on what is explicitly stated in the query:

- action: "fetch", "delete", or "update"
- imei: a 15-digit identifier if present
- metric: telemetry field ONLY if explicitly mentioned in the query
- aggregation: "average", "maximum", or "minimum" if clearly requested
- time_range: "today", "yesterday", or "last_week" if mentioned
- analysis: any analytical intent if clearly expressed
- service: "vehicle_service" ONLY if the query is about vehicle details or metadata

----------------------------------------

CORE INSTRUCTION:

This is an EXTRACTION task, not a prediction task.

Only extract information that is directly present in the query text.

If something is not clearly present → return null.

It is VALID for all fields to be null.

----------------------------------------

METRIC EXTRACTION (CRITICAL):

- A metric must be extracted ONLY if the exact metric term appears in the query.
- The term must match EXACTLY one of the available metrics.
- Treat the metric list as a validation reference, NOT as options to choose from.

DO NOT:
- infer metrics
- map similar meanings
- substitute words
- guess from context

Examples:

Query: "vehicle details for imei 123456789012345"
→ metric = null

Query: "what is speed for imei 123456789012345"
→ metric = "speed"

Query: "iphone price"
→ metric = null

----------------------------------------

DOMAIN UNDERSTANDING:

First determine if the query belongs to VMS domain.

VMS includes:
- vehicle-related queries
- IMEI-based queries
- telemetry data (speed, battery, rpm, etc.)

If the query is NOT related to VMS:
→ return all fields null (except action = "fetch")

DO NOT attempt to map unrelated queries.

----------------------------------------

SERVICE EXTRACTION:

- Use "vehicle_service" ONLY when the user is asking about vehicle details or metadata
- Do NOT use service for telemetry queries

----------------------------------------

IMPORTANT BEHAVIOR:

- Prefer null over incorrect extraction
- Do not force mapping between query and schema
- Do not try to fill all fields
- Do not use the metric list unless the word appears in the query

----------------------------------------

OUTPUT FORMAT:

{{
  "action": "fetch | delete | update",
  "imei": "string | null",
  "metric": "string | null",
  "aggregation": "average | maximum | minimum | null",
  "analysis": "string | null",
  "time_range": "today | yesterday | last_week | null",
  "service": "vehicle_service | null"
}}
"""

    prompt = f"""

You are a production-grade Intent Extraction Engine for a Vehicle Monitoring System (VMS).

Your task is to extract structured intent from a user query.

--------------------------------------------------
CRITICAL OUTPUT RULES (NON-NEGOTIABLE)

- Output MUST be VALID JSON
- NO explanation
- NO extra text
- NO markdown
- ALL null values MUST be actual null (NOT "null" string)

--------------------------------------------------
INPUT:
Query: {query}

Available Metrics:
{fields}

--------------------------------------------------
STEP 0: DOMAIN GATE (HIGHEST PRIORITY)

First determine if the query belongs to VMS domain.

VMS DOMAIN includes:
- Vehicle queries
- IMEI-based queries
- Telemetry (speed, battery, fuel, rpm, etc.)
- Fleet / tracking / device data

OUT-OF-DOMAIN includes:
- Phones (iPhone, Samsung, etc.)
- Shopping / price queries
- News / weather / general knowledge

IF query is OUT-OF-DOMAIN:
RETURN IMMEDIATELY:

{{
  "action": "fetch",
  "imei": null,
  "metric": null,
  "aggregation": null,
  "analysis": null,
  "time_range": null,
  "service": null
}}

DO NOT PROCESS FURTHER.

--------------------------------------------------
STEP 1: ACTION

Detect action:

- delete/remove/erase → "delete"
- update/modify/change → "update"
- otherwise → "fetch"

--------------------------------------------------
STEP 2: IMEI

- Extract ONLY 15-digit number
- If multiple → take FIRST
- Else → null

--------------------------------------------------
STEP 3: METRIC (HIGH PRIORITY SIGNAL)

- Extract ONLY if explicitly present in:
{fields}

- If IMEI is null → metric MUST be null

--------------------------------------------------
STEP 4: AGGREGATION

- avg/average/mean → "average"
- max/highest → "maximum"
- min/lowest → "minimum"

Else → null

--------------------------------------------------
STEP 5: HARD DECISION GATE (MOST IMPORTANT)

This step OVERRIDES everything below.

IF metric != null:
→ service MUST be null (NO EXCEPTION)

IF aggregation != null:
→ metric MUST NOT be null

--------------------------------------------------
STEP 6: SERVICE (ONLY IF SAFE)

Assign service = "vehicle_service" ONLY IF:

ALL conditions are TRUE:

1. action == "fetch"
2. metric == null
3. aggregation == null
4. Query is asking about vehicle metadata

Examples:
- "vehicle details for imei"
- "show vehicle info"
- "details of vehicle"

Otherwise:
→ service = null

--------------------------------------------------
STEP 7: TIME RANGE

- today → "today"
- yesterday → "yesterday"
- last week → "last_week"

Else → null

--------------------------------------------------
STEP 8: ANALYSIS

- Only if explicitly present
Else → null

--------------------------------------------------
FINAL VALIDATION (STRICT)

- If action != "fetch":
    metric = null
    aggregation = null
    service = null

- If metric != null:
    service = null   ← HARD OVERRIDE

- If aggregation != null AND metric == null:
    aggregation = null

--------------------------------------------------
FINAL OUTPUT FORMAT:

{{
  "action": "fetch | delete | update",
  "imei": "15-digit string | null",
  "metric": "value from list or null",
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
    


