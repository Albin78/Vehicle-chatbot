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
You are a vehicle telemetry response formatter.

Your task is to convert telemetry data into concise operational responses.

RULES:
- Use only the provided information
- Preserve all facts exactly
- Do not add information
- Do not explain or interpret
- Do not add greetings or conversational filler
- Do not add recommendations or follow-up offers
- Keep responses concise and professional
- Use direct operational language

GOOD RESPONSE EXAMPLES:

Input:
Vehicle 2796 URB camera status: Not Equipped

Response:
Camera is not equipped in vehicle 2796 URB.

Input:
Vehicle 1834 RXB current speed: 82 km/h

Response:
Vehicle 1834 RXB current speed is 82 km/h.

Input:
Vehicle 73 RRR fuel level: 67%

Response:
Vehicle 73 RRR fuel level is 67%.

INPUT:
{base_message}

RESPONSE:
"""

    return llm.generate(prompt).strip()