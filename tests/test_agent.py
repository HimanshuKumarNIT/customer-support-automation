import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent import process_ticket


def test_process_ticket_returns_expected_shape():
    result = process_ticket("T-TEST-1", "I was charged twice for order #123, please refund me")
    d = result.to_dict()
    assert d["ticket_id"] == "T-TEST-1"
    assert "category" in d["classification"]
    assert isinstance(d["retrieved_articles"], list)
    assert isinstance(d["draft_response"], str) and len(d["draft_response"]) > 0
    assert isinstance(d["escalate"], bool)


def test_high_urgency_always_escalates():
    result = process_ticket(
        "T-TEST-2",
        "This is the THIRD time I've contacted you, unacceptable, I want a manager, legal action if not resolved.",
    )
    assert result.escalate is True


def test_general_low_urgency_can_auto_resolve():
    result = process_ticket("T-TEST-3", "Do your jackets come in petite sizes?")
    # Should not crash and should produce a response either way
    assert isinstance(result.draft_response, str)
