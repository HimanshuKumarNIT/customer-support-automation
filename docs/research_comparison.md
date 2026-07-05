# Part 1 — AI Research & Tool Evaluation

**Use case:** Customer Support Automation (ticket classification + RAG-grounded response drafting + escalation routing)

This document compares the tools evaluated for building this system, and explains
the reasoning behind what was ultimately chosen for the prototype.

---

## 1. Tools Compared

| Tool | Category | Capabilities | Pricing (as of 2026) | Scalability | Ease of Integration | Key Limitations | Best Use Case |
|---|---|---|---|---|---|---|---|
| **Claude (Anthropic)** | LLM API | Strong reasoning, long context, good instruction-following, native tool use / agentic workflows | Pay-per-token; Sonnet-tier models are mid-priced, Haiku-tier is cheap/fast | Scales via API, no infra to manage; rate limits scale with usage tier | Simple REST API, official Python/TS SDKs | No native embeddings endpoint (needs a separate embedding provider); newest/most powerful tiers gated by usage tier | Response generation, complex reasoning steps, agentic multi-step workflows |
| **OpenAI (GPT-4o / GPT-4o-mini)** | LLM API + Embeddings | Strong general performance, native embeddings API, function calling, vision | Pay-per-token; mini models are very cheap | Scales via API; mature ecosystem | Extremely well documented, huge community, many framework integrations | Occasionally less consistent at strict instruction-following than Claude for structured output | Embeddings for RAG, general-purpose generation, cost-sensitive high-volume tasks |
| **Google Gemini** | LLM API | Very long context windows, multimodal, competitive pricing | Pay-per-token; generous free tier for prototyping | Scales via API, tightly integrated with Google Cloud | Good SDKs, native integration if already on GCP | Smaller third-party ecosystem than OpenAI; API surface changes more frequently | Long-document analysis, multimodal tickets (e.g. screenshots attached to a support ticket) |
| **LangChain** | Orchestration framework | Chains, agents, memory, huge library of integrations (vector stores, loaders, tools) | Free/open-source (self-hosted); LangSmith observability has paid tiers | Scales with your own infra; framework overhead can add latency | Python/JS, but has a real learning curve and can be heavier than needed for simple pipelines | Complex multi-tool agents, teams that need pre-built integrations for many data sources |
| **CrewAI** | Multi-agent framework | Role-based multi-agent orchestration (e.g. "classifier agent" + "researcher agent" + "writer agent") | Free/open-source; managed CrewAI+ has paid tiers | Good for multi-agent workflows; adds coordination overhead | Simpler mental model than LangChain for agent teams, still Python-based | Overkill for a single-pipeline task like ticket support; better suited to workflows needing genuine agent-to-agent negotiation | Multi-step business processes with distinct specialized roles |
| **n8n** | No-code/low-code automation | Visual workflow builder, huge library of app connectors (Zendesk, Slack, Gmail, Shopify, etc.) | Free self-hosted (open-source) or paid cloud tiers | Good for connecting existing SaaS tools; less suited to custom ML logic | Very easy for non-engineers; drag-and-drop | Custom logic (like a hybrid heuristic+LLM classifier) is awkward to express visually | Wiring together existing tools (e.g. "new Zendesk ticket → classify with OpenAI node → post to Slack") without writing code |
| **Make (formerly Integromat)** | No-code automation | Similar to n8n: visual scenarios, broad app connector library | Operation-based pricing tiers | Similar profile to n8n | Similar to n8n | Same custom-logic limitation as n8n | Same niche as n8n; choice often comes down to team preference/pricing |
| **Pinecone** | Managed vector database | Purpose-built for large-scale vector search, metadata filtering, high availability | Free tier for small projects; usage-based pricing at scale | Excellent — this is its core selling point | Simple REST/SDK, but adds an external managed dependency | Paid at meaningful scale; another vendor to manage | Production RAG systems with large (100k+ document) knowledge bases |
| **Weaviate** | Vector database (open-source or managed) | Vector + hybrid (keyword+vector) search, can self-host | Free self-hosted; managed cloud has usage pricing | Very good, especially self-hosted for cost control | GraphQL/REST API, moderate setup | Self-hosting requires infra ops work | Teams wanting a vector DB without vendor lock-in, or needing hybrid search |
| **Ollama** | Local LLM runtime | Runs open-weight models (Llama, Mistral, etc.) locally, zero API cost, full data privacy | Free (just compute cost) | Limited by local hardware; not horizontally scalable without extra infra | Very easy local setup; API-compatible with OpenAI format | Lower quality than frontier hosted models; needs GPU for good latency | Privacy-sensitive deployments, offline/on-prem requirements, cost-sensitive high-volume classification |

---

## 2. Why This Prototype's Stack Was Chosen

For the actual POC in this repository, the design goal was: **a system that is
honest about production trade-offs, runs immediately for a reviewer with zero
setup and zero cost, and can be upgraded to a full production stack by
swapping a config value, not rewriting code.**

| Layer | Chosen for the demo | Production upgrade path | Why |
|---|---|---|---|
| Classification | Hybrid: keyword/rule heuristics first, LLM escalation only on low-confidence cases | Same hybrid pattern, with the "cheap" pass being Haiku/GPT-4o-mini instead of pure rules | Real support queues are 80% obvious/repetitive tickets. Paying LLM cost for every single one is wasteful. Escalating only the ambiguous ~20% to an LLM is the standard cost-optimization pattern at this workflow layer. |
| Retrieval (RAG) | scikit-learn TF-IDF + cosine similarity, in-memory | Pinecone or Weaviate with real embeddings (OpenAI or Voyage AI) | TF-IDF requires zero external calls, zero API keys, and zero download of model weights — meaning this repo runs instantly for any reviewer, anywhere, offline. At the scale of a 6-article demo KB, TF-IDF and embeddings perform comparably; at production scale (thousands of KB articles, semantic paraphrase matching) a real vector DB with dense embeddings becomes necessary — the `KnowledgeBase.search()` interface is written narrow enough that this swap doesn't touch the rest of the codebase. |
| Response generation | Claude or OpenAI via a shared `LLMClient` interface, falls back to a KB-grounded template if no key is set | Claude Sonnet in production (strong instruction-following for "answer only from these documents, don't hallucinate policy") | Claude was chosen as the primary generation model because grounded, constrained instruction-following (don't invent a policy not in the retrieved doc) is exactly where Claude tends to be strong. OpenAI is kept as a first-class alternative behind the same interface. |
| Orchestration | Custom lightweight Python agent (no framework) | LangChain if the pipeline grows more branches, or CrewAI if genuinely distinct "agent roles" emerge | For a 4-step linear pipeline (classify → retrieve → decide → generate), a framework like LangChain adds dependency weight and abstraction overhead without adding capability. It becomes worth adopting once the pipeline needs many pluggable tools, memory across turns, or a large ecosystem of pre-built connectors. |
| Workflow glue (routing tickets into/out of this system) | Not built (out of scope for a backend POC) | n8n or Make to connect a real ticket source (Zendesk, Gmail, Shopify) to this API's `/api/ticket/process` endpoint | This project exposes a clean REST endpoint specifically so a no-code tool like n8n could call it as one node in a larger support workflow — a realistic production integration pattern. |

---

## 3. Cost Optimization Takeaway

The single biggest lever in this architecture is **not calling an LLM at all
for tickets the heuristic layer is already confident about.** In the demo
run over 12 sample tickets, roughly half were classified with >90% confidence
by the free heuristic pass alone — meaning a production deployment could
handle roughly half of ticket volume with zero LLM spend on the
classification step, reserving model calls for response drafting and the
genuinely ambiguous cases.
