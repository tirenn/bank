# Tirenn Autonomous Neo-Bank: High-Level System Architecture (HLD)

This document presents the **High-Level Design (HLD)** of the **Tirenn Autonomous Neo-Banking Platform**, detailing the distributed system topology, core component responsibilities, cross-service interactions, and security boundaries.

---

## 1. High-Level System Topology

Tirenn Bank operates as a modern distributed microservices ecosystem designed for high financial throughput, strict ACID data integrity, and autonomous AI-assisted banking operations.

```mermaid
flowchart TB
    subgraph Clients ["Client Applications"]
        WebClient["Web Browser (Customer & Admin)<br/>React 19 + Tailwind CSS"]
    end

    subgraph Ingress ["API Gateway & Ingress Tier"]
        Nginx["Nginx Reverse Proxy (Port 7081)"]
        RateLimiter["Redis Sliding-Window Rate Limiter<br/>(60 req/min/IP)"]
    end

    subgraph CoreBanking ["Core Banking Microservice (Port 8082)"]
        GinAPI["Golang Gin REST API"]
        CleanArch["Clean Architecture Engine<br/>(Transfers, Accounts, Forex, Loans)"]
        ForexGateway["Decoupled Forex Gateway"]
    end

    subgraph AIService ["Autonomous AI Microservice (Port 8083)"]
        FastAPI["Python FastAPI Microservice"]
        Planner["Planner Orchestrator (DAG Engine)"]
        SubAgents["Multi-Agent Swarm<br/>(Transaction, Wealth, Security, Identity, Support)"]
        WorkflowEngine["7-Day Multi-Turn Workflow Engine"]
        CostTracker["Real-Time Token & Cost Tracker"]
        MCP["Private Model Context Protocol (MCP)"]
    end

    subgraph DataTier ["Data & Caching Layer"]
        Postgres[("PostgreSQL 16 Database<br/>• Double-Entry Ledgers<br/>• Customer Accounts & KYC<br/>• AI Model Registry")]
        RedisStore[("Redis 7 In-Memory Store<br/>• 24h Chat Context<br/>• 7-Day Workflow State<br/>• Real-Time Token Telemetry<br/>• Semantic RAG Cache")]
        ChromaStore[("ChromaDB Vector Store<br/>• Bank FAQ Knowledge Base")]
    end

    subgraph ExternalClouds ["External Cloud Providers"]
        OpenRouter["OpenRouter LLM Cloud<br/>(Cascading Free Pool + Paid Models)"]
        ForexAPI["Open Exchange Rates Public API<br/>(open.er-api.com)"]
    end

    %% Flow connections
    WebClient --> Nginx
    Nginx -->|Proxy /api/v1/auth, accounts, forex, loans| GinAPI
    Nginx -->|Proxy /api/v1/ai/chat, analytics, faq| FastAPI

    FastAPI --> RateLimiter
    RateLimiter --> RedisStore

    GinAPI --> CleanArch
    CleanArch --> ForexGateway
    ForexGateway --> ForexAPI
    ForexGateway --> RedisStore
    CleanArch --> Postgres

    FastAPI --> Planner
    Planner --> SubAgents
    SubAgents --> MCP
    SubAgents --> OpenRouter
    SubAgents --> WorkflowEngine
    SubAgents --> CostTracker
    SubAgents --> ChromaStore

    WorkflowEngine --> RedisStore
    CostTracker --> RedisStore
    MCP -->|Internal Authenticated Calls| GinAPI
```

---

## 2. Service Responsibilities & Domain Boundaries

### 2.1 Core Banking Service (`bank-core` - Golang 1.26)
* **Single Source of Truth**: Houses customer identities, accounts, cards, and the transactional ledger.
* **ACID Double-Entry Ledger**: Implements pessimistic row-level locking (`SELECT ... FOR UPDATE`) to prevent race conditions and overdrafts during peer-to-peer transfers.
* **Decoupled Forex Gateway**: Isolates external public API communication from core banking usecases, providing in-memory and Redis multi-level caching with bank spread calculation.

### 2.2 Autonomous AI Microservice (`bank-ai` - Python 3.11)
* **Planner Orchestrator (DAG Generator)**: Automatically decomposes complex multi-intent customer queries into ordered execution graphs.
* **Inter-Agent Shared Scratchpad**: Enables seamless data hand-off (e.g. converted currency amounts) between chained sub-agents in-memory.
* **7-Day Long-Running Workflow Engine**: Stores multi-day application drafts (Loans, Tier-2 KYC, Account Opening) in Redis (`workflow:<type>:<user_id>`) with an isolated 7-day TTL.
* **Real-Time Token & Cost Tracker**: Asynchronously computes token expenses against OpenRouter's live catalog with zero-cost guarantees for free models and real-time Redis telemetry.
* **ChromaDB Vector RAG**: Provides dense vector semantic search across bank policies and fee schedules with Redis answer caching.

### 2.3 Frontend Client (`bank-frontend` - React 19)
* **Customer Hub**: Balances, spending summaries, instant card freeze sliders, and financial calculators.
* **Interactive AI Action Cards**: Human-in-the-loop confirmation widgets for transfers and card lock operations.
* **Admin Telemetry Console**: Real-time token consumption KPIs, sub-agent cost distributions, and live audit stream tables.

---

## 3. High-Level Data Flows

### 3.1 Chained Multi-Agent Execution (Forex + Transfer)

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer
    participant Frontend as React Frontend
    participant AI as AI Planner Orchestrator
    participant SubAgents as Sub-Agent Swarm
    participant CoreAPI as Core Banking API
    participant Redis as Redis Cache

    Customer->>Frontend: "Convert 500 USD to EUR and prepare transfer to Sarah"
    Frontend->>AI: POST /api/v1/ai/chat (Prompt + JWT)
    
    Note over AI: 1. Decompose prompt into DAG: [WEALTH -> TRANSACTION]
    
    AI->>SubAgents: Step 1: WealthSubAgent (Fetch live forex conversion)
    SubAgents->>CoreAPI: POST /api/v1/forex/convert (500 USD -> EUR)
    CoreAPI-->>SubAgents: 431.25 EUR (Rate: 0.8625)
    SubAgents-->>AI: Record 431.25 EUR in Inter-Agent Scratchpad
    
    AI->>SubAgents: Step 2: TransactionSubAgent (Draft transfer with 431.25 EUR)
    SubAgents->>CoreAPI: GET /api/v1/beneficiaries
    CoreAPI-->>SubAgents: Found: Sarah Connor (ACC-984120)
    SubAgents-->>AI: Generated Action Card: TRANSFER_DRAFT
    
    AI->>Redis: Update Real-Time Token & Cost Telemetry
    AI-->>Frontend: Consolidated Answer + Transfer Confirmation Widget
    Frontend-->>Customer: Displays Currency Summary & 1-Click Transfer Button
```

---

### 3.2 7-Day Long-Running Workflow Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Day1_Start: Customer starts application (e.g. Loan / KYC)
    
    state "Day 1: Draft Initialization" as Day1_Start {
        Save_Redis: Store in Redis (workflow:type:user_id) with 7-Day TTL
    }

    Day1_Start --> Idle_Period: Customer closes browser / logs out

    state "Asynchronous Idle Period (1 - 5 Days)" as Idle_Period {
        Chat_Expired: 24h Chat History expires
        Workflow_Alive: 7-Day Form State remains active in Redis
    }

    Idle_Period --> Day4_Resume: Customer returns days later

    state "Day 4: Context Resumption" as Day4_Resume {
        Load_State: AI Service restores form draft and accumulates new inputs
    }

    Day4_Resume --> Completed: Final Submission (Persist to DB & purge Redis draft)
    Day4_Resume --> Cancelled: Explicit Cancellation (Purge Redis draft)

    Completed --> [*]
    Cancelled --> [*]
```

---

## 4. High-Level Security Architecture

```mermaid
flowchart LR
    subgraph Layer1 ["1. Transport & Ingress Security"]
        TLS["HTTPS / TLS Termination"]
        RateLimit["Sliding-Window Rate Limiting (60 req/min)"]
    end

    subgraph Layer2 ["2. Authentication & Isolation"]
        JWT["HMAC-SHA256 Bearer JWT Auth"]
        TenantIso["Strict Multi-Tenant Database Isolation"]
    end

    subgraph Layer3 ["3. Data Privacy & AI Guardrails"]
        PII["Automated PII Redaction (PAN, CVV, Tokens)"]
        HITL["Human-in-the-Loop Confirmation Cards"]
    end

    TLS --> RateLimit --> JWT --> TenantIso --> PII --> HITL
```

---

## 5. Verification & Testing Matrix

* **AI Evaluation Matrix (`make eval-ai`)**: **32/32 Passed (100%)** across 6 layers (Tools, Security, Vector RAG, Planner DAGs, 7-Day Workflows, and Cost Tracking).
* **Core Banking E2E Matrix (`make test-e2e`)**: **31/31 Passed (100%)** across 6 suites (Auth, ACID Ledger, Overdraft, Cards, Wealth, and Admin RBAC).
