# The Role of AI in This Project

Dead Letter Office was built with significant AI assistance across multiple layers of the stack — which is fitting, given that the system itself uses AI agents to automate failure analysis and incident reporting.

## Backend

The backend was developed with assistance from **Claude (Anthropic)** and **ChatGPT (OpenAI)** across several areas. The overall system architecture — including the five-agent pipeline, the API endpoint structure, and the database schema — was designed iteratively through conversation with Claude. The FastAPI application (`app/main.py`, `app/api/`), SQLAlchemy models (`app/models/`), Pydantic schemas (`app/schemas/`), and service layer (`app/services/`) were all produced with AI assistance and refined to fit the specific requirements of the project. Error handling, async session management, and the background task pattern used to trigger the CrewAI crew after event ingestion were worked out with AI support throughout development.

## AI Agents

The CrewAI agent definitions — including the `role`, `goal`, `backstory`, and `Task` descriptions for all five agents (Triage, Diagnosis, Remediation, Severity, Reporter) — were designed with assistance from **ChatGPT**. The prompt engineering required to make each agent return structured, parseable output was also AI-assisted, with iterative refinement based on actual LLM responses during testing. The `crew_service.py` output parsing logic, which extracts structured fields from each agent's `tasks_output`, was developed with **Claude**.

## Database

The database layer — Alembic migration configuration for async SQLAlchemy (`alembic/env.py`, `alembic/versions/001_initial_schema.py`), the declarative base with UUID and timestamp mixins (`app/db/base.py`), and the async session factory (`app/db/session.py`) — was set up with assistance from **Claude**. Debugging of runtime issues such as SQLAlchemy relationship resolution failures and session lifecycle management was also AI-assisted.

## Infrastructure and Deployment

Docker and Docker Compose configuration — the single-stage `Dockerfile` with a non-root user, `docker-compose.yml` for the production stack (FastAPI + PostgreSQL with healthchecks), and `docker-compose.dev.yml` for local development — was drafted and debugged with **Claude**. Several infrastructure issues were resolved with AI assistance, including container permission errors related to CrewAI's memory storage, PostgreSQL healthcheck misconfiguration, and missing Python package dependencies in the slim base image.

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci.yml`), with its three chained jobs — lint, test, and Docker build — was configured with **Claude**. The Ruff linting setup in `pyproject.toml` and the resolution of lint errors across the codebase were also AI-assisted.

## CLI

The Typer-based CLI (`app/cli/dlo.py`) — including the `ingest`, `list`, `report`, and `retry` commands — was developed with **Claude**. Debugging of a Typer and Click version incompatibility that caused the CLI to crash on `--help` was resolved with AI assistance.

## Project Management

The project's Trello board was populated automatically using a Python script (`setup_trello.py`) developed with **Claude**, which interfaced with the Trello REST API to create the board, lists, labels, and all task cards with checklists in a single run. The sprint plan, task delegation, and branch and commit naming conventions were also structured with AI assistance.

## Documentation

The technical documentation — `docs/architecture.md`, `docs/user_guide.md`, and `docs/report.md` — was written with assistance from **Claude**, ensuring consistency across descriptions of the system architecture, data flow, and API usage. This project plan document was also produced with AI support.