"""Receipt upload validation and storage (PDF, JPG, JPEG, PNG, WEBP)."""
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from config import settings

CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def _matches_signature(ext: str, head: bytes) -> bool:
    if ext == ".pdf":
        return head.startswith(b"%PDF")
    if ext in (".jpg", ".jpeg"):
        return head.startswith(b"\xff\xd8\xff")
    if ext == ".png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    if ext == ".webp":
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    return False


async def save_receipt(file: UploadFile) -> dict:
    """Validate extension, size and file signature, then store under a random name."""
    name = Path(file.filename or "").name
    ext = Path(name).suffix.lower()
    if ext not in settings.ALLOWED_RECEIPT_EXT:
        raise HTTPException(400, "Receipt must be a PDF, JPG, JPEG, PNG or WEBP file")

    data = await file.read(settings.MAX_RECEIPT_BYTES + 1)
    if not data:
        raise HTTPException(400, "The uploaded file is empty")
    if len(data) > settings.MAX_RECEIPT_BYTES:
        raise HTTPException(400, f"Receipt exceeds the {settings.MAX_RECEIPT_BYTES // 1024 // 1024} MB limit")
    if not _matches_signature(ext, data[:16]):
        raise HTTPException(400, "File content does not match its extension")

    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid.uuid4().hex}{ext}"
    (settings.UPLOAD_DIR / stored).write_bytes(data)
    return {"file": stored, "name": name[:200], "type": CONTENT_TYPES[ext], "size": len(data)}


def receipt_path(stored: str) -> Path:
    path = (settings.UPLOAD_DIR / Path(stored).name).resolve()
    if settings.UPLOAD_DIR.resolve() not in path.parents or not path.exists():
        raise HTTPException(404, "Receipt file not found")
    return path
