"""
FastAPI application exposing the customer support automation pipeline.

Run with:
    uvicorn app.main:app --reload --port 8000

Then visit:
    http://localhost:8000/docs        (interactive API docs)
    http://localhost:8000/            (simple demo dashboard)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import os
import json

from app.agent import process_ticket
from app.config import settings

app = FastAPI(
    title="AI Customer Support Automation",
    description="Classifies tickets, retrieves knowledge-base context (RAG), "
                "drafts responses, and decides when to escalate to a human.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class TicketRequest(BaseModel):
    ticket_id: str = Field(default="T-ADHOC", description="Optional ticket identifier")
    subject: str = Field(default="", description="Ticket subject line")
    message: str = Field(..., description="The customer's message body")


@app.get("/")
def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"message": "AI Customer Support Automation API. See /docs"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm_provider": settings.effective_provider,
        "embedding_backend": settings.EMBEDDING_BACKEND,
    }


@app.post("/api/ticket/process")
def process(ticket: TicketRequest):
    if not ticket.message.strip():
        raise HTTPException(status_code=400, detail="Ticket message cannot be empty.")

    full_text = f"{ticket.subject}. {ticket.message}".strip(". ")
    result = process_ticket(ticket.ticket_id, full_text)
    return JSONResponse(result.to_dict())


@app.get("/api/tickets/sample")
def sample_tickets():
    """Returns the bundled sample ticket dataset (used by the demo dashboard)."""
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "sample_tickets.json",
    )
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/kb")
def list_kb():
    """List all knowledge-base articles currently indexed."""
    from app.rag import get_knowledge_base
    kb = get_knowledge_base()
    return [
        {"id": a.id, "title": a.title, "category": a.category}
        for a in kb.articles
    ]
