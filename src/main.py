import asyncio
import logging
import signal
from datetime import datetime, timezone

from config import Config
from evcc import EvccClient
from sync import sync_once

log = logging.getLogger("mastertherm-price-modulator")


async def run(cfg: Config) -> None:
    evcc = EvccClient(cfg.evcc_url, cfg.api_key)
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    def _shutdown(sig: signal.Signals) -> None:
        log.info("Received %s, shutting down", sig.name)
        stop.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown, sig)

    try:
        while not stop.is_set():
            try:
                await sync_once(evcc, cfg, datetime.now(timezone.utc))
            except Exception:
                log.exception("Sync error, keeping the current limits")

            try:
                await asyncio.wait_for(stop.wait(), timeout=cfg.poll_interval)
            except asyncio.TimeoutError:
                pass
    finally:
        await evcc.close()


def main() -> None:
    cfg = Config.from_env()
    logging.basicConfig(level=cfg.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    log.info(
        "Starting: evcc=%s loadpoints=%s window=%.0f h interval=%ds%s",
        cfg.evcc_url, ", ".join(f"{title} (cheapest {100 * f:.0f}%)" for title, f in cfg.loadpoints),
        cfg.hours, cfg.poll_interval,
        " (dry run)" if cfg.dry_run else "",
    )
    asyncio.run(run(cfg))


if __name__ == "__main__":
    main()
