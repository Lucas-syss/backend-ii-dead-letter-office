# Dead Letter Office

# Dead Letter Office

[![CI](https://github.com/Lucas-syss/backend-ii-dead-letter-office/actions/workflows/ci.yml/badge.svg)](https://github.com/Lucas-syss/backend-ii-dead-letter-office/actions/workflows/ci.yml)

> AI-powered backend triage system for failed system events.

Most systems silently drop failed jobs, webhooks, or API calls.
Dead Letter Office captures those failures and dispatches a crew of AI agents
to investigate — diagnosing root cause, scoring severity, attempting
auto-remediation, and writing a full incident report. Automatically.

---

## Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| AI agents | CrewAI |
| LLM | NVIDIA Nemotron Super 49B (free) |
| Database | SQLite (dev) · PostgreSQL (prod) |
| CLI | Typer |
| Containerisation | Docker + Docker Compose |

## Agents

| Agent | Role |
|---|---|
| TriageAgent | Classifies the event type |
| DiagnosisAgent | Determines root cause |
| RemediationAgent | Attempts auto-fix |
| SeverityAgent | Assigns P1–P4 priority |
| ReporterAgent | Writes the incident report |

---

## Quickstart

### With Docker (recommended)

```bash
cp .env.example .env      # add your NVIDIA_API_KEY
make docker-up            # starts FastAPI + PostgreSQL
```

API available at: http://localhost:8000
Swagger UI at:    http://localhost:8000/docs

### Local development

```bash
cp .env.example .env      # add your NVIDIA_API_KEY
make install-dev
make migrate
make dev
```

---

## Usage

### Ingest a failed event

```bash
curl -X POST http://localhost:8000/api/v1/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "webhook",
    "service": "payment-service",
    "error_code": 503,
    "error_message": "Upstream timeout after 30s",
    "payload": { "endpoint": "/charge" }
  }'
```

### CLI

```bash
dlo ingest --file event.json
dlo list --severity P1
dlo report --id <event-id>
```

---

## Documentation

- [Architecture](docs/architecture.md)
- [User Guide](docs/user_guide.md)
- [Project Report](docs/report.md)

---

## Team

- Lucas — Infrastructure, API, Database, Docker, CI/CD
- Miguel — AI Agents, Schemas, Tests, Documentation