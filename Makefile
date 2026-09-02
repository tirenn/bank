.PHONY: run-core run-ai run-frontend test-core build all clean

run-core:
	cd backend/core && go run cmd/api/main.go

run-ai:
	cd backend/ai-service && uvicorn app.main:app --port 8005 --reload

run-frontend:
	cd frontend && npm run dev

test-core:
	cd backend/core && go test -v -race ./...

build:
	cd backend/core && go build -o server.exe cmd/api/main.go
	cd frontend && npm run build
