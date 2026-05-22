# ══════════════════════════════════════════════════════════════
#  Dead Letter Office — Makefile
#  Usage: make <target>
#  Run `make help` to see all available targets.
# ══════════════════════════════════════════════════════════════

.PHONY: help install install-dev run dev \
        migrate migrate-create migrate-down \
        test test-fast lint format \
        docker-up docker-up-dev docker-down docker-logs docker-clean \
        dlo clean

# ── Variables ──────────────────────────────────────────────────
PYTHON      := python3
PIP         := pip
APP         := app.main:app
UVICORN     := uvicorn $(APP) --host 0.0.0.0 --port 8000

# ── Default target ─────────────────────────────────────────────
.DEFAULT_GOAL := help

# ── Help ───────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  ╔══════════════════════════════════════════════╗"
	@echo "  ║       Dead Letter Office — Makefile          ║"
	@echo "  ╚══════════════════════════════════════════════╝"
	@echo ""
	@echo "  Setup"
	@echo "    make install          Install production dependencies"
	@echo "    make install-dev      Install dev + test dependencies"
	@echo ""
	@echo "  Run"
	@echo "    make run              Start server (production mode)"
	@echo "    make dev              Start server with hot reload"
	@echo ""
	@echo "  Database"
	@echo "    make migrate          Apply all pending migrations"
	@echo "    make migrate-create   Create a new migration (prompts for name)"
	@echo "    make migrate-down     Roll back one migration"
	@echo ""
	@echo "  Testing"
	@echo "    make test             Run full test suite with coverage"
	@echo "    make test-fast        Run tests, stop on first failure"
	@echo ""
	@echo "  Code quality"
	@echo "    make lint             Run Ruff linter"
	@echo "    make format           Run Ruff formatter"
	@echo ""
	@echo "  Docker"
	@echo "    make docker-up        Build and start prod stack (FastAPI + PostgreSQL)"
	@echo "    make docker-up-dev    Start dev stack (SQLite, hot reload)"
	@echo "    make docker-down      Stop containers"
	@echo "    make docker-logs      Follow app container logs"
	@echo "    make docker-clean     Stop and remove all volumes"
	@echo ""
	@echo "  CLI"
	@echo "    make dlo ARGS='list --severity P1'"
	@echo ""
	@echo "  Cleanup"
	@echo "    make clean            Remove cache files and dev database"
	@echo ""

# ── Setup ──────────────────────────────────────────────────────
install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements.txt -r requirements-dev.txt
	$(PIP) install -e .

# ── Run ────────────────────────────────────────────────────────
run:
	$(UVICORN)

dev:
	$(UVICORN) --reload

# ── Database ───────────────────────────────────────────────────
migrate:
	alembic upgrade head

migrate-create:
	@read -p "Migration name: " name; \
	alembic revision --autogenerate -m "$$name"

migrate-down:
	alembic downgrade -1

# ── Testing ────────────────────────────────────────────────────
test:
	pytest tests/ -v --cov=app --cov-report=term-missing

test-fast:
	pytest tests/ -v -x

# ── Code quality ───────────────────────────────────────────────
lint:
	ruff check app/ tests/

format:
	ruff format app/ tests/

# ── Docker ─────────────────────────────────────────────────────
docker-up:
	sudo docker compose up --build

docker-up-dev:
	sudo docker compose -f docker-compose.dev.yml up --build

docker-down:
	sudo docker compose down

docker-logs:
	sudo docker compose logs -f app

docker-clean:
	sudo docker compose down -v --remove-orphans

# ── CLI shortcut ───────────────────────────────────────────────
dlo:
	$(PYTHON) -m app.cli.dlo $(ARGS)

# ── Clean ──────────────────────────────────────────────────────
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage coverage.xml dev.db
	@echo "Cleaned up cache files."