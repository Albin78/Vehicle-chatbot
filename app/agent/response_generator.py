from app.llm.ollama_client import OllamaClient

llm = OllamaClient()


def generate_response(query, result):

    prompt = f"""
    User Query: {query}

    Tool Result: {result}

    Generate clear answer.
    """

    return llm.generate(prompt)