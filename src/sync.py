import logging
from datetime import datetime

from config import Config
from controller import Decision, decide

log = logging.getLogger("mastertherm-price-modulator")

# evcc receives the limit with 4 decimals, so smaller differences are not a change
PRECISION = 0.0001

# the UI "Solar" mode; evcc renamed pv to smart in evcc-io/evcc#32490
SMART_MODES = ("smart", "pv")


async def sync_once(evcc, cfg: Config, now: datetime) -> Decision | None:
    """Compute the limit for the coming hours and write it to every configured loadpoint."""
    decision = decide(await evcc.fetch_rates(), now, cfg.fraction, cfg.hours, cfg.min_hours)
    if decision is None:
        log.warning("fewer than %.0f h of prices known, limits unchanged", cfg.min_hours)
        return None

    log.info(
        "limit %.4f -> heat %.1f of %.1f h (%.0f%%)",
        decision.limit, decision.heat_hours, decision.known_hours,
        100 * decision.heat_hours / decision.known_hours,
    )

    for lp in await evcc.find_loadpoints(cfg.loadpoints):
        if lp.mode not in SMART_MODES:
            log.warning("loadpoint %d '%s' is in mode '%s': the limit only applies in Solar mode", lp.id, lp.title, lp.mode)
        if lp.smart_cost_limit is not None and abs(lp.smart_cost_limit - decision.limit) < PRECISION:
            continue
        if cfg.dry_run:
            log.info("dry run: would set loadpoint %d '%s' from %s to %.4f", lp.id, lp.title, lp.smart_cost_limit, decision.limit)
            continue
        await evcc.set_smart_cost_limit(lp.id, decision.limit)
        log.info("set loadpoint %d '%s' from %s to %.4f", lp.id, lp.title, lp.smart_cost_limit, decision.limit)

    return decision
