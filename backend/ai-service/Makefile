.PHONY: run test lint

run:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest -v

lint:
	flake8 app/
