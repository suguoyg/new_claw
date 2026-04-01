from fastapi import APIRouter, HTTPException, Depends, Query
import uuid
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from models.schemas import SessionInfo, SessionListResponse, MessageListResponse, Message, ApiResponse
from api.middleware.auth import get_current_user

router = APIRouter(prefix="/sessions", tags=["sessions"])

SESSIONS_DIR = Path("~/.new_claw/config/sessions")
SESSIONS_DIR_PATH = SESSIONS_DIR.expanduser()
SESSIONS_DIR_PATH.mkdir(parents=True, exist_ok=True)

def get_session_file(session_id: str) -> Path:
    """Get session file path"""
    return SESSIONS_DIR_PATH / f"{session_id}.json"

def load_sessions() -> dict:
    """Load sessions index"""
    index_file = SESSIONS_DIR_PATH / "index.json"
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"sessions": []}

def save_sessions_index(index: dict):
    """Save sessions index"""
    index_file = SESSIONS_DIR_PATH / "index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

def load_session(session_id: str) -> dict:
    """Load session data"""
    session_file = get_session_file(session_id)
    if session_file.exists():
        with open(session_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"session_id": session_id, "messages": []}

def save_session(session: dict):
    """Save session data"""
    session_file = get_session_file(session["session_id"])
    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(session, f, indent=2, ensure_ascii=False)

def paginate_list(items: list, page: int, page_size: int) -> dict:
    """Paginate a list"""
    total = len(items)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": items[start:end],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }
    }

@router.get("", response_model=ApiResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    agent_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """List sessions with pagination"""
    sessions_index = load_sessions()

    # Filter by agent_id if specified
    sessions = sessions_index.get("sessions", [])
    if agent_id:
        sessions = [s for s in sessions if s.get("agent_id") == agent_id]

    # Sort by updated_at desc
    sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

    # Paginate
    result = paginate_list(sessions, page, page_size)

    return ApiResponse(data={
        "sessions": result["items"],
        "pagination": result["pagination"]
    })

@router.get("/{session_id}", response_model=ApiResponse)
async def get_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Get session details with messages"""
    session = load_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get messages
    messages = session.get("messages", [])

    return ApiResponse(data={
        "session_id": session_id,
        "title": session.get("title", "Untitled"),
        "agent_id": session.get("agent_id", ""),
        "created_at": session.get("created_at", ""),
        "updated_at": session.get("updated_at", ""),
        "messages": messages
    })

@router.get("/{session_id}/messages", response_model=ApiResponse)
async def get_session_messages(
    session_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get session messages with pagination"""
    session = load_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = session.get("messages", [])
    result = paginate_list(messages, page, page_size)

    return ApiResponse(data={
        "messages": result["items"],
        "pagination": result["pagination"]
    })

@router.delete("/{session_id}", response_model=ApiResponse)
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a session"""
    sessions_index = load_sessions()

    # Remove from index
    sessions = [s for s in sessions_index.get("sessions", []) if s.get("session_id") != session_id]
    sessions_index["sessions"] = sessions
    save_sessions_index(sessions_index)

    # Delete session file
    session_file = get_session_file(session_id)
    if session_file.exists():
        session_file.unlink()

    return ApiResponse(message="Session deleted successfully")

@router.post("", response_model=ApiResponse)
async def create_session(
    agent_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Create a new session"""
    session_id = str(uuid.uuid4())
    now = datetime.now().isoformat() + "Z"

    session = {
        "session_id": session_id,
        "title": "New Chat",
        "agent_id": agent_id,
        "user_id": current_user.get("sub", ""),
        "created_at": now,
        "updated_at": now,
        "messages": []
    }

    # Save session
    save_session(session)

    # Add to index
    sessions_index = load_sessions()
    sessions_index["sessions"].insert(0, {
        "session_id": session_id,
        "title": "New Chat",
        "agent_id": agent_id,
        "created_at": now,
        "updated_at": now
    })
    save_sessions_index(sessions_index)

    return ApiResponse(data={"session_id": session_id})
