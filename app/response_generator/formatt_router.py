# formatter_router.py

from app.response_generator.realtime_formatter import format_realtime
from app.response_generator.alert_formatter import format_alert
from app.response_generator.summary_formatter import format_summary
from app.utils.logger import logger



def build_user_message(result, intent):

    result_type = result.get("type")
    logger.info(f"Result type: {result_type}")

    if result_type in [
        "realtime_status",
        "realtime_metric"
    ]:
        return format_realtime(result, intent)

    if result_type.startswith("alert"):
        return format_alert(result, intent)

    if result_type in [
        "summary",
        "summary_metric"
    ]:
        return format_summary(result, intent)

    # if result_type == "metric":
    #     return format_metric(result, intent)

    return result.get(
        "message",
        "Unable to generate response."
    )