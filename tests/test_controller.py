from datetime import datetime, timedelta, timezone

from controller import Decision, Rate, decide, select_limit, upcoming_slots

NOW = datetime(2026, 9, 26, 3, 30, tzinfo=timezone.utc)


def hourly(prices, start=NOW):
    return [
        Rate(start + timedelta(hours=i), start + timedelta(hours=i + 1), p)
        for i, p in enumerate(prices)
    ]


def test_select_limit_cheapest_fraction():
    slots = [(p, 3600) for p in range(10, 0, -1)]
    assert select_limit(slots, 0.4) == 4


def test_select_limit_weights_by_duration():
    # a 15-minute cheap slot does not count as a full hour
    slots = [(1, 900), (2, 3600), (3, 3600), (4, 3600)]
    assert select_limit(slots, 0.4) == 3


def test_select_limit_equal_prices():
    assert select_limit([(5, 3600)] * 5, 0.4) == 5


def test_upcoming_slots_clips_to_window():
    rates = [
        Rate(NOW - timedelta(minutes=30), NOW + timedelta(minutes=30), 1),
        Rate(NOW + timedelta(hours=23, minutes=30), NOW + timedelta(hours=24, minutes=30), 2),
        Rate(NOW - timedelta(hours=2), NOW - timedelta(hours=1), 9),
    ]
    assert upcoming_slots(rates, NOW, 24) == [(1, 1800.0), (2, 1800.0)]


def test_decide_returns_limit_and_hours():
    decision = decide(hourly(range(24, 0, -1)), NOW, fraction=0.4, hours=24, min_hours=8)
    assert decision == Decision(limit=10, known_hours=24.0, heat_hours=10.0)


def test_decide_refuses_short_horizon():
    assert decide(hourly([1, 2, 3]), NOW, fraction=0.4, hours=24, min_hours=8) is None
