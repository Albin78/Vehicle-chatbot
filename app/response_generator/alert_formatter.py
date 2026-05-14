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

    parts = []

    for alert_name, count in distribution.items():

        parts.append(
            f"{count} {alert_name}"
        )

    return ", ".join(parts)


# =========================================================
# MAIN FORMATTER
# =========================================================

def format_alert(result, intent):

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
    # ALERT SUMMARY
    # =====================================================

    if result_type == "alert_summary":

        insights = []

        # -------------------------------------------------
        # TOTAL ALERTS
        # -------------------------------------------------

        total_alerts = result.get(
            "total_alerts",
            0
        )

        insights.append(

            f"{total_alerts} alerts were "
            f"recorded for vehicle "
            f"{intent.vehicle_id}"
        )

        # -------------------------------------------------
        # DISTRIBUTION
        # -------------------------------------------------

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

                f"Alert distribution: "
                f"{distribution_text}"
            )

        # -------------------------------------------------
        # MOST COMMON
        # -------------------------------------------------

        most_common_alert = result.get(
            "most_common_alert"
        )

        if most_common_alert:

            insights.append(

                f"The most frequent alert "
                f"type was "
                f"{most_common_alert}"
            )

        # -------------------------------------------------
        # LATEST ALERT
        # -------------------------------------------------

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

            if latest_parts:

                insights.append(
                    "Latest alert: "
                    + ", ".join(latest_parts)
                )

        # -------------------------------------------------
        # OVERSPEED
        # -------------------------------------------------

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
                f"overspeed alerts detected"
            )

        highest = overspeed.get(
            "highest"
        )

        if highest:

            highest_parts = []

            if highest.get("speed"):

                highest_parts.append(
                    f"highest speed was "
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

            if highest_parts:

                insights.append(
                    ", ".join(highest_parts)
                )

        # -------------------------------------------------
        # IDLING
        # -------------------------------------------------

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
                f"idling alerts detected"
            )

        longest_idle = idling.get(
            "longest"
        )

        if longest_idle:

            idle_parts = []

            if longest_idle.get("duration"):

                idle_parts.append(
                    f"longest idle duration was "
                    f"{longest_idle.get('duration')}"
                )

            if longest_idle.get("time"):

                idle_parts.append(
                    f"on "
                    f"{format_time_generate(longest_idle.get('time'))}"
                )

            if idle_parts:

                insights.append(
                    ", ".join(idle_parts)
                )

        # -------------------------------------------------
        # AFTER HOURS
        # -------------------------------------------------

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
                f"alerts detected"
            )

        return ". ".join(insights) + "."

    # =====================================================
    # FALLBACK
    # =====================================================

    return "Unable to format alert response."