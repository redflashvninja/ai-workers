"""
AI Workers — FastAPI web server
Run with: uvicorn app.server:app --reload  OR  python main.py serve
"""
from __future__ import annotations

import asyncio
import json
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import anthropic

from config import ANTHROPIC_API_KEY
from agents.orchestrator import OrchestratorAgent
import integrations.polymarket as pm

app = FastAPI(title="AI Workers", version="2.0.0")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

_client: anthropic.Anthropic | None = None
_orchestrator: OrchestratorAgent | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def _get_orchestrator() -> OrchestratorAgent:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent(_get_client())
    return _orchestrator


# ── REST endpoints ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/status")
async def status():
    return {
        "status": "running",
        "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
        "google_auth": Path("token.json").exists(),
        "twilio_configured": bool(os.getenv("TWILIO_ACCOUNT_SID")),
        "time": datetime.now(timezone.utc).isoformat(),
    }


# ── Email endpoints ───────────────────────────────────────────────────────────

@app.get("/api/email/inbox")
async def email_inbox(q: str = "in:inbox", n: int = 20):
    try:
        import integrations.gmail as gmail
        return gmail.search_emails(q, n)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/email/message/{message_id}")
async def email_message(message_id: str):
    try:
        import integrations.gmail as gmail
        return gmail.get_email(message_id)
    except Exception as e:
        raise HTTPException(500, str(e))


class DraftRequest(BaseModel):
    to: str
    subject: str
    body: str
    cc: str = ""


@app.post("/api/email/draft")
async def create_email_draft(req: DraftRequest):
    try:
        import integrations.gmail as gmail
        return gmail.create_draft(req.to, req.subject, req.body, req.cc)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/email/send")
async def send_email(req: DraftRequest):
    try:
        import integrations.gmail as gmail
        return gmail.send_email(req.to, req.subject, req.body, req.cc)
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Calendar endpoints ────────────────────────────────────────────────────────

@app.get("/api/calendar/events")
async def calendar_events(days: int = 7):
    try:
        import integrations.calendar as cal
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days)
        return cal.list_events(time_min=now.isoformat(), time_max=end.isoformat(), max_results=50)
    except Exception as e:
        raise HTTPException(500, str(e))


class EventRequest(BaseModel):
    summary: str
    start: str
    end: str
    description: str = ""
    location: str = ""
    attendees: list[str] = []


@app.post("/api/calendar/events")
async def create_calendar_event(req: EventRequest):
    try:
        import integrations.calendar as cal
        return cal.create_event(
            req.summary, req.start, req.end,
            req.description, req.location, req.attendees
        )
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Polymarket endpoints ──────────────────────────────────────────────────────

@app.get("/api/polymarket/trending")
async def polymarket_trending(limit: int = 12):
    try:
        return pm.get_trending_markets(limit)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/polymarket/search")
async def polymarket_search(q: str, limit: int = 20):
    try:
        return pm.search_markets(q, limit)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/polymarket/market/{condition_id}")
async def polymarket_market(condition_id: str):
    try:
        return pm.get_market(condition_id)
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Outreach endpoints ────────────────────────────────────────────────────────

class CallRequest(BaseModel):
    to: str
    message: str


@app.post("/api/outreach/call")
async def make_call(req: CallRequest):
    try:
        import integrations.twilio_client as twilio
        return twilio.make_call(req.to, req.message)
    except Exception as e:
        raise HTTPException(500, str(e))


class SmsRequest(BaseModel):
    to: str
    body: str


@app.post("/api/outreach/sms")
async def send_sms(req: SmsRequest):
    try:
        import integrations.twilio_client as twilio
        return twilio.send_sms(req.to, req.body)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/outreach/calls")
async def list_calls(limit: int = 20):
    try:
        import integrations.twilio_client as twilio
        return twilio.list_calls(limit)
    except Exception as e:
        raise HTTPException(500, str(e))


# ── WebSocket chat ────────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def send(self, ws: WebSocket, data: dict):
        await ws.send_text(json.dumps(data))


manager = ConnectionManager()


@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    orchestrator = _get_orchestrator()
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            user_msg = data.get("message", "").strip()
            if not user_msg:
                continue

            await manager.send(websocket, {"type": "thinking", "content": "..."})

            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, orchestrator.run, user_msg
                )
                await manager.send(websocket, {"type": "response", "content": result})
            except Exception as e:
                await manager.send(websocket, {"type": "error", "content": str(e)})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
