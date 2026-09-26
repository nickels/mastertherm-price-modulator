from datetime import datetime, timezone

import httpx
import pytest

from controller import Rate
from evcc import EvccClient, Loadpoint

STATE = {
    "loadpoints": [
        {"title": "Alfen Eve Single Pro Line", "mode": "pv", "smartCostLimit": 0.172},
        {"title": "MasterTherm SHW", "mode": "pv", "smartCostLimit": 0.2},
        {"title": "MasterTherm", "mode": "now"},
    ]
}


async def test_fetch_rates(httpx_mock):
    httpx_mock.add_response(
        url="http://test:7070/api/tariff/grid",
        json={"rates": [{"start": "2026-09-26T03:00:00Z", "end": "2026-09-26T04:00:00+00:00", "value": 0.21}]},
    )
    rates = await EvccClient("http://test:7070/").fetch_rates()
    assert rates == [
        Rate(
            datetime(2026, 9, 26, 3, tzinfo=timezone.utc),
            datetime(2026, 9, 26, 4, tzinfo=timezone.utc),
            0.21,
        )
    ]


async def test_find_loadpoints_by_title(httpx_mock):
    httpx_mock.add_response(url="http://test:7070/api/state", json=STATE)
    found = await EvccClient("http://test:7070").find_loadpoints(["MasterTherm", "MasterTherm SHW"])
    assert found == [
        Loadpoint(id=3, title="MasterTherm", mode="now", smart_cost_limit=None),
        Loadpoint(id=2, title="MasterTherm SHW", mode="pv", smart_cost_limit=0.2),
    ]


async def test_find_loadpoints_missing_title(httpx_mock):
    httpx_mock.add_response(url="http://test:7070/api/state", json=STATE)
    with pytest.raises(LookupError, match="Boiler"):
        await EvccClient("http://test:7070").find_loadpoints(["Boiler"])


async def test_set_smart_cost_limit(httpx_mock):
    httpx_mock.add_response(method="POST", url="http://test:7070/api/loadpoints/3/smartcostlimit/0.1875")
    await EvccClient("http://test:7070").set_smart_cost_limit(3, 0.18749)


async def test_api_key_sent_as_bearer(httpx_mock):
    httpx_mock.add_response(url="http://test:7070/api/state", json=STATE)
    await EvccClient("http://test:7070", api_key="k3y").find_loadpoints(["MasterTherm"])
    assert httpx_mock.get_request().headers["Authorization"] == "Bearer k3y"


async def test_http_error_raises(httpx_mock):
    httpx_mock.add_response(url="http://test:7070/api/tariff/grid", status_code=500)
    with pytest.raises(httpx.HTTPStatusError):
        await EvccClient("http://test:7070").fetch_rates()
