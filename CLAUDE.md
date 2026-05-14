# AI Workers — Codebase Guide

## Architecture

```
OrchestratorAgent          agents/orchestrator.py
    ├── EmailAgent          agents/email_agent.py       ← Gmail (13 tools)
    ├── CalendarAgent       agents/calendar_agent.py    ← Google Calendar (8 tools)
    ├── PolymarketAgent     agents/polymarket_agent.py  ← Prediction markets (5 tools)
    ├── OutreachAgent       agents/outreach_agent.py    ← Calls + SMS via Twilio (5 tools)
    └── ResearchAgent       agents/research_agent.py    ← Web search + fetch (2 tools)

BaseAgent                  agents/base.py              ← Shared Claude tool-use loop
```

## Key files

| Path | Purpose |
|------|---------|
| `main.py` | CLI entry point — `serve`, `chat`, `agenda`, `markets`, `research`, `do` |
| `app/server.py` | FastAPI web server + WebSocket chat endpoint |
| `app/static/` | Single-page dashboard (HTML/CSS/JS, no build step) |
| `config.py` | Env var loading |
| `integrations/auth.py` | Google OAuth2 token management |
| `integrations/gmail.py` | Gmail API client |
| `integrations/calendar.py` | Google Calendar API client |
| `integrations/polymarket.py` | Polymarket CLOB + Gamma API client |
| `integrations/twilio_client.py` | Twilio calls + SMS client |

## Running

```bash
pip install -r requirements.txt
cp .env.example .env          # fill in keys
python setup_google.py        # one-time Google OAuth
python main.py serve          # launch dashboard at http://localhost:8000
```

## Adding a new agent

1. Create `agents/my_agent.py` subclassing `BaseAgent`
2. Register tools in `__init__` via `self._register_tool(name, description, schema, handler)`
3. Add a delegation tool in `agents/orchestrator.py`
4. Add REST endpoints in `app/server.py` if needed
5. Add a UI section in `app/static/index.html` + `app/static/app.js`

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | Claude API |
| `GOOGLE_CREDENTIALS_FILE` | Yes (Gmail/Cal) | OAuth client secret JSON |
| `GOOGLE_TOKEN_FILE` | Auto | Cached OAuth token |
| `TWILIO_ACCOUNT_SID` | For calls | Twilio account |
| `TWILIO_AUTH_TOKEN` | For calls | Twilio secret |
| `TWILIO_FROM_NUMBER` | For calls | E.164 phone number |
| `CLAUDE_MODEL` | No | Override model (default: claude-sonnet-4-6) |

## Python version

Requires Python 3.9+. All files use `from __future__ import annotations` where needed for union type hints.
