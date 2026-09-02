# Tirenn Core Banking Engine (`bank-core`): High-Level Architecture (HLD)

This document provides the **High-Level Design (HLD)** of the **Tirenn Core Banking Engine (`bank-core`)**, written in **Golang 1.26** following Clean Architecture principles.

---

## 1. Clean Architecture Layers

`bank-core` enforces strict decoupling of business rules from transport and infrastructure:

```mermaid
flowchart TD
    subgraph DeliveryLayer ["1. Delivery Layer (Gin Handlers)"]
        HTTPHandlers["REST HTTP Controllers<br/>• Auth, Accounts, Transfers, Forex, Loans, Admin"]
        Middleware["Middlewares: JWT Auth, RequestID, CORS"]
    end

    subgraph ServiceLayer ["2. Use Case / Service Layer"]
        TransferService["Transfer Service (ACID Ledger Rules)"]
        AccountService["Account & Limit Management"]
        ForexService["Forex Service (Spread Calculations)"]
        LoanService["Loan Service (Amortization Formulas)"]
    end

    subgraph DomainLayer ["3. Domain Entity & Port Layer"]
        DomainModels["Domain Entities (User, Account, Transaction, Beneficiary)"]
        DomainPorts["Port Interfaces (Repositories & Rate Provider)"]
    end

    subgraph InfraLayer ["4. Infrastructure & Gateways"]
        GORMRepo["GORM PostgreSQL Repositories (ACID Transactions)"]
        ForexGW["Forex Gateway (Multi-Tier Caching & External API)"]
    end

    HTTPHandlers --> Middleware
    Middleware --> ServiceLayer
    ServiceLayer --> DomainPorts
    DomainPorts -.-> DomainModels
    GORMRepo -.->|Implements| DomainPorts
    ForexGW -.->|Implements| DomainPorts
```

---

## 2. Core Subsystems

### 2.1 ACID Double-Entry Transaction Ledger
* **Atomic Fund Transfers**: Uses database transactions (`tx.Begin()`) with row-level pessimistic locking (`SELECT ... FOR UPDATE`) to prevent race conditions and overdrafts.
* **Paired Idempotency References**: Generates debit (`-OUT`) and credit (`-IN`) records per transfer to guarantee unique auditability.

```mermaid
flowchart LR
    TransferReq["Transfer Request ($200)"] --> LockSender["Lock Sender (Alice)"]
    LockSender --> CheckBalance{"Sufficient Balance?"}
    CheckBalance -- "No" --> Rollback["Rollback (HTTP 400)"]
    CheckBalance -- "Yes" --> Deduct["Deduct Alice (-$200)"]
    Deduct --> LockRecipient["Lock Recipient (Bob)"]
    LockRecipient --> Credit["Credit Bob (+$200)"]
    Credit --> Commit["Commit Transaction (tx.Commit)"]
```

### 2.2 Decoupled Forex Gateway
* Isolates the usecase from external network HTTP calls.
* Combines **In-Memory Cache** (`sync.RWMutex`, 15-minute TTL) and **Redis Cache** (`forex:rates:usd`, 1-hour TTL) with automated fallback.

### 2.3 Financial Calculators & Security
* **Compound Loan Amortization**: Simulates monthly payments for Mortgages, Auto, and Personal loans.
* **Role-Based Access Control**: HMAC-SHA256 JWT tokens with role separation (`ROLE_CUSTOMER` and `ROLE_ADMIN`).
