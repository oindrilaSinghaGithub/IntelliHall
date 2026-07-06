"""
IntelliHall — Central API v1 Router

Register all endpoint routers here.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.endpoints import complaints

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(
    complaints.router,
    prefix="/complaints",
    tags=["complaints"],
)

# ---------------------------------------------------------------------------
# Future routers — add here as modules are implemented
# ---------------------------------------------------------------------------
# from app.api.v1.endpoints import auth, users, reports
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(users.router, prefix="/users", tags=["users"])
