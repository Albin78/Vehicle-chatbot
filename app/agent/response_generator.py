from app.llm.ollama_client import OllamaClient

llm = OllamaClient()



def build_user_message(result, intent):
    if not result:
        return "No data found for the given vehicle."

    if result["type"] == "metric":
        value = result.get("value")

        if value is None:
            return "No data found for the requested metric."

        if intent.aggregation:
            return f"{intent.metric.capitalize()} {intent.aggregation} is {value}."
        else:
            return f"Current {intent.metric} is {value}."

    elif result["type"] == "summary":
        return (
            f"The vehicle traveled {result.get('total_distance')} km, "
            f"with {result.get('total_moving_time')} moving time and "
            f"{result.get('total_idle_time')} idle time."
        )
    

def generate_response(query, result, intent):
    
    final_message = build_user_message(result, intent)
    prompt_response = f"""
You are a response rewriter for a Vehicle Monitoring System.

Your job is to improve readability and make the sentence slightly more natural.

----------------------------------------
INPUT:

User Query:
{query}

System Message:
{final_message}

----------------------------------------

RULES (STRICT):

- The System Message is the ONLY source of truth
- DO NOT change any numbers, values, or facts
- DO NOT add new information
- DO NOT remove any information
- You MAY slightly align wording with the user query
- Keep it EXACTLY one sentence

----------------------------------------

Return ONLY the final sentence.
"""

    return llm.generate(prompt_response)