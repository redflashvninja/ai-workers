import anthropic
from agents.base import BaseAgent
import integrations.twilio_client as twilio


SYSTEM = """You are a professional outreach and cold-calling specialist.
You can initiate phone calls, send SMS messages, and track outreach activity via Twilio.

Guidelines:
- Always confirm the phone number before calling (E.164 format: +12025551234).
- For cold calls, keep the spoken message concise and professional.
- Log what you did clearly so the user can track outreach campaigns.
- Never make harassing or spam calls. Respect do-not-call lists.
- If Twilio is not configured, explain the setup steps clearly.
- Today's date is 2026-05-14."""


class OutreachAgent(BaseAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(client, SYSTEM)
        self._register_all()

    def _register_all(self):
        self._register_tool(
            "make_call",
            "Initiate an outbound phone call via Twilio. Speaks the provided message via text-to-speech.",
            {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient phone number in E.164 format (+12025551234)"},
                    "message": {"type": "string", "description": "Message to speak via TTS on the call"},
                    "twiml_url": {"type": "string", "default": "", "description": "Optional: URL to a TwiML document for advanced call scripting"},
                },
                "required": ["to", "message"],
            },
            lambda to, message, twiml_url="": twilio.make_call(to, message, twiml_url),
        )

        self._register_tool(
            "send_sms",
            "Send an SMS text message via Twilio.",
            {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient phone number in E.164 format"},
                    "body": {"type": "string", "description": "SMS message body (max 160 chars for single segment)"},
                },
                "required": ["to", "body"],
            },
            lambda to, body: twilio.send_sms(to, body),
        )

        self._register_tool(
            "list_calls",
            "List recent outbound and inbound calls with their status and duration.",
            {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20},
                },
            },
            lambda limit=20: twilio.list_calls(limit),
        )

        self._register_tool(
            "list_messages",
            "List recent SMS messages sent and received.",
            {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20},
                },
            },
            lambda limit=20: twilio.list_messages(limit),
        )

        self._register_tool(
            "get_call_status",
            "Check the current status of a specific call by its SID.",
            {
                "type": "object",
                "properties": {
                    "call_sid": {"type": "string"},
                },
                "required": ["call_sid"],
            },
            lambda call_sid: twilio.get_call_status(call_sid),
        )
