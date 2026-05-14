import json
import anthropic
from agents.base import BaseAgent
from agents.email_agent import EmailAgent
from agents.calendar_agent import CalendarAgent


SYSTEM = """You are a personal AI chief-of-staff. You have specialist agents at your disposal:

1. **email_agent** — reads, drafts, sends, labels, and organises Gmail.
2. **calendar_agent** — manages Google Calendar: events, RSVPs, scheduling, free-slot finding.

Your job:
- Understand exactly what the user wants.
- Delegate to the right agent (or multiple agents in sequence).
- Synthesise the results into one clear, human-friendly response.
- If you need both email and calendar to complete a task, call them in logical order.
- Never make up information — only report what the agents return.
- Today's date is 2026-05-14."""


class OrchestratorAgent(BaseAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(client, SYSTEM)
        self._email_agent = EmailAgent(client)
        self._calendar_agent = CalendarAgent(client)
        self._register_all()

    def _register_all(self):
        self._register_tool(
            "email_agent",
            (
                "Delegate an email-related task to the email specialist agent. "
                "Use for reading, searching, drafting, sending, labelling, archiving, or organising email."
            ),
            {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "A complete, self-contained description of what the email agent should do.",
                    },
                    "context": {
                        "type": "string",
                        "description": "Any extra context the email agent needs (e.g. results from the calendar agent).",
                        "default": "",
                    },
                },
                "required": ["task"],
            },
            lambda task, context="": self._email_agent.run(task, context),
        )

        self._register_tool(
            "calendar_agent",
            (
                "Delegate a calendar-related task to the calendar specialist agent. "
                "Use for listing events, creating/updating/deleting events, RSVPing, or finding free time."
            ),
            {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "A complete, self-contained description of what the calendar agent should do.",
                    },
                    "context": {
                        "type": "string",
                        "description": "Any extra context the calendar agent needs.",
                        "default": "",
                    },
                },
                "required": ["task"],
            },
            lambda task, context="": self._calendar_agent.run(task, context),
        )
