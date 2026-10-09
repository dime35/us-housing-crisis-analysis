"""CLI: download raw files and load every source into data/interim/<source>.parquet."""

from typing import Optional

from loguru import logger
import typer

from us_housing_crisis_analysis.config import INTERIM_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import SOURCE_NAMES, get_source

# Never print local variables in tracebacks: source download() functions hold API keys.
app = typer.Typer(pretty_exceptions_show_locals=False)


def _selected(source: Optional[str]) -> list[str]:
    if source is None:
        return list(SOURCE_NAMES)
    if source not in SOURCE_NAMES:
        raise typer.BadParameter(f"unknown source {source!r}; choose from {SOURCE_NAMES}")
    return [source]


@app.command()
def download(
    source: Optional[str] = typer.Option(None, help="One source; default all"),
    force: bool = typer.Option(False, help="Download again even if raw files exist"),
):
    for name in _selected(source):
        paths = get_source(name).download(force=force)
        logger.success(f"{name}: {len(paths)} raw files")


@app.command()
def load(source: Optional[str] = typer.Option(None, help="One source; default all")):
    INTERIM_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name in _selected(source):
        df = validate_long(get_source(name).load())
        out = INTERIM_DATA_DIR / f"{name}.parquet"
        df.to_parquet(out, index=False)
        logger.success(f"{name}: {len(df):,} rows -> {out}")


if __name__ == "__main__":
    app()
