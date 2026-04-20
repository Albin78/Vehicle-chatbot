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
# RULE-BASED VEHICLE ID EXTRACTION (STRONG FALLBACK)
# --------------------------------------------------
def extract_vehicle_id_rule_based(query: str) -> str | None:
    """
    Supports:
    - 4673 J R B
    - 6534 AKA
    - 7894 B B B
    - 53380 533
    - 97 J J J
    """

    query_upper = query.upper()

    # Capture flexible formats
    pattern = r"\b\d{2,5}(?:\s+[A-Z0-9]){1,4}\b"
    matches = re.findall(pattern, query_upper)

    if not matches:
        return None

    raw = matches[0]

    # Normalize → remove spaces
    normalized = re.sub(r"\s+", "", raw)

    # Final strict validation
    if not re.match(r"^\d{2,5}[A-Z0-9]{1,4}$", normalized):
        return None

    return normalized


def is_time_range_in_query(query: str) -> bool:
    query = query.lower()

    patterns = [
        r"\bbetween\b",
        r"\bfrom\b",
        r"\bto\b",
        r"\b\d{1,2}\b",            
        r"\bjan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec\b"
    ]

    return any(re.search(p, query) for p in patterns)


# --------------------------------------------------
# SANITIZE LLM OUTPUT
# --------------------------------------------------
def sanitize_llm_output(raw: str) -> dict:

    if not raw:
        return DEFAULT_INTENT

    try:
        match = re.search(r"\{[\s\S]*\}", raw)

        if not match:
            logger.error(f"No JSON found in response: {raw}")
            return DEFAULT_INTENT

        json_str = match.group()
        data = json.loads(json_str)

        if not isinstance(data, dict):
            logger.error(f"LLM returned non-dict JSON: {data}")
            return DEFAULT_INTENT

    except Exception as e:
        logger.error(f"JSON parsing failed: {e}")
        return DEFAULT_INTENT

    clean_data = {}

    for key in DEFAULT_INTENT.keys():
        value = data.get(key, None)

        # Reject invalid types
        if isinstance(value, (dict, list)):
            logger.warning(f"Invalid nested value for {key}: {value}")
            value = None

        # Normalize null-like strings
        if isinstance(value, str) and value.strip().lower() in {"null", "none", ""}:
            value = None

        clean_data[key] = value

    return clean_data


# --------------------------------------------------
# POST VALIDATION (CRITICAL LAYER)
# --------------------------------------------------
def post_validate(clean_data: dict, query: str, fields: list) -> dict:

    # -----------------------------
    # VEHICLE ID VALIDATION
    # -----------------------------
    vid = clean_data.get("vehicle_id")

    if isinstance(vid, str):
        normalized = re.sub(r"\s+", "", vid.upper())

        if re.match(r"^\d{2,5}[A-Z0-9]{1,4}$", normalized):
            clean_data["vehicle_id"] = normalized
        else:
            logger.warning(f"Rejected invalid vehicle_id: {vid}")
            clean_data["vehicle_id"] = None

    # FALLBACK (deterministic)
    if not clean_data.get("vehicle_id"):
        fallback_vid = extract_vehicle_id_rule_based(query)

        if fallback_vid:
            logger.info(f"Recovered vehicle_id from query: {fallback_vid}")
            clean_data["vehicle_id"] = fallback_vid

    # -----------------------------
    # METRIC VALIDATION
    # -----------------------------
    metric = clean_data.get("metric")

    if isinstance(metric, str):
        metric = metric.strip().lower()

        if metric not in fields:
            logger.warning(f"Rejected invalid metric: {metric}")
            clean_data["metric"] = None
        else:
            clean_data["metric"] = metric

    # -----------------------------
    # AGGREGATION VALIDATION
    # -----------------------------
    if clean_data.get("aggregation") and not clean_data.get("metric"):
        clean_data["aggregation"] = None

    # -----------------------------
    # TIME RANGE NORMALIZATION
    # -----------------------------
    tr = clean_data.get("time_range")

    if isinstance(tr, str):
        tr = tr.lower().strip()

        # Normalize patterns
        tr = re.sub(r"between (.+?) and (.+)", r"\1 to \2", tr)
        tr = re.sub(r"from (.+?) to (.+)", r"\1 to \2", tr)
        tr = re.sub(r"(\w+ \d+)-(\d+)", r"\1 to \2", tr)

        clean_data["time_range"] = tr

    return clean_data


# INTENT EXTRACTION
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
VEHICLE ID (STRICT HARD RULE)

A vehicle ID MUST follow this pattern:

- Starts with 2–5 digits
- Followed by 1–4 uppercase letters
- May contain spaces

VALID:
"4673 J R B"
"6534 AKA"
"7894 B B B"

INVALID:
"iphone price"
"vehicle details"
"speed report"

RULES:

- If pattern NOT found → return null
- DO NOT guess
- DO NOT extract random phrases

----------------------------------------
METRIC + AGGREGATION:

VALID BASE METRICS:
{fields}

RULES:

1. Metric MUST match EXACT word from list

2. IGNORE context words like:
   - report
   - details
   - summary
   - data

3. Valid examples:
   "speed report" → metric = "speed"
   "vehicle details" → metric = null

4. Allowed mappings:
   - "top speed" → speed + maximum
   - "highest speed" → speed + maximum

5. If unclear → metric = null

----------------------------------------
TIME RANGE (STRICT)

Extract ONLY if explicitly present in query.

VALID examples:
- "april 1-10" → "april 1 to 10"
- "between april 1 and 10" → "april 1 to 10"

RULES:

- If NO date/time mentioned → MUST return null
- DO NOT infer
- DO NOT guess
- DO NOT reuse example values

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
    clean_data = post_validate(clean_data, query, fields)

    logger.info(f"After post validation JSON: {clean_data}")
    
    tr = clean_data.get("time_range")

    if isinstance(tr, str):
        if not is_time_range_in_query(query):
            logger.warning(f"Removed hallucinated time_range: {tr}")
            clean_data["time_range"] = None
        else:
            tr = tr.lower().strip()

            tr = re.sub(r"between (.+?) and (.+)", r"\1 to \2", tr)
            tr = re.sub(r"from (.+?) to (.+)", r"\1 to \2", tr)
            tr = re.sub(r"(\w+ \d+)-(\d+)", r"\1 to \2", tr)

            clean_data["time_range"] = tr

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