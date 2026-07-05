# Part 3 — Recommendation Report

## Recommended Architecture

For a production customer support automation system, the recommended
architecture builds directly on this prototype's shape:

1. **Ingestion layer** — a no-code connector (n8n or Make) pulling new tickets
   from the existing helpdesk (Zendesk, Freshdesk, Gmail, Shopify inbox, etc.)
   and POSTing them to the automation API.
2. **Classification** — hybrid heuristic + LLM (Claude Haiku or GPT-4o-mini
   for the escalated ambiguous cases), as implemented in this POC.
3. **Retrieval** — a managed vector database (Pinecone for simplicity, or
   self-hosted Weaviate for cost control at scale) holding embeddings of the
   full support knowledge base, product docs, and past resolved-ticket
   transcripts.
4. **Generation** — Claude Sonnet for drafting grounded responses, chosen for
   strong constrained instruction-following ("only answer from these
   documents"), which directly reduces hallucinated policy statements — a
   real compliance risk in support automation.
5. **Human-in-the-loop layer** — the escalation flag routes flagged tickets
   into the existing human queue with the AI's classification and draft
   response attached as a starting point, rather than fully bypassing agents.
6. **Feedback loop** — human edits to AI-drafted responses are logged and
   periodically reviewed to refine the KB content and escalation thresholds.

## Why These Tools Were Selected

- **Claude** for generation: best-in-class at staying grounded to provided
  context and following strict output-format instructions, which matters
  when the cost of a hallucinated refund policy is real money.
- **TF-IDF → Pinecone/Weaviate migration path** for retrieval: start cheap
  and dependency-free, upgrade only once KB size or semantic-matching needs
  actually justify the added infrastructure and cost.
- **Hybrid heuristic+LLM classification**: minimizes per-ticket cost by
  reserving paid model calls for genuinely ambiguous cases.
- **n8n/Make for ingestion**: avoids writing and maintaining custom
  integration code for every helpdesk platform a client might already use.

## Estimated Infrastructure Cost (illustrative, monthly)

Assumptions: 10,000 tickets/month, ~50% auto-resolved by heuristics alone,
remaining ~50% need an LLM call for classification and/or generation.

| Component | Estimate | Notes |
|---|---|---|
| LLM API calls (classification, ~5,000 tickets) | $15 – $40 | Using a small/cheap model (Haiku-tier or GPT-4o-mini-tier pricing) |
| LLM API calls (response generation, ~10,000 tickets) | $60 – $150 | Larger model, longer output per ticket |
| Vector DB (Pinecone starter tier or self-hosted Weaviate) | $0 – $70 | Free tier often sufficient below ~100k vectors; self-hosting trades cost for ops effort |
| Hosting for the API (small VM or serverless container) | $10 – $30 | FastAPI app is lightweight; scales well on serverless (e.g. Cloud Run, Lambda) |
| No-code workflow tool (n8n cloud or self-hosted) | $0 – $50 | Free if self-hosted |
| **Total estimated monthly cost** | **≈ $85 – $340** | Scales roughly linearly with ticket volume; heuristic-first design keeps this well below "LLM call per ticket" baseline cost |

These are directional estimates for planning purposes, not a quote — actual
cost depends on chosen model tiers, average ticket/response length, and
negotiated enterprise pricing at volume.

## Risks and Limitations

- **Hallucination risk in generation** — mitigated by strict "answer only
  from retrieved context" prompting, but not eliminated. Recommend a human
  review sampling process even for auto-resolved tickets, especially during
  rollout.
- **Retrieval quality ceiling with TF-IDF** — keyword-based retrieval misses
  paraphrases and synonyms an embedding model would catch (e.g. "money back"
  vs. "reimbursement"). This is the primary reason production deployment
  should move to dense embeddings once KB size grows.
- **Classification drift** — the heuristic keyword lists will need periodic
  review as product lines, terminology, and common complaint types evolve.
- **Escalation policy is currently rule-based and static** — in production,
  this should be informed by real outcome data (e.g. which auto-resolved
  ticket categories actually see high customer follow-up/dissatisfaction)
  rather than fixed thresholds set at design time.
- **No authentication/rate limiting in this POC** — a production deployment
  needs API auth, rate limiting, and audit logging before handling real
  customer PII.
- **Data privacy** — support tickets often contain PII and order data;
  production deployment must ensure the chosen LLM provider's data handling
  terms meet the company's compliance requirements (e.g. no training on
  customer data, appropriate data residency).

## How the System Could Scale in Production

- **Horizontal scaling**: the API layer is stateless, so it scales
  horizontally behind a load balancer with no architectural changes.
- **Volume growth**: the heuristic-first classification design means LLM
  cost grows sub-linearly with ticket volume as the heuristic rules are
  refined over time (higher heuristic confidence = fewer LLM escalations).
- **Multi-language support**: the pluggable LLM client makes adding
  translation or multilingual prompting a contained addition rather than a
  rewrite.
- **Multi-channel expansion**: the same `/api/ticket/process` endpoint can
  serve tickets from email, chat widget, or social media once routed through
  a common ingestion layer — the core pipeline doesn't need to know the
  ticket's origin channel.
- **Continuous improvement loop**: logging classification outcomes and human
  overrides creates a dataset that can later fine-tune the heuristic rules,
  retrain a lightweight classifier, or build a proper eval set to catch
  regressions when prompts or models change.
