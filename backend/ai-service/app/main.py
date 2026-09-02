from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.logger import setup_logger, app_logger
from app.middleware import RequestIDMiddleware, RedisSlidingWindowRateLimiter
from app.services.faq_service import faq_service
from app.services.rag_cache_service import rag_cache_service
from app.services.chat_history_service import chat_history_service
from app.services.workflow_state_service import workflow_state_service
from app.api.v1.router import api_v1_router


# Initialize Redis sliding window rate limiter
rate_limiter = RedisSlidingWindowRateLimiter(
    redis_url=settings.REDIS_URL,
    max_requests=60,
    window_sec=60
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Initializing ChromaDB FAQ Knowledge Base, Redis rate limiter, Redis RAG cache, Workflow Engine, and Conversation History...")

    await rate_limiter.connect()
    await rag_cache_service.connect()
    await chat_history_service.connect()
    await workflow_state_service.connect()
    yield




app = FastAPI(
    title="Banking AI Microservice",
    description="Clean Architecture AI Microservice with Private MCP, Multi-Agent Orchestration, and ChromaDB Vector RAG",
    version="1.0.0",
    lifespan=lifespan
)

# Cross-cutting middlewares
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "service": "bank-ai-microservice",
        "architecture": "clean-architecture-domain-driven",
        "chroma_connected": faq_service.repo.collection is not None,
        "model_source": "dynamic-database-pool",
        "rate_limiter": "redis-sliding-window",
        "rag_cache": "redis-rag-answer-cache",
        "environment": settings.ENVIRONMENT
    }


# Register V1 API Routes
app.include_router(api_v1_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
