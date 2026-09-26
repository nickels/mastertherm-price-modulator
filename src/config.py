import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    evcc_url: str
    api_key: str | None
    loadpoints: tuple[str, ...]
    fraction: float
    hours: float
    min_hours: float
    poll_interval: int
    dry_run: bool
    log_level: str

    @classmethod
    def from_env(cls) -> "Config":
        fraction = float(os.environ.get("FRACTION", "0.4"))
        if not 0 < fraction <= 1:
            raise ValueError(f"FRACTION must be in (0, 1], got {fraction}")
        return cls(
            evcc_url=os.environ["EVCC_URL"],
            api_key=os.environ.get("EVCC_API_KEY") or None,
            loadpoints=tuple(
                t.strip() for t in os.environ.get("LOADPOINTS", "MasterTherm,MasterTherm SHW").split(",") if t.strip()
            ),
            fraction=fraction,
            hours=float(os.environ.get("HOURS", "24")),
            min_hours=float(os.environ.get("MIN_HOURS", "8")),
            poll_interval=int(os.environ.get("POLL_INTERVAL", "900")),
            dry_run=os.environ.get("DRY_RUN", "false").lower() in ("1", "true", "yes"),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )
