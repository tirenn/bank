.PHONY: run-core run-ai run-frontend test-core eval-ai eval-tools eval-security eval-rag build clean \
        compose-up compose-down compose-restart compose-logs compose-status \
        compose-core-up compose-core-logs compose-core-restart \
        compose-ai-up compose-ai-logs compose-ai-restart \
        compose-frontend-up compose-frontend-logs compose-frontend-restart

# ==============================================================================
# Local Service Development Commands
# ==============================================================================
run-core:
	cd backend/core && go run cmd/api/main.go

run-ai:
	cd backend/ai-service && uvicorn app.main:app --port 8005 --reload

run-frontend:
	cd frontend && npm run dev

test-core:
	cd backend/core && go test -v -race ./...

# ==============================================================================
# End-to-End (E2E) Non-AI Core Banking Test Suite
# ==============================================================================
test-e2e:
	docker exec bank-ai python -m tests.e2e.runner

# ==============================================================================
# AI Service Evaluation Harness (3-Layer Quality, Security & Tool Calling)
# ==============================================================================
eval-ai:
	docker exec bank-ai python -m tests.evals.runner


eval-tools:
	docker exec bank-ai python -c "import asyncio; from tests.evals.test_tool_calling import tool_evaluator; asyncio.run(tool_evaluator.eval_deterministic_tools())"

eval-security:
	docker exec bank-ai python -c "import asyncio; from tests.evals.test_security_privacy import security_evaluator; print(security_evaluator.eval_pii_redaction())"

eval-rag:
	docker exec bank-ai python -c "import asyncio; from tests.evals.test_rag_quality import rag_evaluator; asyncio.run(rag_evaluator.eval_faq_retrieval())"

# ==============================================================================
# Full Docker Compose Orchestration (All Services)
# ==============================================================================
compose-up:
	docker compose up -d --build

compose-down:
	docker compose down

compose-restart:
	docker compose restart

compose-logs:
	docker compose logs -f

compose-status:
	docker compose ps

# ==============================================================================
# Individual Service Docker Compose Commands
# ==============================================================================
compose-core-up:
	docker compose up -d --build bank-core

compose-core-restart:
	docker compose restart bank-core

compose-core-logs:
	docker compose logs -f bank-core

compose-ai-up:
	docker compose up -d --build bank-ai

compose-ai-restart:
	docker compose restart bank-ai

compose-ai-logs:
	docker compose logs -f bank-ai

compose-frontend-up:
	docker compose up -d --build bank-frontend

compose-frontend-restart:
	docker compose restart bank-frontend

compose-frontend-logs:
	docker compose logs -f bank-frontend

# ==============================================================================
# Build & Clean
# ==============================================================================
build:
	cd backend/core && go build -o server.exe cmd/api/main.go
	cd frontend && npm run build

clean:
	cd backend/core && rm -f server.exe server
	cd frontend && rm -rf dist
