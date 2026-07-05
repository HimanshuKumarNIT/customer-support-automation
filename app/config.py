"""
Central configuration for the Customer Support Automation system.
Loads from environment variables (.env) with safe, working defaults so the
whole system runs out-of-the-box in "mock mode" with zero API keys.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM provider selection: "anthropic" | "openai" | "mock"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock").lower()

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Embedding backend: "tfidf" (offline, default) | "openai"
    EMBEDDING_BACKEND: str = os.getenv("EMBEDDING_BACKEND", "tfidf").lower()

    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    ESCALATION_CONFIDENCE_THRESHOLD: float = float(
        os.getenv("ESCALATION_CONFIDENCE_THRESHOLD", "0.55")
    )

    KB_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "knowledge_base",
    )

    @property
    def effective_provider(self) -> str:
        """Resolve the actual provider to use, auto-falling back to mock
        if the requested provider has no API key configured."""
        if self.LLM_PROVIDER == "anthropic" and self.ANTHROPIC_API_KEY:
            return "anthropic"
        if self.LLM_PROVIDER == "openai" and self.OPENAI_API_KEY:
            return "openai"
        # Auto-detect: if a key exists even without explicit provider choice
        if self.ANTHROPIC_API_KEY:
            return "anthropic"
        if self.OPENAI_API_KEY:
            return "openai"
        return "mock"


settings = Settings()
