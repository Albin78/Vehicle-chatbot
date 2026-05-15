from app.parsers.date_parser import (
    format_time_generate
)


# =========================================================
# HELPERS
# =========================================================

def build_distribution_text(
    distribution: dict
) -> str:

    if not distribution:
        return ""

    return ", ".join(

        f"{count} {alert_name}"

        for alert_name, count
        in distribution.items()
    )


def build_daily_summary_text(
    daily_alerts: dict
) -> str:

    if not daily_alerts:
        return ""

    sorted_days = sorted(
        daily_alerts.items()
    )

    return ", ".join(

        f"{count} alerts on {date}"

        for date, count
        in sorted_days
    )


# =========================================================
# ALERT COUNT FORMATTER
# =========================================================

def format_alert_count(
    result,
    intent
):

    total_alerts = result.get(
        "total_alerts",
        0
    )

    return (

        f"{total_alerts} alerts were "
        f"recorded for vehicle "
        f"{intent.vehicle_id}."
    )


# =========================================================
# LATEST ALERT FORMATTER
# =========================================================

def format_latest_alert(
    result,
    intent
):

    latest = result.get(
        "latest_alert",
        {}
    )

    if not latest:

        return (
            f"No latest alert data available "
            f"for vehicle {intent.vehicle_id}."
        )

    latest_parts = []

    alert_name = latest.get(
        "alert_name"
    )

    if alert_name:

        latest_parts.append(
            alert_name
        )

    latest_time = latest.get(
        "time"
    )

    if latest_time:

        latest_parts.append(

            f"on "
            f"{format_time_generate(latest_time)}"
        )

    latest_value = latest.get(
        "value"
    )

    if latest_value:

        latest_parts.append(
            f"value {latest_value}"
        )

    latest_limit = latest.get(
        "limit"
    )

    if latest_limit:

        latest_parts.append(
            f"against limit "
            f"{latest_limit}"
        )

    latest_duration = latest.get(
        "duration"
    )

    if latest_duration:

        latest_parts.append(
            f"lasting "
            f"{latest_duration}"
        )

    return (

        "Latest alert recorded: "
        + ", ".join(latest_parts)
        + "."
    )


# =========================================================
# DAILY ALERT SUMMARY FORMATTER
# =========================================================

def format_daily_alert_summary(
    result,
    intent
):

    insights = []

    daily_alerts = result.get(
        "daily_alerts",
        {}
    )

    if daily_alerts:

        daily_summary = (
            build_daily_summary_text(
                daily_alerts
            )
        )

        insights.append(

            f"Daily alert trend included "
            f"{daily_summary}"
        )

    peak_day = result.get(
        "peak_alert_day"
    )

    peak_count = result.get(
        "peak_alert_count"
    )

    if peak_day and peak_count:

        insights.append(

            f"Highest alert activity "
            f"occurred on {peak_day} "
            f"with {peak_count} alerts"
        )

    return ". ".join(insights) + "."


# =========================================================
# FULL ALERT SUMMARY FORMATTER
# =========================================================

def format_full_alert_summary(
    result,
    intent
):

    insights = []

    # =====================================================
    # TOTAL ALERTS
    # =====================================================

    total_alerts = result.get(
        "total_alerts",
        0
    )

    insights.append(

        f"{total_alerts} alerts were "
        f"recorded for vehicle "
        f"{intent.vehicle_id}"
    )

    # =====================================================
    # DISTRIBUTION
    # =====================================================

    distribution = result.get(
        "alert_distribution",
        {}
    )

    if distribution:

        distribution_text = (
            build_distribution_text(
                distribution
            )
        )

        insights.append(

            f"Alert distribution included "
            f"{distribution_text}"
        )

    # =====================================================
    # MOST COMMON
    # =====================================================

    most_common_alert = result.get(
        "most_common_alert"
    )

    if most_common_alert:

        insights.append(

            f"The most frequent alert "
            f"type was "
            f"{most_common_alert}"
        )

    # =====================================================
    # DAILY ALERTS
    # =====================================================

    daily_alerts = result.get(
        "daily_alerts",
        {}
    )

    if daily_alerts:

        daily_summary = (
            build_daily_summary_text(
                daily_alerts
            )
        )

        insights.append(

            f"Daily alert trend included "
            f"{daily_summary}"
        )

    peak_day = result.get(
        "peak_alert_day"
    )

    peak_count = result.get(
        "peak_alert_count"
    )

    if peak_day and peak_count:

        insights.append(

            f"Highest alert activity "
            f"occurred on {peak_day} "
            f"with {peak_count} alerts"
        )

    # =====================================================
    # LATEST ALERT
    # =====================================================

    latest = result.get(
        "latest_alert",
        {}
    )

    if latest:

        latest_parts = []

        if latest.get("alert_name"):

            latest_parts.append(
                latest.get("alert_name")
            )

        if latest.get("time"):

            latest_parts.append(

                f"on "
                f"{format_time_generate(latest.get('time'))}"
            )

        if latest.get("value"):

            latest_parts.append(
                f"value "
                f"{latest.get('value')}"
            )

        if latest.get("limit"):

            latest_parts.append(
                f"against limit "
                f"{latest.get('limit')}"
            )

        if latest.get("duration"):

            latest_parts.append(
                f"lasting "
                f"{latest.get('duration')}"
            )

        insights.append(

            "Latest alert recorded: "
            + ", ".join(latest_parts)
        )

    # =====================================================
    # OVERSPEED
    # =====================================================

    overspeed = result.get(
        "overspeed",
        {}
    )

    overspeed_count = overspeed.get(
        "count",
        0
    )

    if overspeed_count:

        insights.append(

            f"{overspeed_count} "
            f"overspeed alerts were detected"
        )

        highest = overspeed.get(
            "highest"
        )

        if highest:

            highest_parts = []

            if highest.get("speed"):

                highest_parts.append(

                    f"highest speed reached "
                    f"{highest.get('speed')}"
                )

            if highest.get("limit"):

                highest_parts.append(

                    f"against limit "
                    f"{highest.get('limit')}"
                )

            if highest.get("time"):

                highest_parts.append(

                    f"on "
                    f"{format_time_generate(highest.get('time'))}"
                )

            if highest.get("duration"):

                highest_parts.append(

                    f"lasting "
                    f"{highest.get('duration')}"
                )

            insights.append(
                ", ".join(highest_parts)
            )

    else:

        insights.append(
            "No overspeed alerts were detected"
        )

    # =====================================================
    # IDLING
    # =====================================================

    idling = result.get(
        "idling",
        {}
    )

    idling_count = idling.get(
        "count",
        0
    )

    if idling_count:

        insights.append(

            f"{idling_count} "
            f"idling alerts were detected"
        )

        longest_idle = idling.get(
            "longest"
        )

        if longest_idle:

            idle_parts = []

            if longest_idle.get("duration"):

                idle_parts.append(

                    f"longest idle duration "
                    f"was "
                    f"{longest_idle.get('duration')}"
                )

            if longest_idle.get("time"):

                idle_parts.append(

                    f"on "
                    f"{format_time_generate(longest_idle.get('time'))}"
                )

            insights.append(
                ", ".join(idle_parts)
            )

    else:

        insights.append(
            "No idling alerts were detected"
        )

    # =====================================================
    # AFTER HOURS
    # =====================================================

    afterhours = result.get(
        "afterhoursmovement",
        {}
    )

    afterhours_count = afterhours.get(
        "count",
        0
    )

    if afterhours_count:

        insights.append(

            f"{afterhours_count} "
            f"after-hours movement "
            f"alerts were detected"
        )

    else:

        insights.append(

            "No after-hours movement "
            "alerts were detected"
        )

    return ". ".join(insights) + "."


# =========================================================
# MAIN ROUTER
# =========================================================

def format_alert(
    result,
    intent
):

    result_type = result.get("type")

    # =====================================================
    # ERROR
    # =====================================================

    if result_type == "error":

        return result.get(
            "message",
            "Unable to process alert data."
        )

    # =====================================================
    # ALERT COUNT
    # =====================================================

    if result_type == "alert_count":

        return format_alert_count(
            result,
            intent
        )

    # =====================================================
    # LATEST ALERT
    # =====================================================

    if result_type == "latest_alert":

        return format_latest_alert(
            result,
            intent
        )

    # =====================================================
    # DAILY ALERT SUMMARY
    # =====================================================

    if result_type == "daily_alert_summary":

        return format_daily_alert_summary(
            result,
            intent
        )

    # =====================================================
    # FULL ALERT SUMMARY
    # =====================================================

    if result_type == "alert_summary":

        return format_full_alert_summary(
            result,
            intent
        )

    # =====================================================
    # FALLBACK
    # =====================================================

    return "Unable to format alert response."