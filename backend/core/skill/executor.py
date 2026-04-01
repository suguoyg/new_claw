import asyncio
from typing import Dict, Optional
from pathlib import Path

from core.skill.manager import manager

class SkillExecutor:
    """
    Skill Executor - executes skills with skill manager integration
    """

    def __init__(self):
        self.active_skills: Dict[str, asyncio.Task] = {}

    async def execute_skill(self, skill_name: str, context: dict,
                            websocket=None, task_id: str = "") -> dict:
        """Execute a skill"""
        skill = manager.get_skill(skill_name)
        if not skill:
            return {
                "status": "error",
                "error": f"Skill not found: {skill_name}"
            }

        # Get skill prompt for LLM
        skill_prompt = manager.get_skill_prompt(skill_name)

        # Send execution start
        if websocket:
            from utils.websocket import WSMessage
            await WSMessage.send_async(websocket, {
                "type": "skill_start",
                "task_id": task_id,
                "name": skill_name
            })

        # In real implementation, this would call the LLM with skill instructions
        # For now, return success
        return {
            "status": "success",
            "skill_name": skill_name,
            "prompt": skill_prompt,
            "result": f"Skill {skill_name} executed"
        }

    async def execute_chain(self, skill_names: list, context: dict,
                             websocket=None) -> list:
        """
        Execute a chain of skills sequentially (serial execution)
        Note: Each skill executes one at a time, results feed into next
        """
        results = []
        combined_context = context.copy()

        for skill_name in skill_names:
            result = await self.execute_skill(
                skill_name,
                combined_context,
                websocket
            )
            results.append(result)

            # If skill produced output, add to context for next skill
            if result.get("status") == "success" and result.get("result"):
                combined_context[f"skill_result_{skill_name}"] = result["result"]

        return results

    def list_available_skills(self) -> list:
        """List all available skills"""
        return manager.list_skills()


# Global skill executor instance
executor = SkillExecutor()
