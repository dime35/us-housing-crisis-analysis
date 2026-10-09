"""Source modules. Each exposes download(force=False) -> list[Path] and load() -> DataFrame
in the shared long format (see schema.py)."""

from importlib import import_module
from types import ModuleType

# Run order for `dataset download` / `dataset load`. Each source task appends its module name.
SOURCE_NAMES: list[str] = []


def get_source(name: str) -> ModuleType:
    return import_module(f"us_housing_crisis_analysis.sources.{name}")
