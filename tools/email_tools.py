from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import find_by_id, read_json, write_json


def search_email(runtime_dir: Path, query: str) -> dict[str, Any]:
    emails = read_json(runtime_dir / "emails.json", [])
    needle = query.casefold()
    matches = [
        {"id": item["id"], "sender": item["sender"], "subject": item["subject"]}
        for item in emails
        if needle in " ".join(
            [item.get("sender", ""), item.get("subject", ""), item.get("body", "")]
        ).casefold()
    ]
    return {"matches": matches}


def read_email(runtime_dir: Path, email_id: str) -> dict[str, Any]:
    email = find_by_id(read_json(runtime_dir / "emails.json", []), email_id)
    return {"email": email} if email else {"error": "email_not_found"}


def send_email(runtime_dir: Path, to: str, subject: str, body: str) -> dict[str, Any]:
    outbox_path = runtime_dir / "outbox.json"
    outbox = read_json(outbox_path, [])
    item = {
        "id": f"out-{len(outbox) + 1:03d}",
        "to": to,
        "subject": subject,
        "body": body,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }
    outbox.append(item)
    write_json(outbox_path, outbox)
    return {"sent": True, "message_id": item["id"]}
