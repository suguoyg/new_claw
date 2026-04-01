from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
import uvicorn
import os

from api.routes import auth, agent, skill, tool, memory, model, file, session, chat
from utils.config import get_upload_path

# Create FastAPI app
app = FastAPI(
    title="NewClaw",
    description="Multi-Agent Architecture System",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
upload_path = get_upload_path()
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(skill.router, prefix="/api")
app.include_router(tool.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(model.router, prefix="/api")
app.include_router(file.router, prefix="/api")
app.include_router(session.router, prefix="/api")
app.include_router(chat.router)

# Serve frontend static files in production
frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

@app.get("/")
async def root():
    """Root path - redirect to frontend or API info"""
    if frontend_path.exists():
        return RedirectResponse(url="/index.html")
    return {"message": "NewClaw API", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# API info endpoint (for development mode without frontend)
@app.get("/api")
async def api_info():
    return {
        "name": "NewClaw API",
        "version": "0.1.0",
        "docs": "/docs",
        "frontend": "Build frontend to enable UI"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
