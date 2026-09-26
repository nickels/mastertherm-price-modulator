from dataclasses import dataclass
from datetime import datetime

import httpx

from controller import Rate


@dataclass(frozen=True)
class Loadpoint:
    id: int  # 1-based, as used by the evcc API and the UI (?lp=)
    title: str
    mode: str
    smart_cost_limit: float | None


class EvccClient:
    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), headers=headers, timeout=20.0)

    async def fetch_rates(self) -> list[Rate]:
        resp = await self._client.get("/api/tariff/grid")
        resp.raise_for_status()
        return [
            Rate(_parse_time(r["start"]), _parse_time(r["end"]), float(r["value"]))
            for r in resp.json()["rates"]
        ]

    async def find_loadpoints(self, titles: list[str] | tuple[str, ...]) -> list[Loadpoint]:
        """Return the loadpoints with these titles, in the given order."""
        resp = await self._client.get("/api/state")
        resp.raise_for_status()
        by_title = {
            lp.get("title"): Loadpoint(
                id=index,
                title=lp.get("title"),
                mode=lp.get("mode", ""),
                smart_cost_limit=lp.get("smartCostLimit"),
            )
            for index, lp in enumerate(resp.json()["loadpoints"], start=1)
        }
        missing = [t for t in titles if t not in by_title]
        if missing:
            raise LookupError(f"evcc loadpoint(s) not found: {', '.join(missing)}")
        return [by_title[t] for t in titles]

    async def set_smart_cost_limit(self, loadpoint_id: int, limit: float) -> None:
        resp = await self._client.post(f"/api/loadpoints/{loadpoint_id}/smartcostlimit/{limit:.4f}")
        resp.raise_for_status()

    async def close(self) -> None:
        await self._client.aclose()


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
