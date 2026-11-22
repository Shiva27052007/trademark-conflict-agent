"""FastAPI main application entry point."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.database.engine import init_db
from backend.api.routes import router
from backend.services.dataset_generator import seed_database


app = FastAPI(
    title="Trademark Conflict Screening Agent",
    description=(
        "AI-powered trademark screening platform that identifies potentially "
        "similar existing marks based on textual, phonetic, and goods/services "
        "similarity. Provides preliminary screening only — not legal advice."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.on_event("startup")
def startup_event():
    """Initialize database and seed data on startup."""
    init_db()
    try:
        seed_database()
    except Exception as e:
        print(f"Warning: Could not seed database: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
