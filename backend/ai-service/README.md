# Tirenn Autonomous AI Microservice (`bank-ai`)

Autonomous AI Banking Copilot microservice built with **FastAPI**, **Private Model Context Protocol (MCP)**, **Planner Orchestrator (DAG)**, **ChromaDB Vector RAG**, **7-Day Long-Running Workflow Engine**, and **Dynamic Token/Cost Tracking**.

---

## 🌟 Key Features

* **Autonomous Graph Planning (DAG)**: Decomposes complex multi-intent instructions into ordered execution plans across 5 specialized sub-agents (`Transaction`, `Wealth`, `Security`, `Identity`, `Support`).
* **Inter-Agent Shared Scratchpad**: Passes real-time variables (converted amounts, payee account IDs) seamlessly between sub-agents in-memory.
* **Long-Running Multi-Turn Workflow State Engine**: Persists multi-day application drafts (Loans, Tier-2 KYC, Account Opening) in Redis with a 7-day TTL (604,800s).
* **Dynamic OpenRouter Token & Cost Tracker**: Asynchronously reads token usage, calculates exact USD expense against OpenRouter's live catalog, and provides real-time Redis telemetry.
* **Database-Driven Free Model Fallback Pool**: Automatically cascades across 7 system-provisioned free LLM models on HTTP 429 or provider rate limits.
* **Private Model Context Protocol (MCP)**: 15 typed financial tools with automated Bearer JWT forwarding.
* **ChromaDB Vector RAG**: Dense vector FAQ semantic search with Redis answer caching (0-4ms latency).
* **Automated PII Masking**: Real-time redaction of 16-digit PANs, CVVs, Bearer tokens, and passwords.

---

## 🛠️ Environment Variables

Configure via `.env` or Docker Compose:

```ini
PORT=8083
ENVIRONMENT=development

# Core Banking Bridge
CORE_BANKING_URL=http://bank-core:8082

# Distributed Storage & Caching
REDIS_URL=redis://bank-redis:6379/0

# LLM Provider Configuration
OPENROUTER_API_KEY=your-openrouter-api-key-here
DEFAULT_MODEL=google/gemini-2.0-flash-exp:free

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=60
```

---

## 🚀 API Endpoint Reference

### AI Chat & Workflows (`/api/v1/ai`)
| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/ai/chat` | Send message to AI Copilot (Supports DAG & Workflows) | Bearer JWT |
| `GET` | `/api/v1/ai/session/history` | Retrieve 10-message conversational context from Redis | Bearer JWT |
| `DELETE` | `/api/v1/ai/session` | Clear active conversation history | Bearer JWT |

### Telemetry & Analytics (`/api/v1/ai/analytics`)
| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/ai/analytics/cost` | Retrieve real-time token counts, USD spend & audit stream | Public / Admin |
| `POST` | `/api/v1/ai/analytics/cost/reset` | Reset telemetry counters and audit stream in Redis | Public / Admin |

### Vector Knowledge Base & FAQ RAG (`/api/v1/faq`)
| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/faq` | List all ingested vector document chunks | Bearer JWT |
| `POST` | `/api/v1/faq/upload` | Ingest raw text with sliding-window chunking | Bearer JWT |
| `POST` | `/api/v1/faq/upload-file` | Ingest PDF/TXT document into ChromaDB | Bearer JWT |
| `POST` | `/api/v1/faq/search` | Perform dense vector semantic search | Bearer JWT |

---

## 🧪 6-Layer Automated AI Evaluation Matrix

Run the 32-test evaluation matrix:

```bash
# Inside docker or host
make eval-ai
```

### Evaluated Layers:
1. **Layer 1: Tools** — MCP tool schema compliance & deterministic financial calculators.
2. **Layer 2: Security** — 16-digit PAN masking, CVV removal, JWT redaction, cross-account data isolation.
3. **Layer 3: RAG** — ChromaDB vector retrieval relevance and distance scores.
4. **Layer 4: Planner** — Multi-agent DAG generation (Forex + Transfer, Freeze + History).
5. **Layer 5: Workflow** — 7-Day Redis workflow engine (Init, Resume, Field Accumulation, Teardown).
6. **Layer 6: Cost** — OpenRouter pricing catalog caching, free-tier zero surcharge, and atomic Redis sync.
