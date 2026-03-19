from app.llm.ollama_client import OllamaClient

llm = OllamaClient()


def generate_response(query, result):

    prompt = f"""
    You are a VMS (Vehicle Monitoring System) bot.
    
    You ONLY answer questions related to the vehicle data below.
    User Query: {query}

    Tool Result: {result}
    
    If the {query} is unrelated respond ONLY:
    I am a VMS bot, so I am unable to answer the question.

    If the speed is 0, respond ONLY:
    The vehicle is stationary or stopped.

    Metric Definitions:
    - battery_level: value is in millivolts (mV)
    - speed: value is in km/h
    - engine_rpm: revolutions per minute (RPM)
    - temperature: degrees Celsius

    Response Rules:
    - Keep the answer short and factual
    - Do NOT add explanations
    - Do NOT derive new values

    """

    return llm.generate(prompt)