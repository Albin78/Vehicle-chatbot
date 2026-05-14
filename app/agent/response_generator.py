from app.llm.ollama_client import OllamaClient
from app.response_generator.formatt_router import build_user_message
from app.utils.logger import logger


llm = OllamaClient()


def generate_response(result, intent):
    

    logger.info(f"Result passed into the response generation: {result}")

    if not result:
        return "No data found."

    if "error" in result:
        return result["error"]
    
    

    base_message = build_user_message(
        result=result,
        intent=intent
    )

    prompt = f"""
You are a vehicle telemetry assistant.

Your task is to rewrite the provided response into a
natural and professional conversational reply.

RULES:
- Preserve ALL numbers, units, names, dates, durations, and metrics exactly
- Do NOT add new facts
- Do NOT remove information
- Do NOT summarize away important details
- Keep the response concise but complete
- Sound natural and professional
- Avoid robotic phrasing
- Avoid bullet points
- Return only the final response

INPUT:
{base_message}

FINAL RESPONSE:
"""

    return llm.generate(prompt).strip()