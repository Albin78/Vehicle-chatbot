import requests
from app.config import settings


class OllamaClient:

    def __init__(self):
        self.url = f"{settings.OLLAMA_URL}/api/generate"

    def generate(self, prompt):

        response = requests.post(
            self.url,
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
        )

        return response.json()["response"]