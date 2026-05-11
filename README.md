# Raw Logger

Raw Logger is a local-first CLI for correlating logs across services. It watches or ingests multiple log files, normalizes timestamps, stores events in an in-memory SQLite timeline, and answers operational questions such as "what happened before this 500 error?"

## Features

- Format-aware parsing for JSON, nginx/apache access logs, ISO plaintext, and unknown logs.
- Timestamp normalization with confidence and clock-skew estimation.
- Multi-line stack trace stitching.
- Log rotation and truncation detection.
- In-memory SQLite timeline with WAL settings and indexed queries.
- Priority queues, adaptive sampling, and event fingerprinting.
- Anomaly detection for error spikes, auth cascades, and silent services.
- Incident clustering and causal/timeline/count query routing.
- Safe LLM prompt sanitization and Gemini adapter with retries.

## Install

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e ".[dev]"
```

## Quick Start

```bash
log-corr --no-llm --watch ./api.log --watch ./worker.log --query "what caused the 500 error?"
```

With a config file:

```bash
cp .logcorr.toml.example .logcorr.toml
log-corr --config .logcorr.toml --query "how many errors?"
```

## Supported Formats

JSON, nginx combined access logs, apache-style access logs, ISO timestamp plaintext, syslog-like text, and unknown lines marked for fuzzy parsing.

## Architecture

watcher -> stitcher -> priority queues -> parser pool -> SQLite timeline -> anomaly detector -> query router -> heuristic reducer -> response formatter -> optional LLM reasoner.

## Limitations

The production slice is single-machine and in-memory by default. Timeline state resets on restart unless a SQLite path is supplied by future extensions. Live watchdog loops and Gemini calls are integration points, but tests use deterministic local behavior only.
