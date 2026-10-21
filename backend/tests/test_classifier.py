import json
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from app.services.classifier import classify_ticket, deterministic_fallback_classifier


def test_fallback_classifier_keyword_rules():
    """Verify rule-based keyword mapping for all categories and priorities."""
    # IT test
    it_res = deterministic_fallback_classifier("VPN failing", "Cannot connect to wifi network")
    assert it_res.category == "IT"
    assert it_res.method == "fallback"

    # HR test
    hr_res = deterministic_fallback_classifier("Maternity leave request", "Taking 3 weeks vacation")
    assert hr_res.category == "HR"
    assert hr_res.method == "fallback"

    # Finance test
    fin_res = deterministic_fallback_classifier("Expense reimbursement", "Tax invoice for software subscription")
    assert fin_res.category == "Finance"
    assert fin_res.method == "fallback"

    # Admin test
    admin_res = deterministic_fallback_classifier("Office keycard broken", "Need new security badge")
    assert admin_res.category == "Admin"
    assert admin_res.method == "fallback"

    # High priority test
    high_res = deterministic_fallback_classifier("Production outage", "Urgent emergency, all systems broken")
    assert high_res.priority == "High"


def test_classify_ticket_no_api_key():
    """Without API key, returns fallback without throwing an exception."""
    with patch("app.services.classifier.settings.GROQ_API_KEY", ""):
        result = classify_ticket("VPN issue", "Cannot login to VPN")
        assert result.category == "IT"
        assert result.method == "fallback"
        assert "not configured" in result.reasoning


def test_classify_ticket_mocked_llm_success():
    """Mocked live Groq LLM returning valid structured JSON."""
    mock_response = AIMessage(
        content=json.dumps({
            "category": "HR",
            "priority": "Medium",
            "reasoning": "Ticket relates to employee annual leave policy.",
        })
    )

    with patch("app.services.classifier.settings.GROQ_API_KEY", "gsk_test_key_mock"):
        with patch("langchain_groq.ChatGroq.invoke", return_value=mock_response):
            result = classify_ticket("Annual leave policy question", "How many days of sick leave do I have left?")
            assert result.category == "HR"
            assert result.priority == "Medium"
            assert result.method == "llm"
            assert "annual leave" in result.reasoning.lower()


def test_classify_ticket_mocked_llm_invalid_json():
    """When LLM returns malformed or non-JSON text, safe fallback is executed."""
    mock_response = AIMessage(content="Sorry, as an AI I cannot classify this text.")

    with patch("app.services.classifier.settings.GROQ_API_KEY", "gsk_test_key_mock"):
        with patch("langchain_groq.ChatGroq.invoke", return_value=mock_response):
            result = classify_ticket("Finance invoice", "Need payment for invoice #1234")
            assert result.category == "Finance"
            assert result.method == "fallback"
            assert "JSONDecodeError" in result.reasoning


def test_classify_ticket_mocked_llm_invalid_category():
    """When LLM returns a hallucinated category outside the allowed list, fallback catches it."""
    mock_response = AIMessage(
        content=json.dumps({
            "category": "SpaceExploration",  # Invalid category!
            "priority": "High",
            "reasoning": "Hallucinated category",
        })
    )

    with patch("app.services.classifier.settings.GROQ_API_KEY", "gsk_test_key_mock"):
        with patch("langchain_groq.ChatGroq.invoke", return_value=mock_response):
            result = classify_ticket("Rocket launch delay", "Rocket battery issue")
            assert result.category == "IT"  # Fallback maps battery -> IT
            assert result.method == "fallback"
            assert "invalid category" in result.reasoning.lower()


def test_classify_ticket_mocked_llm_timeout():
    """When LLM call times out or encounters network error, fallback is executed."""
    with patch("app.services.classifier.settings.GROQ_API_KEY", "gsk_test_key_mock"):
        with patch("langchain_groq.ChatGroq.invoke", side_effect=TimeoutError("Connection timed out after 5.0s")):
            result = classify_ticket("Urgent VPN outage", "VPN disconnected")
            assert result.category == "IT"
            assert result.method == "fallback"
            assert "TimeoutError" in result.reasoning