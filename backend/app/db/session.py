from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Create SQLAlchemy Engine
# pool_pre_ping=True checks connections before using them to prevent stale socket errors
engine = create_engine(
    settings.sqlalchemy_database_uri,
    pool_pre_ping=True,
    echo=False,
)

# Thread-local session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request,
    guaranteeing that the session is closed when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
