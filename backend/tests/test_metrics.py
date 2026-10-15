import asyncio
import pytest
from app.services.event_broadcaster import broadcaster


def test_metrics_endpoint_authorized_agent(client):
    """Support agent can query real-time operational desk metrics."""
    agent_resp = client.post("/api/auth/login", json={"email": "agent@quickdesk.com", "password": "agent123"})
    agent_token = agent_resp.json()["access_token"]

    resp = client.get("/api/tickets/metrics", headers={"Authorization": f"Bearer {agent_token}"})
    assert resp.status_code == 200
    data = resp.json()

    assert "total_tickets" in data
    assert "open_tickets" in data
    assert "resolved_tickets" in data
    assert "ai_accuracy_percentage" in data
    assert "override_count" in data
    assert "category_distribution" in data
    assert "priority_distribution" in data
    assert "ai_method_distribution" in data
    assert isinstance(data["ai_accuracy_percentage"], (int, float))


def test_metrics_forbidden_for_employee(client):
    """Employees cannot access agent desk metrics (HTTP 403)."""
    emp_resp = client.post("/api/auth/login", json={"email": "employee@quickdesk.com", "password": "employee123"})
    emp_token = emp_resp.json()["access_token"]

    resp = client.get("/api/tickets/metrics", headers={"Authorization": f"Bearer {emp_token}"})
    assert resp.status_code == 403


def test_sse_endpoint_auth_protection(client):
    """SSE endpoint requires valid agent token (header or ?token= query param)."""
    # 1. No token -> 401
    resp = client.get("/api/tickets/events")
    assert resp.status_code == 401

    # 2. Employee token -> 403
    emp_resp = client.post("/api/auth/login", json={"email": "employee@quickdesk.com", "password": "employee123"})
    emp_token = emp_resp.json()["access_token"]
    resp = client.get(f"/api/tickets/events?token={emp_token}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_event_broadcaster_queue_pubsub():
    """EventBroadcaster distributes events to active subscriber queues."""
    sub_generator = broadcaster.subscribe()

    # 1. First yielded message should be initial connection
    init_msg = await anext(sub_generator)
    assert "event: connected" in init_msg

    # 2. Broadcast a test ticket_created event
    broadcaster.broadcast("ticket_created", {"id": 999, "title": "Real-time Test"})

    # 3. Read broadcasted event from stream
    event_msg = await anext(sub_generator)
    assert "event: ticket_created" in event_msg
    assert "Real-time Test" in event_msg

    # Clean up generator
    await sub_generator.aclose()
