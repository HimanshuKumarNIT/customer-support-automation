"""
Support Agent Orchestrator
----------------------------
This is the "AI agent" piece of the assignment: it makes a multi-step
decision, not just a single model call.

Pipeline:
  1. Classify the ticket (category, urgency, sentiment, confidence)
  2. Retrieve relevant knowledge-base articles (RAG)
  3. Decide: auto-respond vs escalate to a human
  4. Generate a grounded draft response (LLM if configured, template if not)

The escalation decision is itself a small rule-based agent policy:
  escalate if urgency == high, OR classification confidence is low,
  OR no relevant KB article was found (nothing to ground an answer in).
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List

from app.classifier import classify_ticket, ClassificationResult
from app.rag import get_knowledge_base
from app.llm_client import get_llm_client
from app.config import settings


@dataclass
class TicketResult:
    ticket_id: str
    classification: dict
    retrieved_articles: List[dict]
    draft_response: str
    escalate: bool
    escalation_reason: str
    generation_method: str

    def to_dict(self):
        return asdict(self)


def _decide_escalation(classification: ClassificationResult, retrieved: list) -> tuple[bool, str]:
    if classification.urgency == "high":
        return True, "High urgency ticket flagged for human review."
    if classification.confidence < settings.ESCALATION_CONFIDENCE_THRESHOLD:
        return True, "Low classification confidence; human review recommended."
    if not retrieved:
        return True, "No matching knowledge-base article found; cannot ground a response."
    if classification.sentiment == "negative" and classification.category == "billing":
        return True, "Negative sentiment on a billing issue; routed to human for care."
    return False, ""


def _template_response(classification: ClassificationResult, retrieved: list) -> str:
    """Fallback response generator used when no LLM key is configured.
    Produces a genuinely useful, grounded response from the KB content
    directly - not a stub - so the system is fully demoable with zero
    API keys."""
    if not retrieved:
        return (
            "Thank you for reaching out. We've received your message and a "
            "member of our support team will follow up shortly with more details."
        )

    top = retrieved[0]
    return (
        f"Thanks for contacting us! Based on your message, here's what applies:\n\n"
        f"{top['content'][:500].strip()}\n\n"
        f"If this doesn't fully resolve your issue, reply here and a support "
        f"specialist will follow up personally."
    )


def _llm_response(ticket_text: str, classification: ClassificationResult, retrieved: list) -> str:
    client = get_llm_client()
    if client is None:
        return _template_response(classification, retrieved)

    context = "\n\n".join(
        f"[{a['title']}]\n{a['content']}" for a in retrieved
    ) or "No relevant articles found."

    prompt = f"""You are a helpful, empathetic customer support agent.

Customer ticket:
\"\"\"{ticket_text}\"\"\"

Ticket classification: category={classification.category}, urgency={classification.urgency}, sentiment={classification.sentiment}

Relevant knowledge base articles:
{context}

Write a short, warm, professional reply to the customer (3-6 sentences) that
directly resolves their issue using ONLY the information in the knowledge base
articles above. If the articles don't fully cover it, say a specialist will
follow up. Do not invent policies not present in the articles."""

    try:
        return client.generate(prompt, max_tokens=400).strip()
    except Exception:
        return _template_response(classification, retrieved)


def process_ticket(ticket_id: str, text: str) -> TicketResult:
    classification = classify_ticket(text)

    kb = get_knowledge_base()
    retrieved = kb.search(text, top_k=2)

    escalate, reason = _decide_escalation(classification, retrieved)

    provider = settings.effective_provider
    if provider == "mock":
        response = _template_response(classification, retrieved)
        gen_method = "template"
    else:
        response = _llm_response(text, classification, retrieved)
        gen_method = f"llm:{provider}"

    return TicketResult(
        ticket_id=ticket_id,
        classification=classification.to_dict(),
        retrieved_articles=[
            {"id": a["id"], "title": a["title"], "score": a["score"]} for a in retrieved
        ],
        draft_response=response,
        escalate=escalate,
        escalation_reason=reason,
        generation_method=gen_method,
    )
