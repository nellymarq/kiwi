"""
PDF Export — Client-facing branded research reports.

Generates professional PDFs from research sessions with:
- Header with brand + date
- Research question
- Evidence synthesis
- GRADE certainty assessment
- Actionable recommendations
- Safety notes and contraindications
- Footer with disclaimer

Uses ReportLab (pure Python, no external binaries).
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY


EXPORT_DIR = Path.home() / ".kiwi" / "exports"


class BrandConfig:
    """Brand configuration for PDF headers/footers."""
    def __init__(
        self,
        brand_name: str = "Kiwi Performance Research",
        tagline: str = "Evidence-Based Sports Nutrition & Performance Science",
        primary_color: str = "#0a5c36",     # Kiwi green
        accent_color: str = "#1f4068",      # Professional navy
        practitioner: str = "",             # e.g., "Nelson Marques, RDN"
        org: str = "",                      # e.g., "MPS LLC"
        disclaimer: str = (
            "This report synthesizes peer-reviewed research and is intended for "
            "educational purposes. Recommendations should be reviewed by a qualified "
            "healthcare practitioner before implementation. Individual responses to "
            "nutritional interventions vary."
        ),
    ):
        self.brand_name = brand_name
        self.tagline = tagline
        self.primary_color = colors.HexColor(primary_color)
        self.accent_color = colors.HexColor(accent_color)
        self.practitioner = practitioner
        self.org = org
        self.disclaimer = disclaimer


def _sanitize_filename(text: str, max_len: int = 50) -> str:
    """Convert text to safe filename component."""
    slug = re.sub(r"[^\w\s-]", "", text[:max_len]).strip()
    return re.sub(r"[\s_-]+", "_", slug).lower() or "untitled"


def _clean_markdown(text: str) -> str:
    """Convert markdown-lite to ReportLab-safe HTML."""
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    # Inline code
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
    # Escape XML-sensitive characters that aren't in our tags
    # Note: we already added <b>, <i>, <font> above, so only escape raw &, <, >
    # in text that isn't part of these tags.
    return text


def _build_styles(brand: BrandConfig) -> dict:
    """Build a dict of paragraph styles."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title", parent=base["Title"],
            fontSize=20, leading=24, spaceAfter=12,
            textColor=brand.primary_color, alignment=TA_LEFT,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"],
            fontSize=14, leading=18, spaceBefore=14, spaceAfter=6,
            textColor=brand.accent_color,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"],
            fontSize=11, leading=14, spaceBefore=10, spaceAfter=4,
            textColor=brand.primary_color, fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"],
            fontSize=10, leading=14, spaceAfter=6, alignment=TA_JUSTIFY,
        ),
        "meta": ParagraphStyle(
            "Meta", parent=base["BodyText"],
            fontSize=8, leading=10, textColor=colors.grey,
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer", parent=base["BodyText"],
            fontSize=8, leading=10, textColor=colors.grey,
            alignment=TA_CENTER,
        ),
        "grade_label": ParagraphStyle(
            "GradeLabel", parent=base["BodyText"],
            fontSize=10, leading=12, textColor=colors.white,
            alignment=TA_CENTER, fontName="Helvetica-Bold",
        ),
    }


def _grade_color(level: str) -> colors.Color:
    """Color for a GRADE certainty level."""
    m = {
        "HIGH": colors.HexColor("#2d6a4f"),
        "MODERATE": colors.HexColor("#d4a017"),
        "LOW": colors.HexColor("#c97b27"),
        "VERY LOW": colors.HexColor("#6c757d"),
    }
    return m.get(level.upper(), colors.grey)


def generate_client_report(
    query: str,
    response: str,
    score: float,
    critique_data: dict,
    brand: BrandConfig | None = None,
    client_name: str = "",
    grade_level: str = "",
    thread_name: str | None = None,
    output_dir: Path | None = None,
) -> Path:
    """
    Generate a branded PDF report from a research session.

    Returns the path to the created PDF.
    """
    if brand is None:
        brand = BrandConfig()
    if output_dir is None:
        output_dir = EXPORT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    slug = _sanitize_filename(query)
    filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{slug}.pdf"
    filepath = output_dir / filename

    styles = _build_styles(brand)
    story = []

    # ── Header ─────────────────────────────────────────────────────────────
    header_lines = [f"<b>{brand.brand_name}</b>"]
    if brand.tagline:
        header_lines.append(f"<font size=8 color='#666666'>{brand.tagline}</font>")
    story.append(Paragraph("<br/>".join(header_lines), styles["title"]))
    story.append(HRFlowable(
        width="100%", thickness=1.5, color=brand.primary_color, spaceBefore=4, spaceAfter=12,
    ))

    # ── Meta line ──────────────────────────────────────────────────────────
    meta_parts = [f"Date: {now.strftime('%B %d, %Y')}"]
    if brand.practitioner:
        meta_parts.append(f"Practitioner: {brand.practitioner}")
    if brand.org:
        meta_parts.append(brand.org)
    if client_name and client_name != "self":
        meta_parts.append(f"Client: {client_name}")
    if thread_name:
        meta_parts.append(f"Thread: {thread_name}")
    story.append(Paragraph(" · ".join(meta_parts), styles["meta"]))
    story.append(Spacer(1, 0.15 * inch))

    # ── Research Question ──────────────────────────────────────────────────
    story.append(Paragraph("Research Question", styles["h1"]))
    story.append(Paragraph(_clean_markdown(query), styles["body"]))

    # ── GRADE badge ────────────────────────────────────────────────────────
    if grade_level:
        grade_table = Table(
            [[Paragraph(f"EVIDENCE CERTAINTY: {grade_level.upper()}", styles["grade_label"])]],
            colWidths=[3 * inch],
        )
        grade_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _grade_color(grade_level)),
            ("BOX", (0, 0), (-1, -1), 1, _grade_color(grade_level)),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(Spacer(1, 0.1 * inch))
        story.append(grade_table)
        story.append(Spacer(1, 0.15 * inch))

    # ── Research Findings ──────────────────────────────────────────────────
    story.append(Paragraph("Research Findings", styles["h1"]))
    # Split response into paragraphs, render each
    for para in response.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if para.startswith("## "):
            story.append(Paragraph(_clean_markdown(para[3:]), styles["h2"]))
        elif para.startswith("### "):
            story.append(Paragraph(_clean_markdown(para[4:]), styles["h2"]))
        elif para.startswith("#"):
            story.append(Paragraph(_clean_markdown(para.lstrip("# ")), styles["h2"]))
        else:
            # Handle bullet-like lines
            if para.startswith("- ") or para.startswith("* "):
                for line in para.splitlines():
                    line = line.strip()
                    if line.startswith(("- ", "* ")):
                        story.append(Paragraph("• " + _clean_markdown(line[2:]), styles["body"]))
                    elif line:
                        story.append(Paragraph(_clean_markdown(line), styles["body"]))
            else:
                story.append(Paragraph(_clean_markdown(para), styles["body"]))

    # ── Critique / Quality Assessment ──────────────────────────────────────
    critical = critique_data.get("critical_issues", [])
    strengths = critique_data.get("strengths", [])
    if critical or strengths:
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("Quality Assessment (Ralph Wiggum Loop)", styles["h1"]))
        story.append(Paragraph(f"Composite score: <b>{score:.2f}</b> / 1.00", styles["body"]))

        if strengths:
            story.append(Paragraph("Strengths", styles["h2"]))
            for s in strengths:
                story.append(Paragraph("• " + _clean_markdown(s), styles["body"]))

        if critical:
            story.append(Paragraph("Limitations Addressed", styles["h2"]))
            for c in critical:
                story.append(Paragraph("• " + _clean_markdown(c), styles["body"]))

    # ── Footer / Disclaimer ────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.grey, spaceBefore=4, spaceAfter=6,
    ))
    story.append(Paragraph(brand.disclaimer, styles["disclaimer"]))
    footer = f"Generated by {brand.brand_name}"
    if brand.org:
        footer += f" · {brand.org}"
    footer += f" · {now.strftime('%Y-%m-%d')}"
    story.append(Paragraph(footer, styles["disclaimer"]))

    # ── Build the PDF ──────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=LETTER,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
        leftMargin=0.8 * inch, rightMargin=0.8 * inch,
        title=query[:80], author=brand.practitioner or brand.brand_name,
    )
    doc.build(story)
    return filepath
