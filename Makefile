.PHONY: install dev test lint

install:
	pip install -e ".[dev]"

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-include '*.yaml'

lint:
	ruff check app/ tests/
	ruff format --check app/ tests/
