import json
import uuid
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from utils.config import get_memory_path, get_vector_db_path

class MemoryManager:
    """
    Memory Manager - manages memory storage and retrieval
    """

    def __init__(self):
        self.index_file = get_memory_path().parent / "config" / "memory_index.json"
        self.index = self._load_index()

    def _load_index(self) -> dict:
        """Load memory index"""
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"memories": {}}

    def _save_index(self):
        """Save memory index"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)

    def create_memory(self, title: str, content: str, memory_type: str,
                      agent_id: Optional[str] = None) -> str:
        """Create a new memory"""
        memory_id = str(uuid.uuid4())

        # Save to file
        memory_dir = get_memory_path()
        memory_dir.mkdir(parents=True, exist_ok=True)
        file_path = memory_dir / f"{memory_id}.md"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{content}")

        # Update index
        self.index["memories"][memory_id] = {
            "title": title,
            "content": content,
            "type": memory_type,
            "agent_id": agent_id,
            "vectorized": False,
            "created_at": datetime.now().isoformat()
        }
        self._save_index()

        return memory_id

    def get_memory(self, memory_id: str) -> Optional[dict]:
        """Get memory by ID"""
        if memory_id not in self.index.get("memories", {}):
            return None

        meta = self.index["memories"][memory_id]

        # Read content from file
        file_path = get_memory_path() / f"{memory_id}.md"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n', 1)
                meta["content"] = lines[1].strip() if len(lines) > 1 else ""
                meta["title"] = lines[0].lstrip('# ') if lines else ""

        return meta

    def update_memory(self, memory_id: str, title: str, content: str):
        """Update memory"""
        if memory_id not in self.index.get("memories", {}):
            return False

        # Update file
        file_path = get_memory_path() / f"{memory_id}.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{content}")

        # Update index
        self.index["memories"][memory_id]["title"] = title
        self.index["memories"][memory_id]["content"] = content
        self.index["memories"][memory_id]["updated_at"] = datetime.now().isoformat()
        self._save_index()

        return True

    def delete_memory(self, memory_id: str):
        """Delete memory"""
        if memory_id in self.index.get("memories", {}):
            # Delete file
            file_path = get_memory_path() / f"{memory_id}.md"
            if file_path.exists():
                file_path.unlink()

            # Remove from index
            del self.index["memories"][memory_id]
            self._save_index()

    def list_memories(self, memory_type: Optional[str] = None,
                      agent_id: Optional[str] = None) -> List[dict]:
        """List memories with optional filtering"""
        memories = []

        for memory_id, meta in self.index.get("memories", {}).items():
            if memory_type and meta.get("type") != memory_type:
                continue
            if agent_id and meta.get("agent_id") != agent_id:
                continue

            memories.append({
                "memory_id": memory_id,
                "title": meta.get("title", ""),
                "type": meta.get("type", "private"),
                "agent_id": meta.get("agent_id"),
                "created_at": meta.get("created_at", "")
            })

        return memories

    def get_memory_for_context(self, memory_ids: List[str]) -> str:
        """Get memories as context string for LLM"""
        context_parts = []

        for memory_id in memory_ids:
            memory = self.get_memory(memory_id)
            if memory:
                context_parts.append(
                    f"## {memory.get('title', '')}\n\n{memory.get('content', '')}"
                )

        return "\n\n".join(context_parts)


# Global memory manager instance
manager = MemoryManager()
