import anthropic
from agents.base import BaseAgent
from agents.email_agent import EmailAgent
from agents.calendar_agent import CalendarAgent
from agents.polymarket_agent import PolymarketAgent
from agents.outreach_agent import OutreachAgent
from agents.research_agent import ResearchAgent


SYSTEM = """You are a personal AI chief-of-staff with a full team of specialist agents at your disposal:

1. **email_agent** — reads, drafts, sends, labels, and organises Gmail.
2. **calendar_agent** — manages Google Calendar: events, RSVPs, scheduling, free-slot finding.
3. **polymarket_agent** — monitors Polymarket prediction markets, prices, trends, and order books.
4. **outreach_agent** — makes cold calls and sends SMS via Twilio for outreach campaigns.
5. **research_agent** — searches the web, fetches pages, and synthesises information.

Your job:
- Understand exactly what the user wants.
- Delegate to the right agent(s) — or chain multiple agents when needed.
- Synthesise the results into one clear, human-friendly response.
- Chain agents when a task spans multiple domains (e.g. research a lead → draft an email → schedule a call).
- Never make up information — only report what agents return.
- Today's date is 2026-05-14."""


class OrchestratorAgent(BaseAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(client, SYSTEM)
        self._email = EmailAgent(client)
        self._calendar = CalendarAgent(client)
        self._polymarket = PolymarketAgent(client)
        self._outreach = OutreachAgent(client)
        self._research = ResearchAgent(client)
        self._register_all()

    def _register_all(self):
        self._register_tool(
            "email_agent",
            "Delegate an email task: reading, searching, drafting, sending, labelling, archiving.",
            {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "context": {"type": "string", "default": ""},
                },
                "required": ["task"],
            },
            lambda task, context="": self._email.run(task, context),
        )

        self._register_tool(
            "calendar_agent",
            "Delegate a calendar task: list/create/update/delete events, RSVPs, free-slot finding.",
            {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "context": {"type": "string", "default": ""},
                },
                "required": ["task"],
            },
            lambda task, context="": self._calendar.run(task, context),
        )

        self._register_tool(
            "polymarket_agent",
            "Delegate a Polymarket task: search markets, get prices, trending markets, order books.",
            {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "context": {"type": "string", "default": ""},
                },
                "required": ["task"],
            },
            lambda task, context="": self._polymarket.run(task, context),
        )

        self._register_tool(
            "outreach_agent",
            "Delegate a cold-call or SMS outreach task via Twilio.",
            {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "context": {"type": "string", "default": ""},
                },
                "required": ["task"],
            },
            lambda task, context="": self._outreach.run(task, context),
        )

        self._register_tool(
            "research_agent",
            "Delegate a web research task: search for people, companies, news, or any topic.",
            {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "context": {"type": "string", "default": ""},
                },
                "required": ["task"],
            },
            lambda task, context="": self._research.run(task, context),
        )
