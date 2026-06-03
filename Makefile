.PHONY: install dev test lint

install:
	pip3 install -e ".[dev]"

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload --reload-include '*.yaml'