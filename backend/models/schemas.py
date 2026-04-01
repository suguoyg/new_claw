from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============ Auth ============

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    expires_at: str

class UserInfo(BaseModel):
    user_id: str
    username: str

# ============ Agent ============

class ModelConfig(BaseModel):
    provider: str
    model_name: str
    api_url: Optional[str] = ""
    api_key: Optional[str] = ""

class AgentCreate(BaseModel):
    name: str
    description: str = ""
    dialog_model: ModelConfig
    embedding_model: Optional[ModelConfig] = None
    enabled_tools: Optional[List[str]] = None
    enabled_skills: Optional[List[str]] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    dialog_model: Optional[ModelConfig] = None
    embedding_model: Optional[ModelConfig] = None
    enabled_tools: Optional[List[str]] = None
    enabled_skills: Optional[List[str]] = None

class AgentInfo(BaseModel):
    agent_id: str
    name: str
    description: str
    status: str
    dialog_model: Optional[Dict[str, Any]] = None
    embedding_model: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

class AgentFiles(BaseModel):
    AGENTS: str = ""
    SOUL: str = ""
    USER: str = ""
    MEMORY: str = ""
    TOOLS: str = ""
    SKILL: str = ""
    HEARTBEAT: str = ""

# ============ Skill ============

class SkillCreate(BaseModel):
    name: str
    description: str = ""
    trigger: Optional[str] = ""

class SkillUpdate(BaseModel):
    description: Optional[str] = None
    trigger: Optional[str] = None
    content: Optional[str] = None

class SkillInfo(BaseModel):
    name: str
    description: str
    trigger: str
    status: str
    content: Optional[str] = None

# ============ Memory ============

class MemoryCreate(BaseModel):
    title: str
    content: str
    type: str = "private"  # private | shared
    agent_id: Optional[str] = None

class MemoryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class MemoryInfo(BaseModel):
    memory_id: str
    title: str
    content: str
    type: str
    agent_id: Optional[str] = None
    vectorized: bool = False
    relevance_score: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class MemorySearchResult(BaseModel):
    memory_id: str
    title: str
    content: str
    relevance_score: float

# ============ Model ============

class ModelProviderConfig(BaseModel):
    provider: str
    api_url: str
    api_key: Optional[str] = ""
    model: str
    set_default: bool = False

class ModelTestRequest(BaseModel):
    provider: str
    api_url: str
    model: str
    api_key: Optional[str] = ""

class ModelTestResponse(BaseModel):
    status: str
    latency_ms: Optional[int] = None

# ============ File ============

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    type: str
    url: str

class FileContentResponse(BaseModel):
    content: str
    type: str

# ============ Session ============

class Message(BaseModel):
    id: str
    role: str  # user | assistant
    content: str
    files: Optional[List[str]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    timestamp: str

class SessionInfo(BaseModel):
    session_id: str
    title: str
    agent_id: str
    created_at: str
    updated_at: str
    messages: Optional[List[Message]] = None

class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]
    pagination: Dict[str, int]

class MessageListResponse(BaseModel):
    messages: List[Message]
    pagination: Dict[str, int]

# ============ Chat ============

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    agent_id: str
    message: str
    files: Optional[List[str]] = None
    context_mode: str = "full"

class ConfirmResponse(BaseModel):
    task_id: str
    approved: bool

# ============ Common ============

class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
