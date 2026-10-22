import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

# Prevent HuggingFace / Tokenizers Rayon threadpool deadlocks and network latency
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from app.core.config import settings
from app.db.session import engine, get_db
from app.models import Base  # Ensures all models are registered
from app.api import auth, tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Pre-warms local AI models and ChromaDB on server startup.
    Eliminates cold-start latency (10s -> 0.1s) and prevents sub-thread Tokio/Rayon deadlocks.
    """
    from app.services.rag_service import get_embeddings, get_vector_store
    from app.services.event_broadcaster import broadcaster
    try:
        await asyncio.to_thread(get_embeddings)
        await asyncio.to_thread(get_vector_store)
    except Exception as e:
        print(f"[STARTUP] Model pre-warming notice: {e}")
    yield
    # Clean shutdown of SSE streams to prevent reload hangs
    broadcaster.shutdown()


# Automatically create tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="QuickDesk API",
    description="Internal AI-Assisted Helpdesk API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware for React frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(tickets.router)


@app.get("/", tags=["System"])
def root():
    """Root status and documentation link."""
    return {
        "app": "QuickDesk API",
        "status": "healthy",
        "documentation": "/docs",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["System"])
def health_check():
    """Simple health check endpoint."""
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health/db", tags=["System"])
def health_db_check(db: Session = Depends(get_db)):
    """Verifies live PostgreSQL database connectivity."""
    try:
        result = db.execute(text("SELECT current_database(), current_user;")).fetchone()
        return {
            "database": "connected",
            "database_name": result[0],
            "user": result[1],
            "status": "ok",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}",
        )