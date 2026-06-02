import os
import shutil
from pathlib import Path
from fastapi import UploadFile

from app.core.config import settings

# Use the environment-configured storage directory
STORAGE_DIR = Path(settings.DOC_STORAGE_DIR)

def ensure_storage_dir():
    """Ensure the storage directory exists."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def save_upload_file(upload_file: UploadFile, version_id: str) -> str:
    """
    Saves the uploaded file locally. For production, this would be an S3 put_object.
    Returns the file path.
    """
    ensure_storage_dir()
    
    # Prepend version_id to ensure uniqueness in object storage simulation
    filename = f"{version_id}_{upload_file.filename}"
    file_path = STORAGE_DIR / filename
    
    # Needs to rewind file pointer just in case it was read previously
    upload_file.file.seek(0)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return str(file_path)

def delete_stored_file(file_path: str):
    """Deletes a file from storage if it exists (e.g. for rollback on failure)."""
    path = Path(file_path)
    if path.exists() and path.is_file():
        path.unlink()
