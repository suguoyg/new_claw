import chromadb
from chromadb.config import Settings
from typing import List, Optional
from pathlib import Path

from utils.config import get_vector_db_path

class VectorStore:
    """
    Vector Store - handles vector storage and similarity search
    """

    def __init__(self, collection_name: str = "memory"):
        self.collection_name = collection_name
        self.vector_db_path = get_vector_db_path()
        self.client = None
        self.collection = None
        self._connect()

    def _connect(self):
        """Connect to vector database"""
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.vector_db_path),
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Memory vector store"}
            )
        except Exception as e:
            print(f"Error connecting to vector store: {e}")
            self.client = None
            self.collection = None

    def add(self, memory_id: str, text: str, metadata: dict = None):
        """Add a memory to vector store"""
        if not self.collection:
            return False

        try:
            self.collection.add(
                ids=[memory_id],
                documents=[text],
                metadatas=[metadata or {"memory_id": memory_id}]
            )
            return True
        except Exception as e:
            print(f"Error adding to vector store: {e}")
            return False

    def search(self, query: str, top_k: int = 5, filter_metadata: dict = None) -> List[dict]:
        """Search vector store"""
        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=filter_metadata
            )

            search_results = []
            if results and results['ids'] and results['ids'][0]:
                for i, memory_id in enumerate(results['ids'][0]):
                    search_results.append({
                        "memory_id": memory_id,
                        "content": results['documents'][0][i] if results['documents'] else "",
                        "distance": results['distances'][0][i] if results['distances'] else 0.0,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                    })

            return search_results

        except Exception as e:
            print(f"Error searching vector store: {e}")
            return []

    def delete(self, memory_id: str):
        """Delete a memory from vector store"""
        if not self.collection:
            return False

        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            print(f"Error deleting from vector store: {e}")
            return False

    def update(self, memory_id: str, text: str, metadata: dict = None):
        """Update a memory in vector store"""
        # Chromadb doesn't have direct update, so delete and re-add
        self.delete(memory_id)
        return self.add(memory_id, text, metadata)


# Global vector store instance
vector_store = VectorStore()
