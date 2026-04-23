import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.services.base_integration import BaseIntegration, MetricData


class GoogleAdsService(BaseIntegration):
    """
    Google Ads integration via the Google Ads API v17.
    Credentials: developer_token, client_id, client_secret, refresh_token, customer_id
    """

    platform_name = "google_ads"
    required_credentials = ["developer_token", "client_id", "client_secret", "refresh_token", "customer_id"]

    TOKEN_URL = "https://oauth2.googleapis.com/token"
    API_BASE = "https://googleads.googleapis.com/v17"

    async def _get_access_token(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.TOKEN_URL, data={
                "grant_type": "refresh_token",
                "client_id": self.credentials["client_id"],
                "client_secret": self.credentials["client_secret"],
                "refresh_token": self.credentials["refresh_token"],
            })
            resp.raise_for_status()
            return resp.json()["access_token"]

    def _headers(self, access_token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "developer-token": self.credentials["developer_token"],
            "Content-Type": "application/json",
        }

    async def test_connection(self) -> bool:
        try:
            token = await self._get_access_token()
            customer_id = self.credentials["customer_id"]
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.API_BASE}/customers/{customer_id}",
                    headers=self._headers(token),
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def fetch_campaigns(self) -> List[Dict[str, Any]]:
        token = await self._get_access_token()
        customer_id = self.credentials["customer_id"]
        query = """
            SELECT campaign.id, campaign.name, campaign.status,
                   campaign.advertising_channel_type
            FROM campaign
            WHERE campaign.status != 'REMOVED'
            ORDER BY campaign.name
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.API_BASE}/customers/{customer_id}/googleAds:search",
                headers=self._headers(token),
                json={"query": query},
                timeout=30,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            return [
                {
                    "id": r["campaign"]["id"],
                    "name": r["campaign"]["name"],
                    "status": r["campaign"]["status"],
                    "channel": r["campaign"].get("advertisingChannelType"),
                }
                for r in results
            ]

    async def fetch_metrics(
        self,
        date_from: datetime,
        date_to: datetime,
        metrics: Optional[List[str]] = None,
    ) -> List[MetricData]:
        token = await self._get_access_token()
        customer_id = self.credentials["customer_id"]
        date_from_str = date_from.strftime("%Y-%m-%d")
        date_to_str = date_to.strftime("%Y-%m-%d")

        query = f"""
            SELECT
                campaign.id, campaign.name,
                segments.date,
                metrics.impressions, metrics.clicks, metrics.cost_micros,
                metrics.conversions, metrics.ctr, metrics.average_cpc,
                metrics.average_cpm, metrics.all_conversions_value
            FROM campaign
            WHERE segments.date BETWEEN '{date_from_str}' AND '{date_to_str}'
              AND campaign.status != 'REMOVED'
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.API_BASE}/customers/{customer_id}/googleAds:search",
                headers=self._headers(token),
                json={"query": query},
                timeout=60,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])

        metric_rows = []
        for row in results:
            m = row.get("metrics", {})
            campaign = row.get("campaign", {})
            date_str = row.get("segments", {}).get("date", date_from_str)
            record_date = datetime.strptime(date_str, "%Y-%m-%d")
            spend = m.get("costMicros", 0) / 1_000_000

            raw = {
                "campaign_id": campaign.get("id"),
                "campaign_name": campaign.get("name"),
                "impressions": m.get("impressions", 0),
                "clicks": m.get("clicks", 0),
                "spend": spend,
                "conversions": m.get("conversions", 0),
                "ctr": m.get("ctr", 0),
                "cpc": m.get("averageCpc", 0) / 1_000_000,
                "cpm": m.get("averageCpm", 0) / 1_000_000,
                "conversion_value": m.get("allConversionsValue", 0),
            }
            roas = raw["conversion_value"] / spend if spend > 0 else 0

            dims = {"campaign_id": campaign.get("id"), "campaign_name": campaign.get("name")}

            for metric_name, value, unit in [
                ("impressions", raw["impressions"], "count"),
                ("clicks", raw["clicks"], "count"),
                ("spend", raw["spend"], "currency"),
                ("conversions", raw["conversions"], "count"),
                ("ctr", raw["ctr"], "percentage"),
                ("cpc", raw["cpc"], "currency"),
                ("cpm", raw["cpm"], "currency"),
                ("roas", roas, "ratio"),
            ]:
                metric_rows.append(MetricData(
                    platform=self.platform_name,
                    metric_name=metric_name,
                    metric_value=float(value),
                    metric_unit=unit,
                    date=record_date,
                    dimensions=dims,
                    raw_data=raw,
                ))

        return metric_rows
