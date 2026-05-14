import anthropic
from agents.base import BaseAgent
import integrations.gmail as gmail


SYSTEM = """You are an expert email assistant with full access to the user's Gmail inbox.
You can search, read, send, draft, label, archive, trash, and organise emails.

Guidelines:
- Always confirm before sending — draft first unless the user explicitly says "send".
- Summarise long threads; quote only the relevant parts.
- When replying, match the tone of the thread.
- Keep the user informed of exactly what action you took.
- Use labels/archive to keep the inbox tidy when asked.
- Today's date is available via the system clock."""


class EmailAgent(BaseAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(client, SYSTEM)
        self._register_all()

    def _register_all(self):
        self._register_tool(
            "search_emails",
            "Search Gmail using a query string (supports Gmail search operators like from:, subject:, is:unread, etc.).",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Gmail search query"},
                    "max_results": {"type": "integer", "description": "Max emails to return (default 20)", "default": 20},
                },
                "required": ["query"],
            },
            lambda query, max_results=20: gmail.search_emails(query, max_results),
        )

        self._register_tool(
            "get_email",
            "Read the full body and metadata of a single email by its message ID.",
            {
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "Gmail message ID"},
                },
                "required": ["message_id"],
            },
            lambda message_id: gmail.get_email(message_id),
        )

        self._register_tool(
            "get_thread",
            "Read all messages in an email thread by thread ID.",
            {
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string", "description": "Gmail thread ID"},
                },
                "required": ["thread_id"],
            },
            lambda thread_id: gmail.get_thread(thread_id),
        )

        self._register_tool(
            "send_email",
            "Send an email immediately.",
            {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address(es), comma-separated"},
                    "subject": {"type": "string"},
                    "body": {"type": "string", "description": "Plain text body"},
                    "cc": {"type": "string", "description": "CC addresses", "default": ""},
                    "reply_to_thread_id": {"type": "string", "description": "Thread ID to reply into", "default": ""},
                },
                "required": ["to", "subject", "body"],
            },
            lambda to, subject, body, cc="", reply_to_thread_id="": gmail.send_email(to, subject, body, cc, reply_to_thread_id),
        )

        self._register_tool(
            "create_draft",
            "Save an email as a draft without sending.",
            {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                    "cc": {"type": "string", "default": ""},
                    "reply_to_thread_id": {"type": "string", "default": ""},
                },
                "required": ["to", "subject", "body"],
            },
            lambda to, subject, body, cc="", reply_to_thread_id="": gmail.create_draft(to, subject, body, cc, reply_to_thread_id),
        )

        self._register_tool(
            "list_drafts",
            "List current email drafts.",
            {
                "type": "object",
                "properties": {
                    "max_results": {"type": "integer", "default": 10},
                },
            },
            lambda max_results=10: gmail.list_drafts(max_results),
        )

        self._register_tool(
            "label_message",
            "Add or remove labels on a message.",
            {
                "type": "object",
                "properties": {
                    "message_id": {"type": "string"},
                    "add_labels": {"type": "array", "items": {"type": "string"}, "description": "Label IDs or names to add"},
                    "remove_labels": {"type": "array", "items": {"type": "string"}, "description": "Label IDs or names to remove"},
                },
                "required": ["message_id"],
            },
            lambda message_id, add_labels=None, remove_labels=None: gmail.label_message(message_id, add_labels, remove_labels),
        )

        self._register_tool(
            "list_labels",
            "List all Gmail labels.",
            {"type": "object", "properties": {}},
            lambda: gmail.list_labels(),
        )

        self._register_tool(
            "create_label",
            "Create a new Gmail label.",
            {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Label name"},
                },
                "required": ["name"],
            },
            lambda name: gmail.create_label(name),
        )

        self._register_tool(
            "archive_message",
            "Archive a message (remove from inbox).",
            {
                "type": "object",
                "properties": {"message_id": {"type": "string"}},
                "required": ["message_id"],
            },
            lambda message_id: gmail.archive_message(message_id),
        )

        self._register_tool(
            "trash_message",
            "Move a message to trash.",
            {
                "type": "object",
                "properties": {"message_id": {"type": "string"}},
                "required": ["message_id"],
            },
            lambda message_id: gmail.trash_message(message_id),
        )

        self._register_tool(
            "mark_read",
            "Mark a message as read.",
            {
                "type": "object",
                "properties": {"message_id": {"type": "string"}},
                "required": ["message_id"],
            },
            lambda message_id: gmail.mark_read(message_id),
        )

        self._register_tool(
            "mark_unread",
            "Mark a message as unread.",
            {
                "type": "object",
                "properties": {"message_id": {"type": "string"}},
                "required": ["message_id"],
            },
            lambda message_id: gmail.mark_unread(message_id),
        )
