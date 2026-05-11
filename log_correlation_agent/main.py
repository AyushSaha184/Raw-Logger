from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from log_correlation_agent.config import load_config
from log_correlation_agent.graph import run_query
from log_correlation_agent.logger import configure_logging
from log_correlation_agent.parsers.factory import ParserFactory
from log_correlation_agent.timeline.buffer import TimelineBuffer

app = typer.Typer(help="Local-first AI log correlation agent.")
console = Console()


@app.callback(invoke_without_command=True)
def main(
    watch: Annotated[
        list[Path] | None, typer.Option("--watch", "-w", help="Log file to ingest.")
    ] = None,
    config: Annotated[
        Path | None, typer.Option("--config", "-c", help="Path to .logcorr.toml.")
    ] = None,
    query: Annotated[
        str | None, typer.Option("--query", "-q", help="Question to answer against ingested logs.")
    ] = None,
    no_llm: Annotated[
        bool, typer.Option("--no-llm", help="Disable all external LLM calls.")
    ] = False,
) -> None:
    configure_logging()
    cfg = load_config(str(config) if config else None, no_llm=no_llm)
    watched = [str(path) for path in (watch or [])] or [item.path for item in cfg.log_files]
    if not watched and query is None:
        table = Table(title="log-corr")
        table.add_column("Status")
        table.add_column("Detail")
        table.add_row("ready", "Use --watch FILE and --query TEXT, or configure .logcorr.toml")
        table.add_row("llm", "disabled" if cfg.no_llm else "enabled when required")
        console.print(table)
        return

    timeline = TimelineBuffer(retention_minutes=cfg.retention_minutes)
    parser = ParserFactory()
    try:
        for path_value in watched:
            path = Path(path_value)
            if not path.exists():
                console.print(f"[yellow]missing log file skipped:[/yellow] {path}")
                continue
            service = path.stem
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                timeline.insert_sync(parser.parse(line, service=service, source_file=str(path)))
        if query:
            response = run_query(
                timeline.conn, query, no_llm=cfg.no_llm, max_events=cfg.max_events_for_llm
            )
            console.print(response)
        else:
            console.print(f"Ingested logs from {len(watched)} file(s).")
    finally:
        timeline.close()


if __name__ == "__main__":
    app()
