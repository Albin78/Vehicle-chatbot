from datetime import datetime, timezone


def get_today_date():

    return datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")



def build_combined_payload(
    intent,
    plan,
    vehicle,
    company_id
):

    payload = {

        "company_id": company_id,

        "vehicle_id": vehicle["ID"],
    }

    # --------------------------------------------------
    # SUMMARY / ALERT WITH RANGE
    # --------------------------------------------------

    if intent.source in ["summary", "alert"]:

        payload["from_date"] = plan.time_range[0]
        payload["to_date"] = plan.time_range[1]

    # --------------------------------------------------
    # LATEST / CURRENT STATUS
    # --------------------------------------------------

    elif intent.source in ["latest", "realtime"]:

        today = get_today_date()

        payload["from_date"] = today
        payload["to_date"] = today

    return payload