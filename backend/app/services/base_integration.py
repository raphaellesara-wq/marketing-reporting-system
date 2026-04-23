from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class MetricData:
    platform: str
    metric_name: str
    metric_value: float
    metric_unit: str
    date: datetime
    dimensions: Dict[str, Any]
    raw_data: Optional[Dict[str, Any]] = None


class BaseIntegration(ABC):
    """Abstract base class for all platform integrations."""

    platform_name: str = ""
    required_credentials: List[str] = []

    def __init__(self, credentials: Dict[str, Any], config: Dict[str, Any] = None):
        self.credentials = credentials
        self.config = config or {}
        self._validate_credentials()

    def _validate_credentials(self):
        missing = [k for k in self.required_credentials if k not in self.credentials]
        if missing:
            raise ValueError(f"Missing credentials for {self.platform_name}: {missing}")

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the credentials are valid and the API is reachable."""

    @abstractmethod
    async def fetch_metrics(
        self,
        date_from: datetime,
        date_to: datetime,
        metrics: Optional[List[str]] = None,
    ) -> List[MetricData]:
        """Fetch performance metrics for the given date range."""

    @abstractmethod
    async def fetch_campaigns(self) -> List[Dict[str, Any]]:
        """List available campaigns / ad sets."""

    def get_default_metrics(self) -> List[str]:
        """Return default metrics for this platform."""
        return ["impressions", "clicks", "spend", "conversions", "ctr", "cpc", "cpm", "roas"]

    def normalize_metric_name(self, raw_name: str) -> str:
        """Normalize platform-specific metric names to standard names."""
        mapping = {
            "cost": "spend",
            "cost_micros": "spend",
            "actions": "conversions",
            "purchase": "conversions",
            "link_click": "clicks",
        }
        return mapping.get(raw_name.lower(), raw_name.lower())
