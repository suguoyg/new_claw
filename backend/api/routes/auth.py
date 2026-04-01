from fastapi import APIRouter, HTTPException, Depends
from passlib.context import CryptContext
from datetime import datetime
import uuid
import json
from pathlib import Path

from models.schemas import (
    RegisterRequest, LoginRequest, LoginResponse,
    UserInfo, ApiResponse
)
from api.middleware.auth import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User storage (simple JSON file based)
USERS_FILE = Path("~/.new_claw/config/users.json")

def get_users() -> dict:
    """Load users from file"""
    users_path = USERS_FILE.expanduser()
    users_path.parent.mkdir(parents=True, exist_ok=True)
    if users_path.exists():
        with open(users_path, 'r') as f:
            return json.load(f)
    return {}

def save_users(users: dict):
    """Save users to file"""
    users_path = USERS_FILE.expanduser()
    with open(users_path, 'w') as f:
        json.dump(users, f, indent=2)

@router.post("/register", response_model=ApiResponse)
async def register(req: RegisterRequest):
    """Register a new user"""
    users = get_users()

    if req.username in users:
        raise HTTPException(status_code=400, detail="Username already exists")

    user_id = str(uuid.uuid4())
    hashed_password = pwd_context.hash(req.password)

    users[req.username] = {
        "user_id": user_id,
        "username": req.username,
        "hashed_password": hashed_password,
        "created_at": datetime.now().isoformat()
    }

    save_users(users)

    return ApiResponse(data={"user_id": user_id})

@router.post("/login", response_model=ApiResponse)
async def login(req: LoginRequest):
    """Login user"""
    users = get_users()

    if req.username not in users:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = users[req.username]
    if not pwd_context.verify(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": user["user_id"],
        "username": user["username"]
    })

    from api.middleware.auth import ACCESS_TOKEN_EXPIRE_DAYS
    from datetime import timedelta
    expires_at = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    return ApiResponse(data={
        "token": token,
        "expires_at": expires_at.isoformat() + "Z"
    })

@router.get("/me", response_model=ApiResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return ApiResponse(data={
        "user_id": current_user["sub"],
        "username": current_user["username"]
    })
