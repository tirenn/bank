.PHONY: dev build preview lint clean compose-up compose-down compose-restart compose-logs compose-exec

# Local Node/Vite Development
dev:
	npm run dev

build:
	npm run build

preview:
	npm run preview

clean:
	rm -rf dist node_modules

# Docker Compose Management for bank-frontend
compose-up:
	docker compose -f ../docker-compose.yml up -d --build bank-frontend

compose-down:
	docker compose -f ../docker-compose.yml stop bank-frontend

compose-restart:
	docker compose -f ../docker-compose.yml restart bank-frontend

compose-logs:
	docker compose -f ../docker-compose.yml logs -f bank-frontend

compose-exec:
	docker exec -it bank-frontend sh
