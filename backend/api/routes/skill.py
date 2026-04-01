from fastapi import APIRouter, HTTPException, Depends, Body
import aiofiles
import shutil
from pathlib import Path
import yaml

from models.schemas import SkillCreate, SkillUpdate, SkillInfo, ApiResponse
from api.middleware.auth import get_current_user
from utils.config import get_skill_path, load_config
from utils.file_cache import file_cache

router = APIRouter(prefix="/skills", tags=["skills"])

def parse_skill_md(content: str) -> dict:
    """Parse SKILL.md to extract metadata"""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1])
                instructions = parts[2].strip()
                return {
                    "name": metadata.get("name", ""),
                    "description": metadata.get("description", ""),
                    "trigger": metadata.get("trigger", ""),
                    "instructions": instructions
                }
            except:
                pass
    return {
        "name": "",
        "description": "",
        "trigger": "",
        "instructions": content
    }

def load_skills() -> list:
    """Load skills from skills directory"""
    config = load_config()
    skills_dir = Path(config.directories.skills).expanduser()

    if not skills_dir.exists():
        return []

    skills = []
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                with open(skill_md, 'r', encoding='utf-8') as f:
                    content = f.read()
                    parsed = parse_skill_md(content)
                    skills.append({
                        "name": skill_dir.name,
                        "description": parsed.get("description", ""),
                        "trigger": parsed.get("trigger", ""),
                        "status": "active",
                        "has_references": (skill_dir / "references").exists(),
                        "has_scripts": (skill_dir / "scripts").exists(),
                        "has_templates": (skill_dir / "templates").exists(),
                        "has_examples": (skill_dir / "examples").exists()
                    })

    return skills

def get_skill_content(skill_name: str) -> dict:
    """Get skill content and structure"""
    skill_path = get_skill_path(skill_name)
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        raise HTTPException(status_code=404, detail="Skill not found")

    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()

    parsed = parse_skill_md(content)

    # Load additional modules if they exist
    references = {}
    scripts = {}
    templates = {}
    examples = {}

    refs_dir = skill_path / "references"
    if refs_dir.exists():
        for ref_file in refs_dir.iterdir():
            if ref_file.is_file():
                references[ref_file.name] = ref_file.read_text(encoding='utf-8')

    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        for script_file in scripts_dir.iterdir():
            if script_file.is_file():
                scripts[script_file.name] = script_file.read_text(encoding='utf-8')

    templates_dir = skill_path / "templates"
    if templates_dir.exists():
        for tmpl_file in templates_dir.iterdir():
            if tmpl_file.is_file():
                templates[tmpl_file.name] = tmpl_file.read_text(encoding='utf-8')

    examples_dir = skill_path / "examples"
    if examples_dir.exists():
        for example_file in examples_dir.iterdir():
            if example_file.is_file():
                examples[example_file.name] = example_file.read_text(encoding='utf-8')

    return {
        "name": skill_name,
        "description": parsed.get("description", ""),
        "trigger": parsed.get("trigger", ""),
        "instructions": parsed.get("instructions", ""),
        "content": content,
        "references": references,
        "scripts": scripts,
        "templates": templates,
        "examples": examples
    }

async def save_skill_content(skill_name: str, content: str,
                              references: dict = None,
                              scripts: dict = None,
                              templates: dict = None,
                              examples: dict = None):
    """Save skill content and modules"""
    skill_path = get_skill_path(skill_name)
    skill_path.mkdir(parents=True, exist_ok=True)

    # Save SKILL.md
    skill_md = skill_path / "SKILL.md"
    async with aiofiles.open(skill_md, 'w', encoding='utf-8') as f:
        await f.write(content)

    # Save references
    if references:
        refs_dir = skill_path / "references"
        refs_dir.mkdir(exist_ok=True)
        for name, content in references.items():
            ref_file = refs_dir / name
            async with aiofiles.open(ref_file, 'w', encoding='utf-8') as f:
                await f.write(content)

    # Save scripts
    if scripts:
        scripts_dir = skill_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        for name, content in scripts.items():
            script_file = scripts_dir / name
            async with aiofiles.open(script_file, 'w', encoding='utf-8') as f:
                await f.write(content)

    # Save templates
    if templates:
        templates_dir = skill_path / "templates"
        templates_dir.mkdir(exist_ok=True)
        for name, content in templates.items():
            tmpl_file = templates_dir / name
            async with aiofiles.open(tmpl_file, 'w', encoding='utf-8') as f:
                await f.write(content)

    # Save examples
    if examples:
        examples_dir = skill_path / "examples"
        examples_dir.mkdir(exist_ok=True)
        for name, content in examples.items():
            example_file = examples_dir / name
            async with aiofiles.open(example_file, 'w', encoding='utf-8') as f:
                await f.write(content)

@router.get("", response_model=ApiResponse)
async def list_skills(current_user: dict = Depends(get_current_user)):
    """List all skills"""
    skills = load_skills()
    return ApiResponse(data=skills)

@router.post("", response_model=ApiResponse)
async def create_skill(req: SkillCreate, current_user: dict = Depends(get_current_user)):
    """Create a new skill"""
    skill_path = get_skill_path(req.name)

    if skill_path.exists():
        raise HTTPException(status_code=400, detail="Skill already exists")

    # Create default content
    content = f"""---
name: {req.name}
description: {req.description}
trigger: {req.trigger or ""}
---

## 执行规则

**【重要】每次只执行一个 Skill**

当用户请求需要多个 Skill 时，必须串行执行：

1. 先执行第一个 Skill，等待结果
2. 根据结果判断下一步
3. 继续执行下一个 Skill
4. 依此类推...

禁止同时执行多个 Skill，必须串行依次执行。

## 指令

[请在此处填写 Skill 的具体指令]
"""

    await save_skill_content(req.name, content)

    return ApiResponse(data={"name": req.name})

@router.get("/{skill_name}", response_model=ApiResponse)
async def get_skill(skill_name: str, current_user: dict = Depends(get_current_user)):
    """Get skill details with all modules"""
    try:
        data = get_skill_content(skill_name)
        return ApiResponse(data=data)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Skill not found")

@router.get("/{skill_name}/content", response_model=ApiResponse)
async def get_skill_content_only(skill_name: str, current_user: dict = Depends(get_current_user)):
    """Get skill SKILL.md content only"""
    skill_path = get_skill_path(skill_name)
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        raise HTTPException(status_code=404, detail="Skill not found")

    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()

    parsed = parse_skill_md(content)
    return ApiResponse(data={
        "name": skill_name,
        "content": content,
        "instructions": parsed.get("instructions", "")
    })

@router.get("/{skill_name}/references/{filename}", response_model=ApiResponse)
async def get_skill_reference(skill_name: str, filename: str,
                              current_user: dict = Depends(get_current_user)):
    """Get skill reference file"""
    skill_path = get_skill_path(skill_name)
    ref_file = skill_path / "references" / filename

    if not ref_file.exists():
        raise HTTPException(status_code=404, detail="Reference not found")

    return ApiResponse(data={
        "filename": filename,
        "content": ref_file.read_text(encoding='utf-8')
    })

@router.get("/{skill_name}/scripts/{filename}", response_model=ApiResponse)
async def get_skill_script(skill_name: str, filename: str,
                           current_user: dict = Depends(get_current_user)):
    """Get skill script file"""
    skill_path = get_skill_path(skill_name)
    script_file = skill_path / "scripts" / filename

    if not script_file.exists():
        raise HTTPException(status_code=404, detail="Script not found")

    return ApiResponse(data={
        "filename": filename,
        "content": script_file.read_text(encoding='utf-8')
    })

@router.put("/{skill_name}", response_model=ApiResponse)
async def update_skill(skill_name: str, req: SkillUpdate,
                        current_user: dict = Depends(get_current_user)):
    """Update skill"""
    skill_path = get_skill_path(skill_name)
    if not skill_path.exists():
        raise HTTPException(status_code=404, detail="Skill not found")

    # If content is provided, use it; otherwise keep existing
    if req.content is not None:
        # Get existing references, scripts, etc. if not provided
        existing = get_skill_content(skill_name)

        await save_skill_content(
            skill_name,
            req.content,
            references=existing.get("references"),
            scripts=existing.get("scripts"),
            templates=existing.get("templates"),
            examples=existing.get("examples")
        )

        # Invalidate file cache for this skill
        skill_md_path = str(get_skill_path(skill_name) / "SKILL.md")
        file_cache.invalidate(skill_md_path)

    return ApiResponse(message="Skill updated successfully")

@router.post("/{skill_name}/references", response_model=ApiResponse)
async def add_skill_reference(
    skill_name: str,
    filename: str = Body(...),
    content: str = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Add or update a reference file"""
    skill_path = get_skill_path(skill_name)
    if not skill_path.exists():
        raise HTTPException(status_code=404, detail="Skill not found")

    refs_dir = skill_path / "references"
    refs_dir.mkdir(exist_ok=True)

    ref_file = refs_dir / filename
    async with aiofiles.open(ref_file, 'w', encoding='utf-8') as f:
        await f.write(content)

    # Invalidate cache
    file_cache.invalidate_pattern(f"skills/{skill_name}")

    return ApiResponse(message="Reference added successfully")

@router.post("/{skill_name}/scripts", response_model=ApiResponse)
async def add_skill_script(
    skill_name: str,
    filename: str = Body(...),
    content: str = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Add or update a script file"""
    skill_path = get_skill_path(skill_name)
    if not skill_path.exists():
        raise HTTPException(status_code=404, detail="Skill not found")

    scripts_dir = skill_path / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    script_file = scripts_dir / filename
    async with aiofiles.open(script_file, 'w', encoding='utf-8') as f:
        await f.write(content)

    # Invalidate cache
    file_cache.invalidate_pattern(f"skills/{skill_name}")

    return ApiResponse(message="Script added successfully")

@router.delete("/{skill_name}", response_model=ApiResponse)
async def delete_skill(skill_name: str, current_user: dict = Depends(get_current_user)):
    """Delete skill"""
    skill_path = get_skill_path(skill_name)
    if not skill_path.exists():
        raise HTTPException(status_code=404, detail="Skill not found")

    shutil.rmtree(skill_path)

    return ApiResponse(message="Skill deleted successfully")
