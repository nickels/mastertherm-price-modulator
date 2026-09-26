from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Rate:
    start: datetime
    end: datetime
    value: float


@dataclass(frozen=True)
class Decision:
    limit: float
    known_hours: float
    heat_hours: float


def upcoming_slots(rates: list[Rate], now: datetime, hours: float) -> list[tuple[float, float]]:
    """Return (price, duration in s) for every rate that overlaps [now, now + hours)."""
    horizon = now + timedelta(hours=hours)
    slots = []
    for rate in rates:
        start, end = max(rate.start, now), min(rate.end, horizon)
        if end > start:
            slots.append((rate.value, (end - start).total_seconds()))
    return slots


def select_limit(slots: list[tuple[float, float]], fraction: float) -> float:
    """Return the lowest price that covers at least `fraction` of the time in `slots`.

    Weighted by duration, so 15-minute and hourly tariffs give the same result.
    evcc applies the limit as price <= limit, so slots at the limit price are included.
    """
    total = sum(duration for _, duration in slots)
    covered = 0.0
    for price, duration in sorted(slots):
        covered += duration
        if covered >= fraction * total:
            return price
    return max(price for price, _ in slots)


def decide(
    rates: list[Rate], now: datetime, fraction: float, hours: float, min_hours: float, floor: float | None = None,
) -> Decision | None:
    """Compute the smart cost limit, or None when too few future prices are known.

    With a floor, the limit never drops below that price.
    """
    slots = upcoming_slots(rates, now, hours)
    known_hours = sum(duration for _, duration in slots) / 3600
    if known_hours < min_hours:
        return None
    limit = select_limit(slots, fraction)
    if floor is not None:
        limit = max(limit, floor)
    heat_hours = sum(duration for price, duration in slots if price <= limit) / 3600
    return Decision(limit=limit, known_hours=known_hours, heat_hours=heat_hours)
