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
    query_upper = query.upper()

    patterns = [
        r"\b\d{2,5}(?:\s+[A-Z]{1,3}){1,3}\b",  
        r"\b\d{2,5}\s+[A-Z]{2,4}\b",            
        r"\b\d{2,5}\s+\d{2,4}\b",               
        r"\b\d{2,5}[A-Z]{2,4}\b",              
    ]

    for pattern in patterns:
        match = re.search(pattern, query_upper)
        if match:
            raw = match.group()
            normalized = re.sub(r"\s+", "", raw)

            # ✅ Updated validation
            if re.match(r"^\d{2,5}(?:[A-Z]{1,4}|\d{2,4})$", normalized):
                return normalized

    return None


def extract_aggregation_rule_based(query: str) -> str | None:
    query = query.lower()

    if any(word in query for word in ["minimum", "lowest", "least", "min"]):
        return "minimum"

    if any(word in query for word in ["maximum", "highest", "top", "peak", "max"]):
        return "maximum"

    if any(word in query for word in ["average", "mean", "avg"]):
        return "average"

    return None


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
        pattern = r"^\d{2,5}(?:[A-Z]{1,4}|\d{2,4})$"

        if re.match(pattern, normalized):
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
    
    rule_based_agg = extract_aggregation_rule_based(query)

    if rule_based_agg:
        if clean_data.get("aggregation") != rule_based_agg:
            logger.warning(
                f"Corrected aggregation from {clean_data.get('aggregation')} → {rule_based_agg}"
            )
        clean_data["aggregation"] = rule_based_agg

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

----------------------------------------
METRIC:

VALID BASE METRICS:
{fields}

RULES:

1. Metric MUST match EXACT word from list
2. IGNORE context words:
   - report, details, summary, data
3. Examples:
   "speed report" → "speed"
   "vehicle details" → null

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