import json
import re
from app.utils.logger import logger


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
    "intent_type": None,  
    "service": None
}


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


def is_metric_in_query(query: str, metric: str) -> bool:
    if not metric:
        return False

    query = query.lower()
    metric = metric.lower()

    # Handle snake_case like moving_time → ["moving", "time"]
    tokens = metric.split("_")

    return all(token in query for token in tokens)


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


def detect_intent_type(query: str, clean_data: dict) -> str | None:
    q = query.lower()

    has_metric = clean_data.get("metric") is not None
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
        return "realtime"   # 🔥 DEFAULT FALLBACK

    return None


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

    # METRIC VALIDATION
    # -----------------------------
    metric = clean_data.get("metric")

    if isinstance(metric, str):
        metric = metric.strip().lower()

        if metric not in fields:
            logger.warning(f"Rejected invalid metric: {metric}")
            clean_data["metric"] = None

        elif not is_metric_in_query(query, metric):
            logger.warning(f"Rejected hallucinated metric: {metric}")
            clean_data["metric"] = None

        else:
            clean_data["metric"] = metric

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

