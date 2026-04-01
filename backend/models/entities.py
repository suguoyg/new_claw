from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class User:
    user_id: str
    username: str
    hashed_password: str
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Agent:
    agent_id: str
    name: str
    description: str
    status: str = "active"
    dialog_model: Optional[Dict[str, Any]] = None
    embedding_model: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class Skill:
    name: str
    description: str
    trigger: str = ""
    status: str = "active"
    content: str = ""
    directory: str = ""

@dataclass
class Memory:
    memory_id: str
    title: str
    content: str
    type: str  # private | shared
    agent_id: Optional[str] = None
    vectorized: bool = False
    vector_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class Session:
    session_id: str
    title: str
    agent_id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ChatMessage:
    id: str
    session_id: str
    role: str  # user | assistant
    content: str
    files: List[str] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
