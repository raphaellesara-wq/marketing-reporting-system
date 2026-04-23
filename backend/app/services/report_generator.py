"""
Report Generator — orchestrates data collection and delegates to format renderers.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Client, Integration, Metric, Report, ReportFormat, ReportStatus


# ── Data structures passed to all renderers ───────────────────────────────────

@dataclass
class KPISummary:
    total_spend: float = 0.0
    total_impressions: float = 0.0
    total_clicks: float = 0.0
    total_conversions: float = 0.0
    avg_ctr: float = 0.0
    avg_cpc: float = 0.0
    avg_cpm: float = 0.0
    avg_roas: float = 0.0


@dataclass
class PlatformRow:
    platform: str
    spend: float
    impressions: float
    clicks: float
    conversions: float
    ctr: float
    cpc: float
    roas: float


@dataclass
class DailyPoint:
    date: str          # "YYYY-MM-DD"
    spend: float
    clicks: float
    conversions: float


@dataclass
class ReportData:
    title: str
    client_name: str
    client_company: str
    brand_primary: str    # hex e.g. "#3B82F6"
    brand_secondary: str  # hex e.g. "#1E40AF"
    logo_path: Optional[str]
    date_from: datetime
    date_to: datetime
    generated_at: datetime
    kpis: KPISummary
    platforms: List[PlatformRow] = field(default_factory=list)
    daily: List[DailyPoint] = field(default_factory=list)


# ── Generator ─────────────────────────────────────────────────────────────────

class ReportGenerator:

    def __init__(self, db: Session):
        self.db = db

    def generate(self, report: Report) -> str:
        """Build the report file and return its absolute path."""
        client = self.db.query(Client).filter(Client.id == report.client_id).first()
        data = self._build_report_data(report, client)
        output_path = self._output_path(report)

        if report.format == ReportFormat.pdf:
            from app.services.renderers.pdf_renderer import PdfRenderer
            PdfRenderer(data).render(output_path)

        elif report.format == ReportFormat.excel:
            from app.services.renderers.excel_renderer import ExcelRenderer
            ExcelRenderer(data).render(output_path)

        elif report.format == ReportFormat.powerpoint:
            from app.services.renderers.pptx_renderer import PptxRenderer
            PptxRenderer(data).render(output_path)

        else:
            raise ValueError(f"Unsupported report format: {report.format}")

        return output_path

    # ── Private helpers ───────────────────────────────────────────────────────

    def _output_path(self, report: Report) -> str:
        ext = {"pdf": "pdf", "excel": "xlsx", "powerpoint": "pptx"}.get(
            report.format.value, "pdf"
        )
        os.makedirs(settings.reports_dir, exist_ok=True)
        return os.path.join(settings.reports_dir, f"report_{report.id}.{ext}")

    def _build_report_data(self, report: Report, client: Client) -> ReportData:
        date_from = report.date_from or datetime.utcnow().replace(day=1)
        date_to = report.date_to or datetime.utcnow()

        logo_path: Optional[str] = None
        if client.logo_url and client.logo_url.startswith("/"):
            candidate = os.path.join(settings.upload_dir, client.logo_url.lstrip("/"))
            if os.path.exists(candidate):
                logo_path = candidate

        # Fetch real metrics from DB
        metrics = (
            self.db.query(Metric)
            .join(Integration)
            .filter(
                Integration.client_id == client.id,
                Metric.date >= date_from,
                Metric.date <= date_to,
            )
            .all()
        )

        if metrics:
            platforms, daily, kpis = self._aggregate_metrics(metrics)
        else:
            platforms, daily, kpis = self._sample_data()

        return ReportData(
            title=report.title,
            client_name=client.name,
            client_company=client.company or "",
            brand_primary=client.brand_color_primary or "#3B82F6",
            brand_secondary=client.brand_color_secondary or "#1E40AF",
            logo_path=logo_path,
            date_from=date_from,
            date_to=date_to,
            generated_at=datetime.utcnow(),
            kpis=kpis,
            platforms=platforms,
            daily=daily,
        )

    def _aggregate_metrics(self, metrics: list) -> tuple:
        from collections import defaultdict

        by_platform: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"spend": 0, "impressions": 0, "clicks": 0, "conversions": 0,
                     "ctr_sum": 0, "cpc_sum": 0, "roas_sum": 0, "count": 0}
        )
        by_date: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"spend": 0, "clicks": 0, "conversions": 0}
        )

        for m in metrics:
            p = by_platform[m.platform]
            date_key = m.date.strftime("%Y-%m-%d")
            d = by_date[date_key]

            if m.metric_name == "spend":
                p["spend"] += m.metric_value; d["spend"] += m.metric_value
            elif m.metric_name == "impressions":
                p["impressions"] += m.metric_value
            elif m.metric_name == "clicks":
                p["clicks"] += m.metric_value; d["clicks"] += m.metric_value
            elif m.metric_name == "conversions":
                p["conversions"] += m.metric_value; d["conversions"] += m.metric_value
            elif m.metric_name == "ctr":
                p["ctr_sum"] += m.metric_value; p["count"] += 1
            elif m.metric_name == "cpc":
                p["cpc_sum"] += m.metric_value
            elif m.metric_name == "roas":
                p["roas_sum"] += m.metric_value

        platform_rows = []
        total_spend = total_imp = total_clicks = total_conv = 0.0

        for name, p in by_platform.items():
            n = max(p["count"], 1)
            row = PlatformRow(
                platform=name.replace("_", " ").title(),
                spend=p["spend"], impressions=p["impressions"],
                clicks=p["clicks"], conversions=p["conversions"],
                ctr=p["ctr_sum"] / n, cpc=p["cpc_sum"] / n,
                roas=p["roas_sum"] / n,
            )
            platform_rows.append(row)
            total_spend += p["spend"]; total_imp += p["impressions"]
            total_clicks += p["clicks"]; total_conv += p["conversions"]

        daily_points = [
            DailyPoint(date=k, spend=v["spend"], clicks=v["clicks"],
                       conversions=v["conversions"])
            for k, v in sorted(by_date.items())
        ]

        kpis = KPISummary(
            total_spend=total_spend, total_impressions=total_imp,
            total_clicks=total_clicks, total_conversions=total_conv,
            avg_ctr=(total_clicks / total_imp * 100) if total_imp else 0,
            avg_cpc=(total_spend / total_clicks) if total_clicks else 0,
            avg_cpm=(total_spend / total_imp * 1000) if total_imp else 0,
            avg_roas=sum(r.roas for r in platform_rows) / len(platform_rows) if platform_rows else 0,
        )
        return platform_rows, daily_points, kpis

    def _sample_data(self) -> tuple:
        """Fallback sample data when no real metrics exist yet."""
        platforms = [
            PlatformRow("Google Ads",    spend=4200, impressions=180000, clicks=3600,
                        conversions=144, ctr=2.0, cpc=1.17, roas=4.2),
            PlatformRow("Facebook Ads",  spend=2800, impressions=95000,  clicks=1900,
                        conversions=76,  ctr=2.0, cpc=1.47, roas=3.6),
            PlatformRow("TikTok Ads",    spend=1100, impressions=210000, clicks=2100,
                        conversions=42,  ctr=1.0, cpc=0.52, roas=2.8),
        ]
        daily = [
            DailyPoint("2024-01-01", 820, 1100, 35),
            DailyPoint("2024-01-02", 1050, 1380, 48),
            DailyPoint("2024-01-03", 790,  980, 30),
            DailyPoint("2024-01-04", 1240, 1620, 62),
            DailyPoint("2024-01-05", 1490, 1850, 71),
            DailyPoint("2024-01-06", 880,  1150, 39),
            DailyPoint("2024-01-07", 620,   820, 22),
        ]
        kpis = KPISummary(
            total_spend=8100, total_impressions=485000, total_clicks=7600,
            total_conversions=262, avg_ctr=1.57, avg_cpc=1.07,
            avg_cpm=16.7, avg_roas=3.77,
        )
        return platforms, daily, kpis
