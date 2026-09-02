# Project Context: Bank Core Backend Service

## Architecture & Technology Stack
- **Language**: Go 1.26
- **Framework**: Gin (`github.com/gin-gonic/gin`)
- **ORM**: GORM (`gorm.io/gorm` with `gorm.io/driver/postgres`)
- **Database Migrations**: Goose (`github.com/pressly/goose/v3`) in `migrations/`
- **Configuration**: Viper (`github.com/spf13/viper`) loading strictly from `.env`
- **Cache & Rate Limiting**: Redis Sliding Window Rate Limiter (`github.com/redis/go-redis/v9`)
- **Logging**: Grafana Loki-compatible structured JSON logging with Request ID and Trace ID propagation
- **Testing & Mocks**: Testify & Mockery (`mocks/`)
- **Authentication**: JWT HMAC-SHA256 (`github.com/golang-jwt/jwt/v5`)

## Endpoints
- `GET /health`: Service health and ORM/Rate limit status
- `POST /api/v1/auth/register`: User registration + default account creation
- `POST /api/v1/auth/login`: Issue JWT token
- `GET /api/v1/auth/me`: Authenticated profile (Protected)
- `GET /api/v1/accounts/my`: Current user checking balance & status (Protected)
- `GET /api/v1/accounts/lookup/:accountNumber`: Account owner lookup (Protected)
- `POST /api/v1/transfers`: ACID money transfer with `FOR UPDATE` row lock (Protected)
- `POST /api/v1/transfers/deposit`: Cash deposit into account (Protected)
- `GET /api/v1/transactions`: Filterable transaction history (Protected)
- `GET /api/v1/transactions/summary`: Income vs expenses category analytics (Protected)

## Database Schema
- `users`: `id UUID PK`, `email VARCHAR UNIQUE`, `password_hash`, `full_name`, `created_at`
- `accounts`: `id UUID PK`, `user_id UUID FK`, `account_number VARCHAR UNIQUE`, `balance_cents BIGINT`, `currency`, `status`
- `transactions`: `id UUID PK`, `account_id UUID FK`, `type`, `amount_cents BIGINT`, `description`, `category`, `counterparty_account_num`, `counterparty_name`, `reference_number UNIQUE`
