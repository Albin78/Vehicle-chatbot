from typing import Optional
from app.utils.logger import logger
from .intent_validator import (
    resolve_vehicle,
    extract_metrics,
    VALID_METRICS, 
    DEFAULT_INTENT
)

from app.tools.vehicle_cache import get_vehicle_cache


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

    # =====================================
    # 1. LLM ACTION
    # =====================================

    if action:

        normalized = ACTION_MAPPINGS.get(
            action.lower().strip()
        )

        if normalized:
            return normalized


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

    if any(word in q for word in update_keywords):
        return "update"

    if any(word in q for word in delete_keywords):
        return "delete"

    return "fetch"

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



def extract_alert_focus(query: str):

    q = query.lower()

    if "overspeed" in q:
        return "overspeed"

    if "idling" in q:
        return "idling"

    if (
        "afterhours" in q
        or "after-hours" in q
        or "after hours" in q
    ):
        return "afterhoursmovement"

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

        if clean_data:
             clean_data["action"] = normalize_action(
                clean_data.get("action"),
                query
            )
             
        vehicle_cache = get_vehicle_cache(company_id=16)
        vehicle_id = resolve_vehicle(query, vehicle_cache)
        logger.info(f"Vehicle extracted from extraction function: {vehicle_id}")
        
        if vehicle_id:
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
            time_range=clean_data.get("time_range")
        )

        clean_data["source"] = source


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


        # =========================================
        # SUMMARY REQUESTED
        # =========================================

        clean_data["summary_requested"] = (
            detect_summary_requested(query)
        )


        if clean_data["summary_requested"]:
            clean_data["metrics"] = []
        
        logger.info(f"Clean data from post validate: {clean_data}")

        return clean_data

    except Exception as e:

        logger.error(
            f"post_validate failed: {e}",
            exc_info=True
        )

        return DEFAULT_INTENT.copy()