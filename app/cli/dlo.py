"""
dlo — Dead Letter Office CLI

Calls the same service layer as the API (no HTTP involved).
All async service functions are wrapped with asyncio.run().

Commands:
    dlo ingest --file event.json     Ingest a failed event from a JSON file
    dlo list [--severity P1]         List events with optional filters
    dlo report --id <uuid>           Print the incident report for an event
    dlo retry --id <uuid>            Re-trigger remediation for an incident
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from app.db.session import AsyncSessionLocal
from app.schemas.event import FailedEventCreate
from app.services import event_service, incident_service

app = typer.Typer(
    name="dlo",
    help="Dead Letter Office — AI triage for failed system events.",
    add_completion=False,
)
console = Console()


# ── DB helper ─────────────────────────────────────────────────────────────

async def _get_db():
    """
    Returns an async DB session for CLI use.
    Unlike the FastAPI dependency, this is used inside asyncio.run() blocks.
    """
    async with AsyncSessionLocal() as session:
        return session


# ── Commands ──────────────────────────────────────────────────────────────

@app.command()
def ingest(
    file: Path = typer.Option(
        ...,
        "--file",
        "-f",
        help="Path to a JSON file containing the failed event payload.",
        exists=True,
        readable=True,
    ),
) -> None:
    """
    Ingest a failed event from a JSON file and trigger AI triage.

    \b
    Example JSON file:
    {
        "source": "webhook",
        "service": "payment-service",
        "error_code": 503,
        "error_message": "Upstream timeout after 30s",
        "payload": {"endpoint": "/charge"},
        "metadata": {"environment": "production"}
    }
    """

    async def _run():
        raw = json.loads(file.read_text())
        try:
            data = FailedEventCreate(**raw)
        except Exception as exc:
            rprint(f"[red]❌ Invalid event payload:[/red] {exc}")
            raise typer.Exit(code=1)

        async with AsyncSessionLocal() as db:
            event = await event_service.create_event(db, data)

        rprint(f"[green]✓ Event ingested[/green]")
        rprint(f"  Event ID : [bold]{event.id}[/bold]")
        rprint(f"  Service  : {event.service}")
        rprint(f"  Source   : {event.source}")
        rprint(f"  Status   : {event.status}")
        rprint(f"\n[dim]Crew triage runs automatically when the server is running.[/dim]")

    asyncio.run(_run())


@app.command("list")
def list_events(
    severity: Optional[str] = typer.Option(
        None,
        "--severity",
        "-s",
        help="Filter by severity: P1 | P2 | P3 | P4",
    ),
    source: Optional[str] = typer.Option(
        None,
        "--source",
        help="Filter by source: webhook | job | api_call | unknown",
    ),
    status: Optional[str] = typer.Option(
        None,
        "--status",
        help="Filter by status: pending | processing | resolved | escalated | failed",
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results to show"),
) -> None:
    """
    List failed events with optional filters.
    """

    async def _run():
        async with AsyncSessionLocal() as db:
            total, events = await event_service.list_events(
                db,
                severity=severity,
                source=source,
                status=status,
                limit=limit,
                offset=0,
            )

        if not events:
            rprint("[yellow]No events found.[/yellow]")
            return

        table = Table(
            title=f"Dead Letter Office — Events ({total} total)",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("ID", style="dim", max_width=36)
        table.add_column("Service")
        table.add_column("Source")
        table.add_column("Status")
        table.add_column("Severity")
        table.add_column("Created At")

        for event in events:
            severity_val = event.incident.severity if event.incident else "—"
            severity_colour = {
                "P1": "bold red",
                "P2": "red",
                "P3": "yellow",
                "P4": "green",
            }.get(severity_val, "dim")

            table.add_row(
                str(event.id),
                event.service,
                event.source,
                event.status,
                f"[{severity_colour}]{severity_val}[/{severity_colour}]",
                event.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)

    asyncio.run(_run())


@app.command()
def report(
    id: str = typer.Option(
        ...,
        "--id",
        help="Event ID to retrieve the incident report for.",
    ),
) -> None:
    """
    Print the full Markdown incident report for an event.
    """

    async def _run():
        async with AsyncSessionLocal() as db:
            event = await event_service.get_event(db, id)

        if not event:
            rprint(f"[red]❌ Event '{id}' not found.[/red]")
            raise typer.Exit(code=1)

        if not event.incident:
            rprint(f"[yellow]⏳ Event '{id}' has no incident yet — crew may still be processing.[/yellow]")
            rprint(f"   Status: [bold]{event.status}[/bold]")
            raise typer.Exit(code=0)

        inc = event.incident

        # Header summary
        severity_colour = {"P1": "bold red", "P2": "red", "P3": "yellow", "P4": "green"}.get(
            inc.severity, "white"
        )
        rprint(f"\n[bold]Incident Report[/bold] — Event [dim]{id}[/dim]")
        rprint(f"  Severity   : [{severity_colour}]{inc.severity}[/{severity_colour}]")
        rprint(f"  Event type : {inc.event_type}")
        rprint(f"  Escalated  : {'[red]Yes[/red]' if inc.escalated else '[green]No[/green]'}")
        rprint(f"  Remediated : {'[green]Yes[/green]' if inc.remediation_attempted else '[yellow]No[/yellow]'}")
        rprint()

        # Full Markdown report
        console.print(Markdown(inc.report_md))

    asyncio.run(_run())


@app.command()
def retry(
    id: str = typer.Option(
        ...,
        "--id",
        help="Event ID to re-trigger remediation for.",
    ),
) -> None:
    """
    Re-trigger the RemediationAgent for an existing incident.
    """

    async def _run():
        async with AsyncSessionLocal() as db:
            event = await event_service.get_event(db, id)

            if not event:
                rprint(f"[red]❌ Event '{id}' not found.[/red]")
                raise typer.Exit(code=1)

            if not event.incident:
                rprint(f"[yellow]⚠ Event '{id}' has no incident to retry.[/yellow]")
                raise typer.Exit(code=1)

            incident = await incident_service.retry_remediation(db, event.incident)

        rprint(f"[green]✓ Remediation retry triggered[/green]")
        rprint(f"  Incident ID : [bold]{incident.id}[/bold]")
        rprint(f"  Result      : {incident.remediation_result}")

    asyncio.run(_run())


# ── Entrypoint ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()