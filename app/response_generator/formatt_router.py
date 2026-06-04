# formatter_router.py

from app.response_generator.realtime_formatter import format_realtime
from app.response_generator.alert_formatter import format_alert
from app.response_generator.summary_formatter import format_summary
from app.response_generator.alert_enable_formatter import format_alert_enable
from app.response_generator.fleet_analytics_formatter import format_fleet_analytics
from app.utils.logger import logger



def build_user_message(result, intent):

    result_type = result.get("type")
    logger.info(f"Result type: {result_type}")

    if result_type in [
        "realtime_status",
        "realtime_metric"
    ]:
        return format_realtime(result, intent)

    if (
        "alert" in (result_type or "")
        and result_type not in ["fleet_analytics"]
        or result_type in [
            "overspeed_summary",
            "idling_summary",
            "afterhours_summary"
        ]
    ):
        if result_type in [
            "alert_enable_single",
            "alert_enable_all"
        ]:
            return format_alert_enable(result, intent)

        return format_alert(result, intent)

    if result_type in [
        "summary",
        "summary_metric"
    ]:
        return format_summary(result, intent)

    if result_type == "fleet_analytics":
        return format_fleet_analytics(result)

    return result.get(
        "message",
        "Unable to generate response."
    )