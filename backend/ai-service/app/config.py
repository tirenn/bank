import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8005")))
    CORE_BANKING_URL: str = Field(default_factory=lambda: os.getenv("CORE_BANKING_URL", "http://bank-core:8085"))
    INTERNAL_MCP_SECRET: str = Field(default_factory=lambda: os.getenv("INTERNAL_MCP_SECRET", ""))
    OPENROUTER_API_KEY: str = Field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))

    CHROMA_HOST: str = Field(default_factory=lambda: os.getenv("CHROMA_HOST", "chromadb"))
    CHROMA_PORT: int = Field(default_factory=lambda: int(os.getenv("CHROMA_PORT", "8000")))
    CHROMA_COLLECTION: str = Field(default_factory=lambda: os.getenv("CHROMA_COLLECTION", "bank_faq_kb"))
    REDIS_URL: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://redis:6379/0"))
    RAG_CACHE_TTL: int = Field(default_factory=lambda: int(os.getenv("RAG_CACHE_TTL", "86400")))
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))

    # Advanced Hybrid RAG Pipeline Configurations
    RAG_HYBRID_SEARCH_ENABLED: bool = Field(default_factory=lambda: os.getenv("RAG_HYBRID_SEARCH_ENABLED", "true").lower() == "true")
    RAG_TOP_K_CANDIDATES: int = Field(default_factory=lambda: int(os.getenv("RAG_TOP_K_CANDIDATES", "10")))
    RAG_TOP_K_FINAL: int = Field(default_factory=lambda: int(os.getenv("RAG_TOP_K_FINAL", "3")))
    RAG_DEDUPLICATION_THRESHOLD: float = Field(default_factory=lambda: float(os.getenv("RAG_DEDUPLICATION_THRESHOLD", "0.85")))
    RAG_MAX_OUTPUT_CHARS: int = Field(default_factory=lambda: int(os.getenv("RAG_MAX_OUTPUT_CHARS", "2500")))


settings = Settings()






