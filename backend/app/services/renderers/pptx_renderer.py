"""
PowerPoint Renderer — python-pptx branded presentation.
Slides: Cover | KPI Summary | Platform Table | Daily Chart | Thank You
"""

from pptx import Presentation
from pptx.chart.data import ChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Cm, Pt

from app.services.report_generator import ReportData


def _rgb(hex_color: str) -> RGBColor:
    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


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


class PptxRenderer:

    SLIDE_W = Cm(33.87)   # 16:9 widescreen
    SLIDE_H = Cm(19.05)

    def __init__(self, data: ReportData):
        self.data = data
        self.primary   = _rgb(data.brand_primary)
        self.secondary = _rgb(data.brand_secondary)
        self.prs = Presentation()
        self.prs.slide_width  = self.SLIDE_W
        self.prs.slide_height = self.SLIDE_H
        # Use blank layout for full design control
        self.blank_layout = self.prs.slide_layouts[6]

    def render(self, output_path: str):
        self._slide_cover()
        self._slide_kpis()
        self._slide_platform_table()
        self._slide_daily_chart()
        self._slide_thank_you()
        self.prs.save(output_path)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _add_slide(self):
        return self.prs.slides.add_slide(self.blank_layout)

    def _add_rect(self, slide, x, y, w, h, color: RGBColor):
        shape = slide.shapes.add_shape(1, x, y, w, h)  # MSO_SHAPE_TYPE.RECTANGLE=1
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.fill.background()
        return shape

    def _add_text(self, slide, text, x, y, w, h,
                  size=18, bold=False, color=None, align=PP_ALIGN.LEFT):
        tb = slide.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = align
        run = p.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color or RGBColor(0x37, 0x41, 0x51)
        return tb

    def _header_bar(self, slide, title: str):
        """Branded top bar with title on every slide."""
        self._add_rect(slide, 0, 0, self.SLIDE_W, Cm(1.8), self.primary)
        self._add_text(
            slide, title, Cm(0.8), Cm(0.2), self.SLIDE_W - Cm(1.6), Cm(1.4),
            size=16, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF),
        )

    def _footer(self, slide):
        self._add_text(
            slide,
            f"{self.data.client_name}  |  {self.data.generated_at.strftime('%B %Y')}",
            Cm(0.5), self.SLIDE_H - Cm(0.8), self.SLIDE_W - Cm(1), Cm(0.7),
            size=8, color=RGBColor(0x9C, 0xA3, 0xAF),
        )

    # ── Slides ────────────────────────────────────────────────────────────────

    def _slide_cover(self):
        slide = self._add_slide()
        d = self.data

        # Full background accent
        self._add_rect(slide, 0, 0, self.SLIDE_W, self.SLIDE_H, self.primary)
        # White content area
        self._add_rect(slide, Cm(2), Cm(3.5), self.SLIDE_W - Cm(4), Cm(9), RGBColor(0xFF, 0xFF, 0xFF))

        self._add_text(
            slide, d.title,
            Cm(3), Cm(4.2), self.SLIDE_W - Cm(6), Cm(3),
            size=32, bold=True, color=self.primary, align=PP_ALIGN.LEFT,
        )
        self._add_text(
            slide, d.client_name,
            Cm(3), Cm(7.5), self.SLIDE_W - Cm(6), Cm(1.5),
            size=18, bold=False, color=self.secondary,
        )
        period = f"{d.date_from.strftime('%B %d, %Y')} — {d.date_to.strftime('%B %d, %Y')}"
        self._add_text(
            slide, period,
            Cm(3), Cm(9), self.SLIDE_W - Cm(6), Cm(1.2),
            size=12, color=RGBColor(0x6B, 0x72, 0x80),
        )

    def _slide_kpis(self):
        slide = self._add_slide()
        self._header_bar(slide, "Executive Summary")
        self._footer(slide)

        k = self.data.kpis
        kpis = [
            ("Total Spend",  _fmt_currency(k.total_spend)),
            ("Impressions",  _fmt_number(k.total_impressions)),
            ("Clicks",       _fmt_number(k.total_clicks)),
            ("Conversions",  _fmt_number(k.total_conversions)),
            ("Avg CTR",      f"{k.avg_ctr:.2f}%"),
            ("Avg CPC",      _fmt_currency(k.avg_cpc)),
            ("Avg CPM",      _fmt_currency(k.avg_cpm)),
            ("Avg ROAS",     f"{k.avg_roas:.2f}x"),
        ]

        card_w = Cm(7.5)
        card_h = Cm(3.8)
        gap    = Cm(0.6)
        start_x = Cm(1.2)
        start_y = Cm(2.5)

        for i, (label, value) in enumerate(kpis):
            col = i % 4
            row = i // 4
            x = start_x + col * (card_w + gap)
            y = start_y + row * (card_h + gap)

            # Card background
            bg = slide.shapes.add_shape(1, x, y, card_w, card_h)
            bg.fill.solid()
            bg.fill.fore_color.rgb = RGBColor(0xF9, 0xFA, 0xFB)
            bg.line.color.rgb = RGBColor(0xE5, 0xE7, 0xEB)
            bg.line.width = Pt(0.75)

            # Value
            self._add_text(
                slide, value,
                x + Cm(0.3), y + Cm(0.3), card_w - Cm(0.6), Cm(2),
                size=24, bold=True, color=self.primary, align=PP_ALIGN.CENTER,
            )
            # Label
            self._add_text(
                slide, label,
                x + Cm(0.3), y + Cm(2.5), card_w - Cm(0.6), Cm(1),
                size=10, color=RGBColor(0x6B, 0x72, 0x80), align=PP_ALIGN.CENTER,
            )

    def _slide_platform_table(self):
        slide = self._add_slide()
        self._header_bar(slide, "Performance by Platform")
        self._footer(slide)

        if not self.data.platforms:
            return

        cols   = ["Platform", "Spend", "Impressions", "Clicks", "Conv.", "CTR", "CPC", "ROAS"]
        widths = [Cm(5), Cm(3.2), Cm(4), Cm(3), Cm(2.8), Cm(2.5), Cm(3), Cm(3)]
        rows   = [[
            p.platform, _fmt_currency(p.spend), _fmt_number(p.impressions),
            _fmt_number(p.clicks), _fmt_number(p.conversions),
            f"{p.ctr:.2f}%", _fmt_currency(p.cpc), f"{p.roas:.2f}x",
        ] for p in self.data.platforms]

        tbl = slide.shapes.add_table(
            len(rows) + 1, len(cols),
            Cm(0.5), Cm(2.2),
            sum(widths), Cm(1.0) * (len(rows) + 1),
        ).table

        for ci, (col_name, w) in enumerate(zip(cols, widths)):
            tbl.columns[ci].width = w
            cell = tbl.cell(0, ci)
            cell.text = col_name
            cell.fill.solid()
            cell.fill.fore_color.rgb = self.primary
            para = cell.text_frame.paragraphs[0]
            para.alignment = PP_ALIGN.CENTER
            run = para.runs[0]
            run.font.bold = True
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        for ri, row in enumerate(rows):
            bg_color = RGBColor(0xF9, 0xFA, 0xFB) if ri % 2 else RGBColor(0xFF, 0xFF, 0xFF)
            for ci, val in enumerate(row):
                cell = tbl.cell(ri + 1, ci)
                cell.text = str(val)
                cell.fill.solid()
                cell.fill.fore_color.rgb = bg_color
                para = cell.text_frame.paragraphs[0]
                para.alignment = PP_ALIGN.CENTER
                para.runs[0].font.size = Pt(9)

    def _slide_daily_chart(self):
        if not self.data.daily:
            return

        slide = self._add_slide()
        self._header_bar(slide, "Daily Spend Trend")
        self._footer(slide)

        chart_data = ChartData()
        chart_data.categories = [pt.date[-5:] for pt in self.data.daily]
        chart_data.add_series("Spend ($)", [pt.spend for pt in self.data.daily])

        chart = slide.shapes.add_chart(
            XL_CHART_TYPE.COLUMN_CLUSTERED,
            Cm(1), Cm(2), Cm(31), Cm(14),
            chart_data,
        ).chart

        chart.series[0].format.fill.solid()
        chart.series[0].format.fill.fore_color.rgb = self.primary
        chart.has_legend = False
        chart.value_axis.has_title = True
        chart.value_axis.axis_title.text_frame.text = "Spend ($)"
        chart.category_axis.has_title = True
        chart.category_axis.axis_title.text_frame.text = "Date"

    def _slide_thank_you(self):
        slide = self._add_slide()
        self._add_rect(slide, 0, 0, self.SLIDE_W, self.SLIDE_H, self.secondary)

        self._add_text(
            slide, "Thank You",
            Cm(4), Cm(6), self.SLIDE_W - Cm(8), Cm(3),
            size=40, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF),
            align=PP_ALIGN.CENTER,
        )
        self._add_text(
            slide, self.data.client_name,
            Cm(4), Cm(9.5), self.SLIDE_W - Cm(8), Cm(2),
            size=18, color=RGBColor(0xBF, 0xDB, 0xF7),
            align=PP_ALIGN.CENTER,
        )
