# Tirenn Core Banking Microservice (`bank-core`)

High-performance, transactional Core Banking Engine written in **Golang 1.26** following Clean Architecture principles.

---

## 🌟 Key Features

* **ACID Double-Entry Financial Ledger**: Atomic P2P fund transfers with row-level pessimistic locking (`SELECT ... FOR UPDATE`) and collision-free transaction reference numbering (`-OUT` and `-IN`).
* **Multi-Account Hierarchy**: Primary Checking and Secondary Savings accounts per customer with real-time balance tracking.
* **Security & Card Governance**: Dynamic daily spending limit adjustment, one-click card freezing, and unfreezing.
* **Decoupled Live Forex Engine**: Real-time currency conversions via `open.er-api.com` with Redis & In-Memory multi-level caching and 0.25% spread calculation.
* **Financial Calculators**: Standard compound loan amortization simulator for mortgages, auto loans, and personal loans.
* **Role-Based Authentication**: Secure JWT generation and bcrypt password hashing.

---

## 🛠️ Environment Variables Configuration

Copy `.env.example` to `.env` or configure via Docker Compose:

```ini
PORT=8085
ENVIRONMENT=development

# Database Connection (PostgreSQL 16)
DB_HOST=bank-postgres
DB_PORT=5432
DB_USER=bankadmin
DB_PASSWORD=bankpassword123
DB_NAME=bankdb
DB_SSLMODE=disable

# Distributed Cache (Redis 7)
REDIS_URL=redis://bank-redis:6379/0

# Security & Tokens
JWT_SECRET=super-secret-production-grade-hmac-sha256-key-32chars

# External Forex API Gateway
FOREX_API_URL=https://open.er-api.com/v6/latest/USD
```

---

## 🚀 API Endpoint Reference

### Authentication & Customer Identity (`/api/v1/auth`)
| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register new customer & auto-provision account | Public |
| `POST` | `/api/v1/auth/login` | Authenticate customer & issue JWT token | Public |
| `GET` | `/api/v1/auth/profile` | Retrieve customer identity and accounts | Bearer JWT |
| `PUT` | `/api/v1/auth/address` | Update customer residential address | Bearer JWT |

### Accounts, Cards & Ledger (`/api/v1/accounts` & `/api/v1/transactions`)
| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/accounts/me` | List customer's primary & secondary accounts | Bearer JWT |
| `POST` | `/api/v1/accounts` | Open a secondary savings account | Bearer JWT |
| `POST` | `/api/v1/accounts/deposit` | Deposit funds into specified account | Bearer JWT |
| `PUT` | `/api/v1/accounts/limits` | Update daily transfer limits | Bearer JWT |
| `PUT` | `/api/v1/accounts/status` | Freeze or unfreeze debit card | Bearer JWT |
| `POST` | `/api/v1/transactions/transfer` | Execute atomic P2P fund transfer | Bearer JWT |
| `GET` | `/api/v1/transactions/history` | Stream transaction ledger history | Bearer JWT |
| `GET` | `/api/v1/transactions/summary` | Retrieve categorized spending summary | Bearer JWT |
| `POST` | `/api/v1/accounts/statements` | Generate PDF/JSON bank statement | Bearer JWT |

### Wealth & Beneficiaries (`/api/v1/beneficiaries`, `/api/v1/forex`, `/api/v1/loans`)
| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/beneficiaries` | List saved transfer payees | Bearer JWT |
| `POST` | `/api/v1/beneficiaries` | Add new trusted beneficiary | Bearer JWT |
| `DELETE` | `/api/v1/beneficiaries/:id` | Delete trusted beneficiary | Bearer JWT |
| `POST` | `/api/v1/forex/convert` | Live currency conversion with spread | Public / JWT |
| `POST` | `/api/v1/loans/calculate` | Loan amortization simulation | Public / JWT |

### Administrative Registry (`/api/v1/admin`)
| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/admin/models` | List system AI models & priority order | Admin JWT |

---

## 🧪 Development & Testing

```bash
# Run standalone Go unit and integration tests
go test -v ./...

# Run full Core Banking E2E Integration Suite (31 test cases)
make test-e2e
```
