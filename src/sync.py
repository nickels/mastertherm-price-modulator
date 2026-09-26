import logging
from datetime import datetime

from config import Config
from controller import Decision, decide

log = logging.getLogger("mastertherm-price-modulator")

# evcc receives the limit with 4 decimals, so smaller differences are not a change
PRECISION = 0.0001

# the UI "Solar" mode; evcc renamed pv to smart in evcc-io/evcc#32490
SMART_MODES = ("smart", "pv")


async def sync_once(evcc, cfg: Config, now: datetime) -> dict[str, Decision] | None:
    """Compute each loadpoint's limit for the coming hours and write it to evcc."""
    rates = await evcc.fetch_rates()
    decisions = {}
    for spec in cfg.loadpoints:
        decision = decide(rates, now, spec.fraction, cfg.hours, cfg.min_hours, spec.floor)
        if decision is None:
            log.warning("fewer than %.0f h of prices known, limits unchanged", cfg.min_hours)
            return None
        decisions[spec.title] = decision
        log.info(
            "'%s' cheapest %.0f%%%s: limit %.4f -> heat %.1f of %.1f h",
            spec.title, 100 * spec.fraction, f" (floor {spec.floor:.4f})" if spec.floor is not None else "",
            decision.limit, decision.heat_hours, decision.known_hours,
        )

    for lp in await evcc.find_loadpoints([spec.title for spec in cfg.loadpoints]):
        limit = decisions[lp.title].limit
        if lp.mode not in SMART_MODES:
            log.warning("loadpoint %d '%s' is in mode '%s': the limit only applies in Solar mode", lp.id, lp.title, lp.mode)
        if lp.smart_cost_limit is not None and abs(lp.smart_cost_limit - limit) < PRECISION:
            continue
        if cfg.dry_run:
            log.info("dry run: would set loadpoint %d '%s' from %s to %.4f", lp.id, lp.title, lp.smart_cost_limit, limit)
            continue
        await evcc.set_smart_cost_limit(lp.id, limit)
        log.info("set loadpoint %d '%s' from %s to %.4f", lp.id, lp.title, lp.smart_cost_limit, limit)

    return decisions
