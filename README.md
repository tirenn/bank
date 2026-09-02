# Tirenn Digital Banking & AI Assistant Platform

An enterprise-grade Full-Stack Banking Application featuring a high-performance **Go (Golang)** Core Banking backend, a **Python (FastAPI)** AI Microservice with **OpenRouter Free LLM** tool calling and **ChromaDB Vector RAG**, using the unified infrastructure in `Projects/infra` (**PostgreSQL** & **ChromaDB**), and a modern **React (Vite) + Tailwind CSS** banking dashboard.

---

## 🏛️ Architecture Overview

```
Projects/
├── infra/                  # Shared Infrastructure Stack
│   ├── PostgreSQL          # Port 5432 (User: postgres_user111, DB: bank_db)
│   └── ChromaDB            # Port 8002 (Vector RAG Knowledge Base)
│
└── bank/
    ├── backend/
    │   ├── core/           # Go REST API (Auth, Accounts, ACID Transfers, Ledger) (:8085)
    │   └── ai-service/     # Python FastAPI (OpenRouter LLMs, Tool Engine, RAG FAQ) (:8005)
    └── frontend/           # React 18 + Vite + Tailwind CSS Dashboard (:5173)
```

---

## 🚀 Quick Start Guide

### 1. Ensure Infrastructure is Running (`Projects/infra`)
```bash
cd ../infra
docker compose up -d
```
* **PostgreSQL:** `localhost:5432` (User: `postgres_user111`, Password: `password123!!!`, DB: `bank_db`)
* **ChromaDB:** `localhost:8002`

---

### 2. Start Go Core Banking Backend
```bash
cd backend/core
go run cmd/api/main.go
```
* Runs on: `http://localhost:8085`
* Automatically connects to `postgres://postgres_user111:password123!!!@localhost:5432/bank_db?sslmode=disable` and seeds demo accounts.

#### Demo User Credentials:
* **User 1:** `john.doe@bank.com` | `password123` (Account: `ACC-10029384`, Balance: `$12,540.50`)
* **User 2:** `sarah.smith@bank.com` | `password123` (Account: `ACC-83920194`, Balance: `$4,820.00`)
* **User 3:** `alice.johnson@bank.com` | `password123` (Account: `ACC-54910283`, Balance: `$8,900.00`)

---

### 3. Start Python AI Microservice
```bash
cd backend/ai-service
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8005 --reload
```
* Runs on: `http://localhost:8005`
* Connected to ChromaDB on port `8002` and Go Core API on port `8085`.
* Optional: Add your `OPENROUTER_API_KEY` in `backend/ai-service/.env` or in the frontend UI settings.

---

### 4. Start React Frontend
```bash
cd frontend
npm install
npm run dev
```
* Accessible at: `http://localhost:5173`
