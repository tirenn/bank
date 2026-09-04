# 🏦 Tirenn Bank: Autonomous AI-Powered Neo-Banking Platform

[![Go Version](https://img.shields.io/badge/Go-1.26-blue.svg)](https://golang.org)
[![Python Version](https://img.shields.io/badge/Python-3.11-yellow.svg)](https://python.org)
[![React Version](https://img.shields.io/badge/React-19-cyan.svg)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_RAG-purple.svg)](https://trychroma.com)

**Tirenn Bank** is a production-grade, distributed autonomous neo-banking system combining high-integrity double-entry accounting with an autonomous multi-agent AI copilot capable of executing chained workflows, RAG policy retrieval, multi-day long-running form state, and real-time LLM cost analytics.

---

## 🏗️ System Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                          TIRENN SYSTEM TOPOLOGY                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   [ Client Browser ] ──► [ React 19 Frontend (Port 7081) ]             │
│                                │                                       │
│          ┌─────────────────────┴─────────────────────┐                 │
│          ▼                                           ▼                 │
│   [ Core Banking API ]                      [ AI Microservice ]        │
│   • Golang 1.26 (Clean Arch)                • Python 3.11 (FastAPI)    │
│   • ACID Ledger & Pessimistic Locks         • Planner Orchestrator DAG │
│   • Decoupled Forex Gateway                 • ChromaDB Vector RAG      │
│   • Port: 8082                              • Port: 8083               │
│          │                                           │                 │
│          ├─────────────────────┬─────────────────────┤                 │
│          ▼                     ▼                     ▼                 │
│   [ PostgreSQL 16 ]     [ Redis 7 Cache ]     [ OpenRouter API ]       │
│   • Accounts & Ledger   • 7-Day Workflows     • Free Model Cascade     │
│   • Users & Cards       • Cost Telemetry      • Dynamic Token Pricing  │
│   • AI Model Registry   • Rate Limiting                                │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

For comprehensive deep-dive documentation:
* 🏛️ **[Root System Architecture Specification](ARCHITECTURE.md)**
* ⚙️ **[Core Banking Architecture](backend/core/ARCHITECTURE.md)**
* 🤖 **[AI Microservice Architecture](backend/ai-service/ARCHITECTURE.md)**
* 🎨 **[Frontend Architecture](frontend/ARCHITECTURE.md)**

---

## 🌟 Key Features

### 1. Financial Ledger & Transactional Core
* **ACID Double-Entry Ledger**: Atomic P2P fund transfers with row-level pessimistic locking (`SELECT ... FOR UPDATE`) and collision-free reference numbering (`-OUT` and `-IN`).
* **Multi-Account Hierarchy**: Primary Checking and Secondary Savings accounts per customer.
* **Card & Security Controls**: Instant debit card locking/unlocking and dynamic daily spending limits.
* **Decoupled Live Forex Engine**: Live conversion via `open.er-api.com` with Redis & in-memory caching and 0.25% spread markup.
* **Compound Loan Calculator**: Amortization simulation for mortgage, auto, and personal loans.

### 2. Autonomous Multi-Agent AI Banking Copilot
* **Autonomous Graph Planning (DAG)**: Decomposes multi-intent prompts into sequential execution plans across 5 specialized sub-agents (`Transaction`, `Wealth`, `Security`, `Identity`, `Support`).
* **Inter-Agent Shared Scratchpad**: Passes calculated figures (converted currencies, account numbers) between chained agents in-memory without customer repetition.
* **7-Day Long-Running Multi-Turn Workflow State Engine**: Persists multi-day application drafts (Loans, Tier-2 KYC, Account Opening) in Redis (`workflow:<type>:<user_id>`) with an isolated 7-day TTL (604,800s).
* **Real-Time Token & Cost Tracker**: Calculates exact USD expenses from OpenRouter's dynamic pricing catalog with atomic Redis telemetry and zero-cost guarantees for free models.
* **Database-Driven Free Model Fallback Cascade**: Automatically cascades across 7 system-provisioned free LLMs on rate limits.
* **Private Model Context Protocol (MCP)**: 15 typed financial tools with automated Bearer JWT forwarding.
* **ChromaDB Vector RAG**: Dense vector FAQ semantic search with Redis answer caching (0-4ms latency).
* **Automated PII Redaction**: Scans and masks 16-digit PANs, CVVs, Bearer tokens, and passwords in real-time.

### 3. Glassmorphism Client & Admin Dashboard
* **Customer Hub**: Account balances, spending summaries, quick transfers, card lock sliders, and loan calculators.
* **Interactive AI Action Cards**: Human-in-the-loop confirmation cards for transfers (`TRANSFER_DRAFT`) and card freezes (`CARD_FROZEN`).
* **Admin AI Telemetry & Cost Dashboard**: Real-time KPI scorecards, domain cost breakdown, and live 50-entry token audit stream table.
* **Admin Vector RAG Manager**: Ingest documents with visual chunk inspection.

---

## 🚀 Quick Start Guide

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v24.0+)
* [Docker Compose](https://docs.docker.com/compose/) (v2.20+)
* [Make](https://www.gnu.org/software/make/) (optional, but recommended)

### 1. Clone & Start All Services
```bash
# Clone the repository
git clone https://github.com/tirenn/bank.git
cd bank

# Start all microservices in the background
docker compose up -d --build
```

All services will start up automatically:
| Service | URL / Port | Technology |
| :--- | :--- | :--- |
| **Frontend UI** | [http://localhost:7081](http://localhost:7081) | React 19 + Vite + Tailwind |
| **Core Banking API** | [http://localhost:8082](http://localhost:8082) | Golang 1.26 + Gin + GORM |
| **AI Microservice** | [http://localhost:8083](http://localhost:8083) | Python 3.11 + FastAPI + ChromaDB |
| **PostgreSQL Database** | `localhost:5432` | PostgreSQL 16 (DB: `bankdb`) |
| **Redis Cache** | `localhost:6379` | Redis 7 (Alpine) |

---

## 🧪 Comprehensive Automated Test Suites

The platform includes two robust automated evaluation harnesses:

### 1. Run 6-Layer AI Microservice Evaluation Matrix (`make eval-ai`)
```bash
make eval-ai
```
* **Layer 1: Tools** (7 tests) — MCP tool schema compliance & deterministic financial calculators.
* **Layer 2: Security** (7 tests) — 16-digit PAN masking, CVV removal, JWT redaction, cross-account tenant isolation.
* **Layer 3: Vector RAG** (4 tests) — ChromaDB semantic distance & relevance scores.
* **Layer 4: Planner Orchestrator** (4 tests) — Multi-agent DAG generation (Forex + Transfer, Freeze + History).
* **Layer 5: Workflow Engine** (5 tests) — 7-Day Redis workflow lifecycle (Init, Resume, Field Accumulation, Teardown).
* **Layer 6: Token & Cost Tracker** (5 tests) — OpenRouter dynamic pricing rates, free-tier zero cost, atomic Redis sync.
* **Result**: **32/32 Test Cases Passed (100.0%)** ✅

---

### 2. Run 6-Suite Core Banking E2E Integration Suite (`make test-e2e`)
```bash
make test-e2e
```
* **Suite 1: Auth & Identity** (5 tests) — Customer onboarding, JWT authentication, KYC address updates.
* **Suite 2: ACID Ledger** (9 tests) — Account provisioning, deposits, P2P transfers, balance consistency, transaction stream.
* **Suite 3: Boundary Security** (4 tests) — Overdraft denial, invalid accounts, negative transfer rejection, unauthenticated interception.
* **Suite 4: Cards & Limits** (4 tests) — Daily spending limits ($7,500), debit card freeze, state verification, card unfreeze.
* **Suite 5: Wealth & Beneficiaries** (4 tests) — Trusted payees directory, live Forex conversion, loan amortization.
* **Suite 6: Admin RBAC** (5 tests) — Admin authentication, AI model telemetry access, immutable free model protection.
* **Result**: **31/31 Test Cases Passed (100.0%)** ✅

---

## 👥 Default Demo Credentials

| Role | Email | Password | Pre-loaded Features |
| :--- | :--- | :--- | :--- |
| **Customer (John Doe)** | `john.doe@bank.com` | `password123` | \$1,500 balance, Checking & Savings, Active Visa debit card |
| **Administrator** | `admin@bank.com` | `admin123` | AI Model priority controls, Real-time cost analytics, Vector RAG manager |

---

## 📜 License
This project is proprietary and maintained for Tirenn Autonomous Banking Engineering.
