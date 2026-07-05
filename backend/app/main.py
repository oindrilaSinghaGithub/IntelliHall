"""
IntelliHall — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from fastapi.staticfiles import StaticFiles  # Uncomment to serve uploads

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
configure_logging()

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="IntelliHall API",
    description="Backend API for the IntelliHall complaint management system.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static files — uncomment when ready to serve uploaded complaint images
# ---------------------------------------------------------------------------
# app.mount(
#     "/uploads",
#     StaticFiles(directory=settings.UPLOAD_DIR),
#     name="uploads",
# )

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["root"])
async def root() -> dict:
    return {"message": "IntelliHall API is running."}
