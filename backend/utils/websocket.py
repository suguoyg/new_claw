import json
from typing import Dict, Any, Optional
from fastapi import WebSocket
from datetime import datetime

class WSMessage:
    """WebSocket message helper"""

    @staticmethod
    def send(websocket: WebSocket, data: Dict[str, Any]):
        """Send JSON message"""
        import asyncio
        asyncio.get_event_loop().run_until_complete(websocket.send_json(data))

    @staticmethod
    async def send_async(websocket: WebSocket, data: Dict[str, Any]):
        """Send JSON message async"""
        await websocket.send_json(data)

    @staticmethod
    def executing(task_id: str, name: str, status: str = "start", progress: str = "", message: str = ""):
        """Create executing message"""
        return {
            "type": "executing",
            "task_id": task_id,
            "name": name,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def tool_complete(task_id: str, name: str, result: Any):
        """Create tool complete message"""
        return {
            "type": "tool_complete",
            "task_id": task_id,
            "name": name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def skill_complete(task_id: str, name: str, result: Any):
        """Create skill complete message"""
        return {
            "type": "skill_complete",
            "task_id": task_id,
            "name": name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def final(session_id: str, message: str, results: list):
        """Create final message"""
        return {
            "type": "final",
            "session_id": session_id,
            "message": message,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def confirm_request(task_id: str, tool: str, action: str, target: str, warning: str):
        """Create confirm request message"""
        return {
            "type": "confirm_request",
            "task_id": task_id,
            "tool": tool,
            "action": action,
            "target": target,
            "warning": warning,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def error(code: str, message: str):
        """Create error message"""
        return {
            "type": "error",
            "code": code,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }


class ConnectionManager:
    """WebSocket connection manager"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect a new client"""
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        """Disconnect a client"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all clients"""
        for connection in self.active_connections.values():
            await connection.send_json(message)


# Global connection manager
manager = ConnectionManager()
