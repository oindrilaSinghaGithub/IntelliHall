"""
IntelliHall — Image Service

Sits between the API router and the ImageRepository.  All business logic
for image upload and deletion — including authorization, file-type and
size validation, physical file storage, and directory management — lives
here.  The router stays thin; the repository stays pure.

Role model
----------
STUDENT (Complaint_Owner)
  - upload_images()   : own complaint only
  - delete_image()    : own complaint only

HALL_ADMIN
  - upload_images()   : any complaint in their hall
  - delete_image()    : any complaint in their hall
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.complaint import ComplaintImage
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.image_repository import ImageRepository


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS: set[str] = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5 MB
MAX_IMAGES_PER_COMPLAINT: int = 5


class ImageService:
    """Business-logic layer for complaint image management."""

    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
    MAX_FILE_SIZE = MAX_FILE_SIZE
    MAX_IMAGES_PER_COMPLAINT = MAX_IMAGES_PER_COMPLAINT

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    @staticmethod
    async def upload_images(
        session: AsyncSession,
        complaint_id: str,
        files: list[UploadFile],
        current_user: User,
    ) -> list[ComplaintImage]:
        """
        Validate authorization and file constraints, persist files to disk,
        and create database records for each uploaded image.

        Returns the list of newly created ComplaintImage records.
        """
        # 1. Fetch complaint
        complaint = await ComplaintRepository.get_by_id(session, complaint_id)
        if complaint is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint not found.",
            )

        # 2. Authorization check
        if not _is_authorized(current_user, complaint):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload images to this complaint.",
            )

        # 3. Count check
        current_count = await ImageRepository.count_for_complaint(session, complaint_id)
        if current_count + len(files) > MAX_IMAGES_PER_COMPLAINT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Maximum 5 images per complaint. "
                    f"Currently {current_count} images attached."
                ),
            )

        # 4. Process each file
        created_images: list[ComplaintImage] = []
        upload_dir = Path(settings.UPLOAD_DIR) / "complaints"

        for file in files:
            # Validate extension
            filename = file.filename or ""
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file type. Allowed: jpg, jpeg, png, webp.",
                )

            # Read content and validate size
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size exceeds 5MB limit.",
                )

            # Generate UUID filename and write to disk
            stored_filename = f"{uuid4()}.{ext}"
            file_path = upload_dir / stored_filename
            with open(file_path, "wb") as f:
                f.write(content)

            # Create DB record
            image_url = f"/uploads/complaints/{stored_filename}"
            image = await ImageRepository.create(session, complaint_id, image_url)
            created_images.append(image)

        # 5. Commit transaction
        await session.commit()

        return created_images

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    async def delete_image(
        session: AsyncSession,
        image_id: str,
        current_user: User,
    ) -> None:
        """
        Validate authorization, remove the physical file from disk, and
        delete the database record.
        """
        # 1. Fetch image (with joined complaint)
        image = await ImageRepository.get_by_id(session, image_id)
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found.",
            )

        # 2. Authorization check
        complaint = image.complaint
        if not _is_authorized(current_user, complaint):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this image.",
            )

        # 3. Remove physical file (ignore if already gone)
        file_path = Path(settings.UPLOAD_DIR).parent / image.image_url.lstrip("/")
        file_path.unlink(missing_ok=True)

        # 4. Delete DB record
        await ImageRepository.delete(session, image)

        # 5. Commit
        await session.commit()

    # ------------------------------------------------------------------
    # Directory management
    # ------------------------------------------------------------------

    @staticmethod
    def ensure_upload_dir() -> None:
        """Create the uploads/complaints/ directory if it does not exist."""
        upload_path = Path(settings.UPLOAD_DIR) / "complaints"
        upload_path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _is_authorized(user: User, complaint) -> bool:
    """
    Return True if the user is the complaint owner or the hall admin
    for the complaint's hall.
    """
    if user.id == complaint.created_by:
        return True
    if user.role == UserRole.HALL_ADMIN and user.hall_id == complaint.hall_id:
        return True
    return False
