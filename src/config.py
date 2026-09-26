import os
from dataclasses import dataclass

DEFAULT_LOADPOINTS = "MasterTherm:0.4,MasterTherm SHW:0.2:0.15"


@dataclass(frozen=True)
class LoadpointSpec:
    title: str
    fraction: float
    floor: float | None = None  # the limit never goes below this price


@dataclass(frozen=True)
class Config:
    evcc_url: str
    api_key: str | None
    loadpoints: tuple[LoadpointSpec, ...]
    fraction: float
    hours: float
    min_hours: float
    poll_interval: int
    dry_run: bool
    log_level: str

    @classmethod
    def from_env(cls) -> "Config":
        fraction = _fraction(os.environ.get("FRACTION", "0.4"), "FRACTION")
        return cls(
            evcc_url=os.environ["EVCC_URL"],
            api_key=os.environ.get("EVCC_API_KEY") or None,
            loadpoints=_parse_loadpoints(os.environ.get("LOADPOINTS", DEFAULT_LOADPOINTS), fraction),
            fraction=fraction,
            hours=float(os.environ.get("HOURS", "24")),
            min_hours=float(os.environ.get("MIN_HOURS", "8")),
            poll_interval=int(os.environ.get("POLL_INTERVAL", "900")),
            dry_run=os.environ.get("DRY_RUN", "false").lower() in ("1", "true", "yes"),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )


def _parse_loadpoints(raw: str, default: float) -> tuple[LoadpointSpec, ...]:
    """Parse "Title[:fraction[:floor]],..."; a title without a fraction gets the default."""
    result = []
    for entry in raw.split(","):
        title, _, rest = entry.partition(":")
        fraction, _, floor = rest.partition(":")
        title = title.strip()
        if not title:
            continue
        name = f"LOADPOINTS '{title}'"
        result.append(LoadpointSpec(
            title,
            _fraction(fraction, name) if fraction.strip() else default,
            _number(floor, name) if floor.strip() else None,
        ))
    return tuple(result)


def _fraction(value: str, name: str) -> float:
    fraction = _number(value, name)
    if not 0 < fraction <= 1:
        raise ValueError(f"{name}: fraction must be in (0, 1], got {fraction}")
    return fraction


def _number(value: str, name: str) -> float:
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"{name}: expected a number, got '{value.strip()}'") from None
