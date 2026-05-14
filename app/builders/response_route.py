from app.builders.realtime_builder import (
    build_realtime_response
)

from app.builders.alert_builder import (
    build_alert_response
)

from app.builders.summary_builder import (
    build_summary_response
)


def build_response(intent, api_result):

    if intent.source == "latest":

        return build_realtime_response(
            intent,
            api_result
        )

    if intent.source == "alert":

        return build_alert_response(
            intent,
            api_result
        )

    if intent.source == "summary":

        return build_summary_response(
            intent,
            api_result
        )

    return {
        "type": "error",
        "message": "Unsupported source"
    }