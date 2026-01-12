import os
import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")


def query_llm(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    with httpx.Client(timeout=300) as client:
        response = client.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
