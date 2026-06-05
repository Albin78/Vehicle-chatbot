from typing import Optional
from app.utils.logger import logger
from .intent_validator import (
    resolve_vehicle,
    extract_metrics,
    VALID_METRICS, 
    DEFAULT_INTENT
)

from app.tools.vehicle_cache import get_vehicle_cache
from datetime import datetime, timedelta, timezone

ACTION_MAPPINGS = {

    # canonical
    "fetch": "fetch",
    "update": "update",
    "delete": "delete",
    "Update": "update",
    "Delete": "delete",

    # synonyms
    "check": "fetch",
    "get": "fetch",
    "retrieve": "fetch",
    "show": "fetch",
    "find": "fetch",
    "lookup": "fetch",
    "read": "fetch",

    "modify": "update",
    "edit": "update",

    "remove": "delete"
}

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



def normalize_action(
    action: Optional[str],
    query: str
) -> str:

    q = query.lower()

    update_keywords = [
        "update",
        "modify",
        "edit",
        "change"
    ]

    delete_keywords = [
        "delete",
        "remove"
    ]

    # Use word-level matching to avoid false positives like 'updated'
    words = set(q.split())
    if any(word in words for word in update_keywords):
        return "update"

    if any(word in words for word in delete_keywords):
        return "delete"

    # =====================================
    # 2. LLM ACTION FALLBACK
    # =====================================

    if action:

        normalized = ACTION_MAPPINGS.get(
            action.lower().strip()
        )

        if normalized:
            return normalized

    return "fetch"

# =========================================================
# ALERT ENABLE / DISABLE DETECTION
# =========================================================

ALERT_ENABLE_KEYWORDS = [
    "enabled",
    "disabled",
    "is enabled",
    "is disabled",
    "alert enabled",
    "alert disabled",
    "enable alert",
    "disable alert",
    "turned on",
    "turned off",
    "alert on",
    "alert off",
    "which alerts",
    "what alerts",
    "alerts enabled",
    "alerts disabled",
    "alert settings",
    "alert configuration"
]


ALERT_TYPE_SYNONYMS = {
    "overspeed": "overSpeed",
    "over speed": "overSpeed",
    "speed alert": "overSpeed",
    "idling": "idling",
    "idle": "idling",
    "overstay": "overStay",
    "over stay": "overStay",
    "battery disconnection": "batteryDisconnection",
    "battery disconnect": "batteryDisconnection",
    "low battery": "lowBattery",
    "rash driving": "rashDriving",
    "harsh driving": "rashDriving",
    "continuous": "continuous",
    "territory": "territory",
    "geofence": "territory",
    "refuel drain": "refuelDrain",
    "fuel drain": "refuelDrain",
    "fuel disconnection": "fuelDisconnection",
    "parkfence": "parkfence",
    "park fence": "parkfence",
    "overload": "overload",
    "weight tamper": "WeightTamper",
    "accident": "Accident",
    # seatbelt / seat belt are realtime metrics, NOT alert types.
    # They must NOT appear here — remove them so extract_alert_focus()
    # never matches a plain "seatbelt status" query.
    "asset movement": "assetmovement",
    "asset move": "assetmovement",
    "territory overspeed": "territoryOverSpeed",
    "territory speed": "territoryOverSpeed",
    "safe stop fuel drainer": "safeStopFuelDrainer",
    "equipment bypass": "equipmentByPass",
    "after hours movement": "afterhoursmovement",
    "afterhours movement": "afterhoursmovement",
    "afterhours": "afterhoursmovement",
    "after hours": "afterhoursmovement",
    "zone based speed limit": "zoneBasedSpeedLimit",
    "zone speed": "zoneBasedSpeedLimit",
}


def detect_alert_enable_query(query: str) -> bool:
    """
    Return True ONLY when the user explicitly asks about enabling /
    disabling an alert configuration.

    Two conditions must BOTH be met:
      1) An enable/disable cue is present  (e.g. enable, disable, turned on)
      2) The word "alert" / "alerts" is present

    We intentionally do NOT rely on ALERT_TYPE_SYNONYMS here because
    some synonyms (e.g., former "seatbelt" entry) are realtime metrics
    and must NOT trigger the alert-enable pipeline.
    """
    q = query.lower()

    # 1) Must contain an enable / disable keyword
    if not any(kw in q for kw in ALERT_ENABLE_KEYWORDS):
        return False

    # 2) Must explicitly mention "alert" — e.g. "seatbelt alert"
    #    Queries like "seatbelt status" do NOT contain "alert"
    #    and will correctly fall through to the realtime pipeline.
    return "alert" in q or "alerts" in q


def extract_alert_type_focus(query: str) -> str | None:

    q = query.lower()

    for phrase, canonical in ALERT_TYPE_SYNONYMS.items():

        if phrase in q:
            return canonical

    return None


# =========================================================
# DEFAULT ALERT TIME RANGE
# =========================================================

def get_today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def apply_default_alert_time_range(query: str, clean_data: dict) -> bool:
    """
    Fills clean_data["time_range"] with a sensible default when the user
    did not specify one, and returns True to signal a default was applied.

    Rules:
      - "latest <alert-type>" / "recent" / "last alert"  → today only
      - Any other alert query without a time_range        → last 7 days
    """

    if clean_data.get("time_range"):
        return False

    q = query.lower()

    today = get_today_str()

    latest_hints = [
        "latest",
        "recent",
        "last alert",
        "most recent",
        "newest",
    ]

    if any(hint in q for hint in latest_hints):
        clean_data["time_range"] = (today, today)
        return True

    seven_days_ago = (
        datetime.now(timezone.utc) - timedelta(days=7)
    ).strftime("%Y-%m-%d")

    clean_data["time_range"] = (seven_days_ago, today)
    return True


def apply_default_summary_time_range(query: str, clean_data: dict) -> bool:
    if clean_data.get("time_range"):
        return False

    today = get_today_str()
    seven_days_ago = (
        datetime.now(timezone.utc) - timedelta(days=7)
    ).strftime("%Y-%m-%d")

    clean_data["time_range"] = (seven_days_ago, today)
    return True


# =========================================================
# SOURCE DETECTION
# =========================================================

def detect_source(
    query: str,
    aggregation,
    time_range,
    vehicle_id = None
):

    q = query.lower()

    # ALERT ENABLE / DISABLE CHECK
    if detect_alert_enable_query(q):
        return "alert_enable"

    # --------------------------------------------------
    # FLEET ANALYTICS
    # Triggered when NO vehicle_id is present AND the
    # query contains comparative / fleet-wide keywords.
    # Must be checked BEFORE alert / summary detection
    # so that "which driver had most overspeed alerts"
    # is routed to fleet_analytics, not plain "alert".
    # --------------------------------------------------
    if not vehicle_id:
        fleet_keywords = [
            "which driver", "which vehicle", "who drove",
            "all vehicles", "entire fleet", "fleet", "company",
            "most distance", "most idle", "least idle",
            "most moving", "highest speed", "lowest speed",
            "maximum speed", "minimum speed",
            "most overspeed", "most alerts", "most violations",
            "rank", "top vehicle", "top driver",
            "fleet status", "fleet overview", "overview", "overall status",
            "status of vehicle", "status of all vehicles",
            "how many vehicles", "list all vehicles",
            "vehicles moving", "vehicles stopped", "vehicles idle",
            "vehicles are moving", "vehicles are stopped", "vehicles are idle",
        ]
        if any(kw in q for kw in fleet_keywords):
            return "fleet_analytics"

    # ALERT
    if extract_alert_focus(q) is not None or any(word in q for word in [
        "alert",
        "alerts",
        "overspeed",
        "violation",
        "violations"
    ]):
        return "alert"

    # Check if time_range is strictly for today only
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    is_today_only = False
    if time_range:
        if isinstance(time_range, (list, tuple)) and len(time_range) == 2:
            start_date, end_date = time_range
            if start_date == today and end_date == today:
                is_today_only = True

    # SUMMARY
    # If the range is strictly for today, only route to summary if explicitly requested via "summary" or "report"
    if is_today_only:
        if aggregation or "summary" in q or "report" in q:
            return "summary"
    else:
        if aggregation or time_range or "summary" in q or "report" in q:
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



def extract_alert_focus(query: str):

    q = query.lower()

    if "overspeed" in q or "over speed" in q:
        return "overspeed"

    if "idling" in q or "idle" in q:
        return "idling"

    if (
        "afterhours" in q
        or "after-hours" in q
        or "after hours" in q
    ):
        return "afterhoursmovement"

    # Match against other known synonyms, checking longer phrases first
    sorted_synonyms = sorted(ALERT_TYPE_SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True)
    for phrase, canonical in sorted_synonyms:
        if phrase in q:
            return canonical

    return None


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



# =========================================================
# FLEET FIELD EXTRACTION
# =========================================================

def _extract_fleet_fields(query: str) -> dict:
    """
    Parses fleet-specific intent fields from the query text.
    Called only when source == "fleet_analytics".

    Returns a dict with keys:
        fleet_scope, fleet_metric, fleet_aggregation,
        fleet_subject, fleet_filter, fleet_query_type
    """
    q = query.lower()

    # ---- SUBJECT: driver vs vehicle ---------------------------------
    if any(w in q for w in ["driver", "who drove", "which driver"]):
        subject = "driver"
    else:
        subject = "vehicle"

    # ---- AGGREGATION ------------------------------------------------
    if any(w in q for w in ["highest", "maximum", "max", "most", "peak", "worst"]):
        aggregation = "maximum"
    elif any(w in q for w in ["lowest", "minimum", "min", "least", "best"]):
        aggregation = "minimum"
    elif any(w in q for w in ["rank", "list all", "all vehicles", "ranking"]):
        aggregation = "list"
    elif any(w in q for w in ["how many", "count", "total alerts", "number of"]):
        aggregation = "count"
    else:
        aggregation = "maximum"

    # ---- METRIC -----------------------------------------------------
    metric = None

    if any(w in q for w in ["alert", "alerts", "violation", "violations"]):
        metric = "alerts"
    elif any(w in q for w in ["speed", "fast", "overspeed"]):
        metric = "speed"
    elif any(w in q for w in ["distance", "km", "kilometres", "mileage"]):
        metric = "distance"
    elif any(w in q for w in ["idle", "idling"]):
        metric = "idle_time"
    elif any(w in q for w in ["moving time", "drive time", "driving time"]):
        metric = "moving_time"
    elif any(w in q for w in ["engine hour", "engine hours"]):
        metric = "engine_hours"
    elif any(w in q for w in [
        "status", "overview", "summary", "how many vehicles",
        "fleet status", "fleet overview"
    ]):
        metric = "status"

    # ---- FILTER (live status or alert type) -------------------------
    filt = None

    if "moving" in q or "vehicles are moving" in q:
        filt = "moving"
    elif "idle" in q and metric != "idle_time":
        filt = "idle"
    elif "stopped" in q:
        filt = "stopped"
    elif "out of network" in q or "out network" in q:
        filt = "out_network"
    elif "disconnected" in q:
        filt = "disconnected"
    elif "overspeed" in q or "over speed" in q:
        filt = "overspeed"
    elif "seatbelt" in q or "seat belt" in q:
        filt = "seatbelt"
    elif "afterhours" in q or "after hours" in q or "after-hours" in q:
        filt = "afterhoursmovement"
    elif "idling" in q and metric == "alerts":
        filt = "idling"

    # ---- QUERY TYPE (fine-grained routing hint) ---------------------
    qtype = None

    if any(w in q for w in ["fleet status", "fleet overview", "how many vehicles"]):
        qtype = "fleet_overview"
    elif (metric == "alerts" and aggregation == "count") or "how many" in q and ("alert" in q or "violation" in q):
        qtype = "alert_count"
        metric = "alerts"
        aggregation = "count"
    elif any(w in q for w in ["distribution", "breakdown", "types of alert"]):
        qtype = "alert_distribution"
    elif metric == "alerts" and aggregation == "list":
        qtype = "alert_list"

    return {
        "fleet_scope":       True,
        "fleet_metric":      metric,
        "fleet_aggregation": aggregation,
        "fleet_subject":     subject,
        "fleet_filter":      filt,
        "fleet_query_type":  qtype,
    }



def detect_summary_requested(query: str):

    q = query.lower()

    phrases = [
        "current status",
        "vehicle status",
        "latest status",
        "complete status",
        "full status",
        "overall status"
    ]

    if not any(p in q for p in phrases):
        return False

    # If a specific metric qualifier precedes "status",
    # do NOT treat it as a full status request.
    metric_qualifiers = [
        "speed status",
        "fuel status",
        "engine status",
        "battery status",
        "ignition status",
        "door status",
        "seatbelt status",
        "camera status",
        "movement status"
    ]

    if any(m in q for m in metric_qualifiers):
        return False

    return True


# =========================================================
# FINAL POST VALIDATION
# =========================================================

def post_validate(
    clean_data: dict,
    query: str
):

    try:

        if clean_data:
             clean_data["action"] = normalize_action(
                clean_data.get("action"),
                query
            )
             
        vehicle_cache = get_vehicle_cache(company_id=16)
        vehicle_id = resolve_vehicle(query, vehicle_cache)
        logger.info(f"Vehicle extracted from extraction function: {vehicle_id}")
        
        # Explicitly overwrite to prevent LLM hallucinations from slipping through
        clean_data["vehicle_id"] = vehicle_id
         
        extracted_metrics = extract_metrics(query)

        valid_metrics = []

        for metric in extracted_metrics:

            metric = metric.lower().strip()

            if metric in VALID_METRICS:
                valid_metrics.append(metric)
        
       
        clean_data["metrics"] = list(set(valid_metrics))
        clean_data["alert_focus"] = (
            extract_alert_focus(query)
        )

        aggregation = extract_aggregation(query)

        clean_data["aggregation"] = aggregation

        source = detect_source(
            query=query,
            aggregation=clean_data.get("aggregation"),
            time_range=clean_data.get("time_range"),
            vehicle_id=vehicle_id
        )

        clean_data["source"] = source

        if source == "latest":
            clean_data["time_range"] = None

        # =========================================
        # FLEET ANALYTICS FIELD EXTRACTION
        # =========================================
        if source == "fleet_analytics":
            fleet_info = _extract_fleet_fields(query)
            clean_data.update(fleet_info)
            # Ensure no vehicle_id slips through to block fleet queries
            clean_data["vehicle_id"] = None
            
            # Apply default time range for fleet queries
            if not clean_data.get("time_range"):
                from datetime import timedelta
                today     = get_today_str()
                week_ago  = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
                clean_data["time_range"] = (week_ago, today)


        if source == "alert":

            alert_focus = clean_data.get(
                "alert_focus"
            )

            # -------------------------------------
            # Focused alert query
            # -------------------------------------

            if alert_focus == "overspeed":

                clean_data[
                    "alert_response_type"
                ] = "overspeed_summary"

            elif alert_focus == "idling":

                clean_data[
                    "alert_response_type"
                ] = "idling_summary"

            elif alert_focus == "afterhoursmovement":

                clean_data[
                    "alert_response_type"
                ] = "afterhours_summary"

            else:

                clean_data[
                    "alert_response_type"
                ] = extract_alert_response_type(query)

            # Apply time range defaulting for alerts
            defaulted = apply_default_alert_time_range(
                query, clean_data
            )
            clean_data["alert_time_range_default"] = defaulted

        if source == "summary":
            # Apply time range defaulting for summaries if not specified
            defaulted = apply_default_summary_time_range(query, clean_data)
            clean_data["summary_time_range_default"] = defaulted

        # =========================================
        # ALERT ENABLE / DISABLE CHECK
        # =========================================

        if source == "alert_enable":

            clean_data["alert_enable_check"] = True

            clean_data["alert_type_focus"] = (
                extract_alert_type_focus(query)
            )

            clean_data["metrics"] = []

        # =========================================
        # SUMMARY REQUESTED
        # =========================================

        clean_data["summary_requested"] = (
            detect_summary_requested(query)
        )


        if clean_data["summary_requested"]:
            clean_data["metrics"] = []
        
        clean_data["query"] = query
        
        logger.info(f"Clean data from post validate: {clean_data}")

        return clean_data

    except Exception as e:

        logger.error(
            f"post_validate failed: {e}",
            exc_info=True
        )

        return DEFAULT_INTENT.copy()