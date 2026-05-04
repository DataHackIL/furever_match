import json
import os
from typing import Protocol, runtime_checkable

import httpx


@runtime_checkable
class LLMClient(Protocol):
    def extract(self, prompt: str) -> dict:
        ...


class OllamaClient:
    def __init__(
        self,
        model: str = "gemma3:4b",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def extract(self, prompt: str) -> dict:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "num_predict": 2048,
                "temperature": 0.1,
            },
        }
        response = httpx.post(url, json=payload, timeout=300.0)
        response.raise_for_status()
        return json.loads(response.json()["response"])


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    def extract(self, prompt: str) -> dict:
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        m = genai.GenerativeModel(self.model)
        response = m.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            ),
        )
        return json.loads(response.text)


def get_llm_client(provider: str = "ollama", **kwargs) -> LLMClient:
    """
    Factory. Reads defaults from environment variables when kwargs are omitted.

    provider="ollama": uses OLLAMA_MODEL and OLLAMA_BASE_URL env vars
    provider="gemini": uses GEMINI_API_KEY env var
    """
    if provider == "ollama":
        return OllamaClient(
            model=kwargs.get("model", os.getenv("OLLAMA_MODEL", "gemma3:4b")),
            base_url=kwargs.get(
                "base_url",
                os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ),
        )
    if provider == "gemini":
        api_key = kwargs.get("api_key", os.getenv("GEMINI_API_KEY"))
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set for Gemini provider")
        return GeminiClient(
            api_key=api_key,
            model=kwargs.get("model", "gemini-2.0-flash"),
        )
    raise ValueError(f"Unknown LLM provider: {provider!r}. Use 'ollama' or 'gemini'.")
