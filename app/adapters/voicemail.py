from __future__ import annotations

from app.adapters.common import parse_labelled_lines, required
from app.models import Channel, NormalizedIntake, SourceMetadata


def normalize_voicemail(raw_text: str, *, intake_id: str) -> NormalizedIntake:
    header_text, separator, transcript = raw_text.replace("\r\n", "\n").partition("\n\n")
    if not separator or not transcript.strip():
        raise ValueError("voicemail input must contain metadata followed by transcript text")

    header_lines = header_text.splitlines()
    if not header_lines or header_lines[0].strip() != "VOICEMAIL TRANSCRIPT":
        raise ValueError("voicemail input is missing the VOICEMAIL TRANSCRIPT heading")

    metadata = parse_labelled_lines(header_lines[1:])
    return NormalizedIntake(
        intake_id=intake_id,
        source=SourceMetadata(
            type=Channel.VOICEMAIL,
            provider="transcript_webhook",
            external_id=required(metadata, "Call ID"),
            received_at=required(metadata, "Received at"),
        ),
        source_text=transcript.strip(),
    )
