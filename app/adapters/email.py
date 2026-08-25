from __future__ import annotations

from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import parsedate_to_datetime

from app.models import Channel, NormalizedIntake, SourceMetadata


def normalize_email(raw_email: str | bytes, *, intake_id: str) -> NormalizedIntake:
    payload = raw_email.encode("utf-8") if isinstance(raw_email, str) else raw_email
    message = BytesParser(policy=policy.default).parsebytes(payload)
    sender = str(message.get("From", "")).strip()
    subject = str(message.get("Subject", "")).strip()
    message_id = str(message.get("Message-ID", "")).strip().strip("<>")
    date_header = str(message.get("Date", "")).strip()

    if not sender or not subject or not message_id or not date_header:
        raise ValueError("email is missing a required From, Subject, Message-ID, or Date header")

    body = _plain_text_body(message).strip()
    if not body:
        raise ValueError("email does not contain a plain-text body")

    return NormalizedIntake(
        intake_id=intake_id,
        source=SourceMetadata(
            type=Channel.REFERRAL_EMAIL,
            provider="rfc822_email",
            external_id=message_id,
            received_at=parsedate_to_datetime(date_header),
        ),
        source_text=f"From: {sender}\nSubject: {subject}\n\n{body}",
    )


def _plain_text_body(message: Message) -> str:
    if message.is_multipart():
        part = message.get_body(preferencelist=("plain",))
        if part is None:
            raise ValueError("email does not contain a plain-text body")
        return str(part.get_content())
    return str(message.get_content())
