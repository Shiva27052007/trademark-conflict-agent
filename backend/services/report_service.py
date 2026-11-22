"""PDF report generator using ReportLab."""

from pathlib import Path
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)

from backend.core.config import REPORTS_DIR


class PDFReportGenerator:
    """Generates PDF trademark screening reports."""

    def __init__(self):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def generate(self, report_data: dict) -> str:
        """Generate a PDF report and return the file path."""
        screening_id = report_data.get("screening_id", "UNKNOWN")
        filename = f"screening_report_{screening_id}.pdf"
        filepath = REPORTS_DIR / filename

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontSize=20,
            spaceAfter=12,
            textColor=colors.HexColor("#1a237e"),
        ))
        styles.add(ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading2"],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.HexColor("#0d47a1"),
        ))
        styles.add(ParagraphStyle(
            name="Disclaimer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.gray,
            spaceAfter=6,
        ))

        elements = []

        # Title
        elements.append(Paragraph("Trademark Conflict Screening Report", styles["ReportTitle"]))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a237e")))
        elements.append(Spacer(1, 12))

        # Summary
        elements.append(Paragraph("Screening Summary", styles["SectionHeader"]))
        summary_data = [
            ["Screening ID:", screening_id],
            ["Proposed Mark:", report_data.get("proposed_mark", "")],
            ["Jurisdiction:", report_data.get("jurisdiction", "")],
            ["Goods/Services:", report_data.get("goods_description", "")],
            ["Nice Classes:", str(report_data.get("nice_classes", []))],
            ["Screening Date:", report_data.get("screening_date", "")],
            ["Status:", report_data.get("status", "")],
            ["Search Coverage:", report_data.get("search_completeness", "")],
            ["Data Sources:", ", ".join(report_data.get("data_sources", []))],
        ]

        summary_table = Table(summary_data, colWidths=[120, 350])
        summary_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        # Matches
        matches = report_data.get("matches", [])
        elements.append(Paragraph(f"Candidate Matches ({len(matches)} found)", styles["SectionHeader"]))
        elements.append(Spacer(1, 8))

        if matches:
            header = ["Rank", "Mark", "Text", "Phone", "Goods", "Score", "Priority"]
            table_data = [header]

            for i, match in enumerate(matches[:20], 1):
                table_data.append([
                    str(i),
                    match.get("mark_name", ""),
                    f"{match.get('textual_similarity', 0):.0f}",
                    f"{match.get('phonetic_similarity', 0):.0f}",
                    f"{match.get('goods_overlap', 0):.0f}",
                    f"{match.get('combined_score', 0):.0f}",
                    match.get("priority", "").upper(),
                ])

            match_table = Table(table_data, colWidths=[35, 110, 50, 50, 50, 50, 70])
            match_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(match_table)

            # Detailed explanations for top 5
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("Detailed Analysis (Top 5)", styles["SectionHeader"]))

            for i, match in enumerate(matches[:5], 1):
                elements.append(Spacer(1, 8))
                elements.append(Paragraph(
                    f"{i}. {match.get('mark_name', '')} (ID: {match.get('trademark_id', '')})",
                    styles["Heading3"],
                ))
                explanation = match.get("explanation", "No explanation available.")
                # Sanitize for reportlab
                explanation = explanation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                explanation = explanation.replace("\n", "<br/>")
                elements.append(Paragraph(explanation, styles["Normal"]))
        else:
            elements.append(Paragraph("No candidate matches found.", styles["Normal"]))

        # Warnings
        warnings = report_data.get("warnings", [])
        if warnings:
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("Warnings", styles["SectionHeader"]))
            for w in warnings:
                elements.append(Paragraph(f"⚠ {w}", styles["Normal"]))

        # Disclaimer
        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(
            "LEGAL DISCLAIMER: This report is generated by an automated trademark "
            "conflict screening system using synthetic demonstration data. It provides "
            "preliminary screening results only and is NOT legal advice. It does NOT "
            "constitute a formal trademark clearance opinion. The results do not "
            "guarantee that no conflicting trademarks exist. Always consult a qualified "
            "trademark attorney before making trademark filing or business decisions. "
            "Automated screening is not a substitute for professional trademark clearance.",
            styles["Disclaimer"],
        ))
        elements.append(Paragraph(
            f"Report generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} "
            f"by Trademark Conflict Screening Agent v1.0",
            styles["Disclaimer"],
        ))

        doc.build(elements)
        return str(filepath)


# Module-level singleton
pdf_generator = PDFReportGenerator()
