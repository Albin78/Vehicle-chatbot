import json
import re

from app.db.mongoclient import get_collection
from app.llm.ollama_client import OllamaClient
from app.schemas.intent_schema import QueryIntent
from app.utils.logger import logger

llm = OllamaClient()


def get_db_fields():

    collection = get_collection()
    print(f"The mongo collection: {collection}")

    sample = collection.find_one()
    print(f"Sample from mongo: {sample}")

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
You are an intent extraction engine for a Vehicle Monitoring System (VMS).

Return ONLY a valid JSON object.
No explanation.
No extra text.

----------------------------------------
INPUT:
Query: {query}

VALID METRICS (REFERENCE ONLY):
{fields}

----------------------------------------

TASK:

Understand the user query and extract structured intent.

----------------------------------------

STEP 1 — DOMAIN CHECK:

If the query is NOT related to:
- vehicles
- IMEI
- telemetry

Return EXACTLY:

{{
  "action": "fetch",
  "imei": null,
  "metric": null,
  "aggregation": null,
  "analysis": null,
  "time_range": null,
  "service": null
}}

----------------------------------------

STEP 2 — INTENT TYPE CLASSIFICATION:

Classify the query into ONE type:

TYPE A: TELEMETRY QUERY
→ asking for measurable data (speed, battery, rpm, etc.)

TYPE B: VEHICLE METADATA QUERY
→ asking for vehicle details/info using IMEI

IMPORTANT:
- A query CANNOT be both types
- Choose ONLY ONE

----------------------------------------

STEP 3 — EXTRACTION RULES:

COMMON:

- action:
  "delete" or "update" ONLY if explicitly present
  else "fetch"

- imei:
  extract ONLY if exactly 15 digits
  else null

----------------------------------------

IF TYPE A (TELEMETRY):

- metric:
  extract ONLY if exact word appears in query AND exists in VALID METRICS
  else null

- aggregation:
  minimum / min → "minimum"
  maximum / max → "maximum"
  average / avg → "average"
  else null

- service:
  MUST be null

----------------------------------------

IF TYPE B (VEHICLE METADATA):

- service:
  "vehicle_service"

- metric:
  MUST be null

- aggregation:
  MUST be null

----------------------------------------

OTHER FIELDS:

- time_range:
  today / yesterday / last week if explicitly present

- analysis:
  ONLY if explicitly stated

----------------------------------------

CRITICAL BEHAVIOR:

- DO NOT guess
- DO NOT infer
- DO NOT map similar meanings
- DO NOT pick values from list unless present in query
- Prefer null over incorrect extraction

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


    response = llm.generate(prompt)

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
    


