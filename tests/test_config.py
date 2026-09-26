import pytest

from config import Config


def test_defaults(monkeypatch):
    monkeypatch.setenv("EVCC_URL", "http://evcc:7070")
    monkeypatch.delenv("LOADPOINTS", raising=False)
    cfg = Config.from_env()
    assert cfg.loadpoints == ("MasterTherm", "MasterTherm SHW")
    assert (cfg.fraction, cfg.hours, cfg.min_hours, cfg.poll_interval) == (0.4, 24.0, 8.0, 900)
    assert cfg.api_key is None


def test_loadpoint_titles_trimmed(monkeypatch):
    monkeypatch.setenv("EVCC_URL", "http://evcc:7070")
    monkeypatch.setenv("LOADPOINTS", " MasterTherm , MasterTherm SHW ")
    assert Config.from_env().loadpoints == ("MasterTherm", "MasterTherm SHW")


@pytest.mark.parametrize("value", ["0", "1.5", "-0.1"])
def test_fraction_out_of_range(monkeypatch, value):
    monkeypatch.setenv("EVCC_URL", "http://evcc:7070")
    monkeypatch.setenv("FRACTION", value)
    with pytest.raises(ValueError, match="FRACTION"):
        Config.from_env()
