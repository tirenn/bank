.PHONY: run build test migrate-up migrate-down seed reset-db clean

run:
	go run cmd/api/main.go

build:
	go build -o server.exe cmd/api/main.go

test:
	go test -v -race ./...

migrate-up:
	go run github.com/pressly/goose/v3/cmd/goose -dir migrations postgres "postgres://postgres_user111:password123!!!@localhost:5432/bank_db?sslmode=disable" up

migrate-down:
	go run github.com/pressly/goose/v3/cmd/goose -dir migrations postgres "postgres://postgres_user111:password123!!!@localhost:5432/bank_db?sslmode=disable" down

reset-db: migrate-down migrate-up

clean:
	rm -f server.exe server
