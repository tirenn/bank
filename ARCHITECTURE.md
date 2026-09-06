# Tirenn Autonomous Neo-Bank: System Architecture, High-Level Design (HLD) & Low-Level Design (LLD)

This document provides the definitive, comprehensive architectural blueprint for the **Tirenn Autonomous Neo-Banking Platform**, detailing the distributed microservices topology, High-Level Design (HLD) workflows, Low-Level Design (LLD) execution pipelines, database concurrency models, and network isolation boundaries.

---

## 1. High-Level Architecture Overview (HLD)

Tirenn Bank is engineered as a zero-trust, event-driven, distributed neo-banking ecosystem designed for high-concurrency financial throughput, absolute ACID data integrity, and autonomous agentic AI operations.

![Tirenn Autonomous Neo-Bank High-Level Architecture](docs/images/tirenn_architecture.jpg)

### 1.1 Architectural Blueprint & Topology

```mermaid
flowchart TB
    subgraph ClientTier ["1. Client Tier"]
        WebClient["Web Browser (Customer & Admin)<br/>React 19 + Tailwind CSS + Vite"]
    end

    subgraph IngressTier ["2. Ingress & Security Boundary"]
        CFTunnel["Cloudflare Zero-Trust Tunnel<br/>(DDoS, WAF, SSL Termination)"]
        Nginx["Nginx Reverse Proxy<br/>Host Port: 127.0.0.1:7081"]
        RateLimiter["Redis Sliding-Window Rate Limiter<br/>(60 req/min/IP)"]
    end

    subgraph DockerNetwork ["Internal Container Network ('tirenn-net' - Bridge)"]
        direction TB

        subgraph CoreService ["Core Banking Microservice (bank-core)"]
            GinAPI["Golang 1.26 Gin REST Engine<br/>Internal Port: 8082"]
            CleanArch["Clean Domain Layer<br/>(Accounts, Transfers, KYC, Cards)"]
            ACIDLedger["Double-Entry ACID Ledger<br/>(SELECT ... FOR UPDATE Locking)"]
            ForexGateway["Decoupled Forex Engine<br/>(In-Memory & Redis Cache)"]
            MCPServer["Private Model Context Protocol (MCP)<br/>(/mcp/v1/transaction, identity, security, wealth)"]
        end

        subgraph AIService ["Autonomous AI Copilot Microservice (bank-ai)"]
            FastAPI["Python 3.11 FastAPI Engine<br/>Internal Port: 8083"]
            Guardrails["Prompt Injection Guardrail & PII Redactor"]
            Planner["DAG Planner Orchestrator<br/>(Multi-intent Task Decomposition)"]
            SubAgents["Multi-Agent Swarm<br/>• TransactionSubAgent<br/>• SecuritySubAgent<br/>• WealthSubAgent<br/>• IdentitySubAgent<br/>• SupportFaqSubAgent"]
            WorkflowEngine["7-Day Long-Running Multi-Turn Workflow State Engine"]
            CostTracker["Real-Time Token Telemetry & OpenRouter Cost Engine"]
            FallbackQueue["Multi-Model Cascading Fallback Engine<br/>(7 Active Free & Dedicated Paid Models)"]
        end

        subgraph DataLayer ["Data Persistence & Caching Tier"]
            Postgres[("PostgreSQL 16 Relational DB<br/>• General Ledgers (ACID)<br/>• Accounts & Balances<br/>• KYC & Customer Profiles<br/>• AI Model Registry (Source of Truth)")]
            RedisStore[("Redis 7 In-Memory Store<br/>• 24h Conversational Turn History<br/>• 7-Day Form Workflow State (TTL: 604,800s)<br/>• Real-Time Token Consumption Telemetry<br/>• Exact & Semantic FAQ Response Cache")]
            ChromaStore[("ChromaDB Vector Store<br/>• Vectorized Bank System Manuals<br/>• Dense Embeddings (all-MiniLM-L6-v2)")]
        end
    end

    subgraph ExternalServices ["External Cloud Services"]
        OpenRouter["OpenRouter LLM Cloud Gateway<br/>(Unified API for Gemini, LLaMA, Nemotron, Mistral)"]
        ForexAPI["Open Exchange Rates Public API<br/>(open.er-api.com)"]
    end

    %% Client and Ingress Connections
    WebClient -->|HTTPS Traffic| CFTunnel
    CFTunnel -->|Secure Tunnel Loopback| Nginx
    Nginx -->|Rate Limiting Check| RateLimiter
    RateLimiter --> RedisStore

    %% Internal Proxy Routing
    Nginx -->|"Proxy /api/v1/auth, accounts, forex, loans"| GinAPI
    Nginx -->|"Proxy /api/v1/ai/chat, models, analytics, faq"| FastAPI

    %% Core Banking Flow
    GinAPI --> CleanArch
    CleanArch --> ACIDLedger
    ACIDLedger --> Postgres
    CleanArch --> ForexGateway
    ForexGateway --> RedisStore
    ForexGateway -.->|"External Rate Pull"| ForexAPI

    %% AI Copilot Internal Flow
    FastAPI --> Guardrails
    Guardrails --> Planner
    Planner --> SubAgents
    SubAgents --> FallbackQueue
    FallbackQueue -.->|"LLM Completion Calls"| OpenRouter
    SubAgents --> ChromaStore
    SubAgents --> WorkflowEngine
    SubAgents --> CostTracker
    WorkflowEngine --> RedisStore
    CostTracker --> RedisStore
    SubAgents -->|"Internal Authenticated Tool Invocation"| MCPServer
    MCPServer --> CleanArch
```

---

## 2. Architectural Tiers & Component Responsibilities

### 2.1 Ingress & Security Isolation Tier
* **Zero-Trust Host Exposure**: Only the `bank-frontend` (Nginx) container binds to the host loopback interface (`127.0.0.1:7081`). 
* **Complete Backend Port Cloaking**: `bank-core` (port 8082) and `bank-ai` (port 8083) have **zero exposed host ports**. They communicate strictly over the internal isolated bridge network (`tirenn-net`).
* **Cloudflare Zero-Trust Integration**: Public access is channeled via Cloudflare Tunnel directly to `127.0.0.1:7081`, inheriting Cloudflare DDoS mitigation, Web Application Firewall (WAF), and automatic SSL/TLS termination.
* **Nginx Gateway Proxy**: Acts as the single entrypoint, serving production React SPA assets and reverse-proxying API calls:
  * `/api/v1/auth`, `/api/v1/accounts`, `/api/v1/transfers`, `/api/v1/forex`, `/api/v1/loans` $\rightarrow$ `http://bank-core:8082`
  * `/api/v1/ai/*` $\rightarrow$ `http://bank-ai:8083`

---

### 2.2 Core Banking Microservice (`bank-core` - Golang 1.26)
Built according to **Clean Domain Architecture** and **SOLID principles**:
* **ACID Financial Ledger Engine**: Enforces strict double-entry bookkeeping. Every fund movement creates balanced debit and credit entries.
* **Concurrency & Race Condition Defense**: Uses PostgreSQL pessimistic row-level locking (`SELECT ... FOR UPDATE`) within isolated database transactions to prevent double-spending, negative balances, and race conditions during simultaneous transfers.
* **Decoupled Forex Engine**: Provides cached multi-currency conversion (USD, EUR, GBP, JPY, SGD, AUD, CAD, IDR) with configurable bank spread margin fees (0.5% - 1.2%).
* **Private Model Context Protocol (MCP) Servers**:
  * Implements JSON-RPC 2.0 endpoints (`/mcp/v1/transaction`, `/mcp/v1/identity`, `/mcp/v1/security`, `/mcp/v1/wealth`).
  * Protected by dual-layer authorization: requires both the customer's Bearer JWT and the internal service secret (`X-Internal-MCP-Secret`).

---

### 2.3 Autonomous AI Microservice (`bank-ai` - Python 3.11)
Operates as an intelligent multi-agent banking copilot with direct tool calling and RAG capabilities:
* **Edge Security Guardrail**: Inspects all incoming customer prompts for prompt injection, jailbreak attempts, and system prompt extraction before dispatching to LLMs.
* **Planner Orchestrator (DAG Engine)**: Evaluates user intent and decomposes compound queries into ordered Directed Acyclic Graphs (e.g., *Check live conversion of 500 USD to EUR $\rightarrow$ prepare transfer of that amount to Sarah*).
* **Multi-Agent Swarm (`SubAgentRegistry`)**:
  * **`TransactionSubAgent`**: Manages real-time balance checks, transaction history streaming, and smart P2P transfer drafting.
  * **`SecuritySubAgent`**: Executes instant debit card freezing/unfreezing and custom daily spending limit slider updates.
  * **`WealthSubAgent`**: Performs real-time forex conversions, loan amortization simulations, and beneficiary management.
  * **`IdentitySubAgent`**: Retrieves customer verification levels and KYC Tier status.
  * **`SupportFaqSubAgent`**: Queries the ChromaDB vector knowledge base to provide factual, citation-backed answers regarding bank policies, fees, and rules.
* **Dual-Mode LLM Routing & Multi-Tier Fallback Pool**:
  * **Free Tier Mode**: Dynamically fetches active free models from PostgreSQL and runs sequential cascading fallback across 7 models upon rate limits or errors.
  * **Dedicated Paid Mode**: Locks execution to a customer-provided OpenRouter API key and specific paid model (disabling fallback to prevent accidental credit loss).
* **7-Day Long-Running Multi-Turn Workflow State Engine**:
  * Persists multi-step application drafts (e.g., Loan Applications, Tier-2 KYC Verification) in Redis under key `workflow:<type>:<user_id>` with a 7-day TTL (604,800 seconds).

---

### 2.4 Data Persistence & Caching Tier
* **PostgreSQL 16**: Primary relational database with ACID guarantees, foreign-key integrity, and automated Goose migrations.
* **Redis 7**: Multi-purpose high-performance memory store:
  * Sliding-window API rate limiting (60 req/min/IP).
  * 24-hour contextual chat history buffer (Redis List).
  * 7-day multi-turn workflow state storage.
  * Semantic exact-match FAQ answer cache (sub-millisecond retrieval).
  * Real-time token consumption and cost telemetry counters.
* **ChromaDB**: Lightweight, embedded vector database storing chunked bank policy manuals, fee schedules, and operational guides with dense vector embeddings (`all-MiniLM-L6-v2`).

---

## 3. High-Level Design (HLD) Operational Flows

### 3.1 End-to-End P2P Transfer Flow (ACID Ledger & Concurrency Control)

```mermaid
sequenceDiagram
    autonumber
    actor Alice as Sender (Alice)
    actor Bob as Recipient (Bob)
    participant Nginx as Ingress Nginx (7081)
    participant CoreAPI as Core Banking (8082)
    participant Postgres as PostgreSQL 16 (ACID)
    
    Alice->>Nginx: POST /api/v1/transfers {to_account: "1000000002", amount: 150.00, otp: "123456"}
    Nginx->>CoreAPI: Forward Request with Bearer JWT
    
    Note over CoreAPI: 1. Validate JWT Claims & Verify OTP (123456)
    Note over CoreAPI: 2. Begin SQL Transaction (Serializable / Read Committed)
    
    CoreAPI->>Postgres: SELECT * FROM accounts WHERE id = alice_acc FOR UPDATE
    Postgres-->>CoreAPI: Alice Account Locked (Balance: $500.00)
    
    CoreAPI->>Postgres: SELECT * FROM accounts WHERE id = bob_acc FOR UPDATE
    Postgres-->>CoreAPI: Bob Account Locked (Balance: $100.00)
    
    Note over CoreAPI: 3. Verify Balance: $500.00 >= $150.00 (Sufficient Funds)
    Note over CoreAPI: 4. Verify Daily Limit: $150.00 <= $50,000.00
    
    CoreAPI->>Postgres: UPDATE accounts SET balance = balance - 150.00 WHERE id = alice_acc
    CoreAPI->>Postgres: UPDATE accounts SET balance = balance + 150.00 WHERE id = bob_acc
    
    CoreAPI->>Postgres: INSERT INTO transactions (type: DEBIT, amount: 150.00, ref: TX-9021, status: SUCCESS)
    CoreAPI->>Postgres: INSERT INTO transactions (type: CREDIT, amount: 150.00, ref: TX-9021, status: SUCCESS)
    
    CoreAPI->>Postgres: COMMIT TRANSACTION
    Postgres-->>CoreAPI: Transaction Committed (Locks Released)
    
    CoreAPI-->>Nginx: HTTP 200 OK {status: "SUCCESS", ref: "TX-9021", new_balance: 350.00}
    Nginx-->>Alice: Render Instant Transfer Receipt & Updated Balance
```

---

### 3.2 Autonomous AI Copilot Request & Tool Calling Flow

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer
    participant Frontend as React Web Frontend
    participant Nginx as Nginx Gateway
    participant AI as AI Coordinator (FastAPI)
    participant Guardrail as Security Guardrail
    participant SubAgent as TransactionSubAgent
    participant MCP as Private MCP Server (Core)
    participant LLM as OpenRouter LLM Cloud
    participant Redis as Redis Telemetry

    Customer->>Frontend: Types: "Kirim $50 ke rekening 1000000002 untuk makan malam"
    Frontend->>Nginx: POST /api/v1/ai/chat {messages: [...]}
    Nginx->>AI: Proxy request with Bearer JWT
    
    AI->>Guardrail: Inspect Prompt (Regex + Heuristic Injection Filter)
    Guardrail-->>AI: Prompt Validated (Safe)
    
    Note over AI: Planner Orchestrator selects 'TransactionSubAgent'
    
    AI->>SubAgent: Dispatch Task with MCP Tool Definitions
    SubAgent->>LLM: Chat Completion (Prompt + Tools Schema)
    LLM-->>SubAgent: Tool Call Request: execute_transfer(to="1000000002", amount=50.0)
    
    SubAgent->>MCP: POST /mcp/v1/transaction {tool: "execute_transfer", params: {...}}
    Note over MCP: Validates X-Internal-MCP-Secret & User JWT
    MCP-->>SubAgent: Return Tool Result: ActionType="CONFIRM_TRANSFER", DraftID="DRAFT-772"
    
    SubAgent->>LLM: Formulate Final Response with Tool Observations
    LLM-->>SubAgent: "Saya telah menyiapkan draf transfer $50 ke rekening 1000000002..."
    
    AI->>Redis: Record Token Usage & Incurred Cost
    AI-->>Nginx: HTTP 200 OK {reply: "...", action_type: "CONFIRM_TRANSFER", action_data: {...}}
    Nginx-->>Frontend: Transmit Payload
    Frontend-->>Customer: Renders Chat Bubble + Interactive Transfer Card (Prompts for OTP 123456)
```

---

### 3.3 ChromaDB Vector RAG Knowledge Ingestion & Query Flow

```mermaid
flowchart LR
    subgraph Ingestion ["1. Document Ingestion Phase"]
        PDF["Tirenn Bank System Manual<br/>(tirenn_bank_system_manual.pdf)"]
        Parser["Document Parser & Text Extractor"]
        Chunker["Sliding-Window Semantic Chunker<br/>(Chunk Size: 500, Overlap: 100)"]
        Embedder["Embedding Model<br/>(all-MiniLM-L6-v2)"]
        ChromaStore[("ChromaDB Vector Store<br/>Collection: 'bank_policies'")]

        PDF --> Parser --> Chunker --> Embedder --> ChromaStore
    end

    subgraph Query ["2. Real-Time Retrieval Phase"]
        UserQ["User: 'Berapa biaya transfer wire internasional?'"]
        CacheCheck{"Exact Redis Cache Hit?"}
        RedisAnswer[("Redis FAQ Cache")]
        DenseSearch["ChromaDB Vector Similarity Search<br/>(Cosine Distance, Top-K = 3)"]
        Synthesizer["SupportFaqSubAgent<br/>Context-Augmented LLM Synthesis"]
        FinalAnswer["Factual Policy Response with Exact Citations"]

        UserQ --> CacheCheck
        CacheCheck -->|"Cache Hit"| RedisAnswer
        RedisAnswer --> FinalAnswer
        CacheCheck -->|"Cache Miss"| DenseSearch
        ChromaStore -.-> DenseSearch
        DenseSearch --> Synthesizer
        Synthesizer --> RedisAnswer
        Synthesizer --> FinalAnswer
    end
```

---

### 3.4 7-Day Long-Running Multi-Turn Workflow State Machine

```mermaid
stateDiagram-v2
    [*] --> Idle: User enters portal
    
    Idle --> Step1_Initiated: Trigger Multi-Turn Form
    
    state "Step 1: In Progress" as Step1_Initiated {
        Save_S1: Save Draft in Redis (workflow:loan:user_123, TTL 604,800s)
    }
    
    Step1_Initiated --> Interrupted: User closes browser or tab
    
    state "Asynchronous Idle Buffer" as Interrupted {
        Chat_History_Expires: 24h Chat Session Buffer Expires
        Workflow_Preserved: 7-Day Redis State remains intact with Collected Data
    }
    
    Interrupted --> Step2_Resumed: User returns within 7 days
    
    state "Step 2: Context Restoration" as Step2_Resumed {
        Restore_State: AI recovers accumulated form fields from Redis
        Prompt_Next: Prompts user for next required field
    }
    
    Step2_Resumed --> Final_Submission: User completes all required steps
    Step2_Resumed --> Cancelled: User cancels application
    
    state "Completion Phase" as Final_Submission {
        Persist_DB: Write permanently to PostgreSQL 16
        Purge_Draft: Delete draft key from Redis
    }
    
    Cancelled --> [*]: Draft cleared from Redis
    Final_Submission --> [*]: Workflow Completed Successfully
```

---

## 4. Low-Level Design (LLD) & Internal Code Execution Pipeline

The Low-Level Design (LLD) details the exact function-level execution path, concurrency controls, mutex locks, and inter-process communication protocols between Golang and Python engines:

![Tirenn Low-Level Design Flow](docs/images/tirenn_lld_flow.svg)

---

### 4.1 Detailed LLD: Core Banking ACID Transaction Pipeline (`bank-core`)

The Go backend handles financial ledger mutations through strict transactional isolation levels. The code execution flow proceeds as follows:

```
[HTTP Request]
       │
       ▼
1. Gin Engine & Routing (internal/app/router.go)
   ├── gin.Recovery()
   ├── CorsMiddleware()
   ├── RequestIDMiddleware() -> c.Set("X-Request-ID", uuid)
   └── AuthMiddleware(jwtSecret) -> extracts Claims (UserID, Email)
       │
       ▼
2. Transfer Controller (internal/handler/transfer_handler.go)
   ├── Validate JSON Payload (account_number, amount_cents, otp)
   └── Verify 2FA OTP Code (assert otp == "123456")
       │
       ▼
3. Domain Transfer Service (internal/service/transfer_service.go)
   ├── transferService.ExecuteTransfer(ctx, req)
   └── Begin Database Transaction: tx := db.Begin()
       │
       ▼
4. Pessimistic Row Locking (internal/repository/account_repository.go)
   ├── Query Sender:   SELECT * FROM accounts WHERE id = sender_id FOR UPDATE;
   └── Query Receiver: SELECT * FROM accounts WHERE id = recipient_id FOR UPDATE;
       │
       ▼
5. Invariant & Quota Checks
   ├── IF sender.Balance < amount -> tx.Rollback(); return ErrInsufficientFunds
   ├── IF sender.IsFrozen == true -> tx.Rollback(); return ErrCardFrozen
   └── IF dailyAccumulated + amount > dailyLimit -> tx.Rollback(); return ErrLimitExceeded
       │
       ▼
6. Double-Entry Mutation (internal/repository/ledger_repository.go)
   ├── UPDATE accounts SET balance = balance - amount WHERE id = sender_id;
   ├── UPDATE accounts SET balance = balance + amount WHERE id = recipient_id;
   ├── INSERT INTO transactions (type="DEBIT", amount=amount, ref=txRef);
   └── INSERT INTO transactions (type="CREDIT", amount=amount, ref=txRef);
       │
       ▼
7. Commit & Audit Emission
   ├── tx.Commit() -> Releases PostgreSQL Row Locks
   └── Return HTTP 200 OK {status: "SUCCESS", tx_ref: txRef, balance: newBalance}
```

#### Low-Level Concurrency Guarantees:
* **Deadlock Prevention**: When locking accounts in multi-party transfers, account IDs are sorted ascending (`order by id asc`) prior to executing `SELECT ... FOR UPDATE` locks. This guarantees consistent lock acquisition order and eliminates cyclic deadlocks.
* **Pessimistic vs Optimistic**: High-frequency financial accounts utilize pessimistic row locks to prevent write-skew anomalies and eliminate expensive retry loops under heavy load.

---

### 4.2 Detailed LLD: Autonomous AI Copilot ReAct & MCP Pipeline (`bank-ai`)

The Python AI service processes natural language instructions through an asynchronous multi-agent coordination loop:

```
[Client Chat Request: POST /api/v1/ai/chat]
       │
       ▼
1. Ingress & Security Inspection (app/api/v1/chat.py)
   ├── Auth Guard: extract_user_from_token(authorization_header)
   ├── Prompt Injection Inspection: prompt_injection_guardrail.py
   └── PII Redaction: pii_redactor.sanitize_prompt(prompt)
       │
       ▼
2. Caching & Workflow State Recovery (app/services/agent_service.py)
   ├── Semantic Exact Match Cache: rag_cache_service.get_cached_answer(prompt)
   │     └── If HIT: Return cached ChatResponse in < 5ms
   └── Active Workflow State: workflow_state_service.get_active_workflow(user_id)
         └── If Active: Inject accumulated form schema into context
       │
       ▼
3. Centralized Model Routing (app/services/model_fallback.py)
   ├── resolve_model_execution_plan(api_key, model_override, active_db_models)
   │     ├── Paid Mode: Dedicated model locked (Fallback disabled)
   │     └── Free Tier Mode: Cascading Fallback Queue [7 models from DB pool]
       │
       ▼
4. Intent Planning & DAG Orchestration (app/services/planner_service.py)
   ├── generate_execution_plan(messages, openai_client)
   └── Returns ExecutionPlan: {is_multistep: bool, plan: [PlanStep(domain, objective)]}
       │
       ▼
5. Sub-Agent Swarm Execution (app/services/subagents/base.py)
   ├── SubAgentRegistry.get(domain) -> Dispatches TransactionSubAgent
   ├── Model Execution Loop (Thought -> Tool Invocation -> Observation)
   │     └── If OpenRouter model errors/429 -> Cascades to next tier model in pool
       │
       ▼
6. Private JSON-RPC 2.0 MCP Client (app/repositories/mcp_repository.py)
   ├── POST http://bank-core:8082/mcp/v1/<domain>
   ├── Headers: {"X-Internal-MCP-Secret": secret, "Authorization": "Bearer " + jwt}
   ├── Payload: {"jsonrpc": "2.0", "method": "execute_transfer", "params": {...}, "id": 1}
   └── Inter-Agent Scratchpad: Accumulates tool results for downstream DAG steps
       │
       ▼
7. Telemetry & Interactive Response (app/services/cost_tracker_service.py)
   ├── Asynchronously computes token usage & records to Redis
   └── Returns ChatResponse: {
         reply: "Saya telah menyiapkan draf transfer $50...",
         action_type: "CONFIRM_TRANSFER",
         action_data: {to: "1000000002", amount: 50.0, default_otp: "123456"}
       }
```

---

## 5. Security & Network Defense-in-Depth Matrix

Tirenn Bank enforces a 6-layer defense model ensuring banking operations remain resilient against transport tampering, credential abuse, and AI jailbreak attacks:

| Security Layer | Technology / Mechanism | Description & Guarantees |
| :--- | :--- | :--- |
| **1. Edge & Transport** | Cloudflare WAF + TLS 1.3 | Encrypted transport, DDoS mitigation, rate-limiting, and geo-fencing. |
| **2. Ingress Port Cloaking** | Nginx Reverse Proxy (`127.0.0.1:7081`) | Only Nginx port 7081 binds to host loopback. All other services (`8082`, `8083`, `5432`, `6379`) have no host port exposure. |
| **3. API Rate Limiting** | Redis Sliding-Window Counter | Enforces strict threshold of 60 requests per minute per IP to prevent brute-force attacks. |
| **4. Authentication & AuthZ** | HMAC-SHA256 Bearer JWT | Cryptographically signed identity tokens validated on every incoming HTTP and internal MCP request. |
| **5. Private MCP Protocol** | `X-Internal-MCP-Secret` Header | Protects Go Core Banking MCP endpoints from unauthorized intra-container calls. |
| **6. AI Guardrails & Privacy** | Prompt Injection Filter + PII Redactor | Sanitizes PAN, CVV, and sensitive customer credentials prior to forwarding prompts to external LLMs. |

---

## 6. Verification & Automated Testing Matrix

The reliability of this distributed architecture is verified continuously via automated test suites:

* **AI Copilot Evaluation Suite (`make eval-ai`)**: **32/32 Passed (100%)**
  * Evaluates tool calling correctness, prompt injection resilience, vector RAG retrieval fidelity, Planner DAG generation, 7-day workflow state preservation, and token cost telemetry.
* **Core Banking E2E Integration Suite (`make test-e2e`)**: **31/31 Passed (100%)**
  * Evaluates customer registration, JWT lifecycle, multi-account ledger consistency, overdraft protection, card freezing toggles, forex calculators, and admin RBAC immutability.
