import pytest
from app.core.security import get_password_hash, verify_password, create_access_token


def test_password_hashing():
    raw_password = "SuperSecretPassword123!"
    hashed = get_password_hash(raw_password)
    
    assert hashed != raw_password
    assert hashed.startswith("$2b$")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_login_success_agent(client):
    response = client.post("/api/auth/login", json={
        "email": "test_agent@quickdesk.com",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test_agent@quickdesk.com"
    assert data["user"]["role"] == "agent"


def test_login_success_employee(client):
    response = client.post("/api/auth/login", json={
        "email": "test_employee@quickdesk.com",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "employee"


def test_login_invalid_password(client):
    response = client.post("/api/auth/login", json={
        "email": "test_agent@quickdesk.com",
        "password": "incorrect_password",
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    response = client.post("/api/auth/login", json={
        "email": "nobody@quickdesk.com",
        "password": "password123",
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_auth_me_authenticated(client):
    login_resp = client.post("/api/auth/login", json={
        "email": "test_agent@quickdesk.com",
        "password": "password123",
    })
    token = login_resp.json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "test_agent@quickdesk.com"
    assert response.json()["role"] == "agent"


def test_auth_me_unauthenticated(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert "missing or malformed" in response.json()["detail"]


def test_agent_endpoint_authorized(client):
    login_resp = client.post("/api/auth/login", json={
        "email": "test_agent@quickdesk.com",
        "password": "password123",
    })
    agent_token = login_resp.json()["access_token"]

    response = client.get("/api/auth/agent-only-test", headers={"Authorization": f"Bearer {agent_token}"})
    assert response.status_code == 200
    assert "RBAC check passed" in response.json()["message"]


def test_agent_endpoint_forbidden_for_employee(client):
    login_resp = client.post("/api/auth/login", json={
        "email": "test_employee@quickdesk.com",
        "password": "password123",
    })
    emp_token = login_resp.json()["access_token"]

    response = client.get("/api/auth/agent-only-test", headers={"Authorization": f"Bearer {emp_token}"})
    assert response.status_code == 403
    assert "Support Agent role required" in response.json()["detail"]


def test_tampered_token_rejected(client):
    login_resp = client.post("/api/auth/login", json={
        "email": "test_agent@quickdesk.com",
        "password": "password123",
    })
    token = login_resp.json()["access_token"]
    tampered_token = token[:-5] + "XXXXX"

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert response.status_code == 401
    assert "invalid or has expired" in response.json()["detail"]
