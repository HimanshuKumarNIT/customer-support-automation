import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.classifier import classify_ticket


def test_billing_classification():
    result = classify_ticket("I was charged twice for my order, please refund me")
    assert result.category == "billing"


def test_shipping_classification():
    result = classify_ticket("My package tracking says delivered but I never got it")
    assert result.category == "shipping"


def test_account_classification():
    result = classify_ticket("I can't log in, my password reset email never arrives")
    assert result.category == "account"


def test_technical_classification():
    result = classify_ticket("The app keeps crashing every time I open it, error code ERR_5023")
    assert result.category == "technical"


def test_high_urgency_detection():
    result = classify_ticket(
        "This is the THIRD time I'm contacting you. Unacceptable. I want a manager and I am considering legal action."
    )
    assert result.urgency == "high"


def test_low_urgency_general():
    result = classify_ticket("Do your jackets come in petite sizes?")
    assert result.urgency == "low"


def test_confidence_bounds():
    result = classify_ticket("Random unrelated text with no clear signal at all")
    assert 0.0 <= result.confidence <= 1.0
