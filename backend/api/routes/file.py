from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import Response
import uuid
import aiofiles

from models.schemas import FileUploadResponse, FileContentResponse, ApiResponse
from api.middleware.auth import get_current_user
from utils.config import get_upload_path
from utils.file_handler import FileHandler

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload", response_model=ApiResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a file"""
    upload_path = get_upload_path()

    # Read file content
    content = await file.read()
    file_id = await FileHandler.save_file(content, file.filename, upload_path)

    return ApiResponse(data={
        "file_id": file_id,
        "filename": file.filename,
        "size": len(content),
        "type": FileHandler.get_file_type(file.filename),
        "url": f"/api/files/{file_id}"
    })

@router.get("/{file_id}")
async def get_file(file_id: str, current_user: dict = Depends(get_current_user)):
    """Get file content"""
    upload_path = get_upload_path()
    file_path = FileHandler.get_file_path(file_id, upload_path)

    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    # Return file content
    async with aiofiles.open(file_path, 'rb') as f:
        content = await f.read()

    return Response(content=content, media_type="application/octet-stream")

@router.get("/{file_id}/content", response_model=ApiResponse)
async def get_file_content(file_id: str, current_user: dict = Depends(get_current_user)):
    """Get extracted text content from file"""
    upload_path = get_upload_path()
    file_path = FileHandler.get_file_path(file_id, upload_path)

    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    content = await FileHandler.extract_text_content(file_path)

    return ApiResponse(data={
        "content": content,
        "type": FileHandler.get_file_type(file_path.name)
    })

@router.delete("/{file_id}", response_model=ApiResponse)
async def delete_file(file_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a file"""
    upload_path = get_upload_path()
    file_path = FileHandler.get_file_path(file_id, upload_path)

    if file_path and file_path.exists():
        import os
        os.remove(file_path)

    return ApiResponse(message="File deleted successfully")
