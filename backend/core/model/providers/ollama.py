import httpx
from typing import Optional, Dict, Any

class OllamaProvider:
    """Ollama model provider"""

    def __init__(self, api_url: str, model: str, api_key: str = ""):
        self.api_url = api_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    async def chat(self, messages: list, **kwargs) -> Dict[str, Any]:
        """Send chat request"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": kwargs.get("stream", False)
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}

    async def embed(self, text: str) -> Optional[list]:
        """Get embedding for text"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("embedding")
            return None

    async def list_models(self) -> list:
        """List available models"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.api_url}/api/tags")

            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            return []
