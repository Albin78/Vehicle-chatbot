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
    if not result:
        return "No data found for the given vehicle."

    if result["type"] == "metric":
        value = result.get("value")

        if value is None:
            return "No data found for the requested metric."

        unit = get_unit(intent.metric)

        if intent.aggregation:
            return f"The {intent.aggregation} {intent.metric} for the give date range is {value} {unit}."
        else:
            return f"The current {intent.metric} is {value} {unit}."

    elif result["type"] == "summary":
        return (
            f"The vehicle with ID {intent.vehicle_id} is a {result.get('vehicle_type')} "
            f"that traveled {result.get('total_distance')} km, "
            f"with an average speed of {round(result.get('average_speed'),2)} km/h, "
            f"{result.get('total_moving_time')} moving time and "
            f"{result.get('total_idle_time')} idle time."
        )


def generate_response(query, result, intent):
    
    final_message = build_user_message(result, intent)
    prompt_response = f"""
You are a response formatter.

Your job is to slightly improve readability without changing meaning.

----------------------------------------
INPUT SENTENCE:
"{final_message}"

----------------------------------------

STRICT RULES:

- You MUST keep ALL numbers EXACTLY the same
- You MUST keep ALL units EXACTLY the same (e.g., km/h, km, mV)
- DO NOT add any new numbers or units
- DO NOT add explanations, assumptions, or interpretations
- DO NOT add words like "exceeds", "safe", "limit", etc.
- DO NOT remove any information
- Keep it EXACTLY one sentence
- If already clear, return it unchanged

----------------------------------------

Return ONLY the sentence.
"""

    return llm.generate(prompt_response)