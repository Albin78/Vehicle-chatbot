import re

from app.db.mongoclient import get_collection
from app.llm.ollama_client import OllamaClient
from app.schemas.intent_schema import QueryIntent
from app.utils.logger import logger
from app.validators.intent_validators import sanitize_llm_output, post_validate
from app.parsers.date_parser import extract_time_range

llm = OllamaClient()


# --------------------------------------------------
# DEFAULT SAFE INTENT (FALLBACK)
# --------------------------------------------------
DEFAULT_INTENT = {
    "action": "fetch",
    "vehicle_id": None,
    "metric": None,
    "aggregation": None,
    "analysis": None,
    "time_range": None,
    "service": None
}


# --------------------------------------------------
# FETCH DB FIELDS (FOR METRIC CONTROL)
# --------------------------------------------------
def get_db_fields():
    collection = get_collection()
    logger.info(f"Mongo collection: {collection}")

    sample = collection.find_one()

    if not sample:
        logger.warning("No documents found in collection")
        return []

    excluded = {"_id", "imei", "date", "sensor", "moving_time", "last_updated"}
    fields = [k for k in sample.keys() if k not in excluded]
    logger.info(f"Fields available: {fields}")

    return fields



# INTENT EXTRACTION
def extract_intent(query: str) -> QueryIntent:

    fields = get_db_fields()

    prompt = f"""
You are a STRICT JSON extractor for a Vehicle Monitoring System.

You MUST return ONLY ONE valid JSON object.

----------------------------------------
STEP 1: RELEVANCE CHECK (MANDATORY)

First determine if the query is related to vehicle monitoring.

A query is VALID ONLY IF it asks about:
- vehicle data (speed, distance, idle time, moving time, etc.)
- vehicle activity or performance
- vehicle analytics over time

A query is INVALID if:
- it asks about people, general knowledge, or unrelated topics
- it contains a vehicle_id but the intent is NOT about vehicle data

----------------------------------------
EXAMPLES:

VALID:
"maximum speed of vehicle 4673 J R B"
"distance traveled by 6534 AKA from april 1 to 10"

INVALID:
"who is cristiano ronaldo with vehicle 4673 J R B"
"iphone price for vehicle 6534 AKA"
"tell me about elon musk 4673 J R B"

----------------------------------------
CRITICAL RULE:

IF query is INVALID:
RETURN EXACTLY THIS JSON:

{{
  "action": null,
  "vehicle_id": null,
  "metric": null,
  "aggregation": null,
  "analysis": null,
  "time_range": null,
  "service": null
}}

DO NOT extract anything.
DO NOT partially fill fields.
DO NOT explain.

----------------------------------------
ONLY IF query is VALID → continue below

----------------------------------------
SCHEMA (STRICT):

{{
  "action": "fetch | update | delete",
  "vehicle_id": string | null,
  "metric": string | null,
  "aggregation": "minimum" | "maximum" | "average" | null,
  "analysis": string | null,
  "time_range": string | null,
  "service": null
}}

----------------------------------------
CRITICAL OUTPUT RULES:

- Output MUST be valid JSON
- NO explanation
- NO extra text
- NO markdown
- NO multiple JSON blocks
- NO additional keys
- NO nested objects
- NO arrays

----------------------------------------
ACTION:

- "delete" → delete
- "update" → update
- else → fetch

----------------------------------------
VEHICLE ID (STRICT HARD RULE)

A vehicle ID MUST follow:

- Starts with 2–5 digits
- Followed by 1–4 uppercase letters OR digits
- May contain spaces

VALID:
"4673 J R B"
"6534 AKA"
"53380 533"
"6667 DKB"

INVALID:
"iphone price"
"vehicle details"

RULES:
- If pattern NOT found → return null
- DO NOT guess
- DO NOT extract random phrases

METRIC (VERY STRICT)

A metric MUST be extracted ONLY if the EXACT word appears in the query.

STRICT RULES:
- DO NOT infer from words like "details", "report", "summary"
- DO NOT assume default metrics
- DO NOT pick the most common metric
- DO NOT use domain knowledge

CRITICAL:
If the metric word is NOT explicitly present → return null

EXAMPLES:

"speed of vehicle" → "speed"
"average speed" → "speed"

"vehicle details" → null
"vehicle report" → null
"vehicle data" → null

The list of valid metrics is ONLY for validation, NOT for selection.
DO NOT pick a metric just because it exists in the list.

----------------------------------------
AGGREGATION (STRICT — NO EXCEPTIONS)

Map ONLY from user words:

- "minimum", "lowest", "least" → "minimum"
- "maximum", "highest", "top", "peak" → "maximum"
- "average", "mean", "avg" → "average"

RULES:

- NEVER infer aggregation
- NEVER override user wording
- If not present → null

----------------------------------------
TIME RANGE (STRICT)

Extract ONLY if explicitly present.

VALID:
- "april 1-10" → "april 1 to 10"
- "between april 1 and 10" → "april 1 to 10"

RULES:
- If not present → null
- DO NOT guess
- DO NOT reuse examples

----------------------------------------
SERVICE:

Always null

----------------------------------------
INPUT:
{query}

----------------------------------------
OUTPUT:
Return ONLY JSON.
"""

    raw_response = llm.generate(prompt,)

    logger.info(f"Raw LLM Response: {raw_response}")

    # -----------------------------
    # SANITIZE OUTPUT
    # -----------------------------
    clean_data = sanitize_llm_output(raw_response)
    clean_data = post_validate(clean_data, query, fields)

    logger.info(f"After post validation JSON: {clean_data}")
    
    time_range = extract_time_range(query)

    if time_range:
        clean_data["time_range"] = time_range
    else:
        clean_data["time_range"] = None
    # -----------------------------
    # FINAL INTENT OBJECT
    # -----------------------------
    try:
        intent = QueryIntent(**clean_data)
    except Exception as e:
        logger.error(f"Pydantic validation failed: {e}")
        intent = QueryIntent(**DEFAULT_INTENT)

    logger.info(f"Final Intent: {intent}")
    logger.info(f"Type of intent: {type(intent)}")

    return intent