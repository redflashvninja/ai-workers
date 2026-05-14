import anthropic
from agents.base import BaseAgent
import integrations.calendar as cal


SYSTEM = """You are an expert calendar assistant with full access to the user's Google Calendar.
You can list, create, update, delete, and respond to calendar events, and find free time slots.

Guidelines:
- Always show event details (time, attendees, location) clearly.
- Use ISO 8601 format for all datetimes (e.g. 2026-05-14T14:00:00Z).
- When scheduling with others, check free/busy before proposing a time.
- Confirm before deleting or declining events.
- Mention the user's timezone if relevant.
- Today's date is 2026-05-14. Default to UTC unless told otherwise."""


class CalendarAgent(BaseAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(client, SYSTEM)
        self._register_all()

    def _register_all(self):
        self._register_tool(
            "list_calendars",
            "List all calendars in the user's Google account.",
            {"type": "object", "properties": {}},
            lambda: cal.list_calendars(),
        )

        self._register_tool(
            "list_events",
            "List upcoming calendar events, optionally filtered by time range or search query.",
            {
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "default": "primary"},
                    "time_min": {"type": "string", "description": "ISO 8601 start time (defaults to now)"},
                    "time_max": {"type": "string", "description": "ISO 8601 end time"},
                    "max_results": {"type": "integer", "default": 20},
                    "query": {"type": "string", "description": "Free-text search within events"},
                },
            },
            lambda calendar_id="primary", time_min="", time_max="", max_results=20, query="": cal.list_events(
                calendar_id, time_min, time_max, max_results, query
            ),
        )

        self._register_tool(
            "get_event",
            "Get full details of a specific event by ID.",
            {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "calendar_id": {"type": "string", "default": "primary"},
                },
                "required": ["event_id"],
            },
            lambda event_id, calendar_id="primary": cal.get_event(event_id, calendar_id),
        )

        self._register_tool(
            "create_event",
            "Create a new calendar event.",
            {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event title"},
                    "start": {"type": "string", "description": "ISO 8601 start datetime"},
                    "end": {"type": "string", "description": "ISO 8601 end datetime"},
                    "description": {"type": "string", "default": ""},
                    "location": {"type": "string", "default": ""},
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses",
                    },
                    "calendar_id": {"type": "string", "default": "primary"},
                },
                "required": ["summary", "start", "end"],
            },
            lambda summary, start, end, description="", location="", attendees=None, calendar_id="primary": cal.create_event(
                summary, start, end, description, location, attendees, calendar_id
            ),
        )

        self._register_tool(
            "update_event",
            "Update an existing calendar event.",
            {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "summary": {"type": "string", "default": ""},
                    "start": {"type": "string", "default": ""},
                    "end": {"type": "string", "default": ""},
                    "description": {"type": "string", "default": ""},
                    "location": {"type": "string", "default": ""},
                    "attendees": {"type": "array", "items": {"type": "string"}},
                    "calendar_id": {"type": "string", "default": "primary"},
                },
                "required": ["event_id"],
            },
            lambda event_id, summary="", start="", end="", description="", location="", attendees=None, calendar_id="primary": cal.update_event(
                event_id, summary, start, end, description, location, attendees, calendar_id
            ),
        )

        self._register_tool(
            "delete_event",
            "Delete a calendar event permanently.",
            {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "calendar_id": {"type": "string", "default": "primary"},
                },
                "required": ["event_id"],
            },
            lambda event_id, calendar_id="primary": cal.delete_event(event_id, calendar_id),
        )

        self._register_tool(
            "respond_to_event",
            "Accept, decline, or tentatively accept a calendar invitation.",
            {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "response": {
                        "type": "string",
                        "enum": ["accepted", "declined", "tentative"],
                        "description": "Your RSVP response",
                    },
                    "calendar_id": {"type": "string", "default": "primary"},
                },
                "required": ["event_id", "response"],
            },
            lambda event_id, response, calendar_id="primary": cal.respond_to_event(event_id, response, calendar_id),
        )

        self._register_tool(
            "find_free_slots",
            "Check the free/busy schedule for a list of attendees to find available meeting times.",
            {
                "type": "object",
                "properties": {
                    "attendee_emails": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Email addresses of attendees to check",
                    },
                    "duration_minutes": {"type": "integer", "description": "Required meeting duration in minutes"},
                    "time_min": {"type": "string", "description": "ISO 8601 start of search window"},
                    "time_max": {"type": "string", "description": "ISO 8601 end of search window"},
                },
                "required": ["attendee_emails", "duration_minutes", "time_min", "time_max"],
            },
            lambda attendee_emails, duration_minutes, time_min, time_max: cal.find_free_slots(
                attendee_emails, duration_minutes, time_min, time_max
            ),
        )
