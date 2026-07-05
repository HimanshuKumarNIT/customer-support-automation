"""
LLM Client Abstraction
-----------------------
A tiny provider-agnostic wrapper so the rest of the app doesn't care whether
we're calling Anthropic, OpenAI, or running fully offline in mock mode.

This is the single point you'd touch to add another provider (Gemini, local
Ollama model, etc.) - which is the kind of clean architecture boundary the
recommendation report discusses under "scaling in production".
"""
from __future__ import annotations
from typing import Optional
from app.config import settings


class BaseLLMClient:
    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        raise NotImplementedError


class AnthropicClient(BaseLLMClient):
    def __init__(self):
        import anthropic
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL

    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
        return "\n".join(parts)


class OpenAIClient(BaseLLMClient):
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or ""


def get_llm_client() -> Optional[BaseLLMClient]:
    """Returns a configured client, or None if running in mock mode."""
    provider = settings.effective_provider
    try:
        if provider == "anthropic":
            return AnthropicClient()
        if provider == "openai":
            return OpenAIClient()
    except Exception:
        return None
    return None
