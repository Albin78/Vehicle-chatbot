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

Your job is to extract values from a user query into a FIXED JSON structure.

----------------------------------------
OUTPUT FORMAT (STRICT):

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
RULES:

- Output ONLY valid JSON
- Do NOT explain anything
- Do NOT add extra keys
- Use null (not "null")
- Extract values when clearly present
- Do NOT overthink — simple extraction

----------------------------------------
INPUT:

Query: {query}

VALID METRICS:
{fields}

----------------------------------------
1. ACTION:

- If query contains "delete" → "delete"
- If query contains "update" → "update"
- Otherwise → "fetch"

----------------------------------------
2. VEHICLE ID (HIGH PRIORITY):

Extract vehicle identifier if present.

Look for patterns like:
- "vehicle id <value>"
- "vehicle number <value>"
- "vehicle <value>"
- "id <value>"
- "for <value>"
- "of <value>"

IMPORTANT:
- Vehicle ID can contain letters, numbers, and spaces
- Example: "4672 J R B", "33 AZS", "7895 CCC"
- Extract FULL value after keyword
- DO NOT return null if a vehicle is clearly mentioned

----------------------------------------
3. METRIC:

- Match ONLY exact words from VALID METRICS
- Example: speed, battery_level, idle_time
- If not present → null

----------------------------------------
4. AGGREGATION:

- "minimum" or "min" → "minimum"
- "maximum" or "max" → "maximum"
- "average" or "avg" → "average"
- Else → null

----------------------------------------
5. TIME RANGE:

Extract if present.

KEYWORDS:
- "today" → "today"
- "yesterday" → "yesterday"
- "last week" → "last_week"
- "last X days" → "last_X_days"

DATE RANGE:
- "from <date> to <date>"
- "between <date> and <date>"

Examples:
- "from April 1 to April 10"
- "between 2026-04-01 and 2026-04-10"

Return the FULL text span.

----------------------------------------
6. SERVICE:

Always return null.

----------------------------------------
EXAMPLES:

Query: Fetch details of vehicle with id 4672 J R B
Output:
{{
"action": "fetch",
"vehicle_id": "4672 J R B",
"metric": null,
"aggregation": null,
"analysis": null,
"time_range": null,
"service": null
}}

----------------------------------------

RETURN ONLY JSON
"""


    response = llm.generate(prompt)

    logger.info(f"Raw LLM Response: {response}")

    # Extract JSON block
    # json_match = re.search(r"\{.*\}", response, re.DOTALL)
    # json_match = re.findall(r"\{.*?\}", response, re.DOTALL)
    json_match = re.search(r"\{[\s\S]*?\}", response)

    if not json_match:
        logger.error(f"No JSON found. Raw response: {response}")
        raise ValueError("No JSON found in LLM response")

    json_str = json_match.group()

    logger.info(f"Query: {query}")
    logger.info(f"JSON response: {json_str}")

    try:
        data = json.loads(json_str)
        logger.info(f"JSON data: {data}")

    except Exception:
      logger.error("JSON parsing failed")
      data = {
          "action": "fetch",
          "vehicle_id": None,
          "metric": None,
          "aggregation": None,
          "analysis": None,
          "time_range": None,
          "service": None
      }

    return QueryIntent(**data)
    


