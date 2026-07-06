"""
IntelliHall — Central API v1 Router

Register all endpoint routers here.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import complaints, health
from app.api.v1.endpoints import auth

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(
    complaints.router,
    prefix="/complaints",
    tags=["complaints"],
)
