"""The `rimtrans` CLI entry point.

Registers every subcommand from `ARCHITECTURE.md` §10, most still as a
stub identifying the Epic that owns their real implementation (issue
#16). `translate`/`build` are wired to the walking-skeleton pipeline
(issue #73): single mod, `Keyed`-only, pass-through provider — their
full scope remains Epic #5/#8's job.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from rimtrans.config.loader import load_config
from rimtrans.errors import ConfigError, FatalError
from rimtrans.log import configure_logging
from rimtrans.pipeline import run_build, run_translate

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
# 'translate'/'build' are implemented at walking-skeleton scope (issue #73)
# and no longer stub through this map to their full-scope owning Epic.
_OWNING_EPIC: dict[str, tuple[int, str]] = {
    "scan": (2, "RimWorld Localization Extraction"),
    "diff": (2, "RimWorld Localization Extraction"),
    "validate": (6, "Validation & QA"),
    "report": (9, "CLI & Reporting"),
    "glossary": (3, "Translation Memory & Glossary"),
    "benchmark": (10, "Model Benchmark"),
}

DEFAULT_OUTPUT_DIR = Path("./output")


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


ModPathOption = Annotated[
    Path,
    typer.Option(
        "--mod-path",
        help="Path to a single local mod directory to translate (walking-skeleton scope).",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
]
OutputOption = Annotated[
    Path,
    typer.Option("--output", "-o", help="Output directory for pipeline state and the built mod."),
]


@app.command(
    help=(
        "Run the translation pipeline (walking-skeleton scope: single mod, Keyed-only, "
        "pass-through provider; full hybrid routing is Epic #5)."
    )
)
def translate(mod_path: ModPathOption, output: OutputOption = DEFAULT_OUTPUT_DIR) -> None:
    try:
        result = run_translate(mod_path, output)
    except FatalError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(
        f"Translated {len(result.results)} Keyed string(s) from '{result.mod.mod_id}' "
        f"({result.passed_count} passed validation)."
    )


@app.command(help="Re-run validation gates over current Translation Memory state.")
def validate() -> None:
    _not_implemented("validate")


@app.command(
    help=(
        "Generate the standalone translation mod (walking-skeleton scope: single mod, "
        "Keyed-only tree + basic About.xml; full scope is Epic #8). Requires a prior "
        "'rimtrans translate' run against the same --output directory."
    )
)
def build(output: OutputOption = DEFAULT_OUTPUT_DIR) -> None:
    try:
        result = run_build(output)
    except FatalError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(
        f"Generated '{result.output_mod_dir}' with {result.emitted_count} Keyed string(s).\n"
        f"  {result.keyed_path}\n"
        f"  {result.about_path}"
    )


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
