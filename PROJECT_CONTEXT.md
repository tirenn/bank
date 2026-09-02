# Project Context: AURA Core Digital Banking & Nova AI Platform

## Overview
A high-performance digital banking system engineered with strict architectural boundaries, comprehensive distributed logging (Grafana Loki format), Redis sliding window rate limiting, GORM & Goose database migrations, and an intelligent Nova AI financial copilot.

## Architecture Topology
```
Projects/
├── infra/                  # Shared Container Stack (PostgreSQL :5432, Redis :6379, ChromaDB :8002, Loki, Grafana)
│
└── bank/
    ├── backend/
    │   ├── core/           # Go 1.26 + Gin + GORM + Goose + Viper + Redis RateLimiter (:8085)
    │   └── ai-service/     # Python 3.11 + FastAPI + ChromaDB RAG + Redis RateLimiter (:8005)
    └── frontend/           # React 18 + Vite + Tailwind CSS v4 (:5173)
```

## Mandatory Engineering Standards Applied
1. **Clean Architecture by Domain**: Strict isolation between domain entities, repositories, services, and handlers.
2. **Gin Framework & GORM ORM**: High-concurrency Go REST API with GORM connection pooling and row locking (`FOR UPDATE`).
3. **Goose SQL Migrations**: Versioned DDL files in `backend/core/migrations/`.
4. **Mockery Unit Testing**: Mock interfaces with Testify suite verifying auth and transfer workflows.
5. **Grafana/Loki Distributed Logging**: Structured JSON schema outputting timestamp, level, service, caller, trace_id, request_id, and errors.
6. **Request ID Tracing**: `X-Request-ID` injected and propagated across all layers.
7. **Viper Configuration**: Loaded strictly from `.env` with complete secret safety (never committed to git).
8. **Redis Sliding Window Rate Limiting**: Accurate sorted-set timestamp windows protecting against DDoS and brute-force attempts.
9. **Docker & Makefiles**: Root and sub-project Dockerfiles, compose files, and Makefiles.
10. **Anti-AI Slop Frontend Design**: Human-centered fintech UI design with high-contrast ergonomics, real-time filters, and interactive transfer confirmation cards.
