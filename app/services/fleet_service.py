"""
fleet_service.py
================
Orchestrates end-to-end fleet-wide analytical queries:

    1. Resolve date range
    2. Single fleet API call  (no vehicle_id)
    3. Dispatch to FleetAnalyzer method
    4. Return structured result dict for the response generator
"""

from datetime import datetime, timezone, timedelta

from app.tools.fleet_api_tool   import combined_report_fleet
from app.services.fleet_analyzer import FleetAnalyzer
from app.tools.vehicle_cache import get_vehicle_cache
from app.utils.logger            import logger


# =========================================================
# METRIC → API FIELD  mapping
# (operationSummary.dataRows field names)
# =========================================================

METRIC_TO_API_FIELD = {
    "speed":        "maxSpeed",
    "max_speed":    "maxSpeed",
    "distance":     "distance",
    "idle_time":    "idleTime",
    "idle":         "idleTime",
    "moving_time":  "movingTime",
    "moving":       "movingTime",
    "stop_time":    "stopTime",
    "engine_hours": "engineHours",
}


# =========================================================
# MAIN ENTRY
# =========================================================

def handle_fleet_service(intent, plan, company_id: int) -> dict:
    """
    Called by tool_router when intent.source == "fleet_analytics".
    Returns a structured dict with type="fleet_analytics" ready
    for the LLM response generator.
    """

    # --------------------------------------------------
    # 1. READ INTENT FIELDS
    # --------------------------------------------------
    metric      = (getattr(intent, "fleet_metric",      None) or "").lower()
    aggregation = (getattr(intent, "fleet_aggregation",  None) or "maximum").lower()
    subject     = (getattr(intent, "fleet_subject",      None) or "vehicle").lower()
    filt        = (getattr(intent, "fleet_filter",       None) or "").lower()
    qtype       = (getattr(intent, "fleet_query_type",   None) or "").lower()
    metrics_list = getattr(intent, "metrics", [])

    query_text = (getattr(intent, "query", "") or "").lower()
    is_current_query = any(w in query_text for w in ["current", "currently", "now", "latest"])
    valid_state_filters = {"", "on", "off", "open", "closed", "fastened", "unfastened", "enabled", "disabled"}
    
    # We only need live data if asking for specific live metrics OR if filtering by a live status (moving, idle, etc.)
    is_live_metrics_only = False
    if metrics_list and not qtype and filt in valid_state_filters and metric in ("", "status"):
        is_live_metrics_only = True
    elif filt in {"moving", "idle", "stopped", "out_network", "disconnected"} and qtype != "fleet_overview":
        is_live_metrics_only = True

    # --------------------------------------------------
    # 2. RESOLVE DATE RANGE
    # --------------------------------------------------
    today     = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    week_ago  = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

    if is_live_metrics_only or is_current_query:
        from_date, to_date = today, today
    elif plan.time_range:
        from_date, to_date = plan.time_range
    else:
        from_date, to_date = week_ago, today

    time_range_altered_to_week = False
    if not is_live_metrics_only and not is_current_query and from_date == today and to_date == today:
        # Alert data is available intraday — only operation summary data (distance, idle,
        # moving time, etc.) needs a backoff because it is processed nightly.
        # Never override an explicit "today" request for alert queries.
        is_alert_query = metric == "alerts" or qtype in (
            "alert_list", "alert_count", "fleet_alert_list",
            "fleet_vehicle_alert_list", "fleet_alert_count", "alert_distribution"
        )
        if not is_alert_query:
            from_date, to_date = week_ago, today
            time_range_altered_to_week = True

    logger.info(
        f"[FLEET SERVICE] fleet_analytics | "
        f"company={company_id} | {from_date} → {to_date} | live_only={is_live_metrics_only}"
    )

    # --------------------------------------------------
    # 2.5 BUILD ANALYZER WITH VEHICLE ID MAP & SHORT-CIRCUIT LIVE ONLY
    # --------------------------------------------------
    cache = get_vehicle_cache(company_id)
    vid_to_np = {}
    for vehicle in cache.get("data", []):
        vid = vehicle.get("ID")
        np = vehicle.get("NumberPlate")
        if vid and np:
            vid_to_np[vid] = np

    if is_live_metrics_only:
        logger.info("[FLEET SERVICE] Live-only query — calling combined API with today's date for lastRecords.")
        raw = combined_report_fleet(
            company_id=company_id,
            from_date=today,
            to_date=today
        )
    else:
        raw = combined_report_fleet(
            company_id=company_id,
            from_date=from_date,
            to_date=to_date
        )

    if not raw.get("success"):
        return {
            "type":    "error",
            "message": raw.get("error", "Fleet data unavailable")
        }

    analyzer = FleetAnalyzer(raw, vid_to_np)

    # --------------------------------------------------
    # 4. DISPATCH
    # --------------------------------------------------
    result = _dispatch(intent, analyzer)

    result["time_range"]  = (from_date, to_date)
    result["time_range_altered_to_week"] = time_range_altered_to_week
    result["type"]        = "fleet_analytics"

    logger.debug(f"[FLEET SERVICE] Result: {result}")
    return result


# =========================================================
# DISPATCH ROUTER
# =========================================================

def _dispatch(intent, analyzer: FleetAnalyzer) -> dict:
    """
    Reads intent fields (fleet_metric, fleet_aggregation,
    fleet_subject, fleet_filter, fleet_query_type) and
    calls the appropriate FleetAnalyzer method.
    """

    metric      = (getattr(intent, "fleet_metric",      None) or "").lower()
    aggregation = (getattr(intent, "fleet_aggregation",  None) or "maximum").lower()
    subject     = (getattr(intent, "fleet_subject",      None) or "vehicle").lower()
    filt        = (getattr(intent, "fleet_filter",       None) or "").lower()
    qtype       = (getattr(intent, "fleet_query_type",   None) or "").lower()
    metrics_list = getattr(intent, "metrics", [])

    logger.info(
        f"[FLEET DISPATCH] metric={metric!r} agg={aggregation!r} "
        f"subject={subject!r} filter={filt!r} qtype={qtype!r} metrics={metrics_list}"
    )

    query_text = (getattr(intent, "query", "") or "").lower()
    import re
    match = re.search(r'\btop\s+(\d+)\b', query_text)
    top_n = int(match.group(1)) if match else 10

    # --------------------------------------------------
    # 0) Fleet metrics list (specific fields requested)
    # --------------------------------------------------
    valid_state_filters = {"", "on", "off", "open", "closed", "fastened", "unfastened", "enabled", "disabled"}
    if metrics_list and not qtype and filt in valid_state_filters and metric in ("", "status"):
        return {
            "query_type": "fleet_metrics_list",
            "metrics_requested": metrics_list,
            "filter": filt,
            "vehicles": analyzer.get_live_metrics_for_fleet(metrics_list),
        }

    # --------------------------------------------------
    # A) List vehicles by live status (moving/idle/stopped…)
    # --------------------------------------------------
    if filt in {"moving", "idle", "stopped", "out_network", "disconnected"}:
        vehicles = analyzer.find_vehicles_by_status(filt)
        return {
            "query_type": "fleet_status_list",
            "subject":    subject,
            "status":     filt,
            "count":      len(vehicles),
            "vehicles":   vehicles,
        }

    # --------------------------------------------------
    # B) Fleet overview / status counts
    # --------------------------------------------------
    if qtype == "fleet_overview" or metric == "status":
        return {
            "query_type": "fleet_overview",
            "overview":   analyzer.fleet_overview(),
            "totals":     analyzer.fleet_operation_totals(),
            "alerts_total": analyzer.alerts_total,
            "alerts_distribution": analyzer.alert_count_by_type(),
        }

    # --------------------------------------------------
    # C) Alerts — count / distribution / listing
    # --------------------------------------------------
    if qtype == "alert_count" or (metric == "alerts" and aggregation == "count"):
        return {
            "query_type":   "fleet_alert_count",
            "subject":      subject,
            **analyzer.alert_count_summary(filt or None),
            "distribution": analyzer.alert_count_by_type(),
        }

    if qtype == "alert_distribution":
        return {
            "query_type":   "fleet_alert_distribution",
            "distribution": analyzer.alert_count_by_type(),
        }

    # Which driver/vehicle/group had most alerts?
    if metric == "alerts" and aggregation in {"maximum", "most"}:
        if subject == "driver":
            return {
                "query_type": "top_alert_driver",
                **analyzer.most_alerts_driver(filt or None),
            }
        elif subject == "group":
            return {
                "query_type": "top_alert_group",
                **analyzer.most_alerts_group(filt or None),
            }
        return {
            "query_type": "top_alert_vehicle",
            **analyzer.most_alerts_vehicle(filt or None),
        }

    # Which driver/vehicle/group had least alerts?
    if metric == "alerts" and aggregation in {"minimum", "least"}:
        if subject == "driver":
            # Optional: implement least_alerts_driver in analyzer later if needed
            return {"query_type": "fleet_overview", "overview": analyzer.fleet_overview()}
        elif subject == "group":
            return {"query_type": "fleet_overview", "overview": analyzer.fleet_overview()}
        return {
            "query_type": "bottom_alert_vehicle",
            **analyzer.least_alerts_vehicle(filt or None),
        }

    # Ranked alerts (Top N vehicles)
    is_ranking_query = bool(re.search(r'\btop\b', query_text) or re.search(r'\brank', query_text))
    if metric == "alerts" and (aggregation == "list" or qtype == "alert_list") and is_ranking_query:
        return {
            "query_type": "ranked_alerts",
            "alertType":  filt or "all",
            "ranked":     analyzer.rank_vehicles_by_alerts(filt or None, top_n=top_n),
        }

    # List vehicles that had alerts (deduplicated — one entry per vehicle)
    if qtype == "alert_list" or (metric == "alerts" and aggregation == "list"):
        return {
            "query_type": "fleet_vehicle_alert_list",
            "alertType":  filt or "all",
            "vehicles":   analyzer.vehicles_with_alerts(filt or None),
        }

    # --------------------------------------------------
    if metric == "speed" and aggregation == "maximum":
        # Extract maxSpeed strictly from operationSummary
        top = analyzer.top_vehicle_by_metric("maxSpeed", "maximum")
        return {
            "query_type": "top_speed",
            "subject":    subject,
            **top,
        }

    if metric == "speed" and aggregation == "minimum":
        top = analyzer.top_vehicle_by_metric("maxSpeed", "minimum")
        return {
            "query_type": "bottom_speed",
            "subject":    subject,
            **top,
        }

    # Ranked speed list
    if metric == "speed" and aggregation == "list":
        return {
            "query_type": "ranked_speed",
            "ranked":     analyzer.rank_vehicles_by_metric("maxSpeed", top_n=top_n),
        }

    # --------------------------------------------------
    # E) Distance / idle / moving / stop / engine_hours
    # --------------------------------------------------
    api_field = METRIC_TO_API_FIELD.get(metric)
    if api_field:
        if aggregation in {"maximum", "most", "highest"}:
            top = analyzer.top_vehicle_by_metric(api_field, "maximum")
            return {
                "query_type": f"top_{metric.replace(' ', '_')}",
                "subject":    subject,
                **top,
            }
        if aggregation in {"minimum", "least", "lowest"}:
            top = analyzer.top_vehicle_by_metric(api_field, "minimum")
            return {
                "query_type": f"bottom_{metric.replace(' ', '_')}",
                "subject":    subject,
                **top,
            }
        if aggregation == "list":
            return {
                "query_type": f"ranked_{metric.replace(' ', '_')}",
                "ranked":     analyzer.rank_vehicles_by_metric(api_field, top_n=top_n),
            }
        # default — maximum
        top = analyzer.top_vehicle_by_metric(api_field, "maximum")
        return {
            "query_type": f"top_{metric.replace(' ', '_')}",
            "subject":    subject,
            **top,
        }

    # --------------------------------------------------
    # F) Generic fallback — fleet overview + totals
    # --------------------------------------------------
    return {
        "query_type": "fleet_overview",
        "overview":   analyzer.fleet_overview(),
        "totals":     analyzer.fleet_operation_totals(),
        "alerts_total": analyzer.alerts_total,
        "alerts_distribution": analyzer.alert_count_by_type(),
    }
