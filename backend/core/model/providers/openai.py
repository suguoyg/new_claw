import httpx
from typing import Optional, Dict, Any

class OpenAIProvider:
    """OpenAI model provider"""

    def __init__(self, api_url: str, model: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def chat(self, messages: list, **kwargs) -> Dict[str, Any]:
        """Send chat request"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_url}/v1/chat/completions",
                headers=self._get_headers(),
                json={
                    "model": self.model,
                    "messages": messages
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}

    async def embed(self, texts: list) -> Optional[list]:
        """Get embeddings for texts"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_url}/v1/embeddings",
                headers=self._get_headers(),
                json={
                    "model": self.model,
                    "input": texts
                }
            )

            if response.status_code == 200:
                result = response.json()
                return [item["embedding"] for item in result.get("data", [])]
            return None
