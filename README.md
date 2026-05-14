# AI Workers — In-House Agent Platform

A personal AI agent system that runs **everything** — emails, calendar, scheduling, and more — powered by Claude and your own Google account.

## Architecture

```
OrchestratorAgent  ← understands your request, routes to the right specialist
    ├── EmailAgent     ← full Gmail: read, search, draft, send, label, archive, trash
    └── CalendarAgent  ← full Google Calendar: events, RSVPs, free-slot finder
```

Each agent is a Claude-powered tool-use loop that calls real Google APIs. The orchestrator routes your request, runs agents in sequence when needed, and returns one clean answer.

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your Anthropic API key

```bash
cp .env.example .env
# Edit .env and paste your ANTHROPIC_API_KEY
```

### 3. Set up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable **Gmail API** and **Google Calendar API**
3. Create **OAuth 2.0 credentials** (Desktop app)
4. Download the JSON file → save as `credentials.json` in this folder
5. Run the auth flow:

```bash
python setup_google.py
```

A browser window opens; sign in and grant access. Your token is saved to `token.json` automatically.

---

## Usage

### Interactive chat (default)

```bash
python main.py
# or
python main.py chat
```

Talk naturally — the orchestrator figures out what to do:

```
You: What emails do I have unread from this week?
You: Schedule a 1-hour meeting with alice@example.com tomorrow at 2pm
You: Draft a reply to the email from Bob about the proposal, keep it friendly
You: What's on my calendar for the next 3 days?
You: Accept the meeting invite from Sarah and send her an email confirming
```

### One-shot commands

```bash
# Search email
python main.py email-search "is:unread from:boss@company.com"

# Show agenda for next 7 days
python main.py agenda --days 7

# Run any task through the orchestrator
python main.py do "Find all emails about invoices this month and summarise them"
python main.py do "Create a team standup event every weekday at 9am next week"

# Direct agent flags
python main.py --email "Draft a polite follow-up to john@example.com about the proposal"
python main.py --calendar "List all my meetings for tomorrow"
python main.py --task "Check if I have any unanswered emails and show my afternoon schedule"
```

---

## What Each Agent Can Do

### Email Agent
| Tool | Description |
|------|-------------|
| `search_emails` | Gmail search (from:, subject:, is:unread, etc.) |
| `get_email` | Read full message body |
| `get_thread` | Read entire conversation thread |
| `send_email` | Send immediately |
| `create_draft` | Save as draft |
| `list_drafts` | Show pending drafts |
| `label_message` | Add/remove labels |
| `list_labels` | See all labels |
| `create_label` | Create a new label |
| `archive_message` | Remove from inbox |
| `trash_message` | Move to trash |
| `mark_read` / `mark_unread` | Toggle read state |

### Calendar Agent
| Tool | Description |
|------|-------------|
| `list_calendars` | All calendars in your account |
| `list_events` | Upcoming events (filterable) |
| `get_event` | Full event details |
| `create_event` | New event with attendees |
| `update_event` | Edit existing event |
| `delete_event` | Remove event |
| `respond_to_event` | Accept / decline / tentative |
| `find_free_slots` | Check free/busy for attendees |

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Required. From console.anthropic.com |
| `GOOGLE_CREDENTIALS_FILE` | `credentials.json` | OAuth client secret |
| `GOOGLE_TOKEN_FILE` | `token.json` | Cached auth token (auto-created) |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Override the Claude model |

---

## Adding New Agents

1. Create `agents/my_agent.py` subclassing `BaseAgent`
2. Register tools in `__init__` using `self._register_tool(...)`
3. Add a delegation tool in `agents/orchestrator.py`

That's it — the orchestrator will automatically route tasks to it.
