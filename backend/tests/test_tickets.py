import pytest
from app.core.security import get_password_hash
from app.models.user import User
from app.models.ticket import Ticket
from app.models.audit import OverrideAuditLog
from app.db.session import SessionLocal


@pytest.fixture
def auth_tokens(client):
    """
    Returns auth tokens for an agent and two distinct employees.
    """
    # 1. Agent token
    res_agent = client.post("/api/auth/login", json={"email": "agent@quickdesk.com", "password": "agent123"})
    agent_token = res_agent.json()["access_token"]

    # 2. Employee 1 (Bob)
    res_emp1 = client.post("/api/auth/login", json={"email": "employee@quickdesk.com", "password": "employee123"})
    emp1_token = res_emp1.json()["access_token"]
    emp1_id = res_emp1.json()["user"]["id"]

    # 3. Employee 2 (Charlie)
    res_emp2 = client.post("/api/auth/login", json={"email": "charlie@quickdesk.com", "password": "employee123"})
    emp2_token = res_emp2.json()["access_token"]
    emp2_id = res_emp2.json()["user"]["id"]

    return {
        "agent": agent_token,
        "emp1": emp1_token,
        "emp1_id": emp1_id,
        "emp2": emp2_token,
        "emp2_id": emp2_id,
    }


def test_employee_create_ticket(client, auth_tokens):
    """Employee creates a ticket and receives initial AI suggestions."""
    response = client.post(
        "/api/tickets",
        json={
            "title": "VPN connection failing with timeout",
            "description": "I cannot connect to the corporate VPN from home.",
            "attachment_filename": "vpn_error.png",
        },
        headers={"Authorization": f"Bearer {auth_tokens['emp1']}"},
    )
    assert response.status_code == 201
    ticket = response.json()
    assert ticket["title"] == "VPN connection failing with timeout"
    assert ticket["employee_id"] == auth_tokens["emp1_id"]
    assert ticket["status"] == "Open"
    # Verify baseline AI suggestion was stored
    assert ticket["ai_suggested_category"] == "IT"
    assert ticket["category"] == "IT"
    assert ticket["ai_suggested_priority"] in ["Low", "Medium", "High"]
    assert ticket["ai_draft_reply"] is not None
    assert ticket["final_reply"] is None


def test_employee_my_tickets_isolation(client, auth_tokens):
    """Employees only see their own tickets in /my."""
    # Employee 1 creates a ticket
    res1 = client.post(
        "/api/tickets",
        json={"title": "Bob Ticket", "description": "Need password reset"},
        headers={"Authorization": f"Bearer {auth_tokens['emp1']}"},
    )
    ticket1_id = res1.json()["id"]

    # Employee 2 creates a ticket
    res2 = client.post(
        "/api/tickets",
        json={"title": "Charlie Ticket", "description": "Need finance spreadsheet access"},
        headers={"Authorization": f"Bearer {auth_tokens['emp2']}"},
    )
    ticket2_id = res2.json()["id"]

    # Bob's tickets
    bob_tickets = client.get("/api/tickets/my", headers={"Authorization": f"Bearer {auth_tokens['emp1']}"}).json()
    bob_ids = [t["id"] for t in bob_tickets]
    assert ticket1_id in bob_ids
    assert ticket2_id not in bob_ids

    # Charlie's tickets
    charlie_tickets = client.get("/api/tickets/my", headers={"Authorization": f"Bearer {auth_tokens['emp2']}"}).json()
    charlie_ids = [t["id"] for t in charlie_tickets]
    assert ticket2_id in charlie_ids
    assert ticket1_id not in charlie_ids


def test_employee_cannot_view_other_employee_ticket(client, auth_tokens):
    """Cross-employee ticket access returns 404 to avoid ID enumeration."""
    # Bob creates a ticket
    res = client.post(
        "/api/tickets",
        json={"title": "Secret salary question", "description": "HR confidential details"},
        headers={"Authorization": f"Bearer {auth_tokens['emp1']}"},
    )
    bob_ticket_id = res.json()["id"]

    # Charlie tries to view Bob's ticket by ID -> Must receive 404
    forbidden_view = client.get(
        f"/api/tickets/{bob_ticket_id}",
        headers={"Authorization": f"Bearer {auth_tokens['emp2']}"},
    )
    assert forbidden_view.status_code == 404
    assert forbidden_view.json()["detail"] == "Ticket not found"


def test_employee_cannot_access_agent_endpoints(client, auth_tokens):
    """Employees are blocked with 403 Forbidden on agent endpoints."""
    # 1. Employee cannot list all tickets
    res_list = client.get("/api/tickets", headers={"Authorization": f"Bearer {auth_tokens['emp1']}"})
    assert res_list.status_code == 403

    # 2. Employee cannot override classification
    res_override = client.patch(
        "/api/tickets/1/classification",
        json={"category": "HR"},
        headers={"Authorization": f"Bearer {auth_tokens['emp1']}"},
    )
    assert res_override.status_code == 403

    # 3. Employee cannot reply to ticket
    res_reply = client.post(
        "/api/tickets/1/reply",
        json={"reply": "Unauthorized reply"},
        headers={"Authorization": f"Bearer {auth_tokens['emp1']}"},
    )
    assert res_reply.status_code == 403


def test_agent_list_search_and_filter(client, auth_tokens):
    """Agent can search and filter across all company tickets."""
    # Create distinct test tickets
    client.post(
        "/api/tickets",
        json={"title": "Laptop broken screen critical", "description": "Screen cracked"},
        headers={"Authorization": f"Bearer {auth_tokens['emp1']}"},
    )

    # Search by title
    res_search = client.get(
        "/api/tickets?search=screen",
        headers={"Authorization": f"Bearer {auth_tokens['agent']}"},
    )
    assert res_search.status_code == 200
    results = res_search.json()
    assert len(results) >= 1
    assert any("screen" in t["title"].lower() for t in results)


def test_agent_override_audit_lifecycle(client, auth_tokens):
    """
    Agent overrides category and priority.
    - Active category updates.
    - Original ai_suggested_category remains unchanged.
    - Exactly one audit record created per changed field.
    """
    # Create ticket
    res = client.post(
        "/api/tickets",
        json={"title": "Payroll direct deposit issue", "description": "Need to update bank details"},
        headers={"Authorization": f"Bearer {auth_tokens['emp1']}"},
    )
    ticket_id = res.json()["id"]
    orig_ai_cat = res.json()["ai_suggested_category"]

    # Agent overrides category to Finance
    override_res = client.patch(
        f"/api/tickets/{ticket_id}/classification",
        json={"category": "Finance"},
        headers={"Authorization": f"Bearer {auth_tokens['agent']}"},
    )
    assert override_res.status_code == 200
    updated_ticket = override_res.json()
    assert updated_ticket["category"] == "Finance"
    # Baseline unchanged!
    assert updated_ticket["ai_suggested_category"] == orig_ai_cat

    # Check audit log
    audit_res = client.get(
        f"/api/tickets/{ticket_id}/audit",
        headers={"Authorization": f"Bearer {auth_tokens['agent']}"},
    )
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) == 1
    assert logs[0]["field_name"] == "category"
    assert logs[0]["old_value"] == orig_ai_cat
    assert logs[0]["new_value"] == "Finance"


def test_override_with_same_value_does_not_create_audit(client, auth_tokens):
    """Submitting the same value must not pollute the audit trail."""
    res = client.post(
        "/api/tickets",
        json={"title": "Need new mouse", "description": "Hardware replacement"},
        headers={"Authorization": f"Bearer {auth_tokens['emp1']}"},
    )
    ticket_id = res.json()["id"]
    current_cat = res.json()["category"]

    # Override with identical value
    client.patch(
        f"/api/tickets/{ticket_id}/classification",
        json={"category": current_cat},
        headers={"Authorization": f"Bearer {auth_tokens['agent']}"},
    )

    audit_res = client.get(
        f"/api/tickets/{ticket_id}/audit",
        headers={"Authorization": f"Bearer {auth_tokens['agent']}"},
    )
    assert len(audit_res.json()) == 0


def test_agent_reply_and_resolve(client, auth_tokens):
    """
    Agent sends reply:
    - Status set to Resolved.
    - resolved_at is populated.
    - ai_draft_reply is preserved intact.
    - Subsequent replies are rejected with 400 Bad Request.
    """
    res = client.post(
        "/api/tickets",
        json={"title": "Cannot access git repo", "description": "Permission denied publickey"},
        headers={"Authorization": f"Bearer {auth_tokens['emp1']}"},
    )
    ticket_id = res.json()["id"]
    original_draft = res.json()["ai_draft_reply"]

    # Send final reply
    final_message = "I have added your SSH public key to the GitLab group. You should have access now."
    reply_res = client.post(
        f"/api/tickets/{ticket_id}/reply",
        json={"reply": final_message},
        headers={"Authorization": f"Bearer {auth_tokens['agent']}"},
    )
    assert reply_res.status_code == 200
    resolved = reply_res.json()
    assert resolved["status"] == "Resolved"
    assert resolved["final_reply"] == final_message
    assert resolved["ai_draft_reply"] == original_draft  # Draft preserved!
    assert resolved["resolved_at"] is not None

    # Attempting to reply again must be rejected
    duplicate_res = client.post(
        f"/api/tickets/{ticket_id}/reply",
        json={"reply": "Another reply attempt"},
        headers={"Authorization": f"Bearer {auth_tokens['agent']}"},
    )
    assert duplicate_res.status_code == 400
    assert "already resolved" in duplicate_res.json()["detail"]
