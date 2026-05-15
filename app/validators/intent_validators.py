import json
import re

from app.utils.logger import logger


# =========================================================
# DEFAULT SAFE INTENT
# =========================================================

DEFAULT_INTENT = {
    "action": "fetch",
    "vehicle_id": None,
    "source": None,
    "metrics": [],
    "aggregation": None,
    "alert_analysis": None,
    "time_range": None,
    "summary_requested": False
}


# =========================================================
# METRIC CONFIG
# =========================================================

VALID_METRICS = {

    "speed",
    "mileage",
    "distance_travelled",
    "fuel_level",
    "fuel_capacity",
    "fuel_percentage",
    "today_fuel_consumed",
    "tanker_fuel_capacity",
    "tanker_fuel_percentage",
    "battery",
    "ignition",
    "engine_temperature",
    "engine_rpm",
    "engine_hours",
    "location",
    "weight",
    "gsm_signal",
    "wasl",
    "seatbelt",
    "door_open",
    "vehicle_type",
    "make",
    "imei"
}

METRIC_SYNONYMS = {

    "speed": "speed",
    "current speed": "speed",
    "vehicle speed": "speed",

    "fuel": "fuel_level",
    "fuel level": "fuel_level",
    "fuel remaining": "fuel_level",
    "current fuel": "fuel_level",
    "fuel status": "fuel_level",

    "fuel capacity": "fuel_capacity",
    "tank capacity": "fuel_capacity",

    "fuel percentage": "fuel_percentage",

    "today fuel consumed": "today_fuel_consumed",

    "tanker fuel": "tanker_fuel_capacity",
    "tanker fuel capacity": "tanker_fuel_capacity",

    "tanker fuel percentage": "tanker_fuel_percentage",

   
    "battery": "battery",
    "battery level": "battery",
    "battery voltage": "battery",
    
    "seatbelt": "seatbelt",
    "seat belt": "seatbelt",
    "seatbelt status": "seatbelt",

    "ignition": "ignition",
    "engine status": "ignition",

    "engine temperature": "engine_temperature",

    "engine rpm": "engine_rpm",
    "rpm": "engine_rpm",

    "engine hours": "engine_hours",

    "distance": "distance_travelled",
    "distance travelled": "distance_travelled",

    "mileage": "mileage",

    "driver": "driverName",
    "driver name": "driverName",


    "group": "group",
    "group name": "group",

    "vehicle type": "vehicle_type",
    "type": "vehicle_type",

    "weight": "weight",
    "load": "weight",

    "satellites": "satellites",

    "gsm signal": "gsm_signal",
    "signal": "gsm_signal",

    "network": "network",
    "network type": "network",

    "wasl": "wasl_identity_number",
    "wasl identity": "wasl_identity_number",
    "wasl identity number": "wasl_identity_number"
}


# =========================================================
# VEHICLE ID
# =========================================================

VEHICLE_ID_PATTERN = re.compile(
    r"\b\d{2,5}(?:[\s\-]?[A-Z0-9]{1,3}){1,3}\b"
)

VALID_VEHICLE_ID_PATTERN = re.compile(
    r"^\d{2,5}[A-Z]{1,3}$"
)


# =========================================================
# SANITIZE LLM OUTPUT
# =========================================================

def sanitize_llm_output(raw: str) -> dict:

    if not raw:
        return DEFAULT_INTENT.copy()

    try:

        match = re.search(r"\{[\s\S]*\}", raw)

        if not match:
            logger.error(f"No JSON found: {raw}")
            return DEFAULT_INTENT.copy()

        data = json.loads(match.group())

        if not isinstance(data, dict):
            return DEFAULT_INTENT.copy()

        cleaned = {}

        for key in DEFAULT_INTENT.keys():

            value = data.get(key)

            if isinstance(value, (dict, tuple)):
                value = None

            if isinstance(value, str):

                if value.strip().lower() in {
                    "null",
                    "none",
                    ""
                }:
                    value = None

            cleaned[key] = value

        return cleaned

    except Exception as e:
        logger.error(f"sanitize_llm_output failed: {e}")

        return DEFAULT_INTENT.copy()


# =========================================================
# VEHICLE ID EXTRACTION
# =========================================================

def extract_vehicle_id(query: str):

    match = VEHICLE_ID_PATTERN.search(
        query.upper()
    )

    if not match:
        return None

    # Preserve original readable format
    vehicle_id = match.group().strip()

    # Validate using normalized version
    normalized = re.sub(
        r"[\s\-]+",
        "",
        vehicle_id
    )

    if VALID_VEHICLE_ID_PATTERN.match(normalized):
        return vehicle_id

    return None


# =========================================================
# METRIC EXTRACTION
# =========================================================

def extract_metrics(query: str) -> list[str]:

    q = query.lower()

    found = set()

    # phrase priority
    for phrase, metric in METRIC_SYNONYMS.items():

        if phrase in q:
            found.add(metric)

    # direct metrics
    for metric in VALID_METRICS:

        tokens = metric.split("_")

        if all(token in q for token in tokens):
            found.add(metric)

    return list(found)


# =========================================================
# AGGREGATION
# =========================================================

def extract_aggregation(query: str):

    q = query.lower()

    if any(word in q for word in [
        "average",
        "avg",
        "mean"
    ]):
        return "average"

    if any(word in q for word in [
        "maximum",
        "highest",
        "max",
        "peak"
    ]):
        return "maximum"

    if any(word in q for word in [
        "minimum",
        "lowest",
        "min"
    ]):
        return "minimum"

    return None


# =========================================================
# SOURCE DETECTION
# =========================================================

def detect_source(
    query: str,
    aggregation,
    time_range
):

    q = query.lower()

    # ALERT
    if any(word in q for word in [
        "alert",
        "overspeed",
        "violation"
    ]):
        return "alert"

    # SUMMARY
    if aggregation or time_range:
        return "summary"

    # LATEST
    if any(word in q for word in [
        "current",
        "latest",
        "now",
        "status"
    ]):
        return "latest"

    # metric-only queries default latest
    return "latest"


# =========================================================
# ALERT ANALYSIS
# =========================================================

def extract_alert_response_type(query: str):

    q = query.lower()

    count_phrases = [

        "count",
        "how many",
        "number of alerts",
        "total alerts",
        "alerts count"
    ]

    if any(phrase in q for phrase in count_phrases):

        return "alert_count"


    distribution_phrases = [

        "distribution",
        "breakdown",
        "types of alerts",
        "alert types"
    ]

    if any(phrase in q for phrase in distribution_phrases):

        return "alert_distribution"

    latest_phrases = [

        "latest alert",
        "recent alert",
        "last alert"
    ]

    if any(phrase in q for phrase in latest_phrases):

        return "latest_alert"

    overspeed_phrases = [

        "highest speed",
        "maximum speed",
        "overspeed details",
        "max overspeed"
    ]

    if any(phrase in q for phrase in overspeed_phrases):

        return "overspeed_summary"

    daily_phrases = [

        "daily alerts",
        "alerts per day",
        "daily breakdown",
        "alert trend"
    ]

    if any(phrase in q for phrase in daily_phrases):

        return "daily_alert_summary"

    return "full_alert_summary"



def detect_summary_requested(query: str):

    q = query.lower()

    phrases = [
        "current status",
        "vehicle status",
        "latest status",
        "complete status",
        "full status"
    ]

    return any(p in q for p in phrases)


# =========================================================
# FINAL POST VALIDATION
# =========================================================

def post_validate(
    clean_data: dict,
    query: str
):

    try:

        vehicle_id = extract_vehicle_id(query)

        if vehicle_id:
            clean_data["vehicle_id"] = vehicle_id

        extracted_metrics = extract_metrics(query)

        valid_metrics = []

        for metric in extracted_metrics:

            metric = metric.lower().strip()

            if metric in VALID_METRICS:
                valid_metrics.append(metric)

        clean_data["metrics"] = list(set(valid_metrics))


        aggregation = extract_aggregation(query)

        clean_data["aggregation"] = aggregation

        source = detect_source(
            query=query,
            aggregation=clean_data.get("aggregation"),
            time_range=clean_data.get("time_range")
        )

        clean_data["source"] = source


        if source == "alert":

            clean_data["alert_response_type"] = (
                extract_alert_response_type(query)
            )

        # =========================================
        # SUMMARY REQUESTED
        # =========================================

        clean_data["summary_requested"] = (
            detect_summary_requested(query)
        )

        # =========================================
        # RULE:
        # current status => all latest fields
        # =========================================

        if clean_data["summary_requested"]:
            clean_data["metrics"] = []

        return clean_data

    except Exception as e:

        logger.error(
            f"post_validate failed: {e}",
            exc_info=True
        )

        return DEFAULT_INTENT.copy()