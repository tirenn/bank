# AI Microservice Project Context

## Overview
High-performance Python AI microservice for the Nova Banking Platform, implemented following Clean Architecture and Domain-Driven Design principles.

## Clean Architecture Layers
1. **Domain Layer (`app/domain/`)**:
   - `schemas.py`: Pydantic data transfer objects (`ChatMessage`, `ChatRequest`, `ChatResponse`, `DocumentUploadRequest`, `AtomicIngestResponse`).
2. **Repository Layer (`app/repositories/`)**:
   - `faq_repository.py`: ChromaDB vector database client, semantic search, parallel chunking & atomic ingestion with full rollback.
   - `mcp_repository.py`: JSON-RPC 2.0 client for Golang Private MCP microservices (`/mcp/v1/transaction`, `/mcp/v1/identity`, `/mcp/v1/security`, `/mcp/v1/wealth`).
3. **Service Layer (`app/services/`)**:
   - `agent_service.py`: Supervisor intent classifier and 5 dedicated sub-agents (`TransactionSubAgent`, `IdentitySubAgent`, `SecuritySubAgent`, `WealthSubAgent`, `SupportFaqSubAgent`).
   - `faq_service.py`: RAG knowledge base management, in-memory zero-disk PDF parsing.
4. **API Transport Layer (`app/api/`)**:
   - `dependencies.py`: Role-Based Access Control (`require_admin_role`).
   - `v1/chat.py`: `/api/v1/ai/chat` endpoint.
   - `v1/faq.py`: `/api/v1/ai/faq` RAG management endpoints.
   - `v1/router.py`: Aggregated API router.
5. **Middleware Layer (`app/middleware/`)**:
   - `request_id.py`: Distributed `X-Request-ID` tracing context.
   - `rate_limiter.py`: Redis sliding window rate limiter (60 req/min).
6. **Application Entrypoint (`app/main.py`)**:
   - Clean FastAPI setup, CORS, lifespan seeding, and router registration.

## Standards Compliance
- **12-Factor Config**: All configurations loaded strictly from `.env` via Pydantic `Settings`.
- **Zero-Disk-Leak RAG**: PDFs & text files processed 100% in RAM memory.
- **Private MCP Security**: Authenticated over internal Docker network using `X-Internal-MCP-Secret`.
