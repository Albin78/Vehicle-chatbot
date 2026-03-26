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

    prompt_optimized = f"""
You are a STRICT structured intent extraction system for a Vehicle Monitoring System (VMS).

Your output MUST be a valid JSON object.

--------------------------------------------------
INPUT:
Query: {query}

Available Metrics:
{fields}

--------------------------------------------------
CORE PRINCIPLE:

- IMEI is an IDENTIFIER (15-digit number)
- Metrics are TELEMETRY fields (speed, batteryLevel, etc.)
- IMEI and metric are COMPLETELY DIFFERENT
- IMEI MUST NEVER be treated as a metric

--------------------------------------------------
TASK:

Extract the following fields from the query:
- imei
- metric
- aggregation
- analysis
- time_range
- service

--------------------------------------------------
RULES:

1. DOMAIN FILTER (STRICT):
If query is NOT related to:
- vehicle
- telemetry
- IMEI
- vehicle data

Return:
{{
  "imei": null,
  "metric": null,
  "aggregation": null,
  "analysis": null,
  "time_range": null,
  "service": null
}}

--------------------------------------------------
2. IMEI EXTRACTION (HIGHEST PRIORITY):

- Extract ONLY if there is a 15-digit number
- If multiple 15-digit numbers exist → extract the FIRST one
- If none → imei = null
- DO NOT guess or modify IMEI

IMPORTANT:
- IMEI MUST NOT influence metric extraction

--------------------------------------------------
3. METRIC EXTRACTION (STRICT):

- Extract metric ONLY if explicitly mentioned
- Metric MUST be one of: {fields}
- DO NOT infer from IMEI or numbers

IMPORTANT NEGATIVE RULE:
- A 15-digit number (IMEI) is NOT a metric
- DO NOT map IMEI to any metric like "Device"

If metric is not clearly mentioned:
→ metric = null

--------------------------------------------------
4. SERVICE RULE:

- If query asks vehicle metadata (company, model, plate, etc.)
  → service = "vehicle_service"
  → metric MUST be null

- Otherwise:
  → service = null

--------------------------------------------------
5. AGGREGATION RULE:

- avg, mean → "average"
- max → "maximum"
- min → "minimum"
- Else → null

--------------------------------------------------
6. STRICT OUTPUT RULE:

- Return EXACTLY ONE JSON object
- NO explanation
- NO text before JSON
- NO text after JSON
- NO markdown
- NO comments

--------------------------------------------------

OUTPUT FORMAT:

{{
  "imei": "15-digit string | null",
  "metric": "string | null",
  "aggregation": "string | null",
  "analysis": "string | null",
  "time_range": "string | null",
  "service": "vehicle_service | null"
}}
"""



    prompt_3 = f"""
You are a machine system that extracts structured intent for a Vehicle Monitoring System (VMS).

Your output MUST be a valid JSON object.

--------------------------------------------------
INPUT:
Query: {query}

Available Metrics:
{fields}

--------------------------------------------------
TASK:

Extract intent fields from the query.

--------------------------------------------------
RULES:

1. DOMAIN FILTER:
If query is NOT related to:
- vehicle
- telemetry
- IMEI
- vehicle data

Then return:
{{
  "metric": null,
  "aggregation": null,
  "analysis": null,
  "time_range": null,
  "service": null
}}

2. IMEI EXTRACTION:
- Extract IMEI ONLY if it is a 15-digit number
- If not found → imei = null
- DO NOT guess IMEI


3. SERVICE:
- If query asks vehicle metadata (company, model, plate, etc.)
  → "vehicle_service"
- Else → null

4. AGGREGATION:
- avg, mean → "average"
- max → "maximum"
- min → "minimum"
- Else → null

5. STRICT OUTPUT FORMAT:

- Output MUST be in valid JSON format
- NO explanation
- NO extra text
- NO multiple JSON objects
- NO markdown

--------------------------------------------------

OUTPUT FORMAT:

{{
  "imei": "15-digit string | null",
  "metric": "string | null",
  "aggregation": "string | null",
  "analysis": "string | null",
  "time_range": "string | null",
  "service": "vehicle_service | null"
}}
"""

    response = llm.generate(prompt_optimized)

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