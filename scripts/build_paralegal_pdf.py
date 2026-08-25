from __future__ import annotations

import re
from html import escape
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "paralegal-enablement.md"
OUTPUT = ROOT / "docs" / "paralegal-enablement.pdf"


def inline_markup(text: str) -> str:
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(
        r"(https://[^\s<]+)",
        r"<link href='\1' color='#174A7E'>\1</link>",
        text,
    )
    return text


def build_story(markdown: str):
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitlePlain",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=20,
        alignment=TA_CENTER,
        textColor=HexColor("#1F2933"),
        spaceAfter=7,
    )
    heading = ParagraphStyle(
        "HeadingPlain",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=11.5,
        textColor=HexColor("#1F2933"),
        spaceBefore=4.5,
        spaceAfter=2,
        keepWithNext=True,
    )
    body = ParagraphStyle(
        "BodyPlain",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=10.2,
        textColor=HexColor("#202124"),
        spaceAfter=2.3,
    )
    bullet = ParagraphStyle(
        "BulletPlain",
        parent=body,
        leftIndent=11,
        firstLineIndent=-7,
        bulletIndent=3,
        spaceAfter=1.2,
    )

    story = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            story.append(Paragraph(inline_markup(" ".join(paragraph_lines)), body))
            paragraph_lines.clear()

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            continue
        if line.startswith("# "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[2:]), title))
            story.append(Spacer(1, 1))
        elif line.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[3:]), heading))
        elif line.startswith("- "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[2:]), bullet, bulletText="-"))
        elif re.match(r"^\d+\. ", line):
            flush_paragraph()
            number, item = line.split(". ", 1)
            story.append(Paragraph(inline_markup(item), bullet, bulletText=f"{number}."))
        else:
            paragraph_lines.append(line)
    flush_paragraph()
    return story


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(HexColor("#D7DCE1"))
    canvas.line(0.55 * inch, 0.43 * inch, 7.95 * inch, 0.43 * inch)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(HexColor("#5F6368"))
    canvas.drawString(0.55 * inch, 0.27 * inch, "IntakeTrace - synthetic assessment service")
    canvas.drawRightString(7.95 * inch, 0.27 * inch, f"Page {doc.page}")
    canvas.restoreState()


def main() -> None:
    document = BaseDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.42 * inch,
        bottomMargin=0.52 * inch,
        title="IntakeTrace: quick guide for intake staff",
        author="IntakeTrace",
        subject="Plain-language paralegal enablement guide",
    )
    frame = Frame(
        document.leftMargin,
        document.bottomMargin,
        document.width,
        document.height,
        id="body",
    )
    document.addPageTemplates(PageTemplate(id="plain", frames=[frame], onPage=footer))
    document.build(build_story(SOURCE.read_text(encoding="utf-8")))
    print(OUTPUT)


if __name__ == "__main__":
    main()
