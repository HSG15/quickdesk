import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import engine, Base, SessionLocal
from app.models.user import User
from app.core.security import get_password_hash


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database tables exist before running tests."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Ensure test agent and employee exist
    if not db.query(User).filter(User.email == "test_agent@quickdesk.com").first():
        db.add(User(
            name="Test Agent",
            email="test_agent@quickdesk.com",
            password_hash=get_password_hash("password123"),
            role="agent",
        ))
    if not db.query(User).filter(User.email == "test_employee@quickdesk.com").first():
        db.add(User(
            name="Test Employee",
            email="test_employee@quickdesk.com",
            password_hash=get_password_hash("password123"),
            role="employee",
        ))
    db.commit()
    db.close()
    yield


@pytest.fixture(scope="function")
def client():
    """Provides a TestClient instance for API requests."""
    with TestClient(app) as test_client:
        yield test_client
