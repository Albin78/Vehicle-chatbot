import json
import re

from app.db.mongoclient import get_collection
from app.llm.ollama_client import OllamaClient
from app.schemas.intent_schema import QueryIntent
from app.utils.logger import logger

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

    excluded = {"_id", "imei", "date", "sensor"}
    fields = [k for k in sample.keys() if k not in excluded]

    return fields


# --------------------------------------------------
# SANITIZE LLM OUTPUT (CRITICAL)
# --------------------------------------------------
def sanitize_llm_output(raw: str) -> dict:
    """
    Extract and sanitize JSON from LLM output.
    Handles:
    - Extra text
    - Broken JSON
    - Nested structures
    - Hallucinated fields
    """

    if not raw:
        return DEFAULT_INTENT

    try:
        # Extract FIRST valid JSON block (greedy safe)
        match = re.search(r"\{[\s\S]*\}", raw)

        if not match:
            logger.error(f"No JSON found in response: {raw}")
            return DEFAULT_INTENT

        json_str = match.group()

        data = json.loads(json_str)

    except Exception as e:
        logger.error(f"JSON parsing failed: {e}")
        return DEFAULT_INTENT

    # -----------------------------
    # HARD VALIDATION LAYER
    # -----------------------------
    clean_data = {}

    for key in DEFAULT_INTENT.keys():

        value = data.get(key, None)

        # Reject nested objects or lists
        if isinstance(value, (dict, list)):
            logger.warning(f"Invalid nested value for {key}: {value}")
            value = None

        # Normalize null-like strings
        if isinstance(value, str) and value.strip().lower() in {"null", "none", ""}:
            value = None

        clean_data[key] = value

    return clean_data


# --------------------------------------------------
# INTENT EXTRACTION
# --------------------------------------------------
def extract_intent(query: str) -> QueryIntent:

    fields = get_db_fields()

    prompt = f"""
You are a STRICT JSON extractor.

You MUST return ONLY ONE valid JSON object.

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
CRITICAL RULES (DO NOT VIOLATE):

- Output MUST be valid JSON
- NO explanation
- NO extra text
- NO markdown
- NO multiple JSON blocks
- NO additional keys (STRICTLY FORBIDDEN)
- NO nested objects
- NO arrays

VALID OUTPUT EXAMPLE:

{{
  "action": "fetch",
  "vehicle_id": "4673 J R B",
  "metric": "speed",
  "aggregation": "maximum",
  "analysis": null,
  "time_range": "april 1 to 10",
  "service": null
}}

----------------------------------------
INVALID OUTPUT EXAMPLES (DO NOT DO THIS):

❌ {{"vehicle_id": {{"value": "4673"}}}}
❌ {{"data": {{...}}}}
❌ Any extra keys
❌ Multiple JSON objects

----------------------------------------
ACTION:

- "delete" → delete
- "update" → update
- else → fetch

----------------------------------------
VEHICLE ID:

Extract ONLY the value after:
- vehicle
- vehicle id
- vehicle number
- id

Example:
"vehicle 4673 J R B" → "4673 J R B"

----------------------------------------
METRIC + AGGREGATION:

VALID BASE METRICS:
{fields}

RULES:

1. If metric word appears EXACTLY → use it
2. If phrase like:
   - "top speed", "highest speed"
     → metric = "speed"
     → aggregation = "maximum"

3. ONLY map if base word exists (e.g., "speed")

4. If unclear → metric = null

----------------------------------------
TIME RANGE:

Normalize:
- "april 1-10"
- "between april 1 and 10"

→ "april 1 to 10"

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

    raw_response = llm.generate(prompt)

    logger.info(f"Raw LLM Response: {raw_response}")

    # -----------------------------
    # SANITIZE OUTPUT
    # -----------------------------
    clean_data = sanitize_llm_output(raw_response)

    logger.info(f"Sanitized JSON: {clean_data}")

    # -----------------------------
    # FINAL INTENT OBJECT
    # -----------------------------
    try:
        intent = QueryIntent(**clean_data)
    except Exception as e:
        logger.error(f"Pydantic validation failed: {e}")
        intent = QueryIntent(**DEFAULT_INTENT)

    logger.info(f"Final Intent: {intent}")

    return intent