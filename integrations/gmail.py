import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from googleapiclient.discovery import build
from integrations.auth import get_google_credentials


def _service():
    return build("gmail", "v1", credentials=get_google_credentials())


def search_emails(query: str, max_results: int = 20) -> list[dict]:
    svc = _service()
    result = svc.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = result.get("messages", [])
    threads = []
    for msg in messages:
        detail = svc.users().messages().get(
            userId="me", id=msg["id"], format="metadata",
            metadataHeaders=["Subject", "From", "To", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        threads.append({
            "id": msg["id"],
            "threadId": detail["threadId"],
            "subject": headers.get("Subject", "(no subject)"),
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "date": headers.get("Date", ""),
            "snippet": detail.get("snippet", ""),
            "labelIds": detail.get("labelIds", []),
        })
    return threads


def get_email(message_id: str) -> dict:
    svc = _service()
    msg = svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

    body = ""
    payload = msg["payload"]
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain" and "data" in part.get("body", {}):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                break
    elif "body" in payload and "data" in payload["body"]:
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    return {
        "id": msg["id"],
        "threadId": msg["threadId"],
        "subject": headers.get("Subject", "(no subject)"),
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "cc": headers.get("Cc", ""),
        "date": headers.get("Date", ""),
        "body": body,
        "labelIds": msg.get("labelIds", []),
    }


def get_thread(thread_id: str) -> list[dict]:
    svc = _service()
    thread = svc.users().threads().get(userId="me", id=thread_id, format="full").execute()
    return [get_email(m["id"]) for m in thread.get("messages", [])]


def send_email(to: str, subject: str, body: str, cc: str = "", reply_to_thread_id: str = "") -> dict:
    svc = _service()
    msg = MIMEMultipart()
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc
    msg.attach(MIMEText(body, "plain"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body_payload: dict = {"raw": raw}
    if reply_to_thread_id:
        body_payload["threadId"] = reply_to_thread_id

    sent = svc.users().messages().send(userId="me", body=body_payload).execute()
    return {"id": sent["id"], "threadId": sent.get("threadId", "")}


def create_draft(to: str, subject: str, body: str, cc: str = "", reply_to_thread_id: str = "") -> dict:
    svc = _service()
    msg = MIMEMultipart()
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc
    msg.attach(MIMEText(body, "plain"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    message_body: dict = {"raw": raw}
    if reply_to_thread_id:
        message_body["threadId"] = reply_to_thread_id

    draft = svc.users().drafts().create(
        userId="me", body={"message": message_body}
    ).execute()
    return {"draftId": draft["id"]}


def list_drafts(max_results: int = 10) -> list[dict]:
    svc = _service()
    result = svc.users().drafts().list(userId="me", maxResults=max_results).execute()
    drafts = []
    for d in result.get("drafts", []):
        detail = svc.users().drafts().get(userId="me", id=d["id"]).execute()
        headers = {
            h["name"]: h["value"]
            for h in detail["message"]["payload"]["headers"]
        }
        drafts.append({
            "draftId": d["id"],
            "subject": headers.get("Subject", "(no subject)"),
            "to": headers.get("To", ""),
            "snippet": detail["message"].get("snippet", ""),
        })
    return drafts


def label_message(message_id: str, add_labels: list[str] = None, remove_labels: list[str] = None) -> dict:
    svc = _service()
    body = {
        "addLabelIds": add_labels or [],
        "removeLabelIds": remove_labels or [],
    }
    result = svc.users().messages().modify(userId="me", id=message_id, body=body).execute()
    return {"id": result["id"], "labelIds": result.get("labelIds", [])}


def list_labels() -> list[dict]:
    svc = _service()
    result = svc.users().labels().list(userId="me").execute()
    return [{"id": l["id"], "name": l["name"]} for l in result.get("labels", [])]


def create_label(name: str) -> dict:
    svc = _service()
    label = svc.users().labels().create(
        userId="me", body={"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
    ).execute()
    return {"id": label["id"], "name": label["name"]}


def archive_message(message_id: str) -> dict:
    return label_message(message_id, remove_labels=["INBOX"])


def trash_message(message_id: str) -> dict:
    svc = _service()
    result = svc.users().messages().trash(userId="me", id=message_id).execute()
    return {"id": result["id"]}


def mark_read(message_id: str) -> dict:
    return label_message(message_id, remove_labels=["UNREAD"])


def mark_unread(message_id: str) -> dict:
    return label_message(message_id, add_labels=["UNREAD"])
