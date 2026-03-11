from app.llm.ollama_client import OllamaClient
from app.schemas.intent_schema import QueryIntent

llm = OllamaClient()


def extract_intent(query: str) -> QueryIntent:

    prompt = f"""
    Extract telemetry query intent.

    Query: {query}

    Return JSON:
    metric
    imei
    aggregation
    analysis
    time_range
    service
    """

    response = llm.generate(prompt)

    return QueryIntent.model_validate_json(response)