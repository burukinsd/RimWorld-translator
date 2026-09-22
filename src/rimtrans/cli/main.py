"""The `rimtrans` CLI entry point.

Registers every subcommand from `ARCHITECTURE.md` §10 now, as a stub, so
the command surface is fixed early and later Epics fill in behavior
instead of designing it. Each stub identifies the Epic that owns its real
implementation, per issue #16's out-of-scope mapping.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from rimtrans.config.loader import load_config
from rimtrans.errors import ConfigError
from rimtrans.log import configure_logging

app = typer.Typer(
    name="rimtrans",
    help=(
        "Hybrid local+remote LLM pipeline for translating RimWorld mods into "
        "Russian, without ever modifying the original mods."
    ),
    no_args_is_help=True,
    add_completion=False,
)

# command -> (owning Epic number, Epic title), per issue #16's mapping.
_OWNING_EPIC: dict[str, tuple[int, str]] = {
    "scan": (2, "RimWorld Localization Extraction"),
    "diff": (2, "RimWorld Localization Extraction"),
    "translate": (5, "LLM Providers & Hybrid Routing"),
    "validate": (6, "Validation & QA"),
    "build": (8, "Translation Mod Generation"),
    "report": (9, "CLI & Reporting"),
    "glossary": (3, "Translation Memory & Glossary"),
    "benchmark": (10, "Model Benchmark"),
}


def _not_implemented(command: str) -> None:
    epic_number, epic_title = _OWNING_EPIC[command]
    typer.echo(
        f"'rimtrans {command}' is not yet implemented — tracked in "
        f"Epic #{epic_number} ({epic_title})."
    )
    raise typer.Exit(code=0)


ConfigOption = Annotated[
    Path | None, typer.Option("--config", "-c", help="Path to the rimtrans config file.")
]
VerboseOption = Annotated[
    bool, typer.Option("--verbose", "-v", help="Enable verbose (debug) logging.")
]


@app.callback()
def main(
    ctx: typer.Context,
    config: ConfigOption = None,
    verbose: VerboseOption = False,
) -> None:
    configure_logging(verbose=verbose)
    ctx.obj = {"config_path": config, "config": None}
    if config is not None:
        try:
            ctx.obj["config"] = load_config(config)
        except ConfigError as exc:
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(code=1) from exc


@app.command(help="Discover installed/local mods, resolve versions, report coverage.")
def scan() -> None:
    _not_implemented("scan")


@app.command(help="Show what's new/changed/stale vs. Translation Memory.")
def diff() -> None:
    _not_implemented("diff")


@app.command(help="Run the hybrid translation pipeline (respects router policy).")
def translate() -> None:
    _not_implemented("translate")


@app.command(help="Re-run validation gates over current Translation Memory state.")
def validate() -> None:
    _not_implemented("validate")


@app.command(help="Generate the standalone translation mod.")
def build() -> None:
    _not_implemented("build")


@app.command(help="Human-readable coverage/cost/quality report.")
def report() -> None:
    _not_implemented("report")


@app.command(help="Manage global/mod/semantic-type glossary entries.")
def glossary() -> None:
    _not_implemented("glossary")


@app.command(help="Run the benchmark subsystem against registered providers.")
def benchmark() -> None:
    _not_implemented("benchmark")


def run() -> None:
    app()


if __name__ == "__main__":
    run()
