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
        "You are a fleet data relay. Your task: rewrite the INPUT below as OUTPUT.\n"
        "\n"
        "CONTRACT:\n"
        "- OUTPUT contains only facts present in INPUT.\n"
        "- If a field is not in INPUT, it must not appear in OUTPUT.\n"
        "- No notes, headers, caveats, placeholders, or extra commentary.\n"
        "\n"
        "<example>\n"
        "INPUT: For vehicle 1832RXB, Speed is 0 km/h. Fuel capacity is 400 L."
        " Last updated May 22, 2026 10:36 AM UTC.\n"
        "OUTPUT: Vehicle 1832RXB — Speed: 0 km/h | Fuel capacity: 400 L"
        " | Last updated: May 22, 2026, 10:36 AM UTC.\n"
        "</example>\n"
        "\n"
        "Now rewrite only this INPUT:\n"
        f"INPUT: {base_message}\n"
        "OUTPUT:"
    )

    return llm.generate(prompt).strip()