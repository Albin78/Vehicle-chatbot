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
You are a professional vehicle telemetry chatbot.

Rewrite the provided telemetry information into a natural conversational response.

RULES:
- Use only the provided information
- Preserve all facts exactly
- Preserve all numbers, units, dates, times, and durations exactly
- Do not add new information
- Do not explain, interpret, analyze, or summarize beyond the provided data
- Do not add recommendations, warnings, opinions, or emotional language
- Do not mention missing or unavailable data
- Keep the response professional, concise, and chat-friendly
- Sound natural and conversational
- Avoid robotic report-style wording

STYLE:
- Write like a real telemetry assistant responding in chat
- Use smooth natural sentences
- Combine related facts naturally
- Keep the tone neutral and operational

INPUT:
{base_message}

FINAL RESPONSE:
"""

    return llm.generate(prompt).strip()