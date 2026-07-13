"""
IntelliHall — Complaint image file utilities.

Handles validation and local storage of uploaded complaint images.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CONTENT_TYPE_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

_ALLOWED_CONTENT_TYPES = frozenset(_CONTENT_TYPE_EXT.keys())


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _detect_image_type(data: bytes) -> str | None:
    """Return the MIME type inferred from magic bytes, or None if unrecognized."""
    if len(data) >= 3 and data[0:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if len(data) >= 8 and data[0:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


async def read_and_validate_image(file: UploadFile) -> tuple[bytes, str]:
    """
    Read an uploaded file and validate size, declared content-type, and magic bytes.

    Returns:
        (file_bytes, content_type)

    Raises:
        HTTPException 422 on validation failure.
    """
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Unsupported file type '{file.content_type or 'unknown'}'. "
                "Allowed types: JPEG, PNG, WebP."
            ),
        )

    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    if len(data) > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File exceeds the maximum allowed size of {max_mb} MB.",
        )

    detected = _detect_image_type(data)
    if detected is None or detected != file.content_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File content does not match a valid JPEG, PNG, or WebP image.",
        )

    return data, file.content_type


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------


def _complaint_images_dir(complaint_id: str) -> Path:
    """Return (and create) the on-disk directory for a complaint's images."""
    directory = Path(settings.UPLOAD_DIR) / "complaints" / complaint_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_complaint_image(complaint_id: str, data: bytes, content_type: str) -> str:
    """
    Write *data* to disk and return the public URL path stored in the DB.

    Example return value: ``/uploads/complaints/{id}/{uuid}.jpg``
    """
    ext = _CONTENT_TYPE_EXT[content_type]
    filename = f"{uuid.uuid4()}{ext}"
    directory = _complaint_images_dir(complaint_id)
    filepath = directory / filename
    filepath.write_bytes(data)
    return f"/uploads/complaints/{complaint_id}/{filename}"


def delete_complaint_image(image_url: str) -> None:
    """Remove a stored image file from disk. Silently ignores missing files."""
    prefix = "/uploads/"
    if not image_url.startswith(prefix):
        return
    relative = image_url[len(prefix):]
    filepath = Path(settings.UPLOAD_DIR) / relative
    if filepath.is_file():
        filepath.unlink()
