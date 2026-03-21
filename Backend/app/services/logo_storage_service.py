"""Use: Contains the main backend rules for school logo file storage.
Where to use: Use this from routers, workers, or other services when school logo file storage logic is needed.
Role: Service layer. It keeps business logic out of the route files.
"""

from __future__ import annotations

import io
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg"}
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/pjpeg",
    "image/svg+xml",
    "application/octet-stream",
}


def _validate_svg_content(content: bytes) -> None:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid SVG encoding. UTF-8 is required.",
        ) from exc

    lowered = text.lower()
    if "<svg" not in lowered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid SVG content.",
        )

    if "<script" in lowered or "javascript:" in lowered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SVG scripts are not allowed.",
        )


def _validate_raster_content(content: bytes, extension: str) -> None:
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
            image_format = (image.format or "").upper()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file content.",
        ) from exc

    if extension == ".png" and image_format != "PNG":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PNG file content is invalid.",
        )

    if extension in {".jpg", ".jpeg"} and image_format != "JPEG":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JPEG file content is invalid.",
        )


def _safe_extension(filename: str) -> str:
    cleaned_name = filename.strip()
    extension = Path(cleaned_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported logo file type. Allowed: PNG, JPG, JPEG, SVG.",
        )
    return extension


async def store_school_logo(upload: UploadFile) -> str:
    settings = get_settings()

    filename = (upload.filename or "").strip()
    if not filename:
        raise HTTPException(status_code=400, detail="Logo file name is required.")

    extension = _safe_extension(filename)
    content_type = (upload.content_type or "").lower()
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported logo MIME type.",
        )

    content = await upload.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded logo file is empty.")

    max_size_bytes = settings.school_logo_max_file_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Logo file exceeds {settings.school_logo_max_file_size_mb} MB limit.",
        )

    if extension == ".svg":
        _validate_svg_content(content)
    else:
        _validate_raster_content(content, extension)

    storage_dir = Path(settings.school_logo_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    generated_name = f"{uuid.uuid4().hex}{extension}"
    target_path = storage_dir / generated_name
    target_path.write_bytes(content)

    public_prefix = settings.school_logo_public_prefix.rstrip("/")
    return f"{public_prefix}/{generated_name}"


def delete_managed_school_logo(logo_url: str | None) -> None:
    if not logo_url:
        return

    settings = get_settings()
    prefix = settings.school_logo_public_prefix.rstrip("/")
    if not logo_url.startswith(prefix):
        return

    parsed = urlparse(logo_url)
    candidate = Path(parsed.path).name
    if not re.fullmatch(r"[a-f0-9]{32}\.(png|jpg|jpeg|svg)", candidate):
        return

    storage_dir = Path(settings.school_logo_storage_dir).resolve()
    target_path = (storage_dir / candidate).resolve()
    if storage_dir not in target_path.parents:
        return

    if target_path.exists():
        target_path.unlink()
