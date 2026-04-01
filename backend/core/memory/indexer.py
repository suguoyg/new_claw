import asyncio
from typing import Optional
from pathlib import Path

from core.memory.vectorstore import vector_store
from core.memory.manager import manager

class MemoryIndexer:
    """
    Memory Indexer - handles async vectorization of memories
    """

    def __init__(self):
        self.indexing_tasks = {}

    async def index_memory(self, memory_id: str, embedding_model: str = "nomic-embed-text"):
        """Index a memory asynchronously"""
        if memory_id in self.indexing_tasks:
            # Already indexing
            return

        task = asyncio.create_task(self._do_index(memory_id, embedding_model))
        self.indexing_tasks[memory_id] = task

    async def _do_index(self, memory_id: str, embedding_model: str):
        """Do actual indexing"""
        try:
            # Get memory content
            memory = manager.get_memory(memory_id)
            if not memory:
                return

            text = f"{memory.get('title', '')} {memory.get('content', '')}"

            # Get embedding (placeholder - would call embedding model)
            embedding = await self._get_embedding(text, embedding_model)
            if embedding:
                # Add to vector store
                vector_store.add(
                    memory_id=memory_id,
                    text=text,
                    metadata={
                        "memory_id": memory_id,
                        "type": memory.get("type", "private"),
                        "agent_id": memory.get("agent_id")
                    }
                )

        finally:
            if memory_id in self.indexing_tasks:
                del self.indexing_tasks[memory_id]

    async def _get_embedding(self, text: str, model: str) -> Optional[list]:
        """Get text embedding from model"""
        # Placeholder - would call actual embedding model
        # For now, return a dummy embedding
        return [0.0] * 768

    async def reindex_all(self, agent_id: Optional[str] = None):
        """Reindex all memories"""
        memories = manager.list_memories(agent_id=agent_id)

        for memory in memories:
            await self.index_memory(memory["memory_id"])


# Global memory indexer instance
indexer = MemoryIndexer()
