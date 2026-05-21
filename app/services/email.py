"""SMTP email sender. Single outbound path: inquiry notification."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from flask import current_app, url_for

from app.models import Inquiry

logger = logging.getLogger(__name__)


def send_inquiry_notification(inq: Inquiry) -> None:
    cfg = current_app.config
    host = cfg.get("SMTP_HOST")
    if not host:
        logger.info("SMTP_HOST not configured; skipping notification for inquiry %s", inq.id)
        return

    msg = EmailMessage()
    msg["Subject"] = f"[Grog Blossoms] New {inq.kind} inquiry from {inq.from_name}"
    msg["From"] = cfg["SMTP_FROM"]
    msg["To"] = cfg["CONTACT_EMAIL"]
    msg.set_content(_format_body(inq))

    try:
        with smtplib.SMTP(host, cfg.get("SMTP_PORT", 587), timeout=10) as s:
            s.starttls()
            if cfg.get("SMTP_USER"):
                s.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
            s.send_message(msg)
    except Exception:
        logger.exception("Failed to send inquiry notification for inquiry %s", inq.id)


def _format_body(inq: Inquiry) -> str:
    try:
        link = url_for("admin.inquiries_detail", id=inq.id, _external=True)
    except Exception:
        link = f"/admin/inquiries/{inq.id}"
    lines = [
        f"Kind:     {inq.kind}",
        f"From:     {inq.from_name} <{inq.email}>",
    ]
    if inq.phone:
        lines.append(f"Phone:    {inq.phone}")
    if inq.event_date:
        lines.append(f"Event:    {inq.event_date}")
    if inq.venue:
        lines.append(f"Venue:    {inq.venue}")
    if inq.city:
        lines.append(f"City:     {inq.city}")
    lines += ["", "Message:", "--------", inq.message, "", f"Admin: {link}"]
    return "\n".join(lines)
