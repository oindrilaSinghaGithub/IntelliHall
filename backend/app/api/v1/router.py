"""
IntelliHall — Central API v1 Router

Register all endpoint routers here.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, complaints, halls, health, verification, notifications
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.schedule import router as schedule_router

api_router = APIRouter()

api_router.include_router(health.router,        prefix="/health",        tags=["health"])
api_router.include_router(auth.router,          prefix="/auth",          tags=["auth"])
api_router.include_router(complaints.router,    prefix="/complaints",    tags=["complaints"])
api_router.include_router(halls.router,         prefix="/halls",         tags=["halls"])
api_router.include_router(
    verification.router,
    prefix="/verification",
    tags=["verification"],
)
# Student self-service: PATCH /users/me/hall lives on the verification router
# but is exposed under /users prefix for semantic clarity
api_router.include_router(
    verification.router,
    prefix="/users",
    tags=["users"],
    include_in_schema=False,   # avoid duplicate docs — canonical at /verification
)

# Schedule: GET/POST /halls/{hall_id}/schedule
api_router.include_router(
    schedule_router,
    prefix="/halls/{hall_id}/schedule",
    tags=["schedule"],
)

# Analytics: GET /halls/{hall_id}/analytics
api_router.include_router(
    analytics_router,
    prefix="/halls/{hall_id}/analytics",
    tags=["analytics"],
)

# Notifications
api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["notifications"],
)
