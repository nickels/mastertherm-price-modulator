# MasterTherm Price Modulator

A small Python daemon that makes the MasterTherm heat pump heat only in the cheapest hours. It reads the grid price forecast from [evcc](https://evcc.io), computes per loadpoint the price that covers the cheapest share of the next 24 h (40 % for space heating, 20 % for hot water), and sets that value as the **smart cost limit** of that loadpoint in evcc.

evcc stays the only system that writes to the heat pump. This daemon only sets a price limit.

## How it works

1. Every `POLL_INTERVAL` seconds, the daemon reads `GET /api/tariff/grid`.
2. It keeps the price slots in the next `HOURS` hours and weights them by duration, so 15-minute and hourly tariffs give the same result.
3. It sorts the slots by price and takes the lowest price that covers the loadpoint's fraction of the time. That price is the loadpoint's limit.
4. It finds the loadpoints by title in `GET /api/state` and writes the limit with `POST /api/loadpoints/<id>/smartcostlimit/<value>`. It writes only when the value changed.

evcc applies the limit as `price <= limit` in **Solar** mode (API mode `smart`, formerly `pv`). In that mode the loadpoint switches on in cheap slots and on solar surplus, and switches off otherwise. The daemon logs a warning when a loadpoint is in another mode.

| Loadpoint | evcc on (cheap slot) | evcc off (other slots) |
|---|---|---|
| MasterTherm (space heating) | A_40 = 5.0 (heaters start early), A_299 boost | A_40 = 300.0 (heaters wait, comfort floor stays) |
| MasterTherm SHW (hot water) | D_29 = 1 (SHW on) | D_29 = 0 |

The heat pump side is configured in the evcc switch socket of each loadpoint. It is not part of this daemon.

### SHW boost

A separate evcc loadpoint "MasterTherm SHW Boost" raises the SHW setpoint (A_129) to 60 °C when the price is at or below a fixed smart cost limit of 0.15 €/kWh. This daemon does not manage that loadpoint. The SHW floor of 0.15 keeps the SHW loadpoint on whenever the boost is on, also on days when the cheapest 20 % ends below 0.15.

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
| `LOADPOINTS` | no | `MasterTherm:0.4,MasterTherm SHW:0.2:0.15` | Comma-separated `title[:fraction[:floor]]`. The limit never drops below `floor` (€/kWh). |
| `FRACTION` | no | `0.4` | Fraction for a title without its own `:fraction`, in (0, 1] |
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

## Synology deployment

Container Manager on DSM 7 does not support `env_file:`, so put the environment variables inline in the compose YAML.

In Container Manager, go to **Project** > **Create**:

- **Project name**: `mastertherm-price-modulator`
- **Path**: `/docker/mastertherm-price-modulator`
- **Source**: Create docker-compose.yml, and paste:

```yaml
services:
  mastertherm-price-modulator:
    image: ghcr.io/nickels/mastertherm-price-modulator:0.2.0
    container_name: mastertherm-price-modulator
    restart: unless-stopped
    tty: true
    network_mode: host
    environment:
      EVCC_URL: "http://192.168.1.20:7070"
      LOADPOINTS: "MasterTherm:0.4,MasterTherm SHW:0.2:0.15"
      HOURS: "24"
      POLL_INTERVAL: "900"
      DRY_RUN: "false"
      LOG_LEVEL: "INFO"
```

Click **Next**, then **Done**. Container Manager pulls the image from GHCR and starts the container.

To update: change the image tag, then go to **Project** > select the project > **Action** > **Build**.

## Development

```sh
.venv/bin/pytest
```

CI runs the tests on every push. A `v*` tag publishes the image to GHCR with the version tag and the git SHA tag.
