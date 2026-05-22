def format_afterhours_summary(result, intent):
    afterhours = result.get("afterhoursmovement", {})
    count = afterhours.get("count", 0)

    insights = []
    if count:
        insights.append(
            f"{count} after-hours movement alerts were detected for vehicle {intent.vehicle_id}"
        )
    else:
        insights.append(
            f"No after-hours movement alerts were detected for vehicle {intent.vehicle_id}"
        )

    return ". ".join(insights) + "."
