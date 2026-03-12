from app.llm.ollama_client import OllamaClient

llm = OllamaClient()


def generate_response(query, result):

    prompt = f"""
    User Query: {query}

    Tool Result: {result}

    If the question is unrelated respond ONLY:
    I am a VMS bot, so I am unable to answer the question.

    If the speed is 0, respond ONLY:
    The vehicle is stationary or stopped.

    Generate clear answer.
    """

    return llm.generate(prompt)