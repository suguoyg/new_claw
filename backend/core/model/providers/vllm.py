import httpx
from typing import Optional, Dict, Any

class VLLMProvider:
    """vLLM model provider"""

    def __init__(self, api_url: str, model: str, api_key: str = ""):
        self.api_url = api_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    async def chat(self, messages: list, **kwargs) -> Dict[str, Any]:
        """Send chat request"""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_url}/v1/chat/completions",
                headers=headers,
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
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_url}/v1/embeddings",
                headers=headers,
                json={
                    "model": self.model,
                    "input": texts
                }
            )

            if response.status_code == 200:
                result = response.json()
                return [item["embedding"] for item in result.get("data", [])]
            return None
