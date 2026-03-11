from app.llm.ollama_client import OllamaClient
from app.schemas.intent_schema import QueryIntent

llm = OllamaClient()


def extract_intent(query: str) -> QueryIntent:

    prompt = f"""
    Extract the intent and imei from the query.

Return ONLY valid JSON.

Schema:
{
 "intent": string,
 "imei": string | null
}

Query:
{query}

Very important line:

Return ONLY valid JSON. Do not include explanation.
    """

    response = llm.generate(prompt)

    return QueryIntent.model_validate_json(response)