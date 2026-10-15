import json
from unittest.mock import patch
from langchain_core.messages import AIMessage
from app.services.rag_service import (
    index_knowledge_base,
    retrieve_relevant_chunks,
    generate_rag_reply,
)


def test_rag_indexing_and_retrieval():
    """Verify that knowledge base articles are chunked and indexed into Chroma."""
    result = index_knowledge_base()
    assert result["articles_indexed"] == 8
    assert result["chunks_indexed"] >= 25

    # Test retrieval for VPN query
    chunks = retrieve_relevant_chunks("VPN error 800 gateway unreachable", top_k=2)
    assert len(chunks) >= 1
    top_chunk = chunks[0]
    assert top_chunk["article_id"] == "KB-IT-001"
    assert "VPN" in top_chunk["title"]
    assert top_chunk["score"] > 0.30


def test_rag_grounded_draft_with_citations():
    """Relevant query produces grounded draft with real citations from article metadata."""
    res = generate_rag_reply("Password reset help", "How do I reset my SSO password and what are the complexity rules?", category="IT")
    assert res["grounded"] is True
    assert len(res["citations"]) >= 1

    citation_ids = [c["article_id"] for c in res["citations"]]
    assert "KB-IT-002" in citation_ids

    # Verify citation schema
    c = res["citations"][0]
    assert "article_id" in c
    assert "title" in c
    assert "source" in c
    assert "score" in c
    assert isinstance(c["score"], float)

    # Verify draft mentions the policy
    assert "KB-IT-002" in res["draft_reply"] or "Password" in res["draft_reply"]


def test_rag_irrelevant_query_no_hallucination():
    """
    Irrelevant out-of-scope query must NOT fabricate company policy.
    Must return empty citations and a safe escalation notice.
    """
    irrelevant_query = "What is the recipe for chocolate chip brownies in the office kitchen microwave?"
    res = generate_rag_reply("Kitchen recipe", irrelevant_query, category="Other")

    assert res["grounded"] is False
    assert len(res["citations"]) == 0
    assert "escalated" in res["draft_reply"].lower()


def test_rag_aadhar_card_address_update_query():
    """Aadhaar card address update retrieves KB-HR-003 and provides accurate HR guidance."""
    res = generate_rag_reply(
        "Aadhar Card address update",
        "Dear HR, I need to update the address of my aadhar card in company records.",
        category="HR",
    )
    assert res["grounded"] is True
    assert len(res["citations"]) >= 1
    citation_ids = [c["article_id"] for c in res["citations"]]
    assert "KB-HR-003" in citation_ids
    assert "KB-HR-003" in res["draft_reply"] or "hr.company.com/profile" in res["draft_reply"]
    # Ensure IT password reset is NOT cited
    assert "KB-IT-002" not in citation_ids


def test_rag_finance_drive_query():
    """Query regarding finance folder permissions retrieves KB-FIN-001."""
    res = generate_rag_reply("Finance folder access", "I need access to the shared finance payroll spreadsheets.")
    assert res["grounded"] is True
    citation_ids = [c["article_id"] for c in res["citations"]]
    assert "KB-FIN-001" in citation_ids
    assert "Finance Shared Drive" in res["draft_reply"] or "approval" in res["draft_reply"].lower()


def test_rag_regenerate_draft_endpoint(client):
    """Support agent can trigger /draft-reply to refresh RAG draft with citations."""
    # 1. Login agent and employee
    agent_resp = client.post("/api/auth/login", json={"email": "agent@quickdesk.com", "password": "agent123"})
    agent_token = agent_resp.json()["access_token"]

    emp_resp = client.post("/api/auth/login", json={"email": "employee@quickdesk.com", "password": "employee123"})
    emp_token = emp_resp.json()["access_token"]

    # 2. Employee submits ticket
    ticket_resp = client.post(
        "/api/tickets",
        json={"title": "Maternity and annual leave rollover", "description": "How many days of leave can I roll over to next year?"},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert ticket_resp.status_code == 201
    ticket_id = ticket_resp.json()["id"]

    # 3. Agent calls /draft-reply endpoint
    regen_resp = client.post(
        f"/api/tickets/{ticket_id}/draft-reply",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert regen_resp.status_code == 200
    data = regen_resp.json()
    assert data["ai_draft_reply"] is not None
    assert len(data["citations"]) >= 1
    assert any("KB-HR-001" in c["article_id"] for c in data["citations"])
