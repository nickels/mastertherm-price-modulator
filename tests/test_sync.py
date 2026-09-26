from datetime import datetime, timedelta, timezone

import pytest

from config import Config
from controller import Rate
from evcc import Loadpoint
from sync import sync_once

NOW = datetime(2026, 9, 26, 3, 30, tzinfo=timezone.utc)

# hourly prices 24, 23, ..., 1: cheapest 40 % -> limit 10, cheapest 20 % -> limit 5
HEATING, SHW = 10.0, 5.0


def cfg(**overrides):
    base = dict(
        evcc_url="http://evcc", api_key=None,
        loadpoints=(("MasterTherm", 0.4), ("MasterTherm SHW", 0.2)),
        fraction=0.4, hours=24.0, min_hours=8.0, poll_interval=900, dry_run=False, log_level="INFO",
    )
    return Config(**{**base, **overrides})


class FakeEvcc:
    def __init__(self, hours_of_prices=24, limits=(None, 0.2), modes=("smart", "smart")):
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


async def test_sets_own_limit_per_loadpoint():
    evcc = FakeEvcc()
    decisions = await sync_once(evcc, cfg(), NOW)
    assert decisions["MasterTherm"].limit == HEATING
    assert decisions["MasterTherm SHW"].limit == SHW
    assert evcc.writes == [(3, HEATING), (2, SHW)]


async def test_same_fraction_gives_same_limit():
    evcc = FakeEvcc()
    await sync_once(evcc, cfg(loadpoints=(("MasterTherm", 0.4), ("MasterTherm SHW", 0.4))), NOW)
    assert evcc.writes == [(3, HEATING), (2, HEATING)]


async def test_skips_loadpoint_that_already_has_the_limit():
    evcc = FakeEvcc(limits=(HEATING, 0.2))
    await sync_once(evcc, cfg(), NOW)
    assert evcc.writes == [(2, SHW)]


async def test_short_horizon_writes_nothing():
    evcc = FakeEvcc(hours_of_prices=4)
    assert await sync_once(evcc, cfg(), NOW) is None
    assert evcc.writes == []


async def test_dry_run_writes_nothing():
    evcc = FakeEvcc()
    decisions = await sync_once(evcc, cfg(dry_run=True), NOW)
    assert decisions["MasterTherm SHW"].limit == SHW
    assert evcc.writes == []


async def test_warns_when_loadpoint_not_in_solar_mode(caplog):
    evcc = FakeEvcc(modes=("now", "smart"))
    await sync_once(evcc, cfg(), NOW)
    assert "MasterTherm" in caplog.text and "Solar" in caplog.text


@pytest.mark.parametrize("mode", ["smart", "pv"])
async def test_no_warning_in_smart_mode(caplog, mode):
    # evcc renamed pv to smart (evcc-io/evcc#32490); both mean the UI "Solar" mode
    evcc = FakeEvcc(modes=(mode, mode))
    await sync_once(evcc, cfg(), NOW)
    assert "Solar" not in caplog.text


@pytest.mark.parametrize("delta", [-0.00005, 0.00004])
async def test_limit_compare_uses_api_precision(delta):
    evcc = FakeEvcc(limits=(HEATING + delta, SHW + delta))
    await sync_once(evcc, cfg(), NOW)
    assert evcc.writes == []
