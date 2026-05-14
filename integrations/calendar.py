from datetime import datetime, timezone
from typing import Optional
from googleapiclient.discovery import build
from integrations.auth import get_google_credentials


def _service():
    return build("calendar", "v3", credentials=get_google_credentials())


def list_calendars() -> list[dict]:
    svc = _service()
    result = svc.calendarList().list().execute()
    return [
        {"id": c["id"], "summary": c["summary"], "primary": c.get("primary", False)}
        for c in result.get("items", [])
    ]


def list_events(
    calendar_id: str = "primary",
    time_min: str = "",
    time_max: str = "",
    max_results: int = 20,
    query: str = "",
) -> list[dict]:
    svc = _service()
    kwargs: dict = {
        "calendarId": calendar_id,
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime",
    }
    if time_min:
        kwargs["timeMin"] = time_min
    else:
        kwargs["timeMin"] = datetime.now(timezone.utc).isoformat()
    if time_max:
        kwargs["timeMax"] = time_max
    if query:
        kwargs["q"] = query

    result = svc.events().list(**kwargs).execute()
    return [_format_event(e) for e in result.get("items", [])]


def get_event(event_id: str, calendar_id: str = "primary") -> dict:
    svc = _service()
    e = svc.events().get(calendarId=calendar_id, eventId=event_id).execute()
    return _format_event(e)


def create_event(
    summary: str,
    start: str,
    end: str,
    description: str = "",
    location: str = "",
    attendees: list[str] = None,
    calendar_id: str = "primary",
) -> dict:
    svc = _service()
    event_body: dict = {
        "summary": summary,
        "start": {"dateTime": start, "timeZone": "UTC"},
        "end": {"dateTime": end, "timeZone": "UTC"},
    }
    if description:
        event_body["description"] = description
    if location:
        event_body["location"] = location
    if attendees:
        event_body["attendees"] = [{"email": a} for a in attendees]

    created = svc.events().insert(
        calendarId=calendar_id,
        body=event_body,
        sendUpdates="all" if attendees else "none",
    ).execute()
    return _format_event(created)


def update_event(
    event_id: str,
    summary: str = "",
    start: str = "",
    end: str = "",
    description: str = "",
    location: str = "",
    attendees: list[str] = None,
    calendar_id: str = "primary",
) -> dict:
    svc = _service()
    existing = svc.events().get(calendarId=calendar_id, eventId=event_id).execute()

    if summary:
        existing["summary"] = summary
    if start:
        existing["start"] = {"dateTime": start, "timeZone": "UTC"}
    if end:
        existing["end"] = {"dateTime": end, "timeZone": "UTC"}
    if description:
        existing["description"] = description
    if location:
        existing["location"] = location
    if attendees is not None:
        existing["attendees"] = [{"email": a} for a in attendees]

    updated = svc.events().update(
        calendarId=calendar_id,
        eventId=event_id,
        body=existing,
        sendUpdates="all",
    ).execute()
    return _format_event(updated)


def delete_event(event_id: str, calendar_id: str = "primary") -> dict:
    svc = _service()
    svc.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    return {"deleted": event_id}


def respond_to_event(event_id: str, response: str, calendar_id: str = "primary") -> dict:
    """response: 'accepted' | 'declined' | 'tentative'"""
    svc = _service()
    me = svc.calendars().get(calendarId="primary").execute()
    my_email = me["id"]

    event = svc.events().get(calendarId=calendar_id, eventId=event_id).execute()
    for attendee in event.get("attendees", []):
        if attendee.get("email") == my_email or attendee.get("self"):
            attendee["responseStatus"] = response

    updated = svc.events().patch(
        calendarId=calendar_id,
        eventId=event_id,
        body={"attendees": event.get("attendees", [])},
        sendUpdates="all",
    ).execute()
    return _format_event(updated)


def find_free_slots(
    attendee_emails: list[str],
    duration_minutes: int,
    time_min: str,
    time_max: str,
) -> list[dict]:
    svc = _service()
    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": [{"id": e} for e in attendee_emails],
    }
    result = svc.freebusy().query(body=body).execute()
    busy_by_calendar = result.get("calendars", {})

    all_busy: list[tuple] = []
    for cal_data in busy_by_calendar.values():
        for slot in cal_data.get("busy", []):
            all_busy.append((slot["start"], slot["end"]))

    all_busy.sort(key=lambda x: x[0])
    return {"busy_periods": all_busy, "suggestion": "Check busy periods and pick a gap."}


def _format_event(e: dict) -> dict:
    start = e.get("start", {})
    end = e.get("end", {})
    return {
        "id": e.get("id", ""),
        "summary": e.get("summary", "(no title)"),
        "description": e.get("description", ""),
        "location": e.get("location", ""),
        "start": start.get("dateTime", start.get("date", "")),
        "end": end.get("dateTime", end.get("date", "")),
        "status": e.get("status", ""),
        "attendees": [
            {"email": a["email"], "status": a.get("responseStatus", "needsAction")}
            for a in e.get("attendees", [])
        ],
        "htmlLink": e.get("htmlLink", ""),
        "organizer": e.get("organizer", {}).get("email", ""),
    }
