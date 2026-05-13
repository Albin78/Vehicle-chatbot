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
    # SUMMARY
    # --------------------------------------------------

    if intent.source == "summary":

        payload["from_date"] = plan.time_range[0]
        payload["to_date"] = plan.time_range[1]

    # --------------------------------------------------
    # ALERT
    # --------------------------------------------------

    elif intent.source == "alert":

        payload["from_date"] = plan.time_range[0]
        payload["to_date"] = plan.time_range[1]

    return payload