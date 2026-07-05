"""
IntelliHall — Health Check Endpoint
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Health check")
async def health_check() -> dict:
    """Returns a simple liveness response to confirm the API is running."""
    return {"status": "ok", "service": "intellihall-api"}
