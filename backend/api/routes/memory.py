from fastapi import APIRouter, HTTPException, Depends, Query
import uuid
import json
import os
from pathlib import Path
from typing import Optional

from models.schemas import (
    MemoryCreate, MemoryUpdate, MemoryInfo, MemorySearchResult, ApiResponse
)
from api.middleware.auth import get_current_user
from utils.config import get_memory_path, get_vector_db_path

router = APIRouter(prefix="/memory", tags=["memory"])

MEMORY_INDEX_FILE = Path("~/.new_claw/config/memory_index.json")
MEMORY_INDEX_PATH = MEMORY_INDEX_FILE.expanduser()

def load_memory_index() -> dict:
    """Load memory index"""
    MEMORY_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    if MEMORY_INDEX_PATH.exists():
        with open(MEMORY_INDEX_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"memories": {}}

def save_memory_index(index: dict):
    """Save memory index"""
    with open(MEMORY_INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

def get_memory_file_path(memory_id: str) -> Path:
    """Get memory file path"""
    return get_memory_path() / f"{memory_id}.md"

async def create_memory_file(memory_id: str, title: str, content: str) -> Path:
    """Create memory file"""
    memory_dir = get_memory_path()
    memory_dir.mkdir(parents=True, exist_ok=True)

    file_path = memory_dir / f"{memory_id}.md"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n{content}")

    return file_path

def read_memory_file(memory_id: str) -> dict:
    """Read memory file"""
    file_path = get_memory_file_path(memory_id)
    if not file_path.exists():
        return {"title": "", "content": ""}

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse title from first line
    lines = content.split('\n', 1)
    title = lines[0].lstrip('# ')
    body = lines[1].strip() if len(lines) > 1 else ""

    return {"title": title, "content": body}

def update_memory_file(memory_id: str, title: str, content: str):
    """Update memory file"""
    file_path = get_memory_file_path(memory_id)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n{content}")

def delete_memory_file(memory_id: str):
    """Delete memory file"""
    file_path = get_memory_file_path(memory_id)
    if file_path.exists():
        os.remove(file_path)

def search_memories_vector(query: str, agent_id: Optional[str] = None,
                            memory_type: Optional[str] = None, top_k: int = 5) -> list:
    """Search memories using vector similarity"""
    try:
        import chromadb
        from chromadb.config import Settings

        vector_db_path = get_vector_db_path()
        client = chromadb.PersistentClient(path=str(vector_db_path))

        collection_name = "memory"
        try:
            collection = client.get_collection(collection_name)
        except:
            return []

        # Get all memories from index
        index = load_memory_index()
        memories_meta = []

        for mid, meta in index.get("memories", {}).items():
            if agent_id and meta.get("agent_id") != agent_id:
                continue
            if memory_type and meta.get("type") != memory_type:
                continue
            memories_meta.append({
                "memory_id": mid,
                "text": f"{meta.get('title', '')} {meta.get('content', '')}",
                **meta
            })

        if not memories_meta:
            return []

        # Query vector store
        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, len(memories_meta))
        )

        # Map results
        search_results = []
        if results and results['ids'] and results['ids'][0]:
            for i, mem_id in enumerate(results['ids'][0]):
                for meta in memories_meta:
                    if meta['memory_id'] == mem_id:
                        search_results.append({
                            "memory_id": mem_id,
                            "title": meta.get("title", ""),
                            "content": meta.get("content", ""),
                            "relevance_score": float(results['distances'][0][i]) if results['distances'] else 0.0
                        })
                        break

        return search_results

    except Exception as e:
        print(f"Vector search error: {e}")
        return []

@router.get("", response_model=ApiResponse)
async def list_memories(
    type: Optional[str] = Query(None),  # private | shared
    agent_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """List memories"""
    index = load_memory_index()
    memories = []

    for memory_id, meta in index.get("memories", {}).items():
        if type and meta.get("type") != type:
            continue
        if agent_id and meta.get("agent_id") != agent_id:
            continue

        memories.append({
            "memory_id": memory_id,
            "title": meta.get("title", ""),
            "content": meta.get("content", ""),
            "type": meta.get("type", "private"),
            "agent_id": meta.get("agent_id"),
            "vectorized": meta.get("vectorized", False),
            "created_at": meta.get("created_at", ""),
            "updated_at": meta.get("updated_at", "")
        })

    return ApiResponse(data=memories)

@router.post("", response_model=ApiResponse)
async def create_memory(req: MemoryCreate, current_user: dict = Depends(get_current_user)):
    """Create a new memory"""
    memory_id = str(uuid.uuid4())

    # Save to file
    await create_memory_file(memory_id, req.title, req.content)

    # Update index
    index = load_memory_index()
    index["memories"][memory_id] = {
        "title": req.title,
        "content": req.content,
        "type": req.type,
        "agent_id": req.agent_id,
        "vectorized": False,
        "created_at": str(uuid.uuid4())  # Use timestamp
    }
    save_memory_index(index)

    # Async vectorization (placeholder - would integrate with model service)
    # vectorize_memory(memory_id, req.content)

    return ApiResponse(data={"memory_id": memory_id})

@router.get("/{memory_id}", response_model=ApiResponse)
async def get_memory(memory_id: str, current_user: dict = Depends(get_current_user)):
    """Get memory details"""
    index = load_memory_index()

    if memory_id not in index.get("memories", {}):
        raise HTTPException(status_code=404, detail="Memory not found")

    meta = index["memories"][memory_id]
    content = read_memory_file(memory_id)

    return ApiResponse(data={
        "memory_id": memory_id,
        "title": meta.get("title", ""),
        "content": content.get("content", ""),
        "type": meta.get("type", "private"),
        "agent_id": meta.get("agent_id"),
        "vectorized": meta.get("vectorized", False),
        "created_at": meta.get("created_at", ""),
        "updated_at": meta.get("updated_at", "")
    })

@router.put("/{memory_id}", response_model=ApiResponse)
async def update_memory(memory_id: str, req: MemoryUpdate,
                         current_user: dict = Depends(get_current_user)):
    """Update memory"""
    index = load_memory_index()

    if memory_id not in index.get("memories", {}):
        raise HTTPException(status_code=404, detail="Memory not found")

    meta = index["memories"][memory_id]

    title = req.title if req.title is not None else meta.get("title", "")
    content = req.content if req.content is not None else meta.get("content", "")

    # Update file
    update_memory_file(memory_id, title, content)

    # Update index
    meta["title"] = title
    meta["content"] = content
    index["memories"][memory_id] = meta
    save_memory_index(index)

    return ApiResponse(message="Memory updated successfully")

@router.delete("/{memory_id}", response_model=ApiResponse)
async def delete_memory(memory_id: str, current_user: dict = Depends(get_current_user)):
    """Delete memory"""
    index = load_memory_index()

    if memory_id not in index.get("memories", {}):
        raise HTTPException(status_code=404, detail="Memory not found")

    # Delete file
    delete_memory_file(memory_id)

    # Update index
    del index["memories"][memory_id]
    save_memory_index(index)

    # Remove from vector store
    try:
        import chromadb
        vector_db_path = get_vector_db_path()
        client = chromadb.PersistentClient(path=str(vector_db_path))
        collection = client.get_collection("memory")
        collection.delete(ids=[memory_id])
    except:
        pass

    return ApiResponse(message="Memory deleted successfully")

@router.get("/search", response_model=ApiResponse)
async def search_memories(
    q: str = Query(..., description="Search query"),
    agent_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    top_k: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_current_user)
):
    """Search memories"""
    results = search_memories_vector(q, agent_id, type, top_k)
    return ApiResponse(data=results)
