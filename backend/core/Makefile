.PHONY: run build test migrate-up migrate-down reset-db clean compose-up compose-down compose-restart compose-logs compose-exec

# Local Go Development
run:
	go run cmd/api/main.go

build:
	go build -o server.exe cmd/api/main.go

test:
	go test -v -race ./...

test-e2e:
	docker exec bank-ai python -m tests.e2e.runner


migrate-up:
	go run github.com/pressly/goose/v3/cmd/goose -dir migrations postgres "postgres://postgres_user111:password123!!!@localhost:5432/bank_db?sslmode=disable" up

migrate-down:
	go run github.com/pressly/goose/v3/cmd/goose -dir migrations postgres "postgres://postgres_user111:password123!!!@localhost:5432/bank_db?sslmode=disable" down

reset-db: migrate-down migrate-up

clean:
	rm -f server.exe server

# Docker Compose Management for bank-core
compose-up:
	docker compose -f ../../docker-compose.yml up -d --build bank-core

compose-down:
	docker compose -f ../../docker-compose.yml stop bank-core

compose-restart:
	docker compose -f ../../docker-compose.yml restart bank-core

compose-logs:
	docker compose -f ../../docker-compose.yml logs -f bank-core

compose-exec:
	docker exec -it bank-core sh
