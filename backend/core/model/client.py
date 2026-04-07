import httpx
import json
from typing import Optional, Dict, Any
from pathlib import Path

class ModelClient:
    """
    Model Client - unified interface for different model providers
    """

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load model configuration"""
        config_file = Path("~/.new_claw/config/models.json")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    async def chat(self, provider: str, model: str, messages: list,
                   **kwargs) -> Dict[str, Any]:
        """Send chat request to model"""
        if provider == "ollama":
            return await self._chat_ollama(model, messages, **kwargs)
        elif provider == "openai":
            return await self._chat_openai(model, messages, **kwargs)
        elif provider == "vllm":
            return await self._chat_vllm(model, messages, **kwargs)
        else:
            return {"error": f"Unsupported provider: {provider}"}

    async def _chat_ollama(self, model: str, messages: list, **kwargs) -> Dict[str, Any]:
        """Chat with Ollama"""
        config = self.config.get("dialog", {}).get("providers", {}).get("ollama", {})
        api_url = config.get("api_url", "http://localhost:11434")

        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }

        # Add tools if provided (for function calling)
        if "tools" in kwargs:
            payload["tools"] = kwargs["tools"]

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{api_url}/api/chat",
                    json=payload
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return {"error": str(e)}

    async def _chat_openai(self, model: str, messages: list, **kwargs) -> Dict[str, Any]:
        """Chat with OpenAI"""
        config = self.config.get("dialog", {}).get("providers", {}).get("openai", {})
        api_url = config.get("api_url", "https://api.openai.com")
        api_key = config.get("api_key", "")

        payload = {
            "model": model,
            "messages": messages
        }

        # Add tools if provided (OpenAI function calling format)
        if "tools" in kwargs:
            payload["tools"] = kwargs["tools"]

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{api_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return {"error": str(e)}

    async def _chat_vllm(self, model: str, messages: list, **kwargs) -> Dict[str, Any]:
        """Chat with vLLM"""
        config = self.config.get("dialog", {}).get("providers", {}).get("vllm", {})
        api_url = config.get("api_url", "http://localhost:8000")

        payload = {
            "model": model,
            "messages": messages
        }

        # Add tools if provided (vLLM supports OpenAI function calling format)
        if "tools" in kwargs:
            payload["tools"] = kwargs["tools"]

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{api_url}/v1/chat/completions",
                    json=payload
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return {"error": str(e)}

    async def embed(self, provider: str, model: str, texts: list) -> Optional[list]:
        """Get embeddings from model"""
        if provider == "ollama":
            return await self._embed_ollama(model, texts)
        elif provider == "openai":
            return await self._embed_openai(model, texts)
        else:
            return None

    async def _embed_ollama(self, model: str, texts: list) -> Optional[list]:
        """Get embeddings from Ollama"""
        config = self.config.get("embedding", {}).get("providers", {}).get("ollama", {})
        api_url = config.get("api_url", "http://localhost:11434")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{api_url}/api/embeddings",
                    json={
                        "model": model,
                        "prompt": texts[0] if texts else ""
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    return [result.get("embedding", [])]
                else:
                    return None

        except Exception as e:
            print(f"Embedding error: {e}")
            return None

    async def _embed_openai(self, model: str, texts: list) -> Optional[list]:
        """Get embeddings from OpenAI"""
        config = self.config.get("embedding", {}).get("providers", {}).get("openai", {})
        api_url = config.get("api_url", "https://api.openai.com")
        api_key = config.get("api_key", "")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{api_url}/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "input": texts
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    return [item["embedding"] for item in result.get("data", [])]
                else:
                    return None

        except Exception as e:
            print(f"Embedding error: {e}")
            return None


# Global model client instance
client = ModelClient()
