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
    "engine_status",

    "engine_temperature",
    "engine_rpm",
    "engine_hours",

    "location",

    "latitude",
    "longitude",

    "odometer_reading",

    "weight",

    "gsm_signal",

    "wasl",

    "seatbelt",

    "door_open",

    "vehicle_type",

    "make",

    "imei",

    "last_updated",

    "camera_status",

    "remote_immobilization",

    "driver_name",

    "group_name",

    "network",

    "satellites"
}


METRIC_SYNONYMS = {

    "speed": "speed",
    "current speed": "speed",
    "vehicle speed": "speed",
    "running speed": "speed",
    "live speed": "speed",

    "fuel": "fuel_level",
    "fuel level": "fuel_level",
    "fuel remaining": "fuel_level",
    "fuel status": "fuel_level",
    "current fuel": "fuel_level",

    "fuel capacity": "fuel_capacity",
    "tank capacity": "fuel_capacity",

    "fuel percentage": "fuel_percentage",
    "fuel percent": "fuel_percentage",

    "today fuel consumed": "today_fuel_consumed",
    "fuel consumed": "today_fuel_consumed",

    "tanker fuel": "tanker_fuel_capacity",
    "tanker capacity": "tanker_fuel_capacity",
    "tanker fuel capacity": "tanker_fuel_capacity",

    "tanker fuel percentage": "tanker_fuel_percentage",

    "battery": "battery",
    "battery level": "battery",
    "battery voltage": "battery",

    "ignition": "ignition",
    "ignition status": "ignition",

    "engine status": "engine_status",

    "engine temperature": "engine_temperature",

    "rpm": "engine_rpm",
    "engine rpm": "engine_rpm",

    "engine hours": "engine_hours",

    "distance": "distance_travelled",
    "distance travelled": "distance_travelled",
    "distance traveled": "distance_travelled",

    "mileage": "mileage",

    "driver": "driver_name",
    "driver name": "driver_name",

    "group": "group_name",
    "group name": "group_name",

    "vehicle type": "vehicle_type",

    "weight": "weight",
    "load": "weight",

    "satellites": "satellites",

    "gsm signal": "gsm_signal",
    "signal": "gsm_signal",

    "wasl": "wasl",
    "wasl identity": "wasl",
    "wasl identity number": "wasl",

    "seatbelt": "seatbelt",
    "seat belt": "seatbelt",
    "seatbelt status": "seatbelt",

    "door": "door_open",
    "door status": "door_open",
    "door open": "door_open",

    "camera": "camera_status",
    "camera status": "camera_status",

    "location": "location",
    "current location": "location",
    "live location": "location",

    "remote immobilization": "remote_immobilization",
    "immobilizer": "remote_immobilization",

    "imei": "imei",

    "make": "make",
    "manufacturer": "make",

    "last updated": "last_updated",
    "updated time": "last_updated",
    "last report": "last_updated",

    "odometer": "odometer_reading",
    "odometer reading": "odometer_reading",
    "odo": "odometer_reading",
    "mileage reading": "odometer_reading",
    "total distance": "odometer_reading",

    "latitude": "latitude",
    "lat": "latitude",

    "longitude": "longitude",
    "long": "longitude",
    "lon": "longitude",

    "coordinates": "location",
    "gps coordinates": "location",
    "gps location": "location",
    "live coordinates": "location",
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
    """
    Normalize all vehicle IDs into canonical form.

    Examples:
        1834 RXB   -> 1834RXB
        RXB 1834   -> 1834RXB
        97 J J J   -> 97JJJ
        53380 533  -> 53380533
    """

    if not value:
        return ""

    value = value.upper().strip()

    # keep only alphanumeric + spaces
    value = re.sub(r"[^A-Z0-9\s]", " ", value)

    parts = re.findall(r"[A-Z]+|\d+", value)

    numbers = []
    letters = []

    for part in parts:

        if part.isdigit():
            numbers.append(part)

        else:
            letters.append(part)

    return "".join(numbers) + "".join(letters)


# =========================================================
# VEHICLE EXTRACTION PATTERNS
# =========================================================

VEHICLE_PATTERNS = [

    # 1834RXB
    re.compile(
        r"(?<![A-Z0-9])(\d{2,6}[A-Z]{1,4})(?![A-Z0-9])",
        re.IGNORECASE
    ),

    # RXB1834
    re.compile(
        r"(?<![A-Z0-9])([A-Z]{1,4}\d{2,6})(?![A-Z0-9])",
        re.IGNORECASE
    ),

    # 1834 RXB
    re.compile(
        r"(?<![A-Z0-9])(\d{2,6}\s+[A-Z]{1,4})(?![A-Z0-9])",
        re.IGNORECASE
    ),

    # RXB 1834
    re.compile(
        r"(?<![A-Z0-9])([A-Z]{1,4}\s+\d{2,6})(?![A-Z0-9])",
        re.IGNORECASE
    ),

    # 73 RRR
    re.compile(
        r"(?<![A-Z0-9])(\d{2,6}\s+[A-Z]{1,4})(?![A-Z0-9])",
        re.IGNORECASE
    ),

    # 97 J J J
    re.compile(
        r"(?<![A-Z0-9])(\d{2,6}(?:\s+[A-Z]){1,4})(?![A-Z0-9])",
        re.IGNORECASE
    ),

    # 53380 533
    re.compile(
        r"(?<![A-Z0-9])(\d{2,6}\s+\d{2,6})(?![A-Z0-9])"
    ),
]


# =========================================================
# PREFIX REMOVAL
# =========================================================

KNOWN_PREFIXES = [
    "VEHICLE",
    "TRUCK",
    "BUS",
    "CAR",
    "TANKER"
]


def remove_known_prefixes(query: str) -> str:
    """
    Converts:
        vehicle1834RXB -> 1834RXB
        truckRXB1834 -> RXB1834
    """

    query = query.upper()

    for prefix in KNOWN_PREFIXES:

        query = re.sub(
            rf"\b{prefix}(?=[A-Z0-9])",
            " ",
            query,
            flags=re.IGNORECASE
        )

    return query


# =========================================================
# VEHICLE EXTRACTION
# =========================================================

def extract_vehicle_candidates(query: str):

    if not query:
        return []

    # -----------------------------------------
    # NORMALIZATION
    # -----------------------------------------

    query = query.upper()

    query = remove_known_prefixes(query)

    query = re.sub(r"[-_/]", " ", query)

    query = re.sub(r"\s+", " ", query).strip()

    candidates = []

    # -----------------------------------------
    # PATTERN EXTRACTION
    # -----------------------------------------

    for pattern in VEHICLE_PATTERNS:

        matches = pattern.findall(query)

        for raw in matches:

            normalized = normalize_vehicle_id(raw)

            if normalized:
                candidates.append(normalized)

    # -----------------------------------------
    # DEDUPLICATION
    # -----------------------------------------

    final = []
    seen = set()

    for candidate in candidates:

        if candidate not in seen:

            seen.add(candidate)

            final.append(candidate)

    logger.info(
        f"Extracted vehicle candidates: {final}"
    )

    return final


def build_vehicle_lookup(vehicle_cache):

    lookup = {}

    for vehicle in vehicle_cache["data"]:

        vehicle_id = vehicle.get("vehicle_id")

        if vehicle_id:

            normalized = normalize_vehicle_id(vehicle_id)

            lookup[normalized] = vehicle

    return lookup


def resolve_vehicle(query, vehicle_cache):
    
    # logger.info(f"Cache from resolve vehicle: {vehicle_cache}")
    vehicle_lookup = build_vehicle_lookup(vehicle_cache)
    candidates = extract_vehicle_candidates(query)

    for candidate in candidates:

        vehicle = vehicle_lookup.get(candidate)

        if vehicle:
            return vehicle

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

