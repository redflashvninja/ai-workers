"""
Outreach via Twilio (calls + SMS).
Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER in .env
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")  # E.164 e.g. +12025551234
TWIML_BIN_URL = os.getenv("TWILIO_TWIML_URL", "")  # optional hosted TwiML


def _client():
    if not ACCOUNT_SID or not AUTH_TOKEN:
        raise RuntimeError(
            "Twilio credentials not configured. "
            "Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER in .env"
        )
    from twilio.rest import Client
    return Client(ACCOUNT_SID, AUTH_TOKEN)


def make_call(to: str, message: str = "", twiml_url: str = "") -> dict:
    """Initiate an outbound call. Speaks `message` via TTS or uses a TwiML URL."""
    client = _client()
    url = twiml_url or TWIML_BIN_URL
    if not url and message:
        encoded = message.replace("&", "and").replace("<", "").replace(">", "")
        url = f"http://twimlets.com/message?Message%5B0%5D={encoded}"
    if not url:
        url = "http://twimlets.com/message?Message%5B0%5D=Hello%2C+this+is+an+automated+call."

    call = client.calls.create(to=to, from_=FROM_NUMBER, url=url)
    return {
        "sid": call.sid,
        "status": call.status,
        "to": call.to,
        "from": call.from_,
        "direction": call.direction,
    }


def send_sms(to: str, body: str) -> dict:
    client = _client()
    msg = client.messages.create(to=to, from_=FROM_NUMBER, body=body)
    return {
        "sid": msg.sid,
        "status": msg.status,
        "to": msg.to,
        "body": msg.body,
    }


def list_calls(limit: int = 20) -> list[dict]:
    client = _client()
    calls = client.calls.list(limit=limit)
    return [
        {
            "sid": c.sid,
            "to": c.to,
            "from": c.from_,
            "status": c.status,
            "duration": c.duration,
            "start_time": str(c.start_time),
            "direction": c.direction,
        }
        for c in calls
    ]


def list_messages(limit: int = 20) -> list[dict]:
    client = _client()
    msgs = client.messages.list(limit=limit)
    return [
        {
            "sid": m.sid,
            "to": m.to,
            "from": m.from_,
            "body": m.body,
            "status": m.status,
            "date_sent": str(m.date_sent),
            "direction": m.direction,
        }
        for m in msgs
    ]


def get_call_status(call_sid: str) -> dict:
    client = _client()
    call = client.calls(call_sid).fetch()
    return {
        "sid": call.sid,
        "status": call.status,
        "duration": call.duration,
        "to": call.to,
        "from": call.from_,
    }
