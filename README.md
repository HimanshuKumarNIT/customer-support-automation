# AI Customer Support Automation — Research & Prototype

A working prototype of an AI-powered customer support automation system:
tickets are classified, relevant knowledge is retrieved (RAG), a grounded
response is drafted, and the system decides whether to auto-resolve or
escalate to a human — built as a technical assignment covering AI tool
research, a working POC, and a production recommendation report.

**Runs immediately with zero API keys** (mock mode uses local heuristics +
template responses) and upgrades seamlessly to real LLM-generated responses
the moment you add an `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`.

---

## Contents

| Deliverable | Location |
|---|---|
| Part 1 — Tool research & comparison | [`docs/research_comparison.md`](docs/research_comparison.md) |
| Part 2 — Working prototype | this repository (see below) |
| Part 3 — Recommendation report | [`docs/recommendation_report.md`](docs/recommendation_report.md) |
| Architecture diagram & explanation | [`docs/architecture.md`](docs/architecture.md) |

---

## What the prototype does

1. **Classifies** an incoming ticket → category (billing/shipping/returns/account/technical/general), urgency, sentiment, confidence
2. **Retrieves** relevant knowledge-base articles (RAG, via TF-IDF similarity search)
3. **Decides** whether to auto-resolve or escalate to a human, based on urgency, confidence, and retrieval quality
4. **Drafts** a grounded response — using an LLM if configured, or a KB-grounded template if not
5. Exposes all of this via a **FastAPI** backend, a **CLI demo**, and a simple **web dashboard**

---

## Quick Start

```bash
# 1. Clone and enter the repo
git clone <your-repo-url>
cd customer-support-automation

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) add real API keys
cp .env.example .env
# edit .env and add ANTHROPIC_API_KEY or OPENAI_API_KEY if you have one
# the system works fully without this step, in mock mode

# 4a. Run the CLI demo (fastest way to see it work)
python scripts/demo.py

# 4b. OR run the API + dashboard
uvicorn app.main:app --reload --port 8000
# then open http://localhost:8000 in your browser
```

### Run the tests

```bash
python -m pytest tests/ -v
```

### Try a single ad-hoc ticket from the CLI

```bash
python scripts/demo.py --ticket "My package never arrived and tracking hasn't updated in a week"
```

---

## Example Output

```
── Ticket T-1001 ──
  Category:      billing
  Urgency:       medium
  Sentiment:     negative
  Confidence:    0.95
  Classified by: heuristic
  Retrieved KB:
    → Duplicate or Incorrect Charges  (score=0.3397)
    → Refund Policy and Timelines  (score=0.2612)
  Decision:      ESCALATE → HUMAN
  Reason:        Negative sentiment on a billing issue; routed to human for care.
  Response (template):
    Thanks for contacting us! Based on your message, here's what applies:

    # Duplicate or Incorrect Charges
    If a customer reports being charged twice for the same order, first verify...
```

---

## Project Structure

```
customer-support-automation/
├── app/
│   ├── main.py            FastAPI application & routes
│   ├── agent.py           Orchestrates classify → retrieve → decide → generate
│   ├── classifier.py      Hybrid heuristic + LLM ticket classifier
│   ├── rag.py              Knowledge-base loading + TF-IDF retrieval
│   ├── llm_client.py       Provider-agnostic LLM interface (Anthropic/OpenAI/mock)
│   └── config.py           Environment-based settings
├── data/
│   ├── knowledge_base/     Markdown FAQ/policy articles used for RAG
│   └── sample_tickets.json Sample tickets for demos
├── scripts/
│   └── demo.py             CLI demo runner
├── static/
│   └── index.html          Interactive demo dashboard
├── tests/                  pytest test suite (classifier, RAG, agent)
├── docs/
│   ├── research_comparison.md   Part 1 deliverable
│   ├── architecture.md          System architecture + diagram
│   └── recommendation_report.md Part 3 deliverable
├── requirements.txt
├── .env.example
└── README.md
```

---

## Design Highlights (for reviewers)

- **Hybrid classification**: free deterministic rules handle the obvious
  majority of tickets; an LLM is only called for ambiguous cases *and* only
  if a key is configured — a real cost-optimization pattern, not just a demo
  shortcut.
- **Zero-dependency RAG by default**: TF-IDF retrieval means this repo runs
  fully offline with no model downloads, while the retrieval interface is
  narrow enough to swap in Pinecone/Weaviate later without touching the rest
  of the codebase (see `docs/architecture.md`).
- **Provider-agnostic LLM client**: switching between Claude and OpenAI (or
  adding Gemini/Ollama later) is a config change, not a rewrite.
- **Agentic decision-making, not just a single prompt**: the escalation
  policy is a separate, explicit, testable rule set — a deliberate multi-step
  agent pipeline rather than "ask an LLM and hope."
- **Fully tested**: 14 passing unit tests across classification, retrieval,
  and end-to-end agent behavior.

---

## Notes on API Keys

This project supports Anthropic and OpenAI. If neither `ANTHROPIC_API_KEY`
nor `OPENAI_API_KEY` is set in `.env`, the system automatically runs in
**mock mode**:
- Classification uses the heuristic pass only.
- Response generation returns the raw retrieved KB content in a template,
  which is still a genuinely useful, grounded answer — not a stub.

This was a deliberate choice so the assignment reviewer can clone this repo
and get a fully working demo in under a minute with no signup, no billing,
and no waiting on API access.
