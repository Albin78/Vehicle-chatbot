import json
import re
from app.utils.logger import logger
from app.db.mongoclient import get_db_fields


# DEFAULT SAFE INTENT (FALLBACK)
# --------------------------------------------------
DEFAULT_INTENT = {
    "action": "fetch",
    "vehicle_id": None,
    "metric": None,
    "aggregation": None,
    "analysis": None,
    "time_range": None,
    "intent_type": None,  
    "service": None
}

REALTIME_ALLOWED_METRICS = {
    "speed",
    "battery",
    "fuel_capacity",
    "tanker_fuel_capacity",
    "weight",
    "mileage",
    "fuel_level"
}

METRIC_SYNONYMS = {
    "battery": "battery",
    "battery level": "battery",
    "battery status": "battery",
    "battery voltage": "battery",

    
    "fuel level": "fuel_level",
    "fuel status": "fuel_level",
    "current fuel": "fuel_level",
    "fuel remaining": "fuel_level",

    "fuel capacity": "fuel_capacity",
    "tank capacity": "fuel_capacity",

    "tanker": "tanker_fuel_capacity",
    "tanker capacity": "tanker_fuel_capacity",

    "distance": "mileage",
    "mileage": "mileage",

    "speed": "speed",
    "weight": "weight"
}

VEHICLE_ID_PATTERN = re.compile(
    r"\b\d{2,5}(?:[\s\-]?[A-Z0-9]{1,3}){1,3}\b"
)

# VALID_VEHICLE_ID_PATTERN = re.compile(
#     r"^\d{2,5}(?:[A-Z]{1,3}|\d{1,3})+$"
# )

VALID_VEHICLE_ID_PATTERN = re.compile(
    r"^\d{2,5}[A-Z]{1,3}$"
)

fields = get_db_fields()

HISTORICAL_ALLOWED_METRICS = set(fields)  


def normalize_metric(metric: str | None, query: str) -> str | None:
    q = query.lower()

    # If LLM gave something, normalize it
    if metric:
        metric = metric.lower().strip()

        if metric in METRIC_SYNONYMS:
            return METRIC_SYNONYMS[metric]


        if metric == "fuel":
            if any(word in q for word in ["level", "status", "current", "remaining"]):
                return "fuel_level"
            elif any(word in q for word in ["capacity", "tank"]):
                return "fuel_capacity"
            else:
                return "fuel_level"  

        # Try to infer from query phrases
        for phrase, canonical in METRIC_SYNONYMS.items():
            if phrase in q:
                return canonical

        return metric

# --------------------------------------------------
# RULE-BASED VEHICLE ID EXTRACTION (STRONG FALLBACK)
# --------------------------------------------------

def extract_vehicle_id_rule_based(query: str) -> str | None:
    match = VEHICLE_ID_PATTERN.search(query.upper())
    if not match:
        return None

    raw = match.group()
    return re.sub(r"\s+", "", raw)


def is_valid_vehicle_id(vid) -> bool:
    if not isinstance(vid, str):
        return False
    return bool(VALID_VEHICLE_ID_PATTERN.match(vid))


def resolve_vehicle_id(clean_data, query):
    fallback_vid = extract_vehicle_id_rule_based(query)
    llm_vid = clean_data.get("vehicle_id")

    if isinstance(llm_vid, str):
        llm_vid = re.sub(r"\s+", "", llm_vid.upper())

    final_vid = None

    if fallback_vid:
        if not llm_vid:
            final_vid = fallback_vid
        elif not is_valid_vehicle_id(llm_vid):
            final_vid = fallback_vid
        elif len(fallback_vid) > len(llm_vid):
            final_vid = fallback_vid
        else:
            final_vid = llm_vid
    else:
        final_vid = llm_vid

    if final_vid and is_valid_vehicle_id(final_vid):
        return final_vid

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
    
    vid = clean_data.get("vehicle_id")

    if vid is not None:
        try:
            clean_data["vehicle_id"] = str(vid)
        except Exception:
            logger.warning(f"Invalid vehicle_id format: {vid}")
            clean_data["vehicle_id"] = None

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


def is_metric_in_query(query: str, metric: str) -> bool:
    if not metric:
        return False

    q = query.lower()

    # Check synonym phrases
    for phrase, canonical in METRIC_SYNONYMS.items():
        if canonical == metric and phrase in q:
            return True

    # fallback token match
    tokens = metric.split("_")
    return all(token in q for token in tokens)


def extract_metric_rule_based(query: str) -> str | None:
    q = query.lower()
    
    # PRIORITY MATCH (before generic)
    if any(word in q for word in ["fuel level", "fuel status", "current fuel", "fuel remaining"]):
        return "fuel_level"

    if "fuel capacity" in q or "tank capacity" in q:
        return "fuel_capacity"
    
    # First check synonyms (stronger)
    for phrase, canonical in METRIC_SYNONYMS.items():
        if phrase in q:
            return canonical

    # fallback to direct metrics
    for metric in REALTIME_ALLOWED_METRICS:
        tokens = metric.split("_")
        if all(token in q for token in tokens):
            return metric

    return None


def map_service(clean_data):

    intent_type = clean_data.get("intent_type")

    if intent_type == "realtime":
        clean_data["service"] = "realtime_service"

    elif intent_type == "alert":
        clean_data["service"] = "alert_service"

    elif intent_type == "historical":
        clean_data["service"] = "summary_service"

    elif intent_type == "telemetry":
        clean_data["service"] = "db_service"

    else:
        clean_data["service"] = None

    return clean_data


def validate_metric(metric, query, clean_data, fields):

    if not metric:
        return None

    metric = metric.strip().lower()

    intent_type = clean_data.get("intent_type")

  
    if intent_type == "realtime":
        if metric not in REALTIME_ALLOWED_METRICS:
            logger.warning(f"Rejected invalid realtime metric: {metric}")
            return None

    elif intent_type == "historical":
        if metric not in fields:
            logger.warning(f"Rejected invalid historical metric: {metric}")
            return None

    
    if not is_metric_in_query(query, metric):
        logger.warning(f"Rejected hallucinated metric: {metric}")
        return None

    return metric


def detect_intent_type(query: str, clean_data: dict) -> str | None:
    q = query.lower()

    has_metric = clean_data.get("metric") is not None or any(
    word in query.lower() for word in REALTIME_ALLOWED_METRICS
)
    has_agg = clean_data.get("aggregation") is not None
    has_time = clean_data.get("time_range") is not None

    # -----------------------------
    # ALERT (highest priority)
    # -----------------------------
    if any(word in q for word in ["overspeed", "alert", "violation"]):
        return "alert"

    # -----------------------------
    # REALTIME (explicit)
    # -----------------------------
    if any(word in q for word in ["current", "now", "latest", "status"]):
        return "realtime"

    # -----------------------------
    # AGGREGATION WITHOUT TIME
    # -----------------------------
    if has_metric and has_agg:
        return "historical"

    # -----------------------------
    # TIME-BASED
    # -----------------------------
    if has_time:
        return "historical"

    # -----------------------------
    # PURE METRIC (AMBIGUOUS)
    # -----------------------------
    if has_metric:
        return "realtime"   

    return None


# POST VALIDATION (CRITICAL LAYER)
# --------------------------------------------------
def post_validate(clean_data: dict, query: str, fields: list) -> dict:

    # -----------------------------
    # VEHICLE ID RESOLUTION (FINAL FIX)
    # -----------------------------
    
    try:
        resolved_vid = resolve_vehicle_id(clean_data, query)

        if resolved_vid:
            if clean_data.get("vehicle_id") != resolved_vid:
                logger.info(f"Corrected vehicle_id from {clean_data.get('vehicle_id')} → {resolved_vid}")
            clean_data["vehicle_id"] = resolved_vid
        else:
            logger.warning(f"Failed to resolve vehicle_id from query: {query}")
            clean_data["vehicle_id"] = None
        

        # -----------------------------
        # METRIC FALLBACK (CRITICAL FIX)
        # -----------------------------
        if not clean_data.get("metric"):
            fallback_metric = extract_metric_rule_based(query)

            if fallback_metric:
                logger.info(f"Recovered metric from query: {fallback_metric}")
                clean_data["metric"] = fallback_metric
        

        clean_data["metric"] = normalize_metric(
        clean_data.get("metric"),
        query
    )
        
        # METRIC VALIDATION
        # -----------------------------
        clean_data["metric"] = validate_metric(
        clean_data.get("metric"),
        query,
        clean_data,
        fields
    )

        # -----------------------------
        # AGGREGATION VALIDATION
        # -----------------------------
        if clean_data.get("aggregation") and not clean_data.get("metric"):
            clean_data["aggregation"] = None

        if clean_data.get("metric"):  # only if metric exists
            rule_based_agg = extract_aggregation_rule_based(query)

            if rule_based_agg:
                if clean_data.get("aggregation") != rule_based_agg:
                    logger.warning(
                        f"Corrected aggregation from {clean_data.get('aggregation')} → {rule_based_agg}"
                    )
                clean_data["aggregation"] = rule_based_agg
    

        # INTENT TYPE DETECTION (CRITICAL)
        # -----------------------------
        rule_intent = detect_intent_type(query, clean_data)
        llm_intent = clean_data.get("intent_type")

        if rule_intent:
            if llm_intent != rule_intent:
                logger.warning(
                    f"Corrected intent_type from {llm_intent} → {rule_intent}"
                )
            clean_data["intent_type"] = rule_intent
        else:
            clean_data["intent_type"] = llm_intent


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
    
    except Exception as e:
        logger.error(f"[POST_VALIDATE ERROR] {e}", exc_info=True)

        return {
            "action": "fetch",
            "vehicle_id": None,
            "metric": None,
            "aggregation": None,
            "analysis": None,
            "time_range": None,
            "intent_type": None,
            "service": None,
            "error": "Intent processing failed. Please try again."
        }

