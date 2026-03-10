from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List

from config import settings

try:  # pragma: no cover
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except Exception:  # pragma: no cover
    colors = None
    A4 = None
    ParagraphStyle = None
    getSampleStyleSheet = None
    cm = None
    canvas = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None


@dataclass(frozen=True)
class ReportMeta:
    month: date
    pdf_path: str


class ReportTool:
    def __init__(self, reports_dir: str | None = None) -> None:
        self.reports_dir = reports_dir or settings.REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate(self, user_id: str, stats: Dict[str, any], words: List[Dict[str, str]]) -> str:
        """
        Generate a monthly PDF report using ReportLab.
        """
        if SimpleDocTemplate is None:  # ReportLab not available
            return ""

        year = stats.get("year", date.today().year)
        month_num = stats.get("month", date.today().month)
        month_name = stats.get("month_name", date(year, month_num, 1).strftime("%B"))

        filename = os.path.join(self.reports_dir, f"{user_id}_report_{year}_{month_num}.pdf")
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()

        elements: List[object] = []

        # PAGE 1 — Cover
        def cover(canvas_obj, doc_obj):  # pragma: no cover
            canvas_obj.saveState()
            w, h = A4
            canvas_obj.setFillColor(colors.HexColor("#0f0f0f"))
            canvas_obj.rect(0, 0, w, h, stroke=0, fill=1)
            canvas_obj.setFillColor(colors.white)
            canvas_obj.setFont("Helvetica-Bold", 32)
            canvas_obj.drawCentredString(w / 2, h - 5 * cm, "🎬 CineEnglish")
            canvas_obj.setFont("Helvetica", 18)
            canvas_obj.drawCentredString(w / 2, h - 7 * cm, "Monthly Learning Report")
            canvas_obj.setFont("Helvetica", 14)
            canvas_obj.drawCentredString(w / 2, h - 9 * cm, f"{month_name} {year}")
            level_start = stats.get("level_start", "B1")
            level_end = stats.get("level_end", "B1")
            canvas_obj.setFont("Helvetica-Bold", 16)
            canvas_obj.drawCentredString(w / 2, h - 11 * cm, f"Level: {level_start} → {level_end}")
            canvas_obj.restoreState()

        doc.build([], onFirstPage=cover)

        # PAGE 2 — Summary Stats
        words_learned = stats.get("words_learned", 0)
        words_retained = stats.get("words_retained", 0)
        quizzes_taken = stats.get("quizzes_taken", 0)
        avg_score = stats.get("avg_score", 0)
        hours_watched = stats.get("hours_watched", 0.0)

        level_start = stats.get("level_start", "B1")
        level_end = stats.get("level_end", "B1")

        doc2 = SimpleDocTemplate(filename, pagesize=A4)
        elements = []
        title_style = styles["Heading1"]
        title_style.textColor = colors.HexColor("#222222")
        elements.append(Paragraph("Your Month at a Glance", title_style))
        elements.append(Spacer(1, 12))

        data = [
            ["Words Learned", "Words Retained", "Quizzes Taken"],
            [str(words_learned), str(words_retained), str(quizzes_taken)],
            ["Avg Quiz Score", "Hours Watched", "Level Progress"],
            [f"{avg_score:.1f}%", f"{hours_watched:.1f} h", f"{level_start} → {level_end}"],
        ]
        table = Table(data, colWidths=[6 * cm, 6 * cm, 6 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                    ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#f0f0f0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("TEXTCOLOR", (0, 2), (-1, 2), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, 1), 16),
                    ("FONTSIZE", (0, 3), (-1, 3), 16),
                    ("BOX", (0, 0), (-1, -1), 0.25, colors.gray),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.gray),
                ]
            )
        )
        elements.append(table)
        doc2.build(elements)

        # PAGE 3 — Vocabulary Highlights
        doc3 = SimpleDocTemplate(filename, pagesize=A4)
        elements = []
        elements.append(Paragraph("Top Words You Learned", title_style))
        elements.append(Spacer(1, 12))

        table_data = [["Word", "Definition", "Source"]]
        for w in words[:15]:
            table_data.append(
                [
                    w.get("word", ""),
                    w.get("definition", "")[:120],
                    w.get("source_title", ""),
                ]
            )
        vocab_table = Table(table_data, colWidths=[4 * cm, 9 * cm, 4 * cm])
        vocab_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOX", (0, 0), (-1, -1), 0.25, colors.gray),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.gray),
                ]
            )
        )
        elements.append(vocab_table)
        doc3.build(elements)

        # PAGE 4 — Progress & Next Steps
        doc4 = SimpleDocTemplate(filename, pagesize=A4)
        elements = []
        elements.append(Paragraph("Progress & Next Steps", title_style))
        elements.append(Spacer(1, 12))

        weak_areas = stats.get("weak_areas", [])
        top_sources = stats.get("top_sources", [])

        elements.append(Paragraph("Weak Areas to Focus On", styles["Heading2"]))
        for area in weak_areas:
            elements.append(Paragraph(f"• {area}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Content You Watched", styles["Heading2"]))
        for src in top_sources:
            elements.append(Paragraph(f"• {src}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Goals for Next Month", styles["Heading2"]))
        goals = [
            "Finish at least one full season or movie with active vocab practice.",
            "Review your weakest words twice per week.",
            "Try one new genre or show outside your comfort zone.",
        ]
        for g in goals:
            elements.append(Paragraph(f"• {g}", styles["Normal"]))

        elements.append(
            Spacer(1, 24)
        )
        elements.append(
            Paragraph(
                "Generated by CineEnglish • Keep watching, keep learning!",
                ParagraphStyle("Footer", alignment=1, textColor=colors.gray, fontSize=9),
            )
        )
        doc4.build(elements)

        return filename

    # Utility ----------------------------------------------------------
    def _level_to_num(self, level: str) -> int:
        mapping = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
        return mapping.get(level.upper(), 3)

