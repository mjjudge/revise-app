SHELL := /bin/bash

.PHONY: help init env-up env-down build build-backend restart logs test lint fmt backup restore

help:
	@echo "Targets:"
	@echo "  init            Create local folders for data/logs"
	@echo "  env-up          Start stack (backend + caddy)"
	@echo "  env-down        Stop stack"
	@echo "  build           Build containers"
	@echo "  build-backend   Build backend container only"
	@echo "  restart         Restart stack"
	@echo "  logs            Follow logs"
	@echo "  test            Run backend + frontend tests"
	@echo "  lint            Run ruff"
	@echo "  fmt             Format with ruff (safe)"
	@echo "  backup          Create timestamped backup to ./backups (ignored by git)"
	@echo "  restore         Restore latest backup into ./data (DANGEROUS)"

init:
	mkdir -p data logs backups

build:
	docker compose build

build-backend:
	docker compose build app

env-up: init
	docker compose up -d

env-down:
	docker compose down

restart:
	docker compose down
	docker compose build
	docker compose up -d

logs:
	docker compose logs -f --tail=200

test:
	docker compose run --rm app uv run --extra dev pytest
	cd frontend && npm test

lint:
	docker compose run --rm app uv run ruff check .

fmt:
	docker compose run --rm app uv run ruff format .

backup: init
	@ts=$$(date +"%Y%m%d-%H%M%S"); \
	echo "Creating backup $$ts"; \
	tar -czf "backups/backup-$$ts.tgz" data logs docs BACKLOG.md SESSION_STATE.md README.md || true; \
	ls -lh backups | tail -n 5

restore:
	@echo "Restoring latest backup into ./data (THIS WILL OVERWRITE)."; \
	latest=$$(ls -1t backups/*.tgz | head -n 1); \
	echo "Using $$latest"; \
	rm -rf data && mkdir -p data; \
	tar -xzf "$$latest" -C . data