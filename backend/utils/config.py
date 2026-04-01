import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel

class DirectoryConfig(BaseModel):
    skills: str = "~/.new_claw/skills/"
    agents: str = "~/.new_claw/agents/"
    memory: str = "~/.new_claw/memory/"
    uploads: str = "~/.new_claw/uploads/"
    tools: str = "~/.new_claw/tools/"

class ModelProvider(BaseModel):
    api_url: str
    api_key: Optional[str] = ""
    model: str
    status: str = "disconnected"

class ModelsConfig(BaseModel):
    default: str = "ollama"
    providers: Dict[str, ModelProvider] = {}

class DialogModelsConfig(BaseModel):
    default: str = "ollama"
    providers: Dict[str, ModelProvider] = {}

class EmbeddingModelsConfig(BaseModel):
    default: str = "ollama"
    providers: Dict[str, ModelProvider] = {}

class MemoryConfig(BaseModel):
    vector_db: str = "chroma"
    storage_path: str = "~/.new_claw/vector_db/"
    async_indexing: bool = True
    batch_size: int = 100

class SystemConfig(BaseModel):
    workspace: str = "~/.new_claw/"
    log_level: str = "info"

class PluginsConfig(BaseModel):
    enabled: bool = True
    path: str = "~/.new_claw/plugins/"

class Config(BaseModel):
    system: SystemConfig = SystemConfig()
    models: Dict[str, Any] = {}
    memory: MemoryConfig = MemoryConfig()
    plugins: PluginsConfig = PluginsConfig()
    directories: DirectoryConfig = DirectoryConfig()

def get_config_path() -> Path:
    """Get config file path"""
    workspace = os.path.expanduser("~/.new_claw")
    return Path(workspace) / "config.json"

def load_config() -> Config:
    """Load configuration from config.json"""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return Config(**data)
    return Config()

def save_config(config: Config):
    """Save configuration to config.json"""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)

def get_workspace_path() -> Path:
    """Get workspace root path"""
    config = load_config()
    return Path(os.path.expanduser(config.system.workspace))

def get_agent_path(agent_id: str) -> Path:
    """Get agent directory path"""
    config = load_config()
    return Path(os.path.expanduser(config.directories.agents)) / agent_id

def get_skill_path(skill_name: str) -> Path:
    """Get skill directory path"""
    config = load_config()
    return Path(os.path.expanduser(config.directories.skills)) / skill_name

def get_tool_path(tool_name: str) -> Path:
    """Get tool directory path"""
    config = load_config()
    return Path(os.path.expanduser(config.directories.tools)) / tool_name

def get_memory_path() -> Path:
    """Get memory directory path"""
    config = load_config()
    return Path(os.path.expanduser(config.directories.memory))

def get_upload_path() -> Path:
    """Get upload directory path"""
    config = load_config()
    path = Path(os.path.expanduser(config.directories.uploads))
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_vector_db_path() -> Path:
    """Get vector database path"""
    config = load_config()
    path = Path(os.path.expanduser(config.memory.storage_path))
    path.mkdir(parents=True, exist_ok=True)
    return path

# Global config instance
config = load_config()
