from fastapi import APIRouter, HTTPException, Depends
import httpx
import json
from pathlib import Path

from models.schemas import (
    ModelProviderConfig, ModelTestRequest, ModelTestResponse, ApiResponse
)
from api.middleware.auth import get_current_user
from utils.config import load_config, save_config

router = APIRouter(prefix="/models", tags=["models"])

CONFIG_FILE = Path("~/.new_claw/config/models.json")
CONFIG_FILE_PATH = CONFIG_FILE.expanduser()

def load_models_config() -> dict:
    """Load models configuration"""
    CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE_PATH.exists():
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "dialog": {
            "default": "ollama",
            "providers": {}
        },
        "embedding": {
            "default": "ollama",
            "providers": {}
        }
    }

def save_models_config(config: dict):
    """Save models configuration"""
    with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def test_provider_connection(provider: str, api_url: str, model: str,
                              api_key: str = "") -> dict:
    """Test provider connection"""
    import time
    start = time.time()

    try:
        if provider == "ollama":
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_url}/api/tags")
                if response.status_code == 200:
                    return {"status": "connected", "latency_ms": int((time.time() - start) * 1000)}
                return {"status": "error", "error": f"Status {response.status_code}"}

        elif provider == "openai":
            headers = {"Authorization": f"Bearer {api_key}"}
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{api_url}/v1/models",
                    headers=headers
                )
                if response.status_code == 200:
                    return {"status": "connected", "latency_ms": int((time.time() - start) * 1000)}
                return {"status": "error", "error": f"Status {response.status_code}"}

        elif provider == "vllm":
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_url}/v1/models")
                if response.status_code == 200:
                    return {"status": "connected", "latency_ms": int((time.time() - start) * 1000)}
                return {"status": "error", "error": f"Status {response.status_code}"}

        else:
            return {"status": "unsupported", "error": f"Provider {provider} not supported"}

    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("", response_model=ApiResponse)
async def get_models(current_user: dict = Depends(get_current_user)):
    """Get all model configurations"""
    config = load_models_config()

    # Test connection for each provider
    for model_type in ["dialog", "embedding"]:
        for provider, provider_config in config.get(model_type, {}).get("providers", {}).items():
            result = test_provider_connection(
                provider,
                provider_config.get("api_url", ""),
                provider_config.get("model", ""),
                provider_config.get("api_key", "")
            )
            provider_config["status"] = result.get("status", "unknown")

    return ApiResponse(data=config)

@router.post("/dialog", response_model=ApiResponse)
async def add_dialog_model(req: ModelProviderConfig,
                             current_user: dict = Depends(get_current_user)):
    """Add dialog model configuration"""
    config = load_models_config()

    if "dialog" not in config:
        config["dialog"] = {"default": req.provider, "providers": {}}

    config["dialog"]["providers"][req.provider] = {
        "api_url": req.api_url,
        "api_key": req.api_key or "",
        "model": req.model
    }

    if req.set_default:
        config["dialog"]["default"] = req.provider

    save_models_config(config)

    return ApiResponse(data={
        "provider": req.provider,
        "model": req.model
    })

@router.post("/embedding", response_model=ApiResponse)
async def add_embedding_model(req: ModelProviderConfig,
                               current_user: dict = Depends(get_current_user)):
    """Add embedding model configuration"""
    config = load_models_config()

    if "embedding" not in config:
        config["embedding"] = {"default": req.provider, "providers": {}}

    config["embedding"]["providers"][req.provider] = {
        "api_url": req.api_url,
        "api_key": req.api_key or "",
        "model": req.model
    }

    if req.set_default:
        config["embedding"]["default"] = req.provider

    save_models_config(config)

    return ApiResponse(data={
        "provider": req.provider,
        "model": req.model
    })

@router.delete("/dialog/{provider}", response_model=ApiResponse)
async def delete_dialog_model(provider: str, current_user: dict = Depends(get_current_user)):
    """Delete dialog model configuration"""
    config = load_models_config()

    if "dialog" in config and provider in config["dialog"].get("providers", {}):
        del config["dialog"]["providers"][provider]
        save_models_config(config)
        return ApiResponse(message="Model deleted successfully")

    raise HTTPException(status_code=404, detail="Model not found")

@router.delete("/embedding/{provider}", response_model=ApiResponse)
async def delete_embedding_model(provider: str, current_user: dict = Depends(get_current_user)):
    """Delete embedding model configuration"""
    config = load_models_config()

    if "embedding" in config and provider in config["embedding"].get("providers", {}):
        del config["embedding"]["providers"][provider]
        save_models_config(config)
        return ApiResponse(message="Model deleted successfully")

    raise HTTPException(status_code=404, detail="Model not found")

@router.post("/test", response_model=ApiResponse)
async def test_model(req: ModelTestRequest, current_user: dict = Depends(get_current_user)):
    """Test model connection"""
    result = test_provider_connection(req.provider, req.api_url, req.model, req.api_key or "")
    return ApiResponse(data=result)
