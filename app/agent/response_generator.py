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


    prompt = (
        "You are a professional fleet management chatbot. Your task: rewrite the telemetry INPUT below into a natural, friendly, and highly professional OUTPUT sentence.\n"
        "\n"
        "CONTRACT:\n"
        "- OUTPUT contains only facts present in INPUT — nothing added, nothing omitted.\n"
        "- Write in short, professional sentence style. No bullet points, no pipes, no labels.\n"
        "- SPEED & MOVEMENT RULE:\n"
        "  * If Speed is exactly '0 km/h', interpret and describe it as being 'stationary' or 'stopped' (e.g. 'is currently stationary at 0 km/h' or 'is stopped at 0 km/h'). Never just print raw 0 km/h without describing it as stationary or stopped.\n"
        "  * If Speed is greater than '0 km/h', describe it as 'moving' (e.g. 'is currently moving at 45 km/h').\n"
        "- For descriptive fields (camera, seatbelt, ignition, door, immobilization), preserve the exact descriptive phrase from INPUT.\n"
        "- No headers, caveats, or extra commentary.\n"
        "\n"
        "<example>\n"
        "INPUT: For vehicle 1832RXB, Speed is 0 km/h. Fuel capacity is 400 L."
        " Last updated May 22, 2026 10:36 AM UTC.\n"
        "OUTPUT: Vehicle 1832RXB is currently stationary at 0 km/h with a fuel capacity of 400 L."
        " Last updated May 22, 2026, 10:36 AM UTC.\n"
        "</example>\n"
        "\n"
        "<example>\n"
        "INPUT: For vehicle 1832RXB, Speed is 0 km/h."
        " Last updated May 25, 2026 12:56 PM UTC.\n"
        "OUTPUT: Vehicle 1832RXB is currently stationary (stopped at 0 km/h)."
        " Last updated May 25, 2026, 12:56 PM UTC.\n"
        "</example>\n"
        "\n"
        "<example>\n"
        "INPUT: For vehicle 1832RXB, Speed is 65 km/h."
        " Last updated May 25, 2026 01:15 PM UTC.\n"
        "OUTPUT: Vehicle 1832RXB is currently moving at 65 km/h."
        " Last updated May 25, 2026, 01:15 PM UTC.\n"
        "</example>\n"
        "\n"
        "<example>\n"
        "INPUT: For vehicle 1832 RXB, camera is equipped with 1 camera channel."
        " Last updated May 25, 2026 03:58 AM UTC.\n"
        "OUTPUT: Vehicle 1832 RXB has a camera equipped with 1 channel."
        " Last updated May 25, 2026, 03:58 AM UTC.\n"
        "</example>\n"
        "\n"
        "<example>\n"
        "INPUT: For vehicle 5001 ABC, camera is not equipped."
        " Last updated May 25, 2026 08:00 AM UTC.\n"
        "OUTPUT: Vehicle 5001 ABC does not have a camera equipped."
        " Last updated May 25, 2026, 08:00 AM UTC.\n"
        "</example>\n"
        "\n"
        "<example>\n"
        "INPUT: For vehicle 1832 RXB, vehicle supports remote immobilization"
        " and is currently not remotely immobilized. Last updated May 25, 2026 04:18 AM UTC.\n"
        "OUTPUT: Vehicle 1832 RXB supports remote immobilization and is not currently immobilized."
        " Last updated May 25, 2026, 04:18 AM UTC.\n"
        "</example>\n"
        "\n"
        "<example>\n"
        "INPUT: For vehicle 1832 RXB, ignition is on. seatbelt is equipped but not fastened."
        " Last updated May 25, 2026 03:58 AM UTC.\n"
        "OUTPUT: Vehicle 1832 RXB has the ignition on. The seatbelt is equipped but not fastened."
        " Last updated May 25, 2026, 03:58 AM UTC.\n"
        "</example>\n"
        "\n"
        "Now rewrite only this INPUT:\n"
        f"INPUT: {base_message}\n"
        "OUTPUT:"
    )

    return llm.generate(prompt).strip()