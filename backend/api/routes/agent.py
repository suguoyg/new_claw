from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Optional, List
import uuid
import json
import os
import aiofiles
from pathlib import Path

from models.schemas import (
    AgentCreate, AgentUpdate, AgentInfo, AgentFiles, ApiResponse
)
from api.middleware.auth import get_current_user
from utils.config import load_config, get_agent_path
from utils.file_cache import file_cache

router = APIRouter(prefix="/agents", tags=["agents"])

AGENTS_FILE = Path("~/.new_claw/config/agents.json")
AGENTS_FILE_PATH = AGENTS_FILE.expanduser()
AGENTS_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Default agent files template
DEFAULT_FILES = {
    "AGENTS.md": """# Agent Configuration

## Basic Info
- Name: {name}
- Description: {description}

## Model Configuration
- Dialog Model: {dialog_model}
- Embedding Model: {embedding_model}
""",
    "SOUL.md": """# Agent Soul

## Role Definition
You are a helpful AI assistant.

## Personality
- Friendly and professional
- Clear and concise responses
- Helpful and knowledgeable

## Behavior Constraints
- Always prioritize user privacy
- Follow ethical guidelines
- Provide accurate information
""",
    "USER.md": """# User Information

## Current User
- Username: [To be filled]
- Preferences: [To be filled]
- History: [To be filled]
""",
    "MEMORY.md": """# Memory Configuration

## Memory Rules
[User defined memory configuration]

## Important Notes
- Remember user preferences
- Track conversation context
""",
    "HEARTBEAT.md": ""
}

# Built-in tools (always available)
BUILTIN_TOOLS = ["file_read", "file_write", "web_search", "command_exec"]

def get_available_tools() -> set:
    """Get set of all available tool names"""
    from api.routes.tool import BUILTIN_TOOLS, list_tools as list_all_tools
    # Built-in tools
    available = set(BUILTIN_TOOLS.keys())
    # Custom tools
    for tool in list_all_tools():
        available.add(tool["name"])
    return available

def get_available_skills() -> set:
    """Get set of all available skill names"""
    from api.routes.skill import load_skills
    skills = load_skills()
    return {s["name"] for s in skills}

def validate_and_fix_agent(agent_id: str, agent_data: dict) -> tuple[dict, list, list]:
    """
    Validate and fix agent's enabled_skills and enabled_tools.
    Returns (fixed_agent_data, removed_skills, removed_tools)
    """
    available_tools = get_available_tools()
    available_skills = get_available_skills()

    removed_skills = []
    removed_tools = []

    # Validate enabled_tools
    if "enabled_tools" in agent_data:
        valid_tools = [t for t in agent_data["enabled_tools"] if t in available_tools]
        removed_tools = [t for t in agent_data["enabled_tools"] if t not in available_tools]
        agent_data["enabled_tools"] = valid_tools

    # Validate enabled_skills
    if "enabled_skills" in agent_data:
        valid_skills = [s for s in agent_data["enabled_skills"] if s in available_skills]
        removed_skills = [s for s in agent_data["enabled_skills"] if s not in available_skills]
        agent_data["enabled_skills"] = valid_skills

    return agent_data, removed_skills, removed_tools

def load_agents() -> dict:
    """Load agents from file and validate skills/tools"""
    if not AGENTS_FILE_PATH.exists():
        return {}

    with open(AGENTS_FILE_PATH, 'r', encoding='utf-8') as f:
        agents = json.load(f)

    # Validate and fix each agent's config
    needs_save = False
    for agent_id, agent_data in agents.items():
        fixed_data, removed_skills, removed_tools = validate_and_fix_agent(agent_id, agent_data.copy())
        if removed_skills or removed_tools:
            agents[agent_id] = fixed_data
            needs_save = True
            print(f"[Agent Config] {agent_id}: removed invalid skills={removed_skills}, tools={removed_tools}")

    # Save back if any invalid configs were removed
    if needs_save:
        save_agents(agents)

    return agents

def save_agents(agents: dict):
    """Save agents to file"""
    with open(AGENTS_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(agents, f, indent=2, ensure_ascii=False)

async def create_agent_files(agent_id: str, name: str, description: str,
                              dialog_model: dict, embedding_model: dict):
    """Create agent configuration files"""
    agent_path = get_agent_path(agent_id)
    agent_path.mkdir(parents=True, exist_ok=True)

    dialog_model_str = f"{dialog_model.get('provider', 'ollama')}/{dialog_model.get('model_name', 'llama2')}"
    embedding_model_str = f"{embedding_model.get('provider', 'ollama')}/{embedding_model.get('model_name', 'nomic-embed-text')}" if embedding_model else "Not configured"

    for filename, content_template in DEFAULT_FILES.items():
        content = content_template.format(
            name=name,
            description=description,
            dialog_model=dialog_model_str,
            embedding_model=embedding_model_str
        )
        file_path = agent_path / filename
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(content)

def read_agent_file(agent_id: str, filename: str) -> str:
    """Read agent configuration file"""
    agent_path = get_agent_path(agent_id)
    file_path = agent_path / filename
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

async def update_agent_file(agent_id: str, filename: str, content: str):
    """Update agent configuration file"""
    agent_path = get_agent_path(agent_id)
    file_path = agent_path / filename
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
        await f.write(content)

@router.get("", response_model=ApiResponse)
async def list_agents(current_user: dict = Depends(get_current_user)):
    """List all agents"""
    agents = load_agents()
    agent_list = []
    for agent_id, data in agents.items():
        agent_list.append({
            "agent_id": agent_id,
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "status": data.get("status", "active"),
            "enabled_tools": data.get("enabled_tools", []),
            "enabled_skills": data.get("enabled_skills", []),
            "created_at": data.get("created_at", "")
        })
    return ApiResponse(data=agent_list)

@router.post("", response_model=ApiResponse)
async def create_agent(req: AgentCreate, current_user: dict = Depends(get_current_user)):
    """Create a new agent"""
    agents = load_agents()

    agent_id = str(uuid.uuid4())

    # Ensure unique name
    name = req.name
    counter = 1
    while any(a.get("name") == name for a in agents.values()):
        name = f"{req.name}_{counter}"
        counter += 1

    # Default: enable all built-in tools, no skills
    enabled_tools = req.enabled_tools if req.enabled_tools else BUILTIN_TOOLS.copy()
    enabled_skills = req.enabled_skills if req.enabled_skills else []

    agents[agent_id] = {
        "name": name,
        "description": req.description,
        "status": "active",
        "dialog_model": req.dialog_model.model_dump() if req.dialog_model else {},
        "embedding_model": req.embedding_model.model_dump() if req.embedding_model else {},
        "enabled_tools": enabled_tools,
        "enabled_skills": enabled_skills,
        "created_at": str(uuid.uuid4())
    }

    save_agents(agents)

    # Create agent files
    await create_agent_files(
        agent_id, name, req.description,
        req.dialog_model.model_dump() if req.dialog_model else {},
        req.embedding_model.model_dump() if req.embedding_model else {}
    )

    return ApiResponse(data={"agent_id": agent_id})

@router.get("/{agent_id}", response_model=ApiResponse)
async def get_agent(agent_id: str, current_user: dict = Depends(get_current_user)):
    """Get agent details"""
    agents = load_agents()
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    data = agents[agent_id]

    # Read agent files
    files = {
        "AGENTS.md": read_agent_file(agent_id, "AGENTS.md"),
        "SOUL.md": read_agent_file(agent_id, "SOUL.md"),
        "USER.md": read_agent_file(agent_id, "USER.md"),
        "MEMORY.md": read_agent_file(agent_id, "MEMORY.md"),
        "HEARTBEAT.md": read_agent_file(agent_id, "HEARTBEAT.md"),
    }

    return ApiResponse(data={
        "agent_id": agent_id,
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "status": data.get("status", "active"),
        "dialog_model": data.get("dialog_model"),
        "embedding_model": data.get("embedding_model"),
        "enabled_tools": data.get("enabled_tools", []),
        "enabled_skills": data.get("enabled_skills", []),
        "files": files
    })

@router.put("/{agent_id}", response_model=ApiResponse)
async def update_agent(agent_id: str, req: AgentUpdate,
                        current_user: dict = Depends(get_current_user)):
    """Update agent"""
    agents = load_agents()
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    if req.name is not None:
        agents[agent_id]["name"] = req.name
    if req.description is not None:
        agents[agent_id]["description"] = req.description
    if req.status is not None:
        agents[agent_id]["status"] = req.status
    if req.dialog_model is not None:
        agents[agent_id]["dialog_model"] = req.dialog_model.model_dump()
    if req.embedding_model is not None:
        agents[agent_id]["embedding_model"] = req.embedding_model.model_dump()
    if req.enabled_tools is not None:
        agents[agent_id]["enabled_tools"] = req.enabled_tools
    if req.enabled_skills is not None:
        agents[agent_id]["enabled_skills"] = req.enabled_skills

    save_agents(agents)

    return ApiResponse(data={"agent_id": agent_id})

@router.delete("/{agent_id}", response_model=ApiResponse)
async def delete_agent(agent_id: str, current_user: dict = Depends(get_current_user)):
    """Delete agent"""
    agents = load_agents()
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    del agents[agent_id]
    save_agents(agents)

    # Delete agent files
    agent_path = get_agent_path(agent_id)
    import shutil
    if agent_path.exists():
        shutil.rmtree(agent_path)

    return ApiResponse(message="Agent deleted successfully")

@router.get("/{agent_id}/file/{filename}")
async def get_agent_file(agent_id: str, filename: str,
                          current_user: dict = Depends(get_current_user)):
    """Get agent file content"""
    content = read_agent_file(agent_id, filename)
    return {"code": 0, "message": "success", "data": content}

@router.put("/{agent_id}/file/{filename}")
async def update_agent_file_endpoint(agent_id: str, filename: str,
                             content: str = Body(..., media_type="text/plain"),
                             current_user: dict = Depends(get_current_user)):
    """Update agent file content"""
    allowed_files = ["AGENTS.md", "SOUL.md", "USER.md", "MEMORY.md", "HEARTBEAT.md"]
    if filename not in allowed_files:
        raise HTTPException(status_code=400, detail="Invalid filename")

    await update_agent_file(agent_id, filename, content)
    return ApiResponse(message="File updated successfully")

@router.get("/{agent_id}/tools", response_model=ApiResponse)
async def get_agent_tools(agent_id: str, current_user: dict = Depends(get_current_user)):
    """Get enabled tools for agent"""
    agents = load_agents()
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    data = agents[agent_id]
    enabled_tools = data.get("enabled_tools", [])

    return ApiResponse(data={
        "builtin": BUILTIN_TOOLS,
        "enabled": enabled_tools,
        "all": BUILTIN_TOOLS  # For now, all built-in tools are available
    })

@router.put("/{agent_id}/tools", response_model=ApiResponse)
async def update_agent_tools(
    agent_id: str,
    enabled_tools: List[str] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Update enabled tools for agent"""
    agents = load_agents()
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    agents[agent_id]["enabled_tools"] = enabled_tools
    save_agents(agents)

    return ApiResponse(message="Tools updated successfully")

@router.get("/{agent_id}/skills", response_model=ApiResponse)
async def get_agent_skills(agent_id: str, current_user: dict = Depends(get_current_user)):
    """Get enabled skills for agent"""
    agents = load_agents()
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    data = agents[agent_id]
    enabled_skills = data.get("enabled_skills", [])

    # Import here to avoid circular dependency
    from api.routes.skill import list_tools as list_skill_tools

    return ApiResponse(data={
        "enabled": enabled_skills
    })

@router.put("/{agent_id}/skills", response_model=ApiResponse)
async def update_agent_skills(
    agent_id: str,
    enabled_skills: List[str] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Update enabled skills for agent"""
    agents = load_agents()
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    agents[agent_id]["enabled_skills"] = enabled_skills
    save_agents(agents)

    # Invalidate agent config cache
    file_cache.invalidate_pattern(f"agents/{agent_id}")

    return ApiResponse(message="Skills updated successfully")
