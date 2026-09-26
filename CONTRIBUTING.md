# Contributing

## Getting started

```bash
git clone https://github.com/nickels/mastertherm-price-modulator.git
cd mastertherm-price-modulator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running tests

```bash
pytest tests/ -v
```

The tests need no evcc instance. evcc responses are stubbed with pytest-httpx or a fake client.

## Code structure

```
src/
├── config.py       # Environment variable parsing
├── controller.py   # Price slots and the cheapest-fraction limit
├── evcc.py         # evcc REST API client
├── sync.py         # One run: compute the limit and write it to the loadpoints
└── main.py         # Async loop entry point
```

## Making changes

1. Write tests first, then the implementation.
2. Run `pytest tests/ -v` and make sure all tests pass.
3. Use conventional commits: `feat(scope):`, `fix(scope):`, `test(scope):`.

## Releasing

Push a `v*` tag. CI runs the tests and publishes the image to GHCR with the version tag and the git SHA tag.

## Building the Docker image

```bash
docker build -t mastertherm-price-modulator .
```
