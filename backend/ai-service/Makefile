.PHONY: run test lint eval-ai compose-up compose-down compose-restart compose-logs compose-exec

# Local Python Development
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload

test:
	pytest -v

eval-ai:
	python -m tests.evals.runner

lint:
	flake8 app/

# Docker Compose Management for bank-ai
compose-up:
	docker compose -f ../../docker-compose.yml up -d --build bank-ai

compose-down:
	docker compose -f ../../docker-compose.yml stop bank-ai

compose-restart:
	docker compose -f ../../docker-compose.yml restart bank-ai

compose-logs:
	docker compose -f ../../docker-compose.yml logs -f bank-ai

compose-exec:
	docker exec -it bank-ai /bin/bash
