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


settings = Settings()





