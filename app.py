"""ChainTrack -- Supply chain tracking with SHA-256 hash chain.

FastAPI application entry point. Run with:
    uvicorn app:app --host 0.0.0.0 --port 8004
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import config
from models.database import init_db, SessionLocal
from routes.api import router as api_router
from routes.views import router as views_router
from services.tracking import seed_database

# ── Application factory ──────────────────────────────────────────────────

app = FastAPI(
    title="ChainTrack",
    description=(
        "Supply chain tracking system with SHA-256 hash chain, "
        "QR code generation, and tamper detection."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Static files ─────────────────────────────────────────────────────────

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ── Routers ──────────────────────────────────────────────────────────────

app.include_router(api_router)
app.include_router(views_router)

# ── Startup ──────────────────────────────────────────────────────────────


@app.on_event("startup")
# Updated for clarity
def on_startup() -> None:
    """Initialize the database and seed sample data on first run."""
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


# ── Health check ─────────────────────────────────────────────────────────


@app.get("/health", tags=["system"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chaintrack", "version": "1.0.0"}


@app.get("/api/info", tags=["system"])
def api_info():
    """Return application metadata."""
    return {
        "name": "ChainTrack",
        "version": "1.0.0",
        "description": "Supply chain tracking with SHA-256 hash chain",
        "port": config.PORT,
        "features": [
            "SHA-256 hash chain",
            "QR code generation",
            "Tamper detection",
            "Supply chain tracking",
            "Product registry",
            "Chain integrity verification",
        ],
    }
