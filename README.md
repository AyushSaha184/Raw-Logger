# Raw Logger

A local-first CLI tool for correlating logs across multiple services. It watches or ingests log files, normalizes timestamps with clock-skew estimation, stores events in an in-memory SQLite timeline.

## Features

- **Format-aware parsing** - Supports JSON, nginx/apache access logs, ISO plaintext, syslog-like text, and unknown logs (marked for fuzzy parsing)
- **Timestamp normalization** - Normalizes timestamps with confidence scoring and clock-skew estimation
- **Multi-line stitching** - Automatically stitches split stack traces and multi-line log entries
- **Log rotation detection** - Detects log rotation and truncation to prevent reading stale data
- **In-memory timeline** - SQLite timeline with WAL settings and indexed queries for fast retrieval
- **Smart ingestion** - Priority queues, adaptive sampling, and event fingerprinting for efficient processing
- **Anomaly detection** - Detects error spikes, auth cascades, and silent services
- **Query routing** - Routes queries to causal, timeline, or count analysis paths
- **LLM reasoning** - Optional LLM reasoner with safe prompt sanitization and Gemini adapter with retries

## Install

### Option 1: Clone and Install

```bash
git clone https://github.com/AyushSaha184/Raw-Logger.git
cd Raw-Logger

# Standard install
pip install .

# OR development install
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Option 2: Direct Install from GitHub

```bash
pip install git+https://github.com/AyushSaha184/Raw-Logger.git
```

This makes the `rawlogger` command available.

## Configuration

### Using a config file (recommended)

1. Copy the example configuration file:
```bash
cp .logcorr.toml.example your-config.toml
```

2. Edit `your-config.toml` to configure your log sources and LLM settings

### Using environment variables

Alternatively, you can set environment variables in a `.env` file:

```bash
# Set your Gemini API key
export GEMINI_API_KEY=your_api_key_here
```

Then run with `--no-llm` flag for local-only mode, or set the key for LLM-powered analysis.

## Quick Start

### Watch mode - Monitor logs in real-time

Watch your log files and ask questions about ongoing events:

```bash
rawlogger --no-llm --watch your-api.log --watch your-worker.log --query "what caused the 500 error?"
```

### Query mode - Analyze existing logs

Query logs you've already read:

```bash
rawlogger --no-llm --ingest your-app.log --query "how many errors occurred?"
```

### Using config file

```bash
rawlogger --config your-config.toml --query "show me all auth failures in the last hour"
```

### With LLM reasoning enabled

```bash
rawlogger --watch your-api.log --watch your-worker.log --query "what caused the cascade of failures?"
```

This uses the Gemini adapter to provide natural language explanations of correlated events.

## Usage Examples

### Watch multiple service logs

```bash
rawlogger \
  --watch your-api-service.log \
  --watch your-worker-service.log \
  --watch your-database.log \
  --query "find the root cause of the 500 errors"
```

### Ingest and query historical logs

```bash
rawlogger \
  --ingest your-app.log \
  --ingest your-nginx-access.log \
  --query "timeline of memory spike events"
```

### Filter by time range

```bash
rawlogger \
  --watch your-app.log \
  --start-time "2024-01-15T10:00:00" \
  --end-time "2024-01-15T12:00:00" \
  --query "errors in this timeframe"
```

### Enable anomaly detection

```bash
rawlogger \
  --watch your-app.log \
  --detect-anomalies \
  --query "what anomalies did you detect?"
```

## Supported Log Formats

| Format | Description | Example |
|--------|-------------|---------|
| JSON | Structured JSON logs | `{"timestamp": "...", "level": "ERROR", "message": "..."}` |
| Nginx | Nginx combined access logs | `127.0.0.1 - - [10/Oct/2024:13:55:36] "GET /api HTTP/1.1" 500` |
| Apache | Apache-style access logs | Similar to Nginx format |
| ISO Plaintext | ISO timestamp plaintext | `2024-10-10T14:30:00 ERROR Failed to connect` |
| Syslog | Syslog-formatted text | `Oct 11 14:30:00 hostname service: message` |
| Unknown | Unrecognized formats | Sent to fuzzy parser for LLM-assisted parsing |

## Architecture

```
┌─────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐
│ Watcher │ -> │ Stitcher│ -> │  Parser  │ -> │ Timeline │
│         │    │         │    │   Pool   │    │ (SQLite) │
└─────────┘    └─────────┘    └──────────┘    └──────────┘
                                                  │
                                                  v
┌─────────────┐    ┌────────────┐    ┌─────────────────┐
│   Query     │ <- │  Heuristic │ <- │    Anomaly     │
│   Router    │    │   Reducer  │    │   Detector     │
└─────────────┘    └────────────┘    └─────────────────┘
        │
        v
┌─────────────────┐
│  LLM Reasoner   │ (optional)
│   (Gemini)      │
└─────────────────┘
```

### Components

- **Watcher** - Monitors log files for changes using file system events
- **Stitcher** - Joins multi-line log entries (stack traces, JSON spans)
- **Parser Pool** - Parallel parsing with format detection
- **Timeline** - SQLite-based event storage with indexed queries
- **Anomaly Detector** - Identifies error spikes, cascades, and anomalies
- **Query Router** - Routes questions to appropriate analysis paths
- **Heuristic Reducer** - Applies filtering and aggregation rules
- **Response Formatter** - Structures output for display
- **LLM Reasoner** - Provides natural language explanations (optional)

## Development

### Run tests

```bash
pytest
```

### Run with coverage

```bash
pytest --cov=log_correlation_agent
```

### Type checking

```bash
mypy log_correlation_agent
```

### Linting

```bash
ruff check log_correlation_agent
```

## Configuration Options

### Config File (your-config.toml)

```toml
[log_corr]
# Watch or ingest log files
watch = ["your-app.log", "your-worker.log"]
ingest = ["your-historical.log"]

# LLM settings
llm_enabled = true
llm_model = "gemini-2.0-flash"

# Anomaly detection
detect_anomalies = true

# Query settings
default_query = "show me errors"

# Timeline settings
timeline_retention_hours = 24

[parsing]
# Enable fuzzy parsing for unknown formats
fuzzy_parse = true
max_line_length = 10000

[anomaly_detection]
# Sensitivity thresholds
error_spike_threshold = 10
auth_cascade_threshold = 5
silent_service_minutes = 30
```

## Limitations

- **Single-machine** - The production slice runs on a single machine
- **In-memory** - Timeline state resets on restart (no persistence by default)
- **Local-only** - Designed for local development/debugging, not production clusters
- **Integration points** - Live watchdog loops and Gemini API calls are integration points; tests use deterministic local behavior only

## License

See [LICENSE](LICENSE) for details.