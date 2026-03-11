import requests
from app.config import settings


class OllamaClient:

    def generate(self, prompt: str):

        response = requests.post(
            f"{settings.OLLAMA_URL}",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data["response"]