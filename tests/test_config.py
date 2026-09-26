import pytest

from config import Config


@pytest.fixture(autouse=True)
def evcc_url(monkeypatch):
    monkeypatch.setenv("EVCC_URL", "http://evcc:7070")
    monkeypatch.delenv("LOADPOINTS", raising=False)
    monkeypatch.delenv("FRACTION", raising=False)


def test_defaults():
    cfg = Config.from_env()
    assert cfg.loadpoints == (("MasterTherm", 0.4), ("MasterTherm SHW", 0.2))
    assert (cfg.fraction, cfg.hours, cfg.min_hours, cfg.poll_interval) == (0.4, 24.0, 8.0, 900)
    assert cfg.api_key is None


def test_loadpoint_without_fraction_uses_default(monkeypatch):
    monkeypatch.setenv("LOADPOINTS", " MasterTherm , MasterTherm SHW:0.2 ")
    monkeypatch.setenv("FRACTION", "0.5")
    assert Config.from_env().loadpoints == (("MasterTherm", 0.5), ("MasterTherm SHW", 0.2))


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
