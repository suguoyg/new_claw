from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import uuid
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import hashlib
import time

from models.schemas import ChatRequest, ConfirmResponse
from api.middleware.auth import decode_token
from utils.websocket import WSMessage, manager
from utils.file_cache import file_cache
from core.model.client import client
from core.tool.executor import executor

router = APIRouter(prefix="/ws", tags=["websocket"])

router = APIRouter(prefix="/ws", tags=["websocket"])

# Tool definitions for LLM
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "file_read",
            "description": "Read the content of a file from the local filesystem",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The absolute path to the file to read"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "file_write",
            "description": "Write content to a file, creating or overwriting the file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The absolute path to the file to write"},
                    "content": {"type": "string", "description": "The content to write to the file"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "command_exec",
            "description": "Execute a system command and return the output",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default: 30)"}
                },
                "required": ["command"]
            }
        }
    }
]


class ChatSession:
    """Chat session manager"""

    def __init__(self):
        self.pending_confirms: Dict[str, asyncio.Future] = {}
        # Store conversation history per session
        self.conversations: Dict[str, List[dict]] = {}

    async def process_message(self, websocket: WebSocket, message: dict, user_id: str):
        """Process incoming chat message"""
        msg_type = message.get("type")
        session_id = message.get("session_id") or str(uuid.uuid4())

        if msg_type == "chat":
            await self.handle_chat(websocket, message, session_id, user_id)

        elif msg_type == "confirm_response":
            task_id = message.get("task_id")
            if task_id in self.pending_confirms:
                self.pending_confirms[task_id].set_result(message.get("approved", False))

    async def handle_chat(self, websocket: WebSocket, message: dict,
                          session_id: str, user_id: str):
        """Handle chat message with conversation history and tool execution"""
        agent_id = message.get("agent_id")
        user_message = message.get("message", "")
        files = message.get("files", [])

        # Send acknowledgment
        await WSMessage.send_async(websocket, {
            "type": "ack",
            "session_id": session_id
        })

        # Get or create conversation history
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        # Get agent config to determine model and enabled tools
        agent_config = self._get_agent_config(agent_id)
        provider = agent_config.get("provider", "ollama")
        model = agent_config.get("model", "qwen3.5:9b")
        enabled_tools = agent_config.get("enabled_tools", [])

        # Build system prompt
        system_prompt = self._build_system_prompt(agent_config, user_message)

        # Add user message to conversation
        self.conversations[session_id].append({
            "role": "user",
            "content": user_message
        })

        # Build messages with system prompt and conversation history
        messages = [
            {"role": "system", "content": system_prompt}
        ] + self.conversations[session_id]

        # Log LLM request parameters
        print(f"[LLM Request] provider={provider}, model={model}")
        print(f"[Messages] {json.dumps(messages, ensure_ascii=False, indent=2)}")

        # Tool execution loop
        max_turns = 10
        turn = 0
        final_content = ""

        while turn < max_turns:
            turn += 1
            task_id = str(uuid.uuid4())

            # Send executing status
            await WSMessage.send_async(websocket, WSMessage.executing(
                task_id, "llm", "start"
            ))

            # Call LLM with tools if enabled
            try:
                # Filter tool definitions based on enabled tools
                tools = [t for t in TOOL_DEFINITIONS if t["function"]["name"] in enabled_tools] if enabled_tools else TOOL_DEFINITIONS

                if tools:
                    response = await client.chat(provider, model, messages, tools=tools)
                else:
                    response = await client.chat(provider, model, messages)

                print(f"[LLM Response] {json.dumps(response, ensure_ascii=False)[:500]}")

                if "error" in response:
                    await WSMessage.send_async(websocket, WSMessage.error(
                        "llm_error", response["error"]
                    ))
                    return

                # Extract response message
                llm_message = response.get("message", {})
                content = llm_message.get("content", "")
                tool_calls = llm_message.get("tool_calls", [])

                # Add LLM response to conversation
                self.conversations[session_id].append({
                    "role": "assistant",
                    "content": content
                })

                # If no tool calls, we're done
                if not tool_calls:
                    final_content = content
                    break

                # Execute tool calls
                tool_results = []
                for tool_call in tool_calls:
                    func = tool_call.get("function", {})
                    tool_name = func.get("name", "")
                    arguments = func.get("arguments", "")

                    # Parse arguments
                    try:
                        if isinstance(arguments, str):
                            arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {"raw": arguments}

                    print(f"[Tool Call] {tool_name}({arguments})")

                    # Execute tool
                    result = await executor.execute(tool_name, arguments)
                    print(f"[Tool Result] {result}")

                    # Format result for LLM
                    tool_result_content = json.dumps(result, ensure_ascii=False)
                    tool_results.append({
                        "tool_call_id": tool_call.get("id", ""),
                        "name": tool_name,
                        "content": tool_result_content
                    })

                    # Add tool result to conversation
                    self.conversations[session_id].append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", ""),
                        "name": tool_name,
                        "content": tool_result_content
                    })

                    # Send tool result to UI
                    await WSMessage.send_async(websocket, WSMessage.tool_complete(
                        task_id, tool_name, result
                    ))

            except Exception as e:
                print(f"[Error] {str(e)}")
                await WSMessage.send_async(websocket, WSMessage.error(
                    "llm_error", str(e)
                ))
                return

        # Final response
        results = [
            {
                "type": "llm",
                "name": model,
                "input": user_message,
                "output": final_content
            }
        ]

        await WSMessage.send_async(websocket, WSMessage.final(
            session_id,
            final_content,
            results
        ))

    def _get_agent_config(self, agent_id: str) -> dict:
        """Get agent model configuration and files with caching"""
        try:
            agents_file = Path("~/.new_claw/config/agents.json").expanduser()
            if agents_file.exists():
                with open(agents_file, 'r') as f:
                    agents = json.load(f)
                    if agent_id in agents:
                        agent = agents[agent_id]
                        dialog_model = agent.get("dialog_model", {})

                        # Read agent files using cache
                        agent_path = Path(f"~/.new_claw/agents/{agent_id}").expanduser()
                        files = {}
                        for filename in ["SOUL.md", "USER.md", "MEMORY.md", "TOOLS.md", "SKILL.md"]:
                            filepath = agent_path / filename
                            files[filename] = file_cache.get(filepath) or ""

                        # Read enabled skill contents with metadata
                        enabled_skills = agent.get("enabled_skills", [])
                        skill_contents = {}
                        for skill_name in enabled_skills:
                            skill_path = Path(f"~/.new_claw/skills/{skill_name}").expanduser()
                            skill_md_path = skill_path / "SKILL.md"
                            skill_config_path = skill_path / "config.json"

                            content = file_cache.get(skill_md_path) or ""

                            # Read skill config for name/description (from config.json or SKILL.md frontmatter)
                            skill_meta = {"name": skill_name, "description": "", "content": content}

                            # Try config.json first
                            if skill_config_path.exists():
                                try:
                                    with open(skill_config_path, 'r', encoding='utf-8') as f:
                                        config = json.load(f)
                                        skill_meta["name"] = config.get("name", skill_name)
                                        skill_meta["description"] = config.get("description", "")
                                except Exception:
                                    pass

                            # Parse YAML frontmatter from SKILL.md if name/description still empty
                            if not skill_meta["name"] or not skill_meta["description"]:
                                if content.startswith("---"):
                                    parts = content.split("---", 2)
                                    if len(parts) >= 2:
                                        try:
                                            import yaml
                                            frontmatter = yaml.safe_load(parts[1])
                                            if frontmatter:
                                                if not skill_meta["name"]:
                                                    skill_meta["name"] = frontmatter.get("name", skill_name)
                                                if not skill_meta["description"]:
                                                    skill_meta["description"] = frontmatter.get("description", "")
                                        except Exception:
                                            pass

                            skill_contents[skill_name] = skill_meta

                        return {
                            "provider": dialog_model.get("provider", "ollama"),
                            "model": dialog_model.get("model_name", "qwen3.5:9b"),
                            "files": files,
                            "enabled_tools": agent.get("enabled_tools", []),
                            "enabled_skills": enabled_skills,
                            "skill_contents": skill_contents
                        }
        except Exception as e:
            print(f"Error loading agent config: {e}")

        return {
            "provider": "ollama",
            "model": "qwen3.5:9b",
            "files": {},
            "enabled_tools": [],
            "enabled_skills": [],
            "skill_contents": {}
        }

    def _build_system_prompt(self, agent_config: dict, user_message: str) -> str:
        """Build system prompt from agent files and skills"""
        files = agent_config.get("files", {})

        prompt_parts = []

        # Add SOUL.md as system prompt
        soul = files.get("SOUL.md", "")
        if soul:
            prompt_parts.append("## Agent Soul\n" + soul)

        # Add USER.md for user context
        user = files.get("USER.md", "")
        if user:
            prompt_parts.append("## User Context\n" + user)

        # Add MEMORY.md for persistent memory
        memory = files.get("MEMORY.md", "")
        if memory:
            prompt_parts.append("## Agent Memory\n" + memory)

        # Add enabled tools and their full content
        enabled_tools = agent_config.get("enabled_tools", [])
        if enabled_tools:
            prompt_parts.append("## Enabled Tools")
            for tool_name in enabled_tools:
                tool_path = Path(f"~/.new_claw/tools/{tool_name}/SKILL.md").expanduser()
                tool_content = file_cache.get(tool_path)
                if tool_content:
                    prompt_parts.append(f"\n### Tool: {tool_name}\n{tool_content}")
                else:
                    prompt_parts.append(f"\n### Tool: {tool_name}\n(Use built-in tool: {tool_name})")

        # Add enabled skills with full content
        enabled_skills = agent_config.get("enabled_skills", [])
        skill_contents = agent_config.get("skill_contents", {})
        if enabled_skills:
            prompt_parts.append("## Enabled Skills")
            for skill_name in enabled_skills:
                skill_meta = skill_contents.get(skill_name, {})
                skill_name_display = skill_meta.get("name", skill_name)
                skill_desc = skill_meta.get("description", "")
                skill_content = skill_meta.get("content", "")

                # Strip YAML frontmatter from content
                if skill_content and skill_content.startswith("---"):
                    parts = skill_content.split("---", 2)
                    if len(parts) >= 3:
                        skill_content = parts[2].strip()

                prompt_parts.append(f"\n### Skill: {skill_name_display}")
                if skill_desc:
                    prompt_parts.append(f"**Description**: {skill_desc}")
                if skill_content:
                    prompt_parts.append(f"\n{skill_content}")
                else:
                    prompt_parts.append(f"\n### Skill: {skill_name_display}")
                    if skill_desc:
                        prompt_parts.append(f"**Description**: {skill_desc}")
                    prompt_parts.append(f"\n(Execute skill workflow: {skill_name})")

        # Add TOOLS.md for additional tool info
        tools = files.get("TOOLS.md", "")
        if tools:
            prompt_parts.append("## Additional Tool Info\n" + tools)

        # Add SKILL.md for additional skill rules
        skill = files.get("SKILL.md", "")
        if skill:
            prompt_parts.append("## Additional Skill Rules\n" + skill)

        return "\n\n".join(prompt_parts)

    async def wait_for_confirm(self, task_id: str, timeout: float = 30.0) -> bool:
        """Wait for user confirmation"""
        future = asyncio.Future()
        self.pending_confirms[task_id] = future

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return False
        finally:
            del self.pending_confirms[task_id]


chat_session = ChatSession()

@router.websocket("/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket chat endpoint"""
    # Verify token
    if token:
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4001)
            return
        user_id = payload.get("sub", "anonymous")
    else:
        user_id = "anonymous"

    session_id = str(uuid.uuid4())
    await manager.connect(websocket, session_id)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            await chat_session.process_message(websocket, data, user_id)

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        await WSMessage.send_async(websocket, WSMessage.error("server_error", str(e)))
        manager.disconnect(session_id)
