import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.services.base_integration import BaseIntegration, MetricData


class FacebookAdsService(BaseIntegration):
    """
    Facebook / Meta Ads integration via the Marketing API v19.
    Credentials: access_token, ad_account_id
    """

    platform_name = "facebook_ads"
    required_credentials = ["access_token", "ad_account_id"]

    API_BASE = "https://graph.facebook.com/v19.0"

    def _account_url(self, path: str = "") -> str:
        account_id = self.credentials["ad_account_id"]
        prefix = "act_" if not account_id.startswith("act_") else ""
        return f"{self.API_BASE}/{prefix}{account_id}{path}"

    def _params(self, extra: Dict[str, Any] = None) -> Dict[str, Any]:
        p = {"access_token": self.credentials["access_token"]}
        if extra:
            p.update(extra)
        return p

    async def test_connection(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    self._account_url(),
                    params=self._params({"fields": "id,name,account_status"}),
                    timeout=10,
                )
                return resp.status_code == 200 and "id" in resp.json()
        except Exception:
            return False

    async def fetch_campaigns(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self._account_url("/campaigns"),
                params=self._params({
                    "fields": "id,name,status,objective,daily_budget,lifetime_budget",
                    "limit": 500,
                }),
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            return [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "status": c.get("status"),
                    "objective": c.get("objective"),
                }
                for c in data
            ]

    async def fetch_metrics(
        self,
        date_from: datetime,
        date_to: datetime,
        metrics: Optional[List[str]] = None,
    ) -> List[MetricData]:
        date_from_str = date_from.strftime("%Y-%m-%d")
        date_to_str = date_to.strftime("%Y-%m-%d")

        fields = ",".join([
            "campaign_id", "campaign_name", "date_start",
            "impressions", "clicks", "spend",
            "actions", "action_values",
            "ctr", "cpc", "cpm", "reach", "frequency",
        ])

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self._account_url("/insights"),
                params=self._params({
                    "fields": fields,
                    "time_range[since]": date_from_str,
                    "time_range[until]": date_to_str,
                    "level": "campaign",
                    "time_increment": 1,
                    "limit": 500,
                }),
                timeout=60,
            )
            resp.raise_for_status()
            rows = resp.json().get("data", [])

        metric_rows = []
        for row in rows:
            date_str = row.get("date_start", date_from_str)
            record_date = datetime.strptime(date_str, "%Y-%m-%d")
            spend = float(row.get("spend", 0))

            actions = {a["action_type"]: float(a["value"]) for a in row.get("actions", [])}
            action_values = {a["action_type"]: float(a["value"]) for a in row.get("action_values", [])}
            conversions = actions.get("purchase", actions.get("lead", 0))
            conversion_value = action_values.get("purchase", 0)
            roas = conversion_value / spend if spend > 0 else 0

            dims = {
                "campaign_id": row.get("campaign_id"),
                "campaign_name": row.get("campaign_name"),
            }
            raw = {**row, "conversions": conversions, "roas": roas}

            for metric_name, value, unit in [
                ("impressions", float(row.get("impressions", 0)), "count"),
                ("clicks", float(row.get("clicks", 0)), "count"),
                ("spend", spend, "currency"),
                ("conversions", conversions, "count"),
                ("ctr", float(row.get("ctr", 0)), "percentage"),
                ("cpc", float(row.get("cpc", 0)), "currency"),
                ("cpm", float(row.get("cpm", 0)), "currency"),
                ("reach", float(row.get("reach", 0)), "count"),
                ("roas", roas, "ratio"),
            ]:
                metric_rows.append(MetricData(
                    platform=self.platform_name,
                    metric_name=metric_name,
                    metric_value=value,
                    metric_unit=unit,
                    date=record_date,
                    dimensions=dims,
                    raw_data=raw,
                ))

        return metric_rows
