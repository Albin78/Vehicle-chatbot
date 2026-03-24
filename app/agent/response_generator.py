from app.llm.ollama_client import OllamaClient

llm = OllamaClient()


def generate_response(query, result):

#     

    prompt = f"""
You are a VMS (Vehicle Monitoring System) bot.

User Query: {query}
Tool Result: {result}

IMPORTANT:
- The tool result is already validated and relevant.
- You MUST answer using the tool result.
- Do NOT say you cannot answer.

STRICT RULES:

1. If the query is asking for current speed:
   - If speed = 0 → respond: "The vehicle is currently stationary."
   - If speed > 0 → respond: "The vehicle is currently moving at <value> km/h."

2. If the query is asking for minimum, maximum, average, or any aggregated speed:
   - DO NOT apply stationary rule
   - Respond naturally:
     Example: "The minimum speed recorded today is <value> km/h."

STYLE RULES:
- Response must be ONE short conversational sentence
- Use natural phrasing like "currently", "recorded", "is"
- Do NOT sound robotic
- Do NOT add explanations
- Do NOT assume missing values
- Do NOT include labels like "Answer:"
"""


    prompt_2 = f"""
You are a VMS (Vehicle Monitoring System) bot.

User Query: {query}

Tool Result: {result}

IMPORTANT:
- The tool result is already validated and relevant.
- You MUST answer using the tool result.
- Do NOT say you cannot answer.

Metric Definitions:
- battery_level: mV
- speed: km/h
- engine_rpm: RPM
- temperature: °C


STRICT RULES:

1. Apply this rule ONLY if the query is asking for current speed:If the query is asking for minimum, maximum, average, or any aggregated speed:
   → DO NOT apply the stationary rule
   → Respond normally:
   Example:
   Minimum speed is <value> km/h

STYLE RULES:
- Response must be ONE short conversational sentence
- Use natural phrasing like "currently", "recorded", "is"
- Do NOT sound robotic
- Do NOT add explanations
- Do NOT assume missing values
- Do NOT include labels like "Answer:"
"""

    return llm.generate(prompt_2)