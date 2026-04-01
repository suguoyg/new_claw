import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path

from utils.config import get_agent_path, load_config

class AgentSupervisor:
    """
    Agent Supervisor - manages all agents, coordinates task dispatching
    """

    def __init__(self):
        self.agents: Dict[str, dict] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

    def load_agent_config(self, agent_id: str) -> dict:
        """Load agent configuration"""
        agent_path = get_agent_path(agent_id)

        config = {
            "AGENTS.md": "",
            "SOUL.md": "",
            "USER.md": "",
            "MEMORY.md": "",
            "TOOLS.md": "",
            "SKILL.md": "",
            "HEARTBEAT.md": ""
        }

        for filename in config.keys():
            file_path = agent_path / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    config[filename] = f.read()

        return config

    def get_agent_prompt_parts(self, agent_id: str) -> List[str]:
        """Get prompt parts in correct order for LLM"""
        config = self.load_agent_config(agent_id)

        # Order defined in architecture
        order = ["SOUL.md", "AGENTS.md", "USER.md", "MEMORY.md", "TOOLS.md", "SKILL.md", "HEARTBEAT.md"]

        parts = []
        for filename in order:
            if config.get(filename):
                parts.append(config[filename])

        return parts

    def assemble_prompt(self, agent_id: str, context: dict) -> str:
        """Assemble complete prompt from parts and context"""
        parts = self.get_agent_prompt_parts(agent_id)

        # Add context parts
        if context.get("memory_context"):
            parts.append(context["memory_context"])
        if context.get("history_context"):
            parts.append(context["history_context"])
        if context.get("file_context"):
            parts.append(context["file_context"])
        if context.get("current_message"):
            parts.append(f"## Current Message\n\n{context['current_message']}")

        return "\n\n".join(parts)

    async def dispatch_task(self, agent_id: str, task: dict, websocket) -> dict:
        """Dispatch task to agent"""
        task_id = task.get("task_id", str(id(task)))

        # Load agent config
        agent_config = self.load_agent_config(agent_id)

        # Prepare context
        context = {
            "current_message": task.get("message", ""),
            "memory_context": task.get("memory_context", ""),
            "history_context": task.get("history_context", ""),
            "file_context": task.get("file_context", "")
        }

        # Assemble prompt
        prompt = self.assemble_prompt(agent_id, context)

        # This would be where we call the AI model
        # For now, return a placeholder
        return {
            "task_id": task_id,
            "agent_id": agent_id,
            "prompt": prompt,
            "status": "ready"
        }

    def list_agents(self) -> List[dict]:
        """List all registered agents"""
        from api.routes.agent import load_agents

        agents_data = load_agents()
        return [
            {
                "agent_id": agent_id,
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "status": data.get("status", "active")
            }
            for agent_id, data in agents_data.items()
        ]


# Global supervisor instance
supervisor = AgentSupervisor()
