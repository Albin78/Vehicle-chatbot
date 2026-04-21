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
        return "I couldn't find any data for the given vehicle."

    time_context = ""
    if intent.time_range:
        time_context = f" for the time range {intent.time_range}"

    if result["type"] == "metric":
        value = result.get("value")

        if value is None:
            return "I couldn't find data for the requested metric."

        if intent.aggregation:
            return (
                f"For vehicle {intent.vehicle_id}, the {intent.metric} "
                f"{intent.aggregation}{time_context} is {value}."
            )
        else:
            return (
                f"For vehicle {intent.vehicle_id}, the current "
                f"{intent.metric}{time_context} is {value}."
            )

    elif result["type"] == "summary":
        return (
            f"Here’s a quick summary for vehicle {intent.vehicle_id}{time_context}: "
            f"it traveled {result.get('total_distance')} km, "
            f"with an average speed of {result.get('average_speed')} km/h, "
            f"{result.get('total_moving_time')} moving time and "
            f"{result.get('total_idle_time')} idle time."
        )


def generate_response(result, intent):
    
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