#!/usr/bin/env python3
"""
AI Workers — personal in-house agent platform.
Run `python main.py` for an interactive session,
or `python main.py serve` to launch the web dashboard.
"""

import sys
import click
import anthropic
from rich.console import Console
from rich.prompt import Prompt
from rich.rule import Rule

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from agents.orchestrator import OrchestratorAgent
from agents.email_agent import EmailAgent
from agents.calendar_agent import CalendarAgent
from agents.polymarket_agent import PolymarketAgent
from agents.outreach_agent import OutreachAgent
from agents.research_agent import ResearchAgent
from utils.formatting import print_response, print_user, print_error, print_info

console = Console()


def _make_client() -> anthropic.Anthropic:
    if not ANTHROPIC_API_KEY:
        print_error(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
        )
        sys.exit(1)
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _run_agent(agent, task: str):
    print_info(f"Running on model: {CLAUDE_MODEL}")
    print_user(task)
    result = agent.run(task)
    print_response(result)


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--email", "-e", default=None, help="Run a one-shot email task")
@click.option("--calendar", "-c", default=None, help="Run a one-shot calendar task")
@click.option("--task", "-t", default=None, help="Run a one-shot orchestrator task")
def cli(ctx, email, calendar, task):
    """AI Workers — your personal in-house agent platform."""
    if ctx.invoked_subcommand is not None:
        return

    client = _make_client()

    if email:
        _run_agent(EmailAgent(client), email)
    elif calendar:
        _run_agent(CalendarAgent(client), calendar)
    elif task:
        _run_agent(OrchestratorAgent(client), task)
    else:
        ctx.invoke(chat)


@cli.command()
def chat():
    """Start an interactive chat session with the orchestrator."""
    client = _make_client()
    orchestrator = OrchestratorAgent(client)

    console.print(Rule("[bold cyan]AI Workers — Interactive Mode[/bold cyan]"))
    console.print(
        "[dim]Your personal AI chief-of-staff. "
        "Ask it anything about your email, calendar, or both.\n"
        "Type [bold]exit[/bold] or [bold]quit[/bold] to end.[/dim]\n"
    )

    while True:
        try:
            user_input = Prompt.ask("[bold green]You[/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            console.print("[dim]Goodbye.[/dim]")
            break

        try:
            print_info("Thinking...")
            result = orchestrator.run(user_input)
            print_response(result)
        except Exception as exc:
            print_error(str(exc))

    console.print(Rule())


@cli.command()
def setup():
    """Authenticate with Google (runs OAuth flow in browser)."""
    from integrations.auth import get_google_credentials
    console.print("[bold]Starting Google OAuth flow…[/bold]")
    try:
        creds = get_google_credentials()
        console.print(f"[green]✓ Authenticated.[/green] Token saved.")
        console.print(f"[dim]Scopes: {', '.join(creds.scopes or [])}[/dim]")
    except FileNotFoundError as e:
        print_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--max", "-n", default=20, help="Max results")
def email_search(query, max):
    """Search your inbox with a Gmail query string."""
    client = _make_client()
    agent = EmailAgent(client)
    _run_agent(agent, f"Search emails with query: {query}. Max results: {max}. Summarise what you find.")


@cli.command()
@click.option("--days", "-d", default=7, help="How many days ahead to show")
def agenda(days):
    """Show your calendar agenda for the next N days."""
    from datetime import datetime, timedelta, timezone
    client = _make_client()
    agent = CalendarAgent(client)
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)
    task = (
        f"List all events from {now.isoformat()} to {end.isoformat()}. "
        "Format them clearly with date, time, title, and attendees."
    )
    _run_agent(agent, task)


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, help="Port to listen on")
@click.option("--open/--no-open", "open_browser", default=True, help="Open browser automatically")
def serve(host, port, open_browser):
    """Launch the web dashboard (FastAPI + browser UI)."""
    import uvicorn, threading, webbrowser, time
    url = f"http://{host}:{port}"
    console.print(f"[bold cyan]AI Workers Dashboard[/bold cyan] → {url}")
    if open_browser:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    uvicorn.run("app.server:app", host=host, port=port, reload=False)


@cli.command()
@click.argument("query")
def markets(query):
    """Search Polymarket prediction markets."""
    client = _make_client()
    _run_agent(PolymarketAgent(client), f"Search Polymarket for: {query}. Show prices, volumes, and URLs.")


@cli.command()
@click.argument("task_description", nargs=-1, required=True)
def research(task_description):
    """Run a web research task."""
    task = " ".join(task_description)
    client = _make_client()
    _run_agent(ResearchAgent(client), task)


@cli.command()
@click.argument("task_description", nargs=-1, required=True)
def do(task_description):
    """Run any free-form task through the orchestrator. Quote the task if multi-word."""
    task = " ".join(task_description)
    client = _make_client()
    _run_agent(OrchestratorAgent(client), task)


if __name__ == "__main__":
    cli()
