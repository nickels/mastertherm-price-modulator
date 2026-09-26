# MasterTherm Price Modulator

A small Python daemon that makes the MasterTherm heat pump heat only in the cheapest hours. It reads the grid price forecast from [evcc](https://evcc.io), computes the price that covers the cheapest 40 % of the next 24 h, and sets that value as the **smart cost limit** of the MasterTherm loadpoints in evcc.

evcc stays the only system that writes to the heat pump. This daemon only sets a price limit.

## How it works

1. Every `POLL_INTERVAL` seconds, the daemon reads `GET /api/tariff/grid`.
2. It keeps the price slots in the next `HOURS` hours and weights them by duration, so 15-minute and hourly tariffs give the same result.
3. It sorts the slots by price and takes the lowest price that covers `FRACTION` of the time. That price is the limit.
4. It finds the loadpoints by title in `GET /api/state` and writes the limit with `POST /api/loadpoints/<id>/smartcostlimit/<value>`. It writes only when the value changed.

evcc applies the limit as `price <= limit` in **Solar** mode (API mode `smart`, formerly `pv`). In that mode the loadpoint switches on in cheap slots and on solar surplus, and switches off otherwise. The daemon logs a warning when a loadpoint is in another mode.

| Loadpoint | evcc on (cheap slot) | evcc off (other slots) |
|---|---|---|
| MasterTherm (space heating) | A_40 = 5.0 (heaters start early), A_299 boost | A_40 = 300.0 (heaters wait, comfort floor stays) |
| MasterTherm SHW (hot water) | D_29 = 1 (SHW on) | D_29 = 0 |

The heat pump side is configured in the evcc switch socket of each loadpoint. It is not part of this daemon.

## Safety

- The daemon does not change the limit when fewer than `MIN_HOURS` of prices are known. This happens for example before the day-ahead prices appear.
- On any error, the daemon logs it and keeps the current limit.
- "Off" for space heating raises the heater start threshold. It does not block the heaters. When the heat deficit reaches 300 °C×min, the controller starts the heaters anyway.

## Configuration

All via environment variables:

| Variable | Required | Default | Description |
|---|---|---|---|
| `EVCC_URL` | yes | | evcc base URL |
| `EVCC_API_KEY` | no | | evcc API key, sent as Bearer token |
| `LOADPOINTS` | no | `MasterTherm,MasterTherm SHW` | Comma-separated evcc loadpoint titles |
| `FRACTION` | no | `0.4` | Share of the cheapest time to heat in, in (0, 1] |
| `HOURS` | no | `24` | Look-ahead window in hours |
| `MIN_HOURS` | no | `8` | Minimum known price horizon in hours |
| `POLL_INTERVAL` | no | `900` | Seconds between runs |
| `DRY_RUN` | no | `false` | Compute and log, but do not write |
| `LOG_LEVEL` | no | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## Run

```sh
cp .env.example .env   # set EVCC_URL
docker compose up -d
```

Test locally without writes:

```sh
uv venv .venv && uv pip install -r requirements.txt --python .venv/bin/python
EVCC_URL=http://evcc:7070 DRY_RUN=true .venv/bin/python src/main.py
```

## Development

```sh
.venv/bin/pytest
```

CI runs the tests on every push. A `v*` tag publishes the image to GHCR with the version tag and the git SHA tag.
