from fastapi import APIRouter, HTTPException, Depends, Body
import aiofiles
import shutil
import json
from pathlib import Path

from models.schemas import ApiResponse
from api.middleware.auth import get_current_user
from utils.config import get_tool_path

router = APIRouter(prefix="/tools", tags=["tools"])

# Built-in tools (always available, cannot be deleted)
BUILTIN_TOOLS = {
    "file_read": {
        "name": "file_read",
        "description": "Read local file content",
        "type": "builtin",
        "status": "active"
    },
    "file_write": {
        "name": "file_write",
        "description": "Write content to file",
        "type": "builtin",
        "status": "active"
    },
    "web_search": {
        "name": "web_search",
        "description": "Search the internet",
        "type": "builtin",
        "status": "active"
    },
    "command_exec": {
        "name": "command_exec",
        "description": "Execute system command",
        "type": "builtin",
        "status": "active"
    }
}

def get_tools_dir():
    """Get tools directory path"""
    tool_path = Path("~/.new_claw/tools").expanduser()
    tool_path.mkdir(parents=True, exist_ok=True)
    return tool_path

def load_tool_config(tool_name: str) -> dict:
    """Load tool configuration"""
    tool_path = get_tool_path(tool_name)
    config_file = tool_path / "config.json"

    if not config_file.exists():
        return None

    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_tool_config(tool_name: str, config: dict):
    """Save tool configuration"""
    tool_path = get_tool_path(tool_name)
    tool_path.mkdir(parents=True, exist_ok=True)

    config_file = tool_path / "config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_tool_content(tool_name: str) -> dict:
    """Get tool content and modules"""
    if tool_name in BUILTIN_TOOLS:
        return BUILTIN_TOOLS[tool_name]

    tool_path = get_tool_path(tool_name)
    config_file = tool_path / "config.json"

    if not config_file.exists():
        return None

    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Load additional modules
    references = {}
    scripts = {}
    templates = {}

    refs_dir = tool_path / "references"
    if refs_dir.exists():
        for ref_file in refs_dir.iterdir():
            if ref_file.is_file():
                references[ref_file.name] = ref_file.read_text(encoding='utf-8')

    scripts_dir = tool_path / "scripts"
    if scripts_dir.exists():
        for script_file in scripts_dir.iterdir():
            if script_file.is_file():
                scripts[script_file.name] = script_file.read_text(encoding='utf-8')

    templates_dir = tool_path / "templates"
    if templates_dir.exists():
        for tmpl_file in templates_dir.iterdir():
            if tmpl_file.is_file():
                templates[tmpl_file.name] = tmpl_file.read_text(encoding='utf-8')

    return {
        **config,
        "references": references,
        "scripts": scripts,
        "templates": templates
    }

def list_tools() -> list:
    """List all tools including built-in"""
    # Add built-in tools
    tools = list(BUILTIN_TOOLS.values())

    # Add custom tools
    tools_dir = get_tools_dir()

    if tools_dir.exists():
        for tool_dir in tools_dir.iterdir():
            if tool_dir.is_dir():
                config = load_tool_config(tool_dir.name)
                if config:
                    tools.append({
                        "name": tool_dir.name,
                        "description": config.get("description", ""),
                        "type": config.get("type", "custom"),
                        "status": config.get("status", "active"),
                        "has_references": (tool_dir / "references").exists(),
                        "has_scripts": (tool_dir / "scripts").exists(),
                        "has_templates": (tool_dir / "templates").exists()
                    })

    return tools

async def save_tool_content(tool_name: str, config: dict,
                             references: dict = None,
                             scripts: dict = None,
                             templates: dict = None):
    """Save tool content and modules"""
    tool_path = get_tool_path(tool_name)
    tool_path.mkdir(parents=True, exist_ok=True)

    # Save config.json
    config_file = tool_path / "config.json"
    async with aiofiles.open(config_file, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(config, indent=2))

    # Save references
    if references:
        refs_dir = tool_path / "references"
        refs_dir.mkdir(exist_ok=True)
        for name, content in references.items():
            ref_file = refs_dir / name
            async with aiofiles.open(ref_file, 'w', encoding='utf-8') as f:
                await f.write(content)

    # Save scripts
    if scripts:
        scripts_dir = tool_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        for name, content in scripts.items():
            script_file = scripts_dir / name
            async with aiofiles.open(script_file, 'w', encoding='utf-8') as f:
                await f.write(content)

    # Save templates
    if templates:
        templates_dir = tool_path / "templates"
        templates_dir.mkdir(exist_ok=True)
        for name, content in templates.items():
            tmpl_file = templates_dir / name
            async with aiofiles.open(tmpl_file, 'w', encoding='utf-8') as f:
                await f.write(content)

@router.get("", response_model=ApiResponse)
async def list_tools_endpoint(current_user: dict = Depends(get_current_user)):
    """List all available tools"""
    tools = list_tools()
    return ApiResponse(data=tools)

@router.get("/builtin", response_model=ApiResponse)
async def list_builtin_tools(current_user: dict = Depends(get_current_user)):
    """List built-in tools"""
    return ApiResponse(data=list(BUILTIN_TOOLS.values()))

@router.post("", response_model=ApiResponse)
async def create_tool(
    name: str = Body(...),
    description: str = Body(""),
    tool_type: str = Body("custom"),
    current_user: dict = Depends(get_current_user)
):
    """Create a new custom tool"""
    if name in BUILTIN_TOOLS:
        raise HTTPException(status_code=400, detail="Cannot overwrite built-in tool")

    tool_path = get_tool_path(name)

    if tool_path.exists():
        raise HTTPException(status_code=400, detail="Tool already exists")

    tool_config = {
        "name": name,
        "description": description,
        "type": tool_type,
        "status": "active"
    }

    await save_tool_content(name, tool_config)

    return ApiResponse(data={"name": name})

@router.get("/{tool_name}", response_model=ApiResponse)
async def get_tool(tool_name: str, current_user: dict = Depends(get_current_user)):
    """Get tool details with all modules"""
    data = get_tool_content(tool_name)

    if not data:
        raise HTTPException(status_code=404, detail="Tool not found")

    return ApiResponse(data=data)

@router.put("/{tool_name}", response_model=ApiResponse)
async def update_tool(
    tool_name: str,
    description: str = Body(None),
    status: str = Body(None),
    current_user: dict = Depends(get_current_user)
):
    """Update tool"""
    if tool_name in BUILTIN_TOOLS:
        raise HTTPException(status_code=400, detail="Cannot modify built-in tool")

    existing = load_tool_config(tool_name)

    if not existing:
        raise HTTPException(status_code=404, detail="Tool not found")

    if description is not None:
        existing["description"] = description
    if status is not None:
        existing["status"] = status

    await save_tool_content(tool_name, existing)

    return ApiResponse(message="Tool updated successfully")

@router.post("/{tool_name}/references", response_model=ApiResponse)
async def add_tool_reference(
    tool_name: str,
    filename: str = Body(...),
    content: str = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Add or update a reference file"""
    if tool_name in BUILTIN_TOOLS:
        raise HTTPException(status_code=400, detail="Cannot modify built-in tool")

    tool_path = get_tool_path(tool_name)
    if not tool_path.exists():
        raise HTTPException(status_code=404, detail="Tool not found")

    refs_dir = tool_path / "references"
    refs_dir.mkdir(exist_ok=True)

    ref_file = refs_dir / filename
    async with aiofiles.open(ref_file, 'w', encoding='utf-8') as f:
        await f.write(content)

    return ApiResponse(message="Reference added successfully")

@router.post("/{tool_name}/scripts", response_model=ApiResponse)
async def add_tool_script(
    tool_name: str,
    filename: str = Body(...),
    content: str = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Add or update a script file"""
    if tool_name in BUILTIN_TOOLS:
        raise HTTPException(status_code=400, detail="Cannot modify built-in tool")

    tool_path = get_tool_path(tool_name)
    if not tool_path.exists():
        raise HTTPException(status_code=404, detail="Tool not found")

    scripts_dir = tool_path / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    script_file = scripts_dir / filename
    async with aiofiles.open(script_file, 'w', encoding='utf-8') as f:
        await f.write(content)

    return ApiResponse(message="Script added successfully")

@router.delete("/{tool_name}", response_model=ApiResponse)
async def delete_tool(tool_name: str, current_user: dict = Depends(get_current_user)):
    """Delete tool"""
    if tool_name in BUILTIN_TOOLS:
        raise HTTPException(status_code=400, detail="Cannot delete built-in tool")

    tool_path = get_tool_path(tool_name)

    if not tool_path.exists():
        raise HTTPException(status_code=404, detail="Tool not found")

    shutil.rmtree(tool_path)

    return ApiResponse(message="Tool deleted successfully")
