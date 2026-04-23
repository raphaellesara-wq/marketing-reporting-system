"""
PDF Renderer — ReportLab-based branded PDF report.
Sections: Cover → KPI Summary → Platform Breakdown → Spend Chart → Daily Table
"""

import io
import os
from datetime import datetime
from typing import List, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF

from app.services.report_generator import ReportData


def _hex_to_rgb(hex_color: str):
    """Convert #RRGGBB to ReportLab Color."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return colors.Color(r / 255, g / 255, b / 255)


def _fmt_currency(v: float) -> str:
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:.2f}"


def _fmt_number(v: float) -> str:
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.1f}K"
    return f"{v:,.0f}"


class PdfRenderer:

    PAGE_W, PAGE_H = A4

    def __init__(self, data: ReportData):
        self.data = data
        self.primary = _hex_to_rgb(data.brand_primary)
        self.secondary = _hex_to_rgb(data.brand_secondary)
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        d = self.data
        self.h1 = ParagraphStyle(
            "H1", fontSize=28, textColor=self.primary,
            spaceAfter=6, alignment=TA_LEFT, fontName="Helvetica-Bold",
        )
        self.h2 = ParagraphStyle(
            "H2", fontSize=16, textColor=self.secondary,
            spaceBefore=12, spaceAfter=6, fontName="Helvetica-Bold",
        )
        self.body = ParagraphStyle(
            "Body", fontSize=10, textColor=colors.HexColor("#374151"),
            spaceAfter=4, fontName="Helvetica",
        )
        self.small = ParagraphStyle(
            "Small", fontSize=8, textColor=colors.HexColor("#6B7280"),
            fontName="Helvetica",
        )
        self.kpi_value = ParagraphStyle(
            "KPIValue", fontSize=22, textColor=self.primary,
            alignment=TA_CENTER, fontName="Helvetica-Bold",
        )
        self.kpi_label = ParagraphStyle(
            "KPILabel", fontSize=9, textColor=colors.HexColor("#6B7280"),
            alignment=TA_CENTER, fontName="Helvetica",
        )

    # ── Public entry point ────────────────────────────────────────────────────

    def render(self, output_path: str):
        doc = BaseDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm,
        )

        frame = Frame(
            doc.leftMargin, doc.bottomMargin,
            doc.width, doc.height,
            id="main",
        )

        def header_footer(canvas, doc):
            canvas.saveState()
            # Header bar
            canvas.setFillColor(self.primary)
            canvas.rect(0, self.PAGE_H - 1.2 * cm, self.PAGE_W, 1.2 * cm, fill=1, stroke=0)
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawString(2 * cm, self.PAGE_H - 0.85 * cm, self.data.client_name)
            canvas.drawRightString(
                self.PAGE_W - 2 * cm, self.PAGE_H - 0.85 * cm, self.data.title
            )
            # Footer
            canvas.setFillColor(colors.HexColor("#9CA3AF"))
            canvas.setFont("Helvetica", 8)
            canvas.drawString(2 * cm, 0.7 * cm, f"Generated {self.data.generated_at.strftime('%B %d, %Y')}")
            canvas.drawRightString(
                self.PAGE_W - 2 * cm, 0.7 * cm, f"Page {doc.page}"
            )
            canvas.restoreState()

        template = PageTemplate(id="main", frames=[frame], onPage=header_footer)
        doc.addPageTemplates([template])

        story = []
        story += self._cover_section()
        story.append(PageBreak())
        story += self._kpi_section()
        story += self._platform_table()
        story += self._spend_chart()
        story += self._daily_table()

        doc.build(story)

    # ── Sections ──────────────────────────────────────────────────────────────

    def _cover_section(self) -> list:
        d = self.data
        story = [Spacer(1, 3 * cm)]

        # Logo
        if d.logo_path and os.path.exists(d.logo_path):
            story.append(Image(d.logo_path, width=5 * cm, height=2 * cm,
                               kind="proportional"))
            story.append(Spacer(1, 0.5 * cm))

        story.append(Paragraph(d.title, self.h1))
        story.append(HRFlowable(width="100%", thickness=3,
                                color=self.primary, spaceAfter=12))
        story.append(Paragraph(d.client_name, self.h2))
        if d.client_company:
            story.append(Paragraph(d.client_company, self.body))

        story.append(Spacer(1, 1 * cm))
        date_str = (
            f"{d.date_from.strftime('%B %d, %Y')} — {d.date_to.strftime('%B %d, %Y')}"
        )
        story.append(Paragraph(f"Report Period: {date_str}", self.body))
        story.append(Paragraph(
            f"Generated: {d.generated_at.strftime('%B %d, %Y at %H:%M UTC')}",
            self.small,
        ))
        return story

    def _kpi_section(self) -> list:
        k = self.data.kpis
        story = [Paragraph("Executive Summary", self.h2)]
        story.append(HRFlowable(width="100%", thickness=1,
                                color=self.secondary, spaceAfter=8))

        kpi_items = [
            ("Total Spend",       _fmt_currency(k.total_spend)),
            ("Impressions",       _fmt_number(k.total_impressions)),
            ("Clicks",            _fmt_number(k.total_clicks)),
            ("Conversions",       _fmt_number(k.total_conversions)),
            ("Avg CTR",           f"{k.avg_ctr:.2f}%"),
            ("Avg CPC",           _fmt_currency(k.avg_cpc)),
            ("Avg CPM",           _fmt_currency(k.avg_cpm)),
            ("Avg ROAS",          f"{k.avg_roas:.2f}x"),
        ]

        col_w = self.PAGE_W / 4 - 1.5 * cm
        rows = [kpi_items[:4], kpi_items[4:]]
        for row in rows:
            cells = []
            for label, value in row:
                cell = [
                    Paragraph(value, self.kpi_value),
                    Paragraph(label, self.kpi_label),
                ]
                cells.append(cell)
            t = Table([cells], colWidths=[col_w] * 4)
            t.setStyle(TableStyle([
                ("BOX",        (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("INNERGRID",  (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
                ("ROWPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3 * cm))
        return story

    def _platform_table(self) -> list:
        story = [
            Spacer(1, 0.5 * cm),
            Paragraph("Performance by Platform", self.h2),
            HRFlowable(width="100%", thickness=1, color=self.secondary, spaceAfter=8),
        ]

        headers = ["Platform", "Spend", "Impressions", "Clicks", "Conv.", "CTR", "CPC", "ROAS"]
        col_widths = [3.5 * cm, 2 * cm, 2.5 * cm, 2 * cm, 1.8 * cm, 1.8 * cm, 2 * cm, 2 * cm]

        header_style = ParagraphStyle(
            "TH", fontSize=9, textColor=colors.white,
            alignment=TA_CENTER, fontName="Helvetica-Bold",
        )
        cell_style = ParagraphStyle(
            "TD", fontSize=9, textColor=colors.HexColor("#374151"),
            alignment=TA_CENTER, fontName="Helvetica",
        )

        table_data = [[Paragraph(h, header_style) for h in headers]]
        for p in self.data.platforms:
            table_data.append([
                Paragraph(p.platform,                   cell_style),
                Paragraph(_fmt_currency(p.spend),        cell_style),
                Paragraph(_fmt_number(p.impressions),    cell_style),
                Paragraph(_fmt_number(p.clicks),         cell_style),
                Paragraph(_fmt_number(p.conversions),    cell_style),
                Paragraph(f"{p.ctr:.2f}%",              cell_style),
                Paragraph(_fmt_currency(p.cpc),          cell_style),
                Paragraph(f"{p.roas:.2f}x",             cell_style),
            ])

        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0),  self.primary),
            ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F9FAFB")]),
            ("BOX",          (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("INNERGRID",    (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
            ("TOPPADDING",   (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        return story

    def _spend_chart(self) -> list:
        if not self.data.daily:
            return []

        story = [
            Spacer(1, 0.8 * cm),
            Paragraph("Daily Spend Trend", self.h2),
            HRFlowable(width="100%", thickness=1, color=self.secondary, spaceAfter=8),
        ]

        chart_w, chart_h = 16 * cm, 7 * cm
        drawing = Drawing(chart_w, chart_h)

        bc = VerticalBarChart()
        bc.x, bc.y = 1.5 * cm, 1 * cm
        bc.width  = chart_w - 2.5 * cm
        bc.height = chart_h - 1.5 * cm

        spend_values = [pt.spend for pt in self.data.daily]
        bc.data = [spend_values]
        bc.categoryAxis.categoryNames = [pt.date[-5:] for pt in self.data.daily]
        bc.categoryAxis.labels.fontSize = 7
        bc.categoryAxis.labels.angle = 30
        bc.valueAxis.labels.fontSize = 8
        bc.bars[0].fillColor = self.primary
        bc.bars[0].strokeColor = None

        drawing.add(bc)
        story.append(drawing)
        return story

    def _daily_table(self) -> list:
        if not self.data.daily:
            return []

        story = [
            Spacer(1, 0.5 * cm),
            Paragraph("Daily Breakdown", self.h2),
            HRFlowable(width="100%", thickness=1, color=self.secondary, spaceAfter=8),
        ]

        headers = ["Date", "Spend", "Clicks", "Conversions"]
        col_widths = [4 * cm, 4 * cm, 4 * cm, 4 * cm]

        header_style = ParagraphStyle(
            "TH2", fontSize=9, textColor=colors.white,
            alignment=TA_CENTER, fontName="Helvetica-Bold",
        )
        cell_style = ParagraphStyle(
            "TD2", fontSize=9, textColor=colors.HexColor("#374151"),
            alignment=TA_CENTER, fontName="Helvetica",
        )

        table_data = [[Paragraph(h, header_style) for h in headers]]
        for pt in self.data.daily:
            table_data.append([
                Paragraph(pt.date,                    cell_style),
                Paragraph(_fmt_currency(pt.spend),     cell_style),
                Paragraph(_fmt_number(pt.clicks),      cell_style),
                Paragraph(_fmt_number(pt.conversions), cell_style),
            ])

        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0), self.primary),
            ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F9FAFB")]),
            ("BOX",            (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("INNERGRID",      (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
            ("TOPPADDING",     (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 7),
        ]))
        story.append(t)
        return story
