from app.parsers.date_parser import format_time_generate


def format_alert(result, intent):

    result_type = result.get("type")

    # -------------------------
    # ALERT COUNT
    # -------------------------

    if result_type == "alert_count":

        return (
            f"A total of "
            f"{result.get('total_alerts')} alerts "
            f"were recorded for vehicle "
            f"{intent.vehicle_id}."
        )

    # -------------------------
    # ALERT LATEST
    # -------------------------

    if result_type == "alert_latest":

        parts = []

        parts.append(
            f"The latest "
            f"{result.get('alert_name')} alert"
        )

        if result.get("time"):
            parts.append(
                f"occurred on "
                f"{format_time_generate(result.get('time'))}"
            )

        if result.get("driver"):
            parts.append(
                f"by driver "
                f"{result.get('driver')}"
            )

        if result.get("value"):
            parts.append(
                f"with recorded value "
                f"{result.get('value')}"
            )

        if result.get("limit"):
            parts.append(
                f"against allowed limit "
                f"{result.get('limit')}"
            )

        if result.get("duration"):
            parts.append(
                f"lasting "
                f"{result.get('duration')}"
            )

        return ", ".join(parts) + "."

    # -------------------------
    # ALERT SUMMARY
    # -------------------------

    if result_type == "alert_summary":

        insights = []

        insights.append(
            f"{result.get('total_alerts')} alerts "
            f"were recorded"
        )

        if result.get("most_common_alert"):
            insights.append(
                f"with "
                f"{result.get('most_common_alert')} "
                f"being the most frequent"
            )

        highest_overspeed = result.get(
            "highest_overspeed"
        )

        if highest_overspeed:

            insights.append(
                f"highest overspeed was "
                f"{highest_overspeed.get('speed')} "
                f"against limit "
                f"{highest_overspeed.get('limit')} "
                f"on "
                f"{format_time_generate(highest_overspeed.get('time'))}"
            )

        longest_idle = result.get(
            "longest_idle"
        )

        if longest_idle:

            insights.append(
                f"longest idling duration was "
                f"{longest_idle.get('duration')} "
                f"on "
                f"{format_time_generate(longest_idle.get('time'))}"
            )

        latest = result.get("latest_alert")

        if latest:

            insights.append(
                f"latest alert was "
                f"{latest.get('alert_name')} "
                f"on "
                f"{format_time_generate(latest.get('time'))}"
            )

        return ". ".join(insights) + "."