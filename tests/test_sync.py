from datetime import datetime, timedelta, timezone

import pytest

from config import Config
from controller import Rate
from evcc import Loadpoint
from sync import sync_once

NOW = datetime(2026, 9, 26, 3, 30, tzinfo=timezone.utc)


def cfg(**overrides):
    base = dict(
        evcc_url="http://evcc", api_key=None, loadpoints=("MasterTherm", "MasterTherm SHW"),
        fraction=0.4, hours=24.0, min_hours=8.0, poll_interval=900, dry_run=False, log_level="INFO",
    )
    return Config(**{**base, **overrides})


class FakeEvcc:
    def __init__(self, hours_of_prices=24, limits=(None, 0.2), modes=("pv", "pv")):
        self.rates = [
            Rate(NOW + timedelta(hours=i), NOW + timedelta(hours=i + 1), float(24 - i))
            for i in range(hours_of_prices)
        ]
        self.loadpoints = [
            Loadpoint(id=3, title="MasterTherm", mode=modes[0], smart_cost_limit=limits[0]),
            Loadpoint(id=2, title="MasterTherm SHW", mode=modes[1], smart_cost_limit=limits[1]),
        ]
        self.writes = []

    async def fetch_rates(self):
        return self.rates

    async def find_loadpoints(self, titles):
        assert tuple(titles) == ("MasterTherm", "MasterTherm SHW")
        return self.loadpoints

    async def set_smart_cost_limit(self, loadpoint_id, limit):
        self.writes.append((loadpoint_id, limit))


async def test_sets_limit_on_both_mastertherm_loadpoints():
    evcc = FakeEvcc()
    decision = await sync_once(evcc, cfg(), NOW)
    assert decision.limit == 10.0
    assert evcc.writes == [(3, 10.0), (2, 10.0)]


async def test_skips_loadpoint_that_already_has_the_limit():
    evcc = FakeEvcc(limits=(10.0, 0.2))
    await sync_once(evcc, cfg(), NOW)
    assert evcc.writes == [(2, 10.0)]


async def test_short_horizon_writes_nothing():
    evcc = FakeEvcc(hours_of_prices=4)
    assert await sync_once(evcc, cfg(), NOW) is None
    assert evcc.writes == []


async def test_dry_run_writes_nothing():
    evcc = FakeEvcc()
    assert (await sync_once(evcc, cfg(dry_run=True), NOW)).limit == 10.0
    assert evcc.writes == []


async def test_warns_when_loadpoint_not_in_solar_mode(caplog):
    evcc = FakeEvcc(modes=("now", "pv"))
    await sync_once(evcc, cfg(), NOW)
    assert "MasterTherm" in caplog.text and "Solar" in caplog.text


@pytest.mark.parametrize("current", [9.99995, 10.00004])
async def test_limit_compare_uses_api_precision(current):
    evcc = FakeEvcc(limits=(current, 10.0))
    await sync_once(evcc, cfg(), NOW)
    assert evcc.writes == []
