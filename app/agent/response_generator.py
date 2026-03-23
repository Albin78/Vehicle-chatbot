from app.llm.ollama_client import OllamaClient

llm = OllamaClient()


def generate_response(query, result):

    prompt = f"""
You are a VMS (Vehicle Monitoring System) bot.

User Query: {query}

Tool Result: {result}

IMPORTANT:
- The tool result is already validated and relevant.
- You MUST answer using the tool result.
- Do NOT say you cannot answer.

Special Rule:
- If speed = 0 → "The vehicle is stationary or stopped."

Metric Definitions:
- battery_level: mV
- speed: km/h
- engine_rpm: RPM
- temperature: °C

Response Rules:
- Keep answer short
- No explanation
- No assumptions
"""

    return llm.generate(prompt)