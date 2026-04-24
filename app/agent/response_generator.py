from app.llm.ollama_client import OllamaClient

llm = OllamaClient()


def get_unit(metric):
    unit_map = {
        "speed": "km/h",
        "distance": "km",
        "battery": "mV",
        "temperature": "°C"
    }
    return unit_map.get(metric, "")



def build_user_message(result, intent):

    if not result or "error" in result:
        return result.get("error", "I couldn't find any data for the given vehicle.")

    time_context = ""
    if intent.time_range:
        time_context = f" for the time range {intent.time_range}"

    result_type = result.get("type")

    # -----------------------------
    # REALTIME METRIC
    # -----------------------------
    if result_type == "realtime_metric":
        metric = result.get("metric")
        value = result.get("value")

        unit = get_unit(metric)

        return (
            f"The current {metric} of vehicle {result.get('vehicle')} "
            f"is {value} {unit}."
        )

    # -----------------------------
    # REALTIME STATUS
    # -----------------------------
    if result_type == "realtime_status":
        return (
            f"The vehicle {result.get('vehicle')} is currently "
            f"{result.get('status')} (last updated {result.get('last_updated')})."
        )

    # -----------------------------
    # HISTORICAL METRIC
    # -----------------------------
    if result_type == "metric":
        value = result.get("value")

        if value is None:
            return "I couldn't find data for the requested metric."

        unit = get_unit(intent.metric)

        if intent.aggregation:
            return (
                f"For vehicle {intent.vehicle_id}, the {intent.metric} "
                f"{intent.aggregation}{time_context} is {value} {unit}."
            )
        else:
            return (
                f"For vehicle {intent.vehicle_id}, the current "
                f"{intent.metric}{time_context} is {value} {unit}."
            )

    # -----------------------------
    # SUMMARY
    # -----------------------------
    if result_type == "summary":
        return (
            f"Vehicle {intent.vehicle_id}{time_context} traveled "
            f"{result.get('total_distance')} km with an average speed of "
            f"{result.get('average_speed')} km/h and engine hours "
            f"{result.get('engine_hours')}."
        )

    return "Unable to generate response."



def generate_response(result, intent):

    if not result or "error" in result:
        return result.get("error", "No data found.")

    prompt = f"""
You are a vehicle telemetry assistant.

Generate a natural, conversational response using ONLY the provided data.

----------------------------------------
DATA:
{result}

INTENT:
- metric: {intent.metric}
- vehicle: {intent.vehicle_id}
- intent_type: {intent.intent_type}
----------------------------------------

STRICT RULES:

- Use ONLY values present in DATA
- DO NOT modify numbers
- DO NOT infer or assume anything
- DO NOT add explanations beyond the data
- Keep response concise and natural
- Prefer 1–2 sentences max
- If metric query → answer ONLY that metric
- If status query → describe status naturally

----------------------------------------

Generate the response:
"""

    return llm.generate(prompt)