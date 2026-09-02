import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    PORT: int = int(os.getenv("PORT", "8005"))
    CORE_BANKING_URL: str = os.getenv("CORE_BANKING_URL", "http://localhost:8085")
    INTERNAL_MCP_SECRET: str = os.getenv("INTERNAL_MCP_SECRET", "nova-internal-mcp-secret-key-392810")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    OPENROUTER_FALLBACK_MODEL: str = os.getenv("OPENROUTER_FALLBACK_MODEL", "google/gemini-2.0-flash-exp:free")
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8002"))
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "bank_faq_kb")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

settings = Settings()

