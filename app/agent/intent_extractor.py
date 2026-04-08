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

    prompt = f"""
You are a JSON extractor.

Your job is to FILL values into a FIXED JSON structure.

----------------------------------------
OUTPUT (COPY EXACTLY):

{{
  "action": "",
  "vehicle_id": null,
  "metric": null,
  "aggregation": null,
  "analysis": null,
  "time_range": null,
  "service": null
}}

----------------------------------------
RULES (STRICT):

- ONLY fill values
- DO NOT add new keys
- DO NOT output "imei"
- DO NOT output anything outside JSON
- Use null (not "null")

----------------------------------------
INPUT:

Query: {query}

VALID METRICS:
{fields}

----------------------------------------
FILLING RULES:

1. ACTION:
- if "delete" → "delete"
- if "update" → "update"
- else → "fetch"

----------------------------------------
2. VEHICLE ID (MANDATORY - TOP PRIORITY)

Search for EXACT text:

"vehicle id"
"vehicle number"
"vehicle_id"

IF FOUND:
- Take EVERYTHING after it
- Keep exact text (case + spaces)

Example:
"vehicle id 33 AZS" → "33 AZS"

CRITICAL:
- If phrase exists → vehicle_id MUST NOT be null
- Returning null is WRONG

----------------------------------------
3. METRIC:

- Match ONLY exact words from VALID METRICS
- DO NOT use:
  vehicle, vehicle id, vehicle number

----------------------------------------
4. AGGREGATION:

- min/minimum → "minimum"
- max/maximum → "maximum"
- avg/average → "average"

----------------------------------------
5. SERVICE:

IF vehicle_id != null AND metric == null:
→ "vehicle_service"

ELSE:
→ null

----------------------------------------
6. TIME RANGE:

- today → "today"
- yesterday → "yesterday"
- last week → "last_week"

----------------------------------------
7. ANALYSIS:

Always null unless clearly present

----------------------------------------
VALID EXAMPLE:

Query: Fetch details of vehicle with vehicle id 33 AZS

Output:
{{
  "action": "fetch",
  "vehicle_id": "33 AZS",
  "metric": null,
  "aggregation": null,
  "analysis": null,
  "time_range": null,
  "service": "vehicle_service"
}}

----------------------------------------

RETURN ONLY JSON
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
    


