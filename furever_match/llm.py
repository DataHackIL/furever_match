import json
import os
from typing import Protocol

import httpx


class LLMClient(Protocol):
    def extract(self, prompt: str) -> dict: ...


class OllamaClient:
    def __init__(self, model: str = "gemma3:4b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def extract(self, prompt: str) -> dict:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"num_predict": 2048, "temperature": 0.1},
        }
        response = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=300.0)
        response.raise_for_status()
        return json.loads(response.json()["response"])


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def extract(self, prompt: str) -> dict:
        response = self._client.models.generate_content(
            model=self._model, contents=prompt
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)


def get_llm_client(provider: str = "ollama", **kwargs) -> LLMClient:
    if provider == "gemini":
        api_key = kwargs.get("api_key") or os.environ["GEMINI_API_KEY"]
        model = kwargs.get("model") or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        return GeminiClient(api_key=api_key, model=model)
    model = kwargs.get("model") or os.getenv("OLLAMA_MODEL", "llama3.2")
    base_url = kwargs.get("base_url") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    return OllamaClient(model=model, base_url=base_url)
