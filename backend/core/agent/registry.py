import json
from typing import Dict, Optional, List
from pathlib import Path

class AgentRegistry:
    """
    Agent Registry - manages agent registration and discovery
    """

    def __init__(self):
        self.agents: Dict[str, dict] = {}

    def register(self, agent_id: str, agent_data: dict):
        """Register an agent"""
        self.agents[agent_id] = {
            "agent_id": agent_id,
            "name": agent_data.get("name", ""),
            "description": agent_data.get("description", ""),
            "status": "active",
            "dialog_model": agent_data.get("dialog_model", {}),
            "embedding_model": agent_data.get("embedding_model", {}),
        }

    def unregister(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]

    def get(self, agent_id: str) -> Optional[dict]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def list_all(self) -> List[dict]:
        """List all agents"""
        return list(self.agents.values())

    def update_status(self, agent_id: str, status: str):
        """Update agent status"""
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = status

    def load_from_config(self):
        """Load agents from config file"""
        from api.routes.agent import load_agents

        agents_data = load_agents()
        for agent_id, data in agents_data.items():
            self.register(agent_id, data)


# Global registry instance
registry = AgentRegistry()
