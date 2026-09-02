# Tirenn Autonomous Neo-Bank: System Architecture & Design Specification

This document provides a comprehensive, end-to-end architectural specification of **Tirenn Bank**, covering high-level system topology, domain boundaries, cross-cutting concerns, distributed data flows, security mechanisms, and low-level component interactions.

---

## 1. High-Level System Topology & Network Architecture

Tirenn Bank is designed as a distributed, decoupled multi-service system comprising:
1. **Core Banking Engine (`bank-core`)**: A high-performance Golang transactional ledger microservice implementing Clean/Hexagonal Architecture, ACID compliance, JWT authentication, role-based access control (RBAC), and external financial gateway integration.
2. **Autonomous AI Microservice (`bank-ai`)**: A Python FastAPI service implementing an Autonomous Planner Orchestrator, Private Model Context Protocol (MCP) server, ReAct reasoning harnesses, ChromaDB vector retrieval-augmented generation (RAG), a 7-day multi-turn workflow engine in Redis, and a dynamic LLM token/cost tracking engine.
3. **Frontend Client Application (`bank-frontend`)**: A React 19 single-page application built with Vite and Tailwind CSS, featuring glassmorphism aesthetics, interactive AI action cards, customer financial dashboards, and administrative telemetry control panels.
4. **Data & Infrastructure Backbone**:
   - **PostgreSQL 16**: Primary relational storage for accounts, ACID transactions, users, beneficiaries, and immutable AI model registries.
   - **Redis 7 (Alpine)**: Distributed high-speed cache for sliding-window rate limiting, semantic RAG query caching, 24-hour conversational history, 7-day multi-turn workflow state, and atomic token/cost telemetry counters.
   - **ChromaDB**: High-dimensional vector database for banking FAQ semantic retrieval and dynamic document embeddings.

```mermaid
flowchart TB
    subgraph Users ["🌐 Client Devices & Endpoints"]
        CustomerBrowser["👤 Customer Browser<br/>(Desktop / Mobile)"]
        AdminBrowser["👨‍💼 Admin Console<br/>(Telemetry & Vector RAG)"]
    end

    subgraph PresentationTier ["🎨 Presentation Tier (Port 5173)"]
        FrontendSPA["React 19 SPA (Vite + Tailwind)<br/>Glassmorphism UI System"]
        NginxServer["Nginx 1.25 Alpine Web Server<br/>SPA Static Router & Reverse Proxy"]
        CustomerBrowser --> FrontendSPA
        AdminBrowser --> FrontendSPA
        FrontendSPA --- NginxServer
    end

    subgraph SecurityGateways ["🛡️ Ingress & Security Filters"]
        RateLimiter["Redis Sliding Window Rate Limiter<br/>60 Requests / Minute / IP"]
        PIIFilter["Automated PII Scrubber & Masker<br/>Regex PAN, CVV, JWT, Passwords"]
    end

    subgraph CoreBankingService ["⚙️ Core Banking Engine (Golang 1.26 - Port 8085)"]
        GinRouter["Gin HTTP REST Router"]
        JWTAuthMiddleware["JWT HMAC-SHA256 Auth Middleware"]
        
        subgraph CoreDomainServices ["Domain Usecases & Rules"]
            TransferSvc["Transfer Service<br/>(ACID Double-Entry)"]
            AccountSvc["Account Service<br/>(Multi-Account Tree)"]
            ForexSvc["Forex Service<br/>(0.25% Spread Markup)"]
            LoanSvc["Loan Amortization<br/>(Compound Math)"]
        end

        subgraph CoreGateways ["Infrastructure Gateways"]
            ForexGW["Forex Gateway<br/>(RWMutex + Redis Cache)"]
            GORMRepositories["GORM Repositories<br/>(Row-Level Pessimistic Locking)"]
        end
    end

    subgraph AIServiceMicroservice ["🤖 Autonomous AI Microservice (Python 3.11 - Port 8005)"]
        FastAPIRouter["FastAPI Async Router"]
        
        subgraph OrchestrationEngine ["Supervisor & DAG Planning"]
            PlannerDAG["Supervisor Planner Orchestrator<br/>(DAG Plan Generator)"]
            Scratchpad["Inter-Agent Shared Scratchpad<br/>(In-Memory Blackboard Context)"]
        end

        subgraph MultiAgentSwarm ["Specialized Sub-Agent Domain Pool"]
            TxAgent["TransactionSubAgent"]
            WltAgent["WealthSubAgent"]
            SecAgent["SecuritySubAgent"]
            IdAgent["IdentitySubAgent"]
            FaqAgent["SupportFaqSubAgent"]
        end

        subgraph EnginesAndHarness ["Execution Engines & Telemetry"]
            ReActLoop["ReAct Reasoning Harness<br/>(Multi-Turn Tool Invocations)"]
            WorkflowState["7-Day Workflow State Engine<br/>(Redis workflow:type:user_id)"]
            CostTracker["Real-Time Token & Cost Tracker<br/>(OpenRouter Live Pricing)"]
            MCPBridge["Private Model Context Protocol (MCP)<br/>(15 Typed Financial Tools)"]
        end
    end

    subgraph PersistenceTier ["💾 Data & Storage Backbone"]
        PostgresDB[("🐘 PostgreSQL 16 DB<br/>• Accounts & Ledgers<br/>• Users & Cards<br/>• AI Model Registry")]
        RedisDB[("⚡ Redis 7 Alpine Store<br/>• 24h Chat History<br/>• 7-Day Workflow State<br/>• Atomic Cost Metrics<br/>• RAG Cache & Rate Limits")]
        ChromaVectorDB[("🔮 ChromaDB Vector Store<br/>• Banking FAQ Embeddings<br/>• all-MiniLM-L6-v2 (384-d)")]
    end

    subgraph ExternalProviders ["🌍 External APIs & Cloud"]
        OpenRouterAPI["🌐 OpenRouter LLM Cloud<br/>(Free Tier Fallback Pool + Dynamic Pricing)"]
        PublicForexAPI["💱 Open Exchange Rates API<br/>(open.er-api.com)"]
    end

    %% Network Connections
    NginxServer -->|HTTP REST: /api/v1/auth, accounts, forex, loans| GinRouter
    NginxServer -->|HTTP REST: /api/v1/ai/chat, analytics, faq| FastAPIRouter

    FastAPIRouter --> RateLimiter
    FastAPIRouter --> PIIFilter
    RateLimiter --> RedisDB

    GinRouter --> JWTAuthMiddleware
    JWTAuthMiddleware --> CoreDomainServices
    TransferSvc --> GORMRepositories
    AccountSvc --> GORMRepositories
    ForexSvc --> ForexGW
    ForexGW --> PublicForexAPI
    ForexGW --> RedisDB
    GORMRepositories -->|ACID tx.Begin / Row Lock| PostgresDB

    PIIFilter --> PlannerDAG
    PlannerDAG --> Scratchpad
    PlannerDAG --> MultiAgentSwarm
    MultiAgentSwarm --> ReActLoop
    ReActLoop --> MCPBridge
    ReActLoop --> OpenRouterAPI
    ReActLoop --> WorkflowState
    ReActLoop --> CostTracker
    CostTracker --> RedisDB
    WorkflowState --> RedisDB
    MCPBridge -->|Internal HTTP Call with Bearer Token| GinRouter
    FaqAgent --> ChromaVectorDB
```

---

## 2. Core Service Boundaries & Clean Architecture

### 2.1 Core Banking Engine (`backend/core`)
The Core Banking Engine strictly adheres to **Clean Architecture / Hexagonal Architecture** with four distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Enterprise Domain Entities (internal/domain)            │
│    • Pure Go structs: User, Account, Transaction, Beneficiary│
│    • Domain Interfaces: UserRepository, AccountRepository,  │
│      ForexRateProvider, TransactionRepository               │
├─────────────────────────────────────────────────────────────┤
│ 2. Application Use Cases (internal/service)                 │
│    • Business Rules: TransferService, AccountService,       │
│      ForexService, LoanService, AuthService                 │
│    • Pure domain logic: zero direct network/HTTP dependencies│
├─────────────────────────────────────────────────────────────┤
│ 3. Infrastructure & Gateways (internal/gateway, repository) │
│    • GORM PostgreSQL Repositories with ACID row-locking     │
│    • ForexGateway: HTTP client, Redis cache & fallback rates│
├─────────────────────────────────────────────────────────────┤
│ 4. Delivery & Transport (internal/handler, internal/app)    │
│    • Gin REST HTTP Handlers, JWT Middleware, RequestID, CORS│
│    • Dependency Injection Container (app.go)                │
└─────────────────────────────────────────────────────────────┘
```

#### Key Design Patterns in `bank-core`:
* **Dependency Inversion Principle (DIP)**: Services depend exclusively on domain abstractions (interfaces), never on concrete repository or external HTTP implementations.
* **ACID Double-Entry Ledger**: Funds transfers execute inside atomic PostgreSQL transactions (`tx.Begin()`) utilizing row-level pessimistic locking (`SELECT ... FOR UPDATE`) to guarantee absolute consistency under concurrent load.
* **Deterministic Transaction Reference Tagging**: Transfers generate paired transaction records with `-OUT` (debit) and `-IN` (credit) suffixes to ensure unique idempotency keys.
* **Multi-Level Forex Caching**: The `ForexGateway` combines in-memory read-write mutex locks (`sync.RWMutex`, 15-minute TTL) and distributed Redis caching (`forex:rates:usd`, 1-hour TTL) before calling external APIs.

---

### 2.2 Autonomous AI Microservice (`backend/ai-service`)
The AI Service is structured around **Domain-Driven Multi-Agent Systems** and **Autonomous Graph Planning**:

```mermaid
flowchart TD
    UserQuery[Customer Chat Inquiry] --> PII[PII Sanitizer & Redactor]
    PII --> CacheCheck{Redis Exact & Semantic Cache?}
    CacheCheck -- Hit (0-4ms) --> ReturnCache[Instant Cached Response]
    CacheCheck -- Miss --> Supervisor[Supervisor Planner Orchestrator]

    Supervisor --> PlanGen[Generate Execution Plan DAG JSON]
    PlanGen --> IsMulti{Is Multi-Step Plan?}

    IsMulti -- No (Single Step) --> FastPath[Single Sub-Agent Fast Path]
    IsMulti -- Yes (Multi-Step) --> ChainedLoop[Chained Sequential Execution Loop]

    ChainedLoop --> Step1[Step 1: Execute First Sub-Agent]
    Step1 --> RecordScratchpad[Record Output in Inter-Agent Scratchpad]
    RecordScratchpad --> Step2[Step 2: Inject Scratchpad Context & Execute Next Sub-Agent]
    Step2 --> Synthesize[Synthesize Consolidated Response]

    FastPath --> ReActHarness[ReAct Reasoning Loop Harness]
    Synthesize --> ReturnResponse[Return ChatResponse + Action Card]
    ReActHarness --> ReturnResponse

    subgraph Telemetry & State Layer
        WorkflowState[7-Day Workflow State Engine in Redis]
        CostTelemetry[Real-Time Token & Dynamic Pricing Tracker]
    end

    ReActHarness -.-> WorkflowState
    ReActHarness -.-> CostTelemetry
```

---

## 3. Data Flow & Sequence Diagrams

### 3.1 Chained Multi-Agent Execution Flow (Forex + Transfer)

```mermaid
sequenceDiagram
    autonumber
    actor Customer as 👤 Customer
    participant UI as 📱 React Copilot UI
    participant Planner as 🗺️ Planner Orchestrator
    participant WLT as 💎 WealthSubAgent
    participant Scratchpad as 📋 Shared Scratchpad
    participant TX as 💳 TransactionSubAgent
    participant MCP as 🔌 Private MCP Server
    participant Core as ⚙️ Core Banking API
    participant Cost as 💰 Cost Tracker

    Customer->>UI: "Convert 500 USD to EUR then transfer to Sarah"
    UI->>Planner: POST /api/v1/ai/chat (Prompt + JWT)
    
    rect rgb(30, 41, 59)
    Note over Planner: 1. Generate Structured Execution Plan (DAG)
    Planner->>Planner: Plan: [Step 1: WEALTH (Forex), Step 2: TRANSACTION (Transfer)]
    end

    rect rgb(15, 23, 42)
    Note over WLT,Core: Step 1: Execute WealthSubAgent
    Planner->>WLT: Execute Step 1 (Objective: Convert 500 USD to EUR)
    WLT->>MCP: Call Tool: convert_currency(from: "USD", to: "EUR", amount: 500)
    MCP->>Core: POST /api/v1/forex/convert
    Core-->>MCP: 200 OK -> 431.25 EUR (Rate: 0.8625)
    MCP-->>WLT: Observation: 431.25 EUR
    WLT-->>Planner: Response: "500 USD successfully converted to 431.25 EUR"
    Planner->>Scratchpad: Store: { converted_amount: 431.25, currency: "EUR" }
    end

    rect rgb(23, 37, 84)
    Note over TX,Core: Step 2: Execute TransactionSubAgent (Using Step 1 Output)
    Planner->>TX: Execute Step 2 (Enriched with Scratchpad: 431.25 EUR)
    TX->>MCP: Call Tool: get_beneficiaries()
    MCP->>Core: GET /api/v1/beneficiaries
    Core-->>MCP: Found: Sarah Connor (Account: ACC-984120)
    TX-->>Planner: Generated Action: TRANSFER_DRAFT (431.25 EUR to ACC-984120)
    end

    Planner->>Cost: Record Usage (Tokens & Cost in USD)
    Planner-->>UI: Consolidated Reply + Interactive Confirmation Action Card
    UI-->>Customer: Displays Currency Summary & 1-Click Transfer Confirmation
```

---

## 4. Long-Running Multi-Turn Workflow State Engine (7-Day TTL)

```mermaid
stateDiagram-v2
    [*] --> Day1_Start: User: "I want to apply for a $35,000 loan"
    
    state "Day 1: Draft Initialization" as Day1_Start {
        AI_Detect: AI Service detects intent LOAN_APPLICATION
        Save_Redis_S1: Save to Redis (workflow:loan_application:user_123)
        Set_TTL: Set TTL = 7 Days (604,800 seconds)
        AI_Detect --> Save_Redis_S1
        Save_Redis_S1 --> Set_TTL
    }

    Day1_Start --> Sleep: Customer closes browser / logs out

    state "Asynchronous Idle Period (1 - 5 Days)" as Sleep {
        ChatHistory: Daily Chat History expires after 24 Hours
        WorkflowAlive: Loan Application Draft Remains Active in Redis (7-Day TTL)
    }

    Sleep --> Day4_Resume: 3 Days Later User Logs In: "Continue my loan application, my income is $7,500"

    state "Day 4: Context Resumption" as Day4_Resume {
        Check_Key: AI Service reads key workflow:loan_application:user_123
        Load_Step1: Load Step 1 State ($35,000 / 36 months)
        Accumulate_Step2: Merge Income $7,500 -> Advance to Step 2/4
        Check_Key --> Load_Step1
        Load_Step1 --> Accumulate_Step2
    }

    Day4_Resume --> User_Decision: Customer decides final action

    state User_Decision <<choice>>
    User_Decision --> Complete_Form: User: "Submit Application"
    User_Decision --> Cancel_Form: User: "Cancel Application"

    state "Finalization & Cleanup" as Complete_Form {
        Submit_Postgres: Application persisted to Core Banking Database
        Purge_Draft: Delete workflow draft key from Redis
        Submit_Postgres --> Purge_Draft
    }

    state "Cancellation" as Cancel_Form {
        Purge_All: Delete draft form & active pointer from Redis
    }

    Complete_Form --> [*]: Loan Application Approved
    Cancel_Form --> [*]: Draft Cleared
```

---

## 5. Real-Time Token & Dynamic Pricing Architecture

```mermaid
flowchart LR
    subgraph Trigger ["LLM Completion Trigger"]
        LLMResp["OpenRouter Completion Response"]
    end

    subgraph Extractor ["Extraction & Pricing Engine"]
        Usage["Extract response.usage<br/>(Prompt Tokens & Completion Tokens)"]
        Catalog["OpenRouter Pricing Catalog<br/>(Cached in Redis: 423 Models)"]
        Calculator{"Check Model Type"}
    end

    subgraph PricingLogic ["Cost Calculation Logic"]
        FreeTier["Model :free<br/>Cost = $0.000000 USD"]
        PaidTier["Commercial Models (GPT-4o, Claude 3.5)<br/>Cost = (Prompt × In_Rate) + (Output × Out_Rate)"]
    end

    subgraph RedisAggregator ["Redis Real-Time Telemetry Store"]
        TotalUSD["HINCRBYFLOAT cost:summary total_usd"]
        TotalTokens["HINCRBY cost:summary total_tokens"]
        DomainCost["HINCRBYFLOAT cost:by_domain:usd <DOMAIN>"]
        AuditStream["LPUSH cost:stream (Last 50 Records)"]
    end

    subgraph AdminUI ["Admin Control Dashboard"]
        KPICards["Live Scorecards (USD Spend & Token Counts)"]
        DomainBreakdown["Sub-Agent Distribution Badges"]
        LiveAuditTable["Live Real-Time Audit Stream Table"]
    end

    LLMResp --> Usage
    Usage --> Calculator
    Catalog --> Calculator
    Calculator -- Slug contains ':free' --> FreeTier
    Calculator -- Paid Model Slug --> PaidTier

    FreeTier --> TotalUSD
    PaidTier --> TotalUSD
    FreeTier --> TotalTokens
    PaidTier --> TotalTokens
    FreeTier --> DomainCost
    PaidTier --> DomainCost
    FreeTier --> AuditStream
    PaidTier --> AuditStream

    TotalUSD -.-> KPICards
    TotalTokens -.-> KPICards
    DomainCost -.-> DomainBreakdown
    AuditStream -.-> LiveAuditTable
```

---

## 6. Core Banking ACID Ledger & Row Locking Flow

```mermaid
flowchart TD
    StartTx["POST /api/v1/transactions/transfer<br/>(Sender: Alice, Recipient: Bob, Amount: $200)"]
    
    subgraph DBTx ["Atomic PostgreSQL Transaction: tx.Begin()"]
        LockSender["1. SELECT * FROM accounts WHERE id = alice_id FOR UPDATE<br/>(Locks Alice row, prevents concurrent race conditions)"]
        CheckBalance{"2. Is Alice Balance >= $200?"}
        
        OverdraftError["3a. Rollback Transaction (tx.Rollback)<br/>Return HTTP 400 Insufficient Funds"]
        
        DeductSender["3b. Deduct Alice Balance ($1,500 - $200 = $1,300)"]
        LockRecipient["4. SELECT * FROM accounts WHERE id = bob_id FOR UPDATE<br/>(Locks Bob row)"]
        CreditRecipient["5. Credit Bob Balance ($500 + $200 = $700)"]
        
        CreateSenderLog["6. Insert Transaction Record (Alice):<br/>• ref_number: TX-9841-OUT<br/>• amount: -$200.00"]
        CreateRecipientLog["7. Insert Transaction Record (Bob):<br/>• ref_number: TX-9841-IN<br/>• amount: +$200.00"]
        
        CommitTx["8. Commit Transaction (tx.Commit)<br/>(Releases row locks, persists state atomically)"]
    end

    SuccessResponse["Return HTTP 200 OK<br/>Transfer Successful & Balances Synced"]

    StartTx --> LockSender
    LockSender --> CheckBalance
    CheckBalance -- Insufficient Balance --> OverdraftError
    CheckBalance -- Sufficient Balance --> DeductSender
    DeductSender --> LockRecipient
    LockRecipient --> CreditRecipient
    CreditRecipient --> CreateSenderLog
    CreateSenderLog --> CreateRecipientLog
    CreateRecipientLog --> CommitTx
    CommitTx --> SuccessResponse
```

---

## 7. Security Architecture & Boundary Isolation

1. **Defense-in-Depth Authentication**: Every core banking endpoint requires a cryptographically signed HMAC-SHA256 JWT Bearer token with expiration verification.
2. **Multi-Tenant Account Isolation**: Database queries strictly enforce `WHERE user_id = ?`. Cross-account lookups return HTTP 403 / 404.
3. **Automated PII Masking & Redaction**: Inbound prompts and outbound completions pass through regex filters in `pii_redactor.py` (PANs masked to `•••• •••• •••• 1234`, CVVs to `[CVV_REDACTED]`, JWTs to `[AUTH_TOKEN_REDACTED]`).
4. **Human-in-the-Loop Financial Guardrail**: Sub-Agents produce structured `TRANSFER_DRAFT` cards requiring explicit customer approval on the frontend before funds move.
5. **Rate Limiting**: Distributed sliding-window rate limiting in Redis restricts traffic to 60 requests per minute.

---

## 8. Automated Verification Matrix

1. **AI Evaluation Matrix (`make eval-ai`)**: 32/32 Test Cases Passed (100.0%) across 6 layers (Tools, Security, Vector RAG, Planner Orchestrator DAGs, 7-Day Workflow State, and Dynamic Cost Tracker).
2. **Core Banking E2E Matrix (`make test-e2e`)**: 31/31 Test Cases Passed (100.0%) across 6 suites (Auth, ACID Ledger, Overdraft, Cards, Wealth, and Admin RBAC).
