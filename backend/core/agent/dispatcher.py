import asyncio
import uuid
from typing import Dict, Callable, Any, Optional
from datetime import datetime

class TaskDispatcher:
    """
    Task Dispatcher - manages task distribution and result aggregation
    """

    def __init__(self):
        self.pending_tasks: Dict[str, dict] = {}
        self.completed_tasks: Dict[str, dict] = {}

    async def submit_task(self, agent_id: str, task_type: str,
                          task_data: dict, callback: Optional[Callable] = None) -> str:
        """Submit a new task"""
        task_id = str(uuid.uuid4())

        task = {
            "task_id": task_id,
            "agent_id": agent_id,
            "type": task_type,
            "data": task_data,
            "status": "pending",
            "callback": callback,
            "created_at": datetime.now().isoformat()
        }

        self.pending_tasks[task_id] = task

        # Execute task
        asyncio.create_task(self._execute_task(task_id))

        return task_id

    async def _execute_task(self, task_id: str):
        """Execute a task"""
        if task_id not in self.pending_tasks:
            return

        task = self.pending_tasks[task_id]
        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat()

        try:
            # This would call the actual executor based on task type
            result = await self._do_execute(task)
            task["status"] = "completed"
            task["result"] = result
            task["completed_at"] = datetime.now().isoformat()

            # Call callback if provided
            if task.get("callback"):
                await task["callback"](result)

        except Exception as e:
            task["status"] = "failed"
            task["error"] = str(e)

        # Move to completed
        self.completed_tasks[task_id] = task
        del self.pending_tasks[task_id]

    async def _do_execute(self, task: dict) -> dict:
        """Do actual task execution"""
        # Placeholder - real implementation would call appropriate executor
        task_type = task.get("type")
        task_data = task.get("data", {})

        if task_type == "tool":
            return {"status": "success", "output": "Tool executed"}
        elif task_type == "skill":
            return {"status": "success", "output": "Skill executed"}
        elif task_type == "chat":
            return {"status": "success", "output": "Chat response"}
        else:
            return {"status": "unknown_task_type"}

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get task status"""
        if task_id in self.pending_tasks:
            return self.pending_tasks[task_id]
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        return None

    async def wait_for_task(self, task_id: str, timeout: float = 60.0) -> Optional[dict]:
        """Wait for task completion"""
        start = datetime.now()
        while (datetime.now() - start).total_seconds() < timeout:
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id]
            await asyncio.sleep(0.1)
        return None


# Global dispatcher instance
dispatcher = TaskDispatcher()
