import os
from dataclasses import dataclass

DEFAULT_LOADPOINTS = "MasterTherm:0.4,MasterTherm SHW:0.2"


@dataclass(frozen=True)
class Config:
    evcc_url: str
    api_key: str | None
    loadpoints: tuple[tuple[str, float], ...]  # (title, fraction)
    fraction: float
    hours: float
    min_hours: float
    poll_interval: int
    dry_run: bool
    log_level: str
    # (title, floor loadpoint title): the limit never drops below that loadpoint's smart cost limit
    floors: tuple[tuple[str, str], ...] = ()

    @classmethod
    def from_env(cls) -> "Config":
        fraction = _fraction(os.environ.get("FRACTION", "0.4"), "FRACTION")
        loadpoints, floors = _parse_loadpoints(os.environ.get("LOADPOINTS", DEFAULT_LOADPOINTS), fraction)
        return cls(
            evcc_url=os.environ["EVCC_URL"],
            api_key=os.environ.get("EVCC_API_KEY") or None,
            loadpoints=loadpoints,
            floors=floors,
            fraction=fraction,
            hours=float(os.environ.get("HOURS", "24")),
            min_hours=float(os.environ.get("MIN_HOURS", "8")),
            poll_interval=int(os.environ.get("POLL_INTERVAL", "900")),
            dry_run=os.environ.get("DRY_RUN", "false").lower() in ("1", "true", "yes"),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )


def _parse_loadpoints(raw: str, default: float) -> tuple[tuple[tuple[str, float], ...], tuple[tuple[str, str], ...]]:
    """Parse "Title[:fraction[:floor loadpoint title]],..."; a title without a fraction gets the default."""
    loadpoints, floors = [], []
    for entry in raw.split(","):
        title, _, rest = entry.partition(":")
        value, _, floor = rest.partition(":")
        title = title.strip()
        if not title:
            continue
        loadpoints.append((title, _fraction(value, f"LOADPOINTS '{title}'") if value.strip() else default))
        if floor.strip():
            floors.append((title, floor.strip()))
    return tuple(loadpoints), tuple(floors)


def _fraction(value: str, name: str) -> float:
    try:
        fraction = float(value)
    except ValueError:
        raise ValueError(f"{name}: fraction must be a number, got '{value.strip()}'") from None
    if not 0 < fraction <= 1:
        raise ValueError(f"{name}: fraction must be in (0, 1], got {fraction}")
    return fraction
