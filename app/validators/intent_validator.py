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
    "imei",
    "ignition"
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
    "wasl identity number": "wasl_identity_number",

    "ignition_on": "ignition",
    "ignition status": "ignition"
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



STOPWORDS = {

    "FROM",
    "TO",
    "ON",
    "AT",
    "IN",
    "OF",
    "THE",
    "SHOW",
    "GET",
    "FETCH",
    "DETAILS",
    "STATUS",
    "VEHICLE",
    "APRIL",
    "MAY",
    "JUNE"
}


def normalize_vehicle_id(value: str) -> str:

    value = value.upper()

    parts = re.findall(
        r"[A-Z]+|\d+",
        value
    )

    numbers = []
    letters = []

    for part in parts:

        if part.isdigit():
            numbers.append(part)

        else:
            letters.append(part)

    return "".join(numbers) + "".join(letters)


VEHICLE_PATTERNS = [

    # 1834 RXB
    re.compile(
        r"\b(\d{2,5})\s+([A-Z]{1,4})\b"
    ),

    # RXB 1834
    re.compile(
        r"\b([A-Z]{1,4})\s+(\d{2,5})\b"
    ),

    # 7894 B B B
    re.compile(
        r"\b(\d{2,5})(?:\s+([A-Z])){1,4}\b"
    ),

    # B B B 7894
    re.compile(
        r"\b(?:([A-Z])\s+){1,4}(\d{2,5})\b"
    ),

    # numeric-only IDs
    re.compile(
        r"\b\d{5,10}\b"
    )
]


def extract_vehicle_candidates(query: str):

    if not query:
        return []

    query = query.upper()


    query = re.sub(
        r"([A-Z])(\d)",
        r"\1 \2",
        query
    )

    query = re.sub(
        r"(\d)([A-Z])",
        r"\1 \2",
        query
    )

    query = re.sub(
        r"[^A-Z0-9 ]",
        " ",
        query
    )

    query = re.sub(
        r"\s+",
        " ",
        query
    ).strip()

    candidates = []

    for pattern in VEHICLE_PATTERNS:

        matches = pattern.finditer(query)

        for match in matches:

            raw = match.group(0)

            normalized = normalize_vehicle_id(raw)

            candidates.append(normalized)

    # ---------------------------------------------------
    # REMOVE DUPLICATES
    # ---------------------------------------------------

    final = []

    seen = set()

    for candidate in candidates:

        if candidate not in seen:

            seen.add(candidate)

            final.append(candidate)
    
    return final


def resolve_vehicle(query, vehicle_cache):

    candidates = extract_vehicle_candidates(query)

    for candidate in candidates:

        if candidate in vehicle_cache["data"]:

            return vehicle_cache[candidate]

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

