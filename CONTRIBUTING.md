# Contributing

## Setup

```bash
git clone https://github.com/your-username/log-corr
cd log-corr
python -m venv .venv
. .venv/Scripts/activate
pip install -e ".[dev]"
cp .env.example .env
cp .logcorr.toml.example .logcorr.toml
```

## Checks

```bash
python -m pytest tests -q
ruff check .
ruff format --check .
mypy log_correlation_agent --strict --ignore-missing-imports
```

## Adding Parsers

Add parser logic under `log_correlation_agent/parsers/`, route it from `ParserFactory`, keep regex patterns anchored and safe, and add tests in `tests/`.

## Adding Anomalies

Add the SQL/local rule in `nodes/anomaly_detector.py`, respect suppression, and cover threshold, below-threshold, and suppression behavior.

## Pull Requests

Use `feat/`, `fix/`, `chore/`, `docs/`, or `perf/` branch prefixes. Include tests, avoid hardcoded secrets, and update README when user-facing behavior changes.
