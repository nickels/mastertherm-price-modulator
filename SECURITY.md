# Security

## Threat model

This daemon changes one setting in evcc: the smart cost limit of the configured loadpoints. evcc then switches the MasterTherm heat pump (space heating and hot water) through its own configuration. The daemon has no direct connection to the heat pump.

### Attack surface

- **evcc API**: The loadpoint endpoints need no authentication unless evcc is configured for it. A compromised evcc instance or a man-in-the-middle can feed false price data. The daemon then sets a wrong limit, and the heat pump heats at expensive times or waits longer.
- **Environment variables**: `EVCC_URL` and the optional `EVCC_API_KEY` must stay out of version control.

### Mitigations

- Deploy on the same isolated VLAN or subnet as evcc.
- Do not expose the evcc API to the internet.
- The daemon only writes a price limit. It cannot switch the heat pump directly, and it cannot override the controller's safety functions.
- For space heating, evcc "off" raises the heater start threshold. It does not block the heaters, so the controller still heats when the heat deficit gets large.
- On an error, the daemon keeps the current limit. When it stops, evcc keeps the last limit.

## Reporting a vulnerability

If you discover a security issue, please report it privately via [GitHub Security Advisories](https://github.com/nickels/mastertherm-price-modulator/security/advisories/new) rather than opening a public issue.
