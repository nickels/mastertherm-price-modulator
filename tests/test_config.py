import pytest

from config import Config, LoadpointSpec


@pytest.fixture(autouse=True)
def evcc_url(monkeypatch):
    monkeypatch.setenv("EVCC_URL", "http://evcc:7070")
    monkeypatch.delenv("LOADPOINTS", raising=False)
    monkeypatch.delenv("FRACTION", raising=False)


def test_defaults():
    cfg = Config.from_env()
    assert cfg.loadpoints == (LoadpointSpec("MasterTherm", 0.4), LoadpointSpec("MasterTherm SHW", 0.2, floor=0.15))
    assert (cfg.fraction, cfg.hours, cfg.min_hours, cfg.poll_interval) == (0.4, 24.0, 8.0, 900)
    assert cfg.api_key is None


def test_loadpoint_without_fraction_uses_default(monkeypatch):
    monkeypatch.setenv("LOADPOINTS", " MasterTherm , MasterTherm SHW:0.2 ")
    monkeypatch.setenv("FRACTION", "0.5")
    assert Config.from_env().loadpoints == (LoadpointSpec("MasterTherm", 0.5), LoadpointSpec("MasterTherm SHW", 0.2))


@pytest.mark.parametrize("value", ["0", "1.5", "-0.1"])
def test_fraction_out_of_range(monkeypatch, value):
    monkeypatch.setenv("FRACTION", value)
    with pytest.raises(ValueError, match="FRACTION"):
        Config.from_env()


@pytest.mark.parametrize("value", ["0", "1.5", "abc"])
def test_loadpoint_fraction_invalid(monkeypatch, value):
    monkeypatch.setenv("LOADPOINTS", f"MasterTherm,MasterTherm SHW:{value}")
    with pytest.raises(ValueError, match="MasterTherm SHW"):
        Config.from_env()


def test_loadpoint_floor(monkeypatch):
    # third field: the limit never drops below this price (SHW boost threshold)
    monkeypatch.setenv("LOADPOINTS", "MasterTherm:0.4,MasterTherm SHW:0.2:0.15")
    assert Config.from_env().loadpoints[1] == LoadpointSpec("MasterTherm SHW", 0.2, floor=0.15)


def test_loadpoint_floor_without_fraction_uses_default(monkeypatch):
    monkeypatch.setenv("LOADPOINTS", "MasterTherm SHW::0.15")
    assert Config.from_env().loadpoints == (LoadpointSpec("MasterTherm SHW", 0.4, floor=0.15),)


def test_loadpoint_floor_invalid(monkeypatch):
    monkeypatch.setenv("LOADPOINTS", "MasterTherm SHW:0.2:cheap")
    with pytest.raises(ValueError, match="MasterTherm SHW"):
        Config.from_env()
