from typing import Dict, Callable, Optional, List

class ToolRegistry:
    """
    Tool Registry - manages tool registration and discovery
    """

    def __init__(self):
        self.tools: Dict[str, dict] = {}

    def register(self, name: str, description: str = "", params: dict = None,
                 func: Optional[Callable] = None):
        """Register a tool"""
        self.tools[name] = {
            "name": name,
            "description": description,
            "params": params or {},
            "func": func
        }

    def unregister(self, name: str):
        """Unregister a tool"""
        if name in self.tools:
            del self.tools[name]

    def get(self, name: str) -> Optional[dict]:
        """Get tool by name"""
        return self.tools.get(name)

    def list_all(self) -> List[dict]:
        """List all tools"""
        return [
            {
                "name": name,
                "description": tool["description"],
                "params": tool["params"]
            }
            for name, tool in self.tools.items()
        ]

    def get_by_category(self, category: str) -> List[dict]:
        """Get tools by category"""
        # Placeholder for category filtering
        return self.list_all()


# Global registry instance
registry = ToolRegistry()
