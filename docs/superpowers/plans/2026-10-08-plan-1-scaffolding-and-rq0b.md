# Plan 1: Scaffolding and RQ0b (US Structural Break) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the project scaffolding and the US long-run pipeline far enough to answer RQ0b: does US population growth stop following income, and when? There are two versions, states 1880–2020 and metros 1940–2020.

**Architecture:** Each source module downloads raw files to `data/raw/<source>/` and parses them into one shared long-format table, validated by `schema.py` and written to `data/interim/<source>.parquet`. `features.py` joins those tables into two wide panels, `us_state_longrun` and `us_metro_longrun`. Counties are mapped to constant 2023 CBSA boundaries in `geography.py`. `modeling/breaks.py` estimates the decade coefficients and break tests, and notebook `1.1` produces the figure and tables.

**Tech Stack:** Python 3.12, pandas, pyarrow, requests, ipumspy (NHGIS and IPUMS USA APIs), openpyxl, statsmodels, matplotlib, typer, loguru, pytest, jupytext and nbconvert.

**Spec:** `docs/superpowers/specs/2026-10-08-housing-growth-mismatch-design.md`. This plan covers build-order step 1 and the RQ0b half of step 2. RQ0a (city-proper population) is Plan 2.

## Global Constraints

- `requires-python = ">=3.12"`. The project venv is `venv/` (not `.venv`). Run tools as `venv/bin/python -m ...`.
- Every source module exposes `download(force: bool = False) -> list[Path]` and `load() -> pd.DataFrame`. If raw files already exist, `download()` skips them unless `force=True`.
- `load()` returns exactly these columns: `geo_id, geo_name, geo_level, country_iso3, year, variable, value, unit, source`.
- `geo_id` prefixes depend on `geo_level`:
  - `county:` for county;
  - `cbsa:` or `oecd:` for metro;
  - `state:` for state;
  - `iso3:` for country;
  - `place:` for city;
  - `wup:` for agglomeration.
- Constant metro boundaries use the **2023 CBSA delineation**, and metropolitan areas only.
- `/data/` is gitignored. Hand-collected inputs go in `references/manual_data/` and reviewed crosswalks in `references/crosswalks/`; both are committed.
- API keys are read from `.env` as `IPUMS_API_KEY` (one key covers both NHGIS and IPUMS USA) and `BEA_API_KEY`. They are never committed or logged.
- RQ0b start-year rule: each version starts at the first decade from which income exists for every decade onward, with no interpolation. States start in 1880 and metros in 1940.
- **Docs:** every task that adds a source, method or decision updates `Claude/research/sources.md`, `Claude/methods/*.md` or `Claude/methods/decisions.md` in the same commit.
- **Commits:** commit after every task. Messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Prerequisite:** before Task 4, the user registers for IPUMS (https://account.ipums.org/api_keys) and BEA (https://apps.bea.gov/API/signup/) and adds both keys to `.env`.

## Review Focus

1. **Running `make data` a second time** should skip every download that already exists, including the NHGIS and IPUMS extracts. Re-requesting them would cost hours. Tested in Tasks 2, 4 and 8.
2. **A missing API key** should fail immediately with a message naming the variable and `.env`, not with a KeyError or HTTP 401 deep in a library. Tested in Task 2 (`require_env`), and every API module calls it before any network work.
3. **Historical counties with no modern FIPS code**, or that merged (Virginia independent cities, Dade → Miami-Dade), should be harmonized or reported, never silently dropped. Tested in Task 3 (fixes) and Task 10 (unmatched population share ≤ 0.5%).
4. **BEA suppressed values (`(NA)`, `(D)`) and BEA error payloads that arrive with HTTP 200:** suppressed values should become dropped rows, and error payloads should raise and not be cached. Tested in Task 6.
5. **A unit missing income or population in some decade** (territories before statehood, metros missing a source) should drop out of that decade only, never be zero-filled or crash. Tested in Task 10 (panels keep NaN) and Task 11 (`prepare_decade_panel` excludes the row).

---

## File structure

| File | Responsibility |
|---|---|
| `us_housing_crisis_analysis/config.py` | Paths, env var names, RQ0b year rules |
| `us_housing_crisis_analysis/schema.py` | Long-format columns and `validate_long()` |
| `us_housing_crisis_analysis/sources/__init__.py` | `SOURCE_NAMES` registry and `get_source()` |
| `us_housing_crisis_analysis/sources/_http.py` | `download_file()`, `require_env()` |
| `us_housing_crisis_analysis/sources/_ipums.py` | Shared submit, wait and download for IPUMS extracts |
| `us_housing_crisis_analysis/sources/nhgis.py` | State and county population 1790–2020 |
| `us_housing_crisis_analysis/sources/icpsr.py` | County median family income 1950 and 1960 (ICPSR 2896, manual download) |
| `us_housing_crisis_analysis/sources/census_pep.py` | 2020 CBSA estimates base and county membership (validation only) |
| `us_housing_crisis_analysis/sources/bea.py` | State per capita income 1929+; county personal income and population 1969+ (summed to CBSAs in Task 10) |
| `us_housing_crisis_analysis/sources/manual.py` | Klein and Easterlin state income tables |
| `us_housing_crisis_analysis/sources/ipums.py` | 1940 full-count wage income aggregated to counties |
| `us_housing_crisis_analysis/geography.py` | 2023 delineation, county → CBSA, Connecticut legacy counties, county fixes, NHGIS code → FIPS |
| `us_housing_crisis_analysis/dataset.py` | Typer CLI with `download` and `load` |
| `us_housing_crisis_analysis/features.py` | Builds `us_state_longrun` and `us_metro_longrun` |
| `us_housing_crisis_analysis/modeling/breaks.py` | Decade panel, β_d, Chow, break search, standardization |
| `us_housing_crisis_analysis/plots.py` | Figure style and save helper |
| `references/crosswalks/ct_legacy_counties.csv` | Old Connecticut counties → 2023 CBSA |
| `references/crosswalks/county_fixes.csv` | Historical FIPS → successor FIPS |
| `references/crosswalks/growth_allowlist.csv` | Reviewed extreme-growth metro decades |
| `references/manual_data/state_income_historical.csv` | Klein and Easterlin state income, transcribed |
| `references/known_values.csv` | Known values checked by data tests |
| `tests/…` | One test file per module, plus `tests/data/` for data tests |
| `notebooks/1.1-lr-us-structural-break.ipynb` | RQ0b analysis |

---

### Task 1: Scaffolding, config, and the long-format schema

**Files:**
- Modify: `pyproject.toml`, `requirements.txt`, `Makefile`, `us_housing_crisis_analysis/config.py`
- Delete: `us_housing_crisis_analysis/modeling/train.py`, `us_housing_crisis_analysis/modeling/predict.py`
- Create: `us_housing_crisis_analysis/schema.py`, `tests/__init__.py`, `tests/conftest.py`, `tests/test_schema.py`

**Interfaces:**
- Produces:
  - `schema.LONG_COLUMNS: list[str]`
  - `schema.GEO_PREFIXES: dict[str, tuple[str, ...]]`
  - `schema.SchemaError(ValueError)`
  - `schema.validate_long(df: pd.DataFrame) -> pd.DataFrame` (returns `df[LONG_COLUMNS]`)
  - config constants: `INTERIM_DATA_DIR`, `PROCESSED_DATA_DIR`, `RAW_DATA_DIR`, `REFERENCES_DIR`, `CROSSWALKS_DIR`, `MANUAL_DATA_DIR`, `FIGURES_DIR`, `TABLES_DIR`, `IPUMS_API_KEY_ENV = "IPUMS_API_KEY"`, `BEA_API_KEY_ENV = "BEA_API_KEY"`, `RQ0B_STATE_START = 1880`, `RQ0B_METRO_START = 1940`, `RQ0B_END = 2020`, `METRO_LONGRUN_START = 1900`
  - pytest fixtures `fixtures_dir`, `interim`, `processed`

- [ ] **Step 1: Update `pyproject.toml`.** Set `description = "US housing constraints and the growth mismatch of American cities"`, `authors = [{ name = "dime35" }]`, `requires-python = ">=3.12"`, and add:

```toml
dependencies = [
  "pandas>=2.2", "pyarrow>=15", "requests>=2.31", "python-dotenv>=1.0", "typer>=0.12",
  "loguru>=0.7", "tqdm>=4.66", "statsmodels>=0.14", "linearmodels>=6.0", "ipumspy>=0.5",
  "openpyxl>=3.1", "matplotlib>=3.8", "plotly>=5.20", "jupyter>=1.0", "jupytext>=1.16",
  "nbconvert>=7.16", "pytest>=8.0", "ruff>=0.4",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["data: needs built data in data/; skipped when it is absent"]
```

Set `requirements.txt` to the single line `-e .`.

- [ ] **Step 2: Install and confirm the environment.**

Run: `venv/bin/python -m pip install -e . && venv/bin/python -c "import ipumspy, statsmodels, openpyxl; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Delete the template model files.**

Run: `git rm us_housing_crisis_analysis/modeling/train.py us_housing_crisis_analysis/modeling/predict.py`

- [ ] **Step 4: Extend `config.py`.** Append after the existing path block:

```python
REFERENCES_DIR = PROJ_ROOT / "references"
CROSSWALKS_DIR = REFERENCES_DIR / "crosswalks"
MANUAL_DATA_DIR = REFERENCES_DIR / "manual_data"
TABLES_DIR = REPORTS_DIR / "tables"

# Names of the .env variables holding API keys (values are never stored here)
IPUMS_API_KEY_ENV = "IPUMS_API_KEY"  # one key covers NHGIS and IPUMS USA
BEA_API_KEY_ENV = "BEA_API_KEY"

# RQ0b: each version starts at the first decade from which income exists for every
# decade onward (spec §5). No decade is interpolated.
RQ0B_STATE_START = 1880
RQ0B_METRO_START = 1940
RQ0B_END = 2020
METRO_LONGRUN_START = 1900
```

- [ ] **Step 5: Write the failing schema tests** in `tests/test_schema.py`:

```python
import pandas as pd
import pytest

from us_housing_crisis_analysis.schema import LONG_COLUMNS, SchemaError, validate_long


def good_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "geo_id": ["county:24510", "state:24"],
            "geo_name": ["Baltimore city", "Maryland"],
            "geo_level": ["county", "state"],
            "country_iso3": ["USA", "USA"],
            "year": pd.Series([2020, 2020], dtype="int64"),
            "variable": ["population", "population"],
            "value": [585708.0, 6177224.0],
            "unit": ["persons", "persons"],
            "source": ["nhgis", "nhgis"],
        }
    )


def test_valid_frame_passes_and_orders_columns():
    df = good_frame()[list(reversed(LONG_COLUMNS))]
    assert list(validate_long(df).columns) == LONG_COLUMNS


def test_missing_column_fails():
    with pytest.raises(SchemaError, match="missing columns"):
        validate_long(good_frame().drop(columns="unit"))


def test_extra_column_fails():
    with pytest.raises(SchemaError, match="unexpected columns"):
        validate_long(good_frame().assign(extra=1))


def test_null_value_fails():
    df = good_frame()
    df.loc[0, "value"] = None
    with pytest.raises(SchemaError, match="null"):
        validate_long(df)


def test_year_must_be_integer():
    with pytest.raises(SchemaError, match="year"):
        validate_long(good_frame().assign(year=[2020.0, 2020.0]))


def test_prefix_must_match_level():
    df = good_frame()
    df.loc[0, "geo_id"] = "cbsa:12580"
    with pytest.raises(SchemaError, match="prefix"):
        validate_long(df)


def test_unknown_level_fails():
    df = good_frame()
    df.loc[0, "geo_level"] = "planet"
    with pytest.raises(SchemaError, match="geo_level"):
        validate_long(df)


def test_duplicate_key_fails():
    df = pd.concat([good_frame(), good_frame().iloc[[0]]])
    with pytest.raises(SchemaError, match="duplicate"):
        validate_long(df)


def test_one_unit_per_variable():
    df = good_frame()
    df.loc[1, "unit"] = "thousands"
    with pytest.raises(SchemaError, match="more than one unit"):
        validate_long(df)
```

- [ ] **Step 6: Run the tests and confirm they fail.**

Run: `venv/bin/python -m pytest tests/test_schema.py -q`
Expected: collection error `ModuleNotFoundError: ... schema`

- [ ] **Step 7: Implement `us_housing_crisis_analysis/schema.py`:**

```python
"""Shared long format that every source's load() returns (spec §4, source module contract)."""

import pandas as pd

LONG_COLUMNS = [
    "geo_id", "geo_name", "geo_level", "country_iso3",
    "year", "variable", "value", "unit", "source",
]

# geo_id prefixes allowed for each geo_level, so IDs from different namespaces never collide
GEO_PREFIXES: dict[str, tuple[str, ...]] = {
    "city": ("place:",),
    "county": ("county:",),
    "metro": ("cbsa:", "oecd:"),
    "agglomeration": ("wup:",),
    "state": ("state:",),
    "country": ("iso3:",),
}


class SchemaError(ValueError):
    """Raised when a frame does not conform to the long format."""


def validate_long(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in LONG_COLUMNS if c not in df.columns]
    if missing:
        raise SchemaError(f"missing columns: {missing}")
    extra = [c for c in df.columns if c not in LONG_COLUMNS]
    if extra:
        raise SchemaError(f"unexpected columns: {extra}")
    null_cols = [c for c in LONG_COLUMNS if df[c].isna().any()]
    if null_cols:
        raise SchemaError(f"null values in columns: {null_cols}")
    if not pd.api.types.is_integer_dtype(df["year"]):
        raise SchemaError(f"year must be an integer dtype, got {df['year'].dtype}")
    if not pd.api.types.is_float_dtype(df["value"]):
        raise SchemaError(f"value must be a float dtype, got {df['value'].dtype}")
    unknown = set(df["geo_level"]) - set(GEO_PREFIXES)
    if unknown:
        raise SchemaError(f"unknown geo_level values: {sorted(unknown)}")
    for level, prefixes in GEO_PREFIXES.items():
        ids = df.loc[df["geo_level"] == level, "geo_id"]
        bad = ids[~ids.str.startswith(prefixes)]
        if len(bad):
            raise SchemaError(f"geo_id prefix does not match geo_level {level!r}: {bad.iloc[0]}")
    dupes = df.duplicated(["geo_id", "year", "variable"])
    if dupes.any():
        raise SchemaError(f"{int(dupes.sum())} duplicate (geo_id, year, variable) rows")
    units = df.groupby("variable")["unit"].nunique()
    mixed = units[units > 1]
    if len(mixed):
        raise SchemaError(f"variables with more than one unit: {list(mixed.index)}")
    return df[LONG_COLUMNS]
```

- [ ] **Step 8: Write `tests/__init__.py`** (empty) **and `tests/conftest.py`:**

```python
from pathlib import Path

import pandas as pd
import pytest

from us_housing_crisis_analysis.config import INTERIM_DATA_DIR, PROCESSED_DATA_DIR

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


def _read_or_skip(path: Path) -> pd.DataFrame:
    if not path.exists():
        pytest.skip(f"{path.name} is not built; run `make data` and `make features`")
    return pd.read_parquet(path)


@pytest.fixture
def interim():
    """interim("nhgis") -> data/interim/nhgis.parquet, or skip the test if it is absent."""
    return lambda source: _read_or_skip(INTERIM_DATA_DIR / f"{source}.parquet")


@pytest.fixture
def processed():
    """processed("us_state_longrun") -> data/processed/<panel>.parquet, or skip."""
    return lambda panel: _read_or_skip(PROCESSED_DATA_DIR / f"{panel}.parquet")
```

- [ ] **Step 9: Run the tests and confirm they pass.**

Run: `venv/bin/python -m pytest tests/test_schema.py -q`
Expected: `9 passed`

- [ ] **Step 10: Update the Makefile.** Set `PYTHON_VERSION = 3.12` and `PYTHON_INTERPRETER = venv/bin/python`. Replace the `requirements` recipe body with `$(PYTHON_INTERPRETER) -m pip install -U pip` and `$(PYTHON_INTERPRETER) -m pip install -e .`. Change `lint` and `format` to call `$(PYTHON_INTERPRETER) -m ruff`. Replace the `PROJECT RULES` block with:

```make
## Download and load every source into data/interim
.PHONY: data
data:
	$(PYTHON_INTERPRETER) -m us_housing_crisis_analysis.dataset download
	$(PYTHON_INTERPRETER) -m us_housing_crisis_analysis.dataset load

## Build analysis panels into data/processed
.PHONY: features
features:
	$(PYTHON_INTERPRETER) -m us_housing_crisis_analysis.features

## Execute all notebooks in order
.PHONY: notebooks
notebooks:
	$(PYTHON_INTERPRETER) -m jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb

## Run all tests (data tests skip when data/ is not built)
.PHONY: test
test:
	$(PYTHON_INTERPRETER) -m pytest

## Run only tests that need no downloaded data
.PHONY: test-fast
test-fast:
	$(PYTHON_INTERPRETER) -m pytest -m "not data"

## Rebuild everything implemented so far
.PHONY: all
all: data features notebooks test
```

Run: `make test`
Expected: `9 passed`

- [ ] **Step 11: Update the docs.** In `Claude/CLAUDE.md`, fill `## Development Commands` with `make test`, `make test-fast`, `make data`, `make features`, `make notebooks`, and the note "use `venv/bin/python`". In `Claude/methods/pipeline.md`, add a "Schema validation" line: `dataset.py load` runs `validate_long()` on every source before writing.

- [ ] **Step 12: Commit.**

```bash
git add -A pyproject.toml requirements.txt Makefile us_housing_crisis_analysis tests Claude
git commit -m "Add scaffolding: dependencies, config, long-format schema, test harness

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Download helpers, source registry, and the dataset CLI

**Files:**
- Create: `us_housing_crisis_analysis/sources/__init__.py`, `us_housing_crisis_analysis/sources/_http.py`, `tests/test_http.py`, `tests/test_dataset_cli.py`
- Modify: `us_housing_crisis_analysis/dataset.py` (replace the template entirely)

**Interfaces:**
- Consumes: `schema.validate_long`, `config.INTERIM_DATA_DIR`
- Produces:
  - `sources.SOURCE_NAMES: list[str]` (each later task appends its module name)
  - `sources.get_source(name: str) -> ModuleType`
  - `_http.MissingCredentialError(RuntimeError)`
  - `_http.require_env(name: str) -> str`
  - `_http.download_file(url: str, dest: Path, *, force: bool = False, params: dict | None = None, timeout: int = 300) -> Path`
  - CLI: `python -m us_housing_crisis_analysis.dataset download [--source NAME] [--force]` and `... load [--source NAME]`

- [ ] **Step 1: Write the failing tests** in `tests/test_http.py`:

```python
import pytest

from us_housing_crisis_analysis.sources import _http
from us_housing_crisis_analysis.sources._http import MissingCredentialError, download_file, require_env


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        yield self.body


def test_existing_file_is_not_downloaded_again(tmp_path, monkeypatch):
    dest = tmp_path / "raw.csv"
    dest.write_text("cached")

    def fail(*args, **kwargs):
        raise AssertionError("network called for a cached file")

    monkeypatch.setattr(_http.requests, "get", fail)
    assert download_file("https://example.org/raw.csv", dest) == dest
    assert dest.read_text() == "cached"


def test_force_downloads_again(tmp_path, monkeypatch):
    dest = tmp_path / "raw.csv"
    dest.write_text("old")
    monkeypatch.setattr(_http.requests, "get", lambda *a, **k: FakeResponse(b"new"))
    download_file("https://example.org/raw.csv", dest, force=True)
    assert dest.read_text() == "new"
    assert not (tmp_path / "raw.csv.part").exists()


def test_missing_key_names_the_variable(monkeypatch):
    monkeypatch.delenv("BEA_API_KEY", raising=False)
    with pytest.raises(MissingCredentialError, match="BEA_API_KEY.*\\.env"):
        require_env("BEA_API_KEY")


def test_blank_key_counts_as_missing(monkeypatch):
    monkeypatch.setenv("BEA_API_KEY", "   ")
    with pytest.raises(MissingCredentialError):
        require_env("BEA_API_KEY")
```

And in `tests/test_dataset_cli.py`:

```python
import types

import pandas as pd
from typer.testing import CliRunner

from us_housing_crisis_analysis import dataset
from tests.test_schema import good_frame


def fake_module():
    return types.SimpleNamespace(download=lambda force=False: [], load=good_frame)


def test_load_writes_validated_parquet(tmp_path, monkeypatch):
    monkeypatch.setattr(dataset, "SOURCE_NAMES", ["fake"])
    monkeypatch.setattr(dataset, "get_source", lambda name: fake_module())
    monkeypatch.setattr(dataset, "INTERIM_DATA_DIR", tmp_path)
    result = CliRunner().invoke(dataset.app, ["load"])
    assert result.exit_code == 0, result.output
    assert len(pd.read_parquet(tmp_path / "fake.parquet")) == 2


def test_unknown_source_is_rejected(monkeypatch):
    monkeypatch.setattr(dataset, "SOURCE_NAMES", ["fake"])
    result = CliRunner().invoke(dataset.app, ["download", "--source", "nope"])
    assert result.exit_code != 0
    assert "unknown source" in result.output
```

- [ ] **Step 2: Run the tests and confirm they fail.**

Run: `venv/bin/python -m pytest tests/test_http.py tests/test_dataset_cli.py -q`
Expected: collection errors (modules missing)

- [ ] **Step 3: Implement `sources/_http.py`:**

```python
"""Shared download helpers for source modules."""

import os
from pathlib import Path

from loguru import logger
import requests

HEADERS = {"User-Agent": "us-housing-crisis-analysis (academic research)"}


class MissingCredentialError(RuntimeError):
    """An API key needed by a source is not set in the environment."""


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise MissingCredentialError(
            f"{name} is not set. Add `{name}=<your key>` to the .env file in the project root."
        )
    return value


def download_file(
    url: str, dest: Path, *, force: bool = False, params: dict | None = None, timeout: int = 300
) -> Path:
    """Stream url to dest. Skip if dest exists, unless force. Writes via a .part file so an
    interrupted download never looks complete."""
    dest = Path(dest)
    if dest.exists() and not force:
        logger.info(f"skip {dest.name}: already downloaded")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    with requests.get(url, params=params, headers=HEADERS, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    tmp.replace(dest)
    logger.info(f"downloaded {dest.name}")
    return dest
```

- [ ] **Step 4: Implement `sources/__init__.py`:**

```python
"""Source modules. Each exposes download(force=False) -> list[Path] and load() -> DataFrame
in the shared long format (see schema.py)."""

from importlib import import_module
from types import ModuleType

# Run order for `dataset download` / `dataset load`. Each source task appends its module name.
SOURCE_NAMES: list[str] = []


def get_source(name: str) -> ModuleType:
    return import_module(f"us_housing_crisis_analysis.sources.{name}")
```

- [ ] **Step 5: Replace `dataset.py`:**

```python
"""CLI: download raw files and load every source into data/interim/<source>.parquet."""

from typing import Optional

from loguru import logger
import typer

from us_housing_crisis_analysis.config import INTERIM_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import SOURCE_NAMES, get_source

app = typer.Typer()


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
```

- [ ] **Step 6: Run the tests and confirm they pass.**

Run: `venv/bin/python -m pytest tests -q`
Expected: all pass (15 tests)

- [ ] **Step 7: Commit.**

```bash
git add us_housing_crisis_analysis tests
git commit -m "Add download helpers, source registry, and dataset CLI

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Geography — 2023 CBSA delineation, Connecticut legacy counties, county fixes

**Files:**
- Create: `us_housing_crisis_analysis/geography.py`, `references/crosswalks/ct_legacy_counties.csv`, `references/crosswalks/county_fixes.csv`, `tests/test_geography.py`
- Modify: `tests/conftest.py` (add the `delineation_xlsx` fixture), `Claude/methods/geography.md`, `Claude/research/sources.md`

**Interfaces:**
- Consumes: `_http.download_file`, `config.RAW_DATA_DIR`, `config.CROSSWALKS_DIR`
- Produces:
  - `geography.download(force: bool = False) -> list[Path]`
  - `geography.parse_delineation(path: Path) -> pd.DataFrame` with columns `county_fips, cbsa_code, cbsa_title, area_type` (`area_type` ∈ {`metro`, `micro`})
  - `geography.county_to_cbsa(delineation: pd.DataFrame | None = None, metro_only: bool = True) -> pd.DataFrame` (same columns; one row per county, including old Connecticut counties)
  - `geography.load_county_fixes() -> pd.DataFrame` with columns `old_fips, new_fips, year_changed, note`
  - `geography.harmonize_county_fips(df: pd.DataFrame, col: str = "county_fips") -> pd.DataFrame`
  - `geography.fips_from_nhgis_code(code: str) -> str | None` (7-character NHGIS state+county code)
  - `geography.fips_from_gisjoin(gisjoin: str) -> str | None`

- [ ] **Step 1: Create `references/crosswalks/ct_legacy_counties.csv`.** Historical data uses Connecticut's 8 old counties, but the 2023 CBSAs are built from planning regions. Each old county is assigned to the 2023 CBSA that holds most of its population:

```csv
county_fips,county_name,cbsa_code,note
09001,Fairfield County,14860,Bridgeport-Stamford-Danbury; Shelton area now in Waterbury-Shelton (47930)
09003,Hartford County,25540,Hartford-West Hartford-East Hartford
09005,Litchfield County,45860,Torrington (micropolitan; dropped from metro panels)
09007,Middlesex County,25540,Lower Connecticut River Valley region is in the Hartford CBSA
09009,New Haven County,35300,New Haven; Waterbury area now in Waterbury-Shelton (47930)
09011,New London County,35980,Norwich-New London-Willimantic
09013,Tolland County,25540,Hartford-West Hartford-East Hartford
09015,Windham County,49340,Northeastern Connecticut region is in Worcester MA-CT
```

- [ ] **Step 2: Create `references/crosswalks/county_fixes.csv`.** These are historical county FIPS codes that no longer exist, with their successors. Task 10 extends this list from the unmatched-county report.

```csv
old_fips,new_fips,year_changed,note
12025,12086,1997,Dade County renamed Miami-Dade County; FIPS code changed
51515,51019,2013,Bedford city merged into Bedford County
51560,51005,2001,Clifton Forge city merged into Alleghany County
51780,51083,1995,South Boston city merged into Halifax County
51123,51800,1974,Nansemond County merged into Suffolk city
51151,51810,1963,Princess Anne County merged into Virginia Beach city
51129,51550,1963,Norfolk County merged with South Norfolk to form Chesapeake city
51785,51550,1963,South Norfolk city merged into Chesapeake city
51055,51650,1952,Elizabeth City County merged into Hampton city
```

- [ ] **Step 3: Add the `delineation_xlsx` fixture to `tests/conftest.py`.** It reproduces the real file's layout: two title rows, a header row, data rows, then footnotes.

```python
DELINEATION_HEADER = [
    "CBSA Code", "Metropolitan Division Code", "CSA Code", "CBSA Title",
    "Metropolitan/Micropolitan Statistical Area", "Metropolitan Division Title", "CSA Title",
    "County/County Equivalent", "State Name", "FIPS State Code", "FIPS County Code",
    "Central/Outlying County",
]
METRO, MICRO = "Metropolitan Statistical Area", "Micropolitan Statistical Area"
DELINEATION_ROWS = [
    ["12580", "", "548", "Baltimore-Columbia-Towson, MD", METRO, "", "", "Baltimore city", "Maryland", "24", "510", "Central"],
    ["12580", "", "548", "Baltimore-Columbia-Towson, MD", METRO, "", "", "Baltimore County", "Maryland", "24", "005", "Central"],
    ["33100", "", "370", "Miami-Fort Lauderdale-West Palm Beach, FL", METRO, "", "", "Miami-Dade County", "Florida", "12", "086", "Central"],
    ["25540", "", "278", "Hartford-West Hartford-East Hartford, CT", METRO, "", "", "Capitol Planning Region", "Connecticut", "09", "110", "Central"],
    ["14860", "", "408", "Bridgeport-Stamford-Danbury, CT", METRO, "", "", "Western Connecticut Planning Region", "Connecticut", "09", "190", "Central"],
    ["45860", "", "278", "Torrington, CT", MICRO, "", "", "Northwest Hills Planning Region", "Connecticut", "09", "160", "Central"],
    ["31340", "", "", "Lynchburg, VA", METRO, "", "", "Bedford County", "Virginia", "51", "019", "Outlying"],
]


@pytest.fixture
def delineation_xlsx(tmp_path) -> Path:
    blank = [""] * len(DELINEATION_HEADER)
    rows = (
        [["List 1. CORE BASED STATISTICAL AREAS (CBSAs) ..."] + blank[1:], ["July 2023"] + blank[1:]]
        + [DELINEATION_HEADER]
        + DELINEATION_ROWS
        + [blank, ["Note: footnote text"] + blank[1:]]
    )
    path = tmp_path / "list1_2023.xlsx"
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    return path
```

- [ ] **Step 4: Write the failing tests** in `tests/test_geography.py`:

```python
import pandas as pd

from us_housing_crisis_analysis import geography as geo


def test_parse_delineation_builds_padded_fips(delineation_xlsx):
    d = geo.parse_delineation(delineation_xlsx)
    assert len(d) == 7  # title, blank and footnote rows dropped
    assert "24510" in set(d.county_fips)
    assert d.set_index("county_fips").loc["09160", "area_type"] == "micro"


def test_each_county_maps_to_at_most_one_cbsa(delineation_xlsx):
    cw = geo.county_to_cbsa(geo.parse_delineation(delineation_xlsx), metro_only=False)
    assert not cw.county_fips.duplicated().any()


def test_legacy_ct_counties_map_to_2023_cbsas(delineation_xlsx):
    cw = geo.county_to_cbsa(geo.parse_delineation(delineation_xlsx)).set_index("county_fips")
    assert cw.loc["09003", "cbsa_code"] == "25540"  # Hartford County
    assert cw.loc["09001", "cbsa_title"] == "Bridgeport-Stamford-Danbury, CT"
    assert "09005" not in cw.index  # Litchfield -> Torrington is micropolitan


def test_metro_only_drops_micropolitan(delineation_xlsx):
    cw = geo.county_to_cbsa(geo.parse_delineation(delineation_xlsx))
    assert set(cw.area_type) == {"metro"}


def test_fixes_merge_bedford_city_into_bedford_county():
    df = pd.DataFrame({"county_fips": ["51515", "51019", "24510"], "population": [6222.0, 68676.0, 1.0]})
    out = geo.harmonize_county_fips(df).groupby("county_fips")["population"].sum()
    assert out["51019"] == 74898.0
    assert "51515" not in out.index


def test_fixes_are_not_chained():
    fixes = geo.load_county_fixes()
    assert not set(fixes.new_fips) & set(fixes.old_fips)
    assert not fixes.old_fips.duplicated().any()


def test_fips_from_nhgis_codes():
    assert geo.fips_from_nhgis_code("2405100") == "24510"
    assert geo.fips_from_gisjoin("G2405100") == "24510"
    assert geo.fips_from_nhgis_code("4600015") is None  # historical county, no FIPS
    assert geo.fips_from_nhgis_code("") is None
```

- [ ] **Step 5: Run the tests and confirm they fail.**

Run: `venv/bin/python -m pytest tests/test_geography.py -q`
Expected: collection error (module missing)

- [ ] **Step 6: Implement `geography.py`:**

```python
"""Constant 2023 CBSA boundaries built from counties, plus county code harmonization.
Decisions are documented in Claude/methods/geography.md."""

from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import CROSSWALKS_DIR, RAW_DATA_DIR
from us_housing_crisis_analysis.sources._http import download_file

DELINEATION_URL = (
    "https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/"
    "2023/delineation-files/list1_2023.xlsx"
)
RAW_DIR = RAW_DATA_DIR / "geography"
DELINEATION_PATH = RAW_DIR / "list1_2023.xlsx"
AREA_TYPES = {"Metropolitan Statistical Area": "metro", "Micropolitan Statistical Area": "micro"}


def download(force: bool = False) -> list[Path]:
    return [download_file(DELINEATION_URL, DELINEATION_PATH, force=force)]


def parse_delineation(path: Path) -> pd.DataFrame:
    # Two title rows precede the header; footnote rows at the end have no county code.
    raw = pd.read_excel(path, skiprows=2, dtype=str).dropna(subset=["FIPS County Code"])
    return pd.DataFrame(
        {
            "county_fips": raw["FIPS State Code"].str.zfill(2) + raw["FIPS County Code"].str.zfill(3),
            "cbsa_code": raw["CBSA Code"].str.zfill(5),
            "cbsa_title": raw["CBSA Title"],
            "area_type": raw["Metropolitan/Micropolitan Statistical Area"].map(AREA_TYPES),
        }
    ).reset_index(drop=True)


def county_to_cbsa(delineation: pd.DataFrame | None = None, metro_only: bool = True) -> pd.DataFrame:
    """One row per county FIPS -> 2023 CBSA. Adds Connecticut's 8 old counties, which
    historical data uses, mapped to the 2023 CBSA holding most of each county's population."""
    d = parse_delineation(DELINEATION_PATH) if delineation is None else delineation
    cbsas = d.drop_duplicates("cbsa_code").set_index("cbsa_code")[["cbsa_title", "area_type"]]
    ct = pd.read_csv(CROSSWALKS_DIR / "ct_legacy_counties.csv", dtype=str)
    ct = ct[ct.cbsa_code.isin(cbsas.index)].join(cbsas, on="cbsa_code")
    out = pd.concat([d, ct[d.columns]], ignore_index=True)
    if metro_only:
        out = out[out.area_type == "metro"]
    dupes = out.county_fips[out.county_fips.duplicated()]
    if len(dupes):
        raise ValueError(f"counties mapped to more than one CBSA: {sorted(dupes)}")
    return out.reset_index(drop=True)


def load_county_fixes() -> pd.DataFrame:
    return pd.read_csv(CROSSWALKS_DIR / "county_fixes.csv", dtype=str)


def harmonize_county_fips(df: pd.DataFrame, col: str = "county_fips") -> pd.DataFrame:
    """Replace historical county codes with their successors. Callers group and sum afterwards,
    so merged counties (e.g., Bedford city into Bedford County) add up."""
    fixes = load_county_fixes()
    return df.assign(**{col: df[col].replace(dict(zip(fixes.old_fips, fixes.new_fips)))})


def fips_from_nhgis_code(code: str) -> str | None:
    """NHGIS codes are 3-digit state + 4-digit county, each FIPS x 10 for counties that have a
    FIPS code. Historical counties without one use other final digits and return None."""
    code = (code or "").strip()
    if len(code) != 7 or not code.isdigit() or code[2] != "0" or code[6] != "0":
        return None
    return code[:2] + code[3:6]


def fips_from_gisjoin(gisjoin: str) -> str | None:
    return fips_from_nhgis_code((gisjoin or "")[1:])
```

- [ ] **Step 7: Run the tests and confirm they pass.**

Run: `venv/bin/python -m pytest tests/test_geography.py -q`
Expected: `7 passed`

- [ ] **Step 8: Check the parser against the real file.**

Run: `venv/bin/python -c "from us_housing_crisis_analysis import geography as g; g.download(); d=g.parse_delineation(g.DELINEATION_PATH); print(len(d), d.area_type.value_counts().to_dict()); print(g.county_to_cbsa().cbsa_code.nunique())"`
Expected: about 1,900 counties, `metro` about 1,250, and about 390 metro CBSAs. If the header row is not on line 3, fix `skiprows` and the fixture together.

- [ ] **Step 9: Update the docs.**
  - `Claude/methods/geography.md`: replace "Manual fixes log: None yet." with a short description of both CSVs. Document the Connecticut approximation: the Waterbury-Shelton CBSA (47930) has no historical data, and the Connecticut CBSAs are excluded from the 2020 tolerance check. Also note that `fips_from_nhgis_code` is the rule for converting NHGIS codes to FIPS.
  - `Claude/research/sources.md`: set the CBSA delineation row to `active`, with today's access date.

- [ ] **Step 10: Commit.**

```bash
git add us_housing_crisis_analysis/geography.py references/crosswalks tests Claude
git commit -m "Add 2023 CBSA crosswalk with Connecticut legacy counties and county fixes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: NHGIS state and county population (1790–2020)

**Files:**
- Create: `us_housing_crisis_analysis/sources/_ipums.py`, `us_housing_crisis_analysis/sources/nhgis.py`, `tests/fixtures/nhgis/a00_state.csv`, `tests/fixtures/nhgis/a00_county.csv`, `tests/test_nhgis.py`
- Modify: `us_housing_crisis_analysis/sources/__init__.py` (`SOURCE_NAMES = ["nhgis"]`)

**Interfaces:**
- Consumes: `_http.require_env`, `config.IPUMS_API_KEY_ENV`, `geography.fips_from_gisjoin`, `schema.validate_long`
- Produces:
  - `_ipums.run_extract(extract, dest_dir: Path) -> Path` (submits, waits, downloads into `dest_dir`)
  - `_ipums.unpack_csvs(dest_dir: Path, patterns: dict[str, str]) -> list[Path]`
  - `nhgis.download(force=False) -> list[Path]`
  - `nhgis.parse_population(state_csv: Path, county_csv: Path) -> pd.DataFrame` (long format)
  - `nhgis.load() -> pd.DataFrame`
  - Rows produced:
    - `geo_level` ∈ {`state`, `county`};
    - `geo_id` is `state:SS` / `county:SSCCC`, or `state:nhgis-<GISJOIN>` / `county:nhgis-<GISJOIN>` when there is no FIPS code;
    - `variable="population"`, `unit="persons"`, `source="nhgis"`.

- [ ] **Step 1: Create the fixtures.** The column layout follows NHGIS time series tables in `time_by_row_layout`.

`tests/fixtures/nhgis/a00_state.csv`:
```csv
NHGISCODE,GISJOIN,YEAR,STATE,STATEFP,STATENH,A00AA
G240,G240,1880,Maryland,24,240,934943
G240,G240,2020,Maryland,24,240,6177224
G465,G465,1880,Dakota Territory,,465,135177
```

`tests/fixtures/nhgis/a00_county.csv`:
```csv
NHGISCODE,GISJOIN,YEAR,STATE,STATEFP,STATENH,COUNTY,COUNTYFP,COUNTYNH,A00AA
G2405100,G2405100,1950,Maryland,24,240,Baltimore city,510,5100,949708
G2405100,G2405100,2020,Maryland,24,240,Baltimore city,510,5100,585708
G5100190,G5100190,2010,Virginia,51,510,Bedford County,19,0190,68676
G4650015,G4650015,1880,Dakota Territory,,465,Old County,,0015,1234
G2405100,G2405100,1790,Maryland,24,240,Baltimore city,510,5100,
```

- [ ] **Step 2: Write the failing tests** in `tests/test_nhgis.py`:

```python
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import nhgis


def parsed(fixtures_dir):
    d = fixtures_dir / "nhgis"
    return nhgis.parse_population(d / "a00_state.csv", d / "a00_county.csv")


def test_output_is_valid_long_format(fixtures_dir):
    validate_long(parsed(fixtures_dir))


def test_fips_ids_are_zero_padded(fixtures_dir):
    ids = set(parsed(fixtures_dir).geo_id)
    assert {"state:24", "county:24510", "county:51019"} <= ids


def test_rows_without_fips_keep_a_traceable_id(fixtures_dir):
    df = parsed(fixtures_dir)
    assert "state:nhgis-G465" in set(df.geo_id)
    assert "county:nhgis-G4650015" in set(df.geo_id)


def test_blank_population_rows_are_dropped(fixtures_dir):
    df = parsed(fixtures_dir)
    assert not ((df.geo_id == "county:24510") & (df.year == 1790)).any()


def test_download_skips_when_files_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(nhgis, "A00_DIR", tmp_path)
    for name in ("a00_state.csv", "a00_county.csv"):
        (tmp_path / name).write_text("x")

    def fail(*args, **kwargs):
        raise AssertionError("extract submitted although files exist")

    monkeypatch.setattr(nhgis, "run_extract", fail)
    assert len(nhgis.download()) == 2
```

- [ ] **Step 3: Run the tests and confirm they fail.**

Run: `venv/bin/python -m pytest tests/test_nhgis.py -q`
Expected: collection error (module missing)

- [ ] **Step 4: Implement `sources/_ipums.py`:**

```python
"""Submit, wait for, and download IPUMS extracts (NHGIS and IPUMS USA share one API key)."""

from fnmatch import fnmatch
from pathlib import Path
import zipfile

from loguru import logger

from us_housing_crisis_analysis.config import IPUMS_API_KEY_ENV
from us_housing_crisis_analysis.sources._http import require_env


def client():
    from ipumspy import IpumsApiClient

    return IpumsApiClient(require_env(IPUMS_API_KEY_ENV))


def run_extract(extract, dest_dir: Path) -> Path:
    api = client()
    api.submit_extract(extract)
    logger.info(f"submitted {extract.collection} extract {extract.extract_id}; waiting (can take hours)")
    api.wait_for_extract(extract)
    dest_dir.mkdir(parents=True, exist_ok=True)
    api.download_extract(extract, download_dir=dest_dir)
    return dest_dir


def unpack_csvs(dest_dir: Path, patterns: dict[str, str]) -> list[Path]:
    """Copy CSVs out of downloaded NHGIS zips under stable names: {glob pattern: new name}."""
    written: dict[str, Path] = {}
    members_seen = []
    for zpath in sorted(dest_dir.glob("*_csv.zip")):
        with zipfile.ZipFile(zpath) as z:
            for member in z.namelist():
                members_seen.append(member)
                for pattern, name in patterns.items():
                    if fnmatch(Path(member).name, pattern):
                        (dest_dir / name).write_bytes(z.read(member))
                        written[name] = dest_dir / name
    missing = set(patterns.values()) - set(written)
    if missing:
        raise FileNotFoundError(f"{sorted(missing)} not found in extract; members: {members_seen}")
    return [written[n] for n in patterns.values()]
```

- [ ] **Step 5: Implement `sources/nhgis.py`:**

```python
"""NHGIS (IPUMS): state and county population from time series table A00 (1790-2020)."""

from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._ipums import run_extract, unpack_csvs

RAW_DIR = RAW_DATA_DIR / "nhgis"
A00_DIR = RAW_DIR / "a00"
A00_FILES = {"*_ts_nominal_state.csv": "a00_state.csv", "*_ts_nominal_county.csv": "a00_county.csv"}


def download(force: bool = False) -> list[Path]:
    paths = [A00_DIR / name for name in A00_FILES.values()]
    if all(p.exists() for p in paths) and not force:
        return paths
    from ipumspy import AggregateDataExtract, TimeSeriesTable

    extract = AggregateDataExtract(
        collection="nhgis",
        description="Total population, states and counties, 1790-2020",
        time_series_tables=[TimeSeriesTable("A00", geog_levels=["state", "county"])],
        tst_layout="time_by_row_layout",
    )
    run_extract(extract, A00_DIR)
    return unpack_csvs(A00_DIR, A00_FILES)


def _read(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path, dtype=str, encoding="latin-1")


def _long(raw: pd.DataFrame, level: str, ids: pd.Series, names: pd.Series) -> pd.DataFrame:
    value = pd.to_numeric(raw["A00AA"], errors="coerce")
    df = pd.DataFrame(
        {
            "geo_id": ids, "geo_name": names, "geo_level": level, "country_iso3": "USA",
            "year": raw["YEAR"].astype("int64"), "variable": "population",
            "value": value.astype("float64"), "unit": "persons", "source": "nhgis",
        }
    )
    return df[value.notna()]


def parse_population(state_csv: Path, county_csv: Path) -> pd.DataFrame:
    s = _read(state_csv)
    sfp = s["STATEFP"].fillna("").str.zfill(2)
    s_ids = ("state:" + sfp).where(s["STATEFP"].notna(), "state:nhgis-" + s["GISJOIN"])

    c = _read(county_csv)
    has_fips = c["STATEFP"].notna() & c["COUNTYFP"].notna()
    c_fips = c["STATEFP"].fillna("").str.zfill(2) + c["COUNTYFP"].fillna("").str.zfill(3)
    c_ids = ("county:" + c_fips).where(has_fips, "county:nhgis-" + c["GISJOIN"])
    c_names = c["COUNTY"] + ", " + c["STATE"]

    out = pd.concat([_long(s, "state", s_ids, s["STATE"]), _long(c, "county", c_ids, c_names)])
    return validate_long(out.reset_index(drop=True))


def load() -> pd.DataFrame:
    return parse_population(A00_DIR / "a00_state.csv", A00_DIR / "a00_county.csv")
```

Set `SOURCE_NAMES = ["nhgis"]` in `sources/__init__.py`.

- [ ] **Step 6: Run the tests and confirm they pass.**

Run: `venv/bin/python -m pytest tests/test_nhgis.py -q`
Expected: `5 passed`

- [ ] **Step 7: Download the real data and check the headers.** This needs `IPUMS_API_KEY` in `.env`. Extracts take minutes to hours.

Run: `venv/bin/python -m us_housing_crisis_analysis.dataset download --source nhgis && head -2 data/raw/nhgis/a00/a00_county.csv`
Expected: a header with `GISJOIN`, `YEAR`, `STATEFP`, `COUNTYFP`, `A00AA`.
- If ipumspy rejects `tst_layout` or `TimeSeriesTable`, check `help(ipumspy.AggregateDataExtract)` for the installed version and adjust the call.
- If the real headers differ, change the fixture to match the real header first, then the parser, and rerun Step 6.

- [ ] **Step 8: Load and check the totals.**

Run: `venv/bin/python -m us_housing_crisis_analysis.dataset load --source nhgis && venv/bin/python -c "import pandas as pd; d=pd.read_parquet('data/interim/nhgis.parquet'); s=d[(d.geo_level=='state')&(d.year==2020)&(d.geo_id!='state:72')]; print(s.value.sum())"`
Expected: `331449281.0`

- [ ] **Step 9: Update the docs.** In `Claude/research/sources.md`, set the NHGIS row to `active` with today's access date. In `Claude/methods/pipeline.md`, note that NHGIS A00 is "nominally integrated" (counties are linked by name and code, not boundaries), and that rows without FIPS codes use `nhgis-` IDs.

- [ ] **Step 10: Commit.**

```bash
git add us_housing_crisis_analysis tests Claude
git commit -m "Add NHGIS state and county population source (1790-2020)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Census Bureau CBSA estimates base (validation source)

**Files:**
- Create: `us_housing_crisis_analysis/sources/census_pep.py`, `tests/fixtures/census_pep/cbsa-est2023-alldata.csv`, `tests/test_census_pep.py`
- Modify: `sources/__init__.py` (`SOURCE_NAMES = ["nhgis", "census_pep"]`)

**Interfaces:**
- Consumes: `_http.download_file`, `schema.validate_long`
- Produces:
  - `census_pep.download(force=False) -> list[Path]`
  - `census_pep.parse_cbsa_base(path: Path) -> pd.DataFrame`: long format; `geo_id="cbsa:NNNNN"`, `geo_level="metro"`, `year=2020`, `variable="population_estimates_base"`, `unit="persons"`
  - `census_pep.parse_county_membership(path: Path) -> pd.DataFrame` with columns `county_fips, cbsa_code`
  - `census_pep.load() -> pd.DataFrame`

- [ ] **Step 1: Create the fixture.** The columns are a subset of the real file, which has more.

```csv
CBSA,MDIV,STCOU,NAME,LSAD,ESTIMATESBASE2020,POPESTIMATE2020
12580,,,"Baltimore-Columbia-Towson, MD",Metropolitan Statistical Area,2844510,2842145
12580,,24005,"Baltimore County, Maryland",County or equivalent,854535,853351
12580,,24510,"Baltimore city, Maryland",County or equivalent,585708,583132
45860,,,"Torrington, CT",Micropolitan Statistical Area,185186,185000
```

- [ ] **Step 2: Write the failing tests:**

```python
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import census_pep


def test_cbsa_base_keeps_metros_only(fixtures_dir):
    df = validate_long(census_pep.parse_cbsa_base(fixtures_dir / "census_pep/cbsa-est2023-alldata.csv"))
    assert list(df.geo_id) == ["cbsa:12580"]
    assert df.value.iloc[0] == 2844510.0


def test_county_membership(fixtures_dir):
    m = census_pep.parse_county_membership(fixtures_dir / "census_pep/cbsa-est2023-alldata.csv")
    assert set(m.county_fips) == {"24005", "24510"}
    assert set(m.cbsa_code) == {"12580"}
```

- [ ] **Step 3: Run the tests and confirm they fail.** Run: `venv/bin/python -m pytest tests/test_census_pep.py -q`. Expected: collection error.

- [ ] **Step 4: Implement `sources/census_pep.py`:**

```python
"""Census Bureau Population Estimates: 2020 estimates base by CBSA (2023 delineation). Used to
validate the county -> CBSA build; annual estimates are added in the Tier 2 plan."""

from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file

URL = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/metro/totals/cbsa-est2023-alldata.csv"
RAW_PATH = RAW_DATA_DIR / "census_pep" / "cbsa-est2023-alldata.csv"


def download(force: bool = False) -> list[Path]:
    return [download_file(URL, RAW_PATH, force=force)]


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, encoding="latin-1")


def parse_cbsa_base(path: Path) -> pd.DataFrame:
    raw = _read(path)
    m = raw[raw.LSAD == "Metropolitan Statistical Area"]
    df = pd.DataFrame(
        {
            "geo_id": "cbsa:" + m.CBSA.str.zfill(5), "geo_name": m.NAME, "geo_level": "metro",
            "country_iso3": "USA", "year": 2020, "variable": "population_estimates_base",
            "value": m.ESTIMATESBASE2020.astype("float64"), "unit": "persons", "source": "census_pep",
        }
    )
    return validate_long(df.astype({"year": "int64"}).reset_index(drop=True))


def parse_county_membership(path: Path) -> pd.DataFrame:
    raw = _read(path)
    c = raw[raw.LSAD == "County or equivalent"]
    return pd.DataFrame({"county_fips": c.STCOU.str.zfill(5), "cbsa_code": c.CBSA.str.zfill(5)}).reset_index(drop=True)


def load() -> pd.DataFrame:
    return parse_cbsa_base(RAW_PATH)
```

- [ ] **Step 5: Run the tests and confirm they pass.** Run: `venv/bin/python -m pytest tests/test_census_pep.py -q`. Expected: `2 passed`.

- [ ] **Step 6: Check against the real file.** Run: `venv/bin/python -m us_housing_crisis_analysis.dataset download --source census_pep && venv/bin/python -m us_housing_crisis_analysis.dataset load --source census_pep`. Expected: about 390 rows. If column names differ (e.g., no `ESTIMATESBASE2020`), copy the real header into the fixture and fix the parser.

- [ ] **Step 7: Update the docs.** In `Claude/research/sources.md`, set the Population Estimates Program row to `active`, and add "2020 estimates base by CBSA, used for validation" to its coverage.

- [ ] **Step 8: Commit.**

```bash
git add us_housing_crisis_analysis tests Claude
git commit -m "Add Census Bureau CBSA estimates base for crosswalk validation

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: BEA per capita personal income (states 1929+, metros 1969+)

**Files:**
- Create: `us_housing_crisis_analysis/sources/bea.py`, `tests/fixtures/bea/sainc1_state_pcpi.json`, `tests/fixtures/bea/cainc1_msa_pcpi.json`, `tests/test_bea.py`
- Modify: `sources/__init__.py` (append `"bea"`)

**Interfaces:**
- Consumes: `_http.download_file`, `_http.require_env`, `config.BEA_API_KEY_ENV`, `schema.validate_long`
- Produces:
  - `bea.BeaApiError(RuntimeError)`
  - `bea.parse_bea_json(path: Path, geo_level: str) -> pd.DataFrame`: long format; `variable="income_pc"`, `unit="usd_current"`, `source="bea"`; `geo_id` is `state:SS` for states or `cbsa:NNNNN` for metros
  - `bea.download(force=False) -> list[Path]`
  - `bea.load() -> pd.DataFrame`

- [ ] **Step 1: Create the fixtures.**

`tests/fixtures/bea/sainc1_state_pcpi.json`:
```json
{"BEAAPI": {"Request": {}, "Results": {"Statistic": "Per capita personal income", "UnitOfMeasure": "Dollars", "PublicTable": "SAINC1", "Data": [
  {"Code": "SAINC1-3", "GeoFips": "00000", "GeoName": "United States", "TimePeriod": "1929", "CL_UNIT": "Dollars", "UNIT_MULT": "0", "DataValue": "703"},
  {"Code": "SAINC1-3", "GeoFips": "24000", "GeoName": "Maryland", "TimePeriod": "1929", "CL_UNIT": "Dollars", "UNIT_MULT": "0", "DataValue": "779"},
  {"Code": "SAINC1-3", "GeoFips": "24000", "GeoName": "Maryland", "TimePeriod": "2020", "CL_UNIT": "Dollars", "UNIT_MULT": "0", "DataValue": "68,258"},
  {"Code": "SAINC1-3", "GeoFips": "91000", "GeoName": "New England", "TimePeriod": "1929", "CL_UNIT": "Dollars", "UNIT_MULT": "0", "DataValue": "900"},
  {"Code": "SAINC1-3", "GeoFips": "02000", "GeoName": "Alaska *", "TimePeriod": "1929", "CL_UNIT": "Dollars", "UNIT_MULT": "0", "DataValue": "(NA)"}
]}}}
```

`tests/fixtures/bea/cainc1_msa_pcpi.json`:
```json
{"BEAAPI": {"Request": {}, "Results": {"Statistic": "Per capita personal income", "UnitOfMeasure": "Dollars", "PublicTable": "CAINC1", "Data": [
  {"Code": "CAINC1-3", "GeoFips": "12580", "GeoName": "Baltimore-Columbia-Towson, MD (Metropolitan Statistical Area)", "TimePeriod": "1970", "CL_UNIT": "Dollars", "UNIT_MULT": "0", "DataValue": "4,301"},
  {"Code": "CAINC1-3", "GeoFips": "00998", "GeoName": "United States (Metropolitan Portion)", "TimePeriod": "1970", "CL_UNIT": "Dollars", "UNIT_MULT": "0", "DataValue": "4,500"},
  {"Code": "CAINC1-3", "GeoFips": "12580", "GeoName": "Baltimore-Columbia-Towson, MD (Metropolitan Statistical Area)", "TimePeriod": "1971", "CL_UNIT": "Dollars", "UNIT_MULT": "0", "DataValue": "(D)"}
]}}}
```

- [ ] **Step 2: Write the failing tests** in `tests/test_bea.py`:

```python
import json

import pytest

from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import bea


def test_states_only_and_values_parsed(fixtures_dir):
    df = validate_long(bea.parse_bea_json(fixtures_dir / "bea/sainc1_state_pcpi.json", "state"))
    assert set(df.geo_id) == {"state:24"}  # US, regions and suppressed Alaska dropped
    assert df.set_index("year").loc[2020, "value"] == 68258.0


def test_msa_names_cleaned_and_us_portion_dropped(fixtures_dir):
    df = validate_long(bea.parse_bea_json(fixtures_dir / "bea/cainc1_msa_pcpi.json", "metro"))
    assert list(df.geo_id) == ["cbsa:12580"]  # (D) value in 1971 dropped
    assert df.geo_name.iloc[0] == "Baltimore-Columbia-Towson, MD"


def test_error_payload_raises(tmp_path):
    p = tmp_path / "err.json"
    p.write_text(json.dumps({"BEAAPI": {"Results": {"Error": {"APIErrorDescription": "Invalid UserID"}}}}))
    with pytest.raises(bea.BeaApiError, match="Invalid UserID"):
        bea.parse_bea_json(p, "state")


def test_error_payload_is_not_cached(tmp_path, monkeypatch):
    monkeypatch.setenv("BEA_API_KEY", "k")
    monkeypatch.setattr(bea, "RAW_DIR", tmp_path)

    def fake_download(url, dest, **kwargs):
        dest.write_text(json.dumps({"BEAAPI": {"Error": {"APIErrorDescription": "bad"}}}))
        return dest

    monkeypatch.setattr(bea, "download_file", fake_download)
    with pytest.raises(bea.BeaApiError):
        bea.download()
    assert not list(tmp_path.glob("*.json"))
```

- [ ] **Step 3: Run the tests and confirm they fail.** Run: `venv/bin/python -m pytest tests/test_bea.py -q`. Expected: collection error.

- [ ] **Step 4: Implement `sources/bea.py`:**

```python
"""BEA Regional API: per capita personal income for states (SAINC1, 1929+) and metros
(CAINC1 at MSA level, 1969+). BEA publishes MSAs on the current OMB delineation."""

import json
from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import BEA_API_KEY_ENV, RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file, require_env

API_URL = "https://apps.bea.gov/api/data"
RAW_DIR = RAW_DATA_DIR / "bea"
# file stem -> (table, line code, GeoFips scope, geo_level). Line 3 = per capita personal income.
REQUESTS = {
    "sainc1_state_pcpi": ("SAINC1", 3, "STATE", "state"),
    "cainc1_msa_pcpi": ("CAINC1", 3, "MSA", "metro"),
}


class BeaApiError(RuntimeError):
    """BEA returned an error payload (BEA reports errors with HTTP 200)."""


def _results(payload: dict) -> dict:
    api = payload.get("BEAAPI", {})
    results = api.get("Results", {})
    error = api.get("Error") or (results.get("Error") if isinstance(results, dict) else None)
    if error or "Data" not in results:
        raise BeaApiError(f"BEA API error: {error or 'no Data in response'}")
    return results


def download(force: bool = False) -> list[Path]:
    key = require_env(BEA_API_KEY_ENV)
    paths = []
    for stem, (table, line, scope, _) in REQUESTS.items():
        dest = RAW_DIR / f"{stem}.json"
        params = {
            "UserID": key, "method": "GetData", "datasetname": "Regional", "TableName": table,
            "LineCode": line, "GeoFips": scope, "Year": "ALL", "ResultFormat": "json",
        }
        existed = dest.exists() and not force
        download_file(API_URL, dest, force=force, params=params)
        if not existed:
            try:
                _results(json.loads(dest.read_text()))
            except BeaApiError:
                dest.unlink()  # never cache an error payload
                raise
        paths.append(dest)
    return paths


def parse_bea_json(path: Path, geo_level: str) -> pd.DataFrame:
    data = pd.DataFrame(_results(json.loads(Path(path).read_text()))["Data"])
    fips = data.GeoFips.str.zfill(5)
    if geo_level == "state":
        keep = fips.str.endswith("000") & fips.str[:2].between("01", "56")
        ids = "state:" + fips.str[:2]
    else:
        keep = ~fips.str.startswith("009")  # 00998/00999 = US metro and nonmetro portions
        ids = "cbsa:" + fips
    # "(NA)", "(D)" and similar suppression codes become NaN and are dropped
    value = pd.to_numeric(data.DataValue.str.replace(",", "", regex=False), errors="coerce")
    value = value * 10.0 ** pd.to_numeric(data.UNIT_MULT, errors="coerce").fillna(0)
    names = data.GeoName.str.replace(r"\s*\(Metropolitan Statistical Area\)", "", regex=True)
    df = pd.DataFrame(
        {
            "geo_id": ids, "geo_name": names.str.rstrip(" *"), "geo_level": geo_level,
            "country_iso3": "USA", "year": data.TimePeriod.astype("int64"), "variable": "income_pc",
            "value": value.astype("float64"), "unit": "usd_current", "source": "bea",
        }
    )
    return df[keep & value.notna()].reset_index(drop=True)


def load() -> pd.DataFrame:
    frames = [parse_bea_json(RAW_DIR / f"{stem}.json", level) for stem, (*_, level) in REQUESTS.items()]
    return validate_long(pd.concat(frames, ignore_index=True))
```

Append `"bea"` to `SOURCE_NAMES`.

- [ ] **Step 5: Run the tests and confirm they pass.** Run: `venv/bin/python -m pytest tests/test_bea.py -q`. Expected: `4 passed`.

- [ ] **Step 6: Check against the real API.** Run: `venv/bin/python -m us_housing_crisis_analysis.dataset download --source bea && venv/bin/python -m us_housing_crisis_analysis.dataset load --source bea && venv/bin/python -c "import pandas as pd; d=pd.read_parquet('data/interim/bea.parquet'); print(d.groupby('geo_level').agg(n=('geo_id','nunique'), y0=('year','min')))"`. Expected: state n=51, y0=1929; metro n≈384, y0=1969. If the response shape differs (e.g., `Results` is a list), fix `_results` and add a fixture of that shape.

- [ ] **Step 7: Update the docs.** In `sources.md`, set the BEA row to `active`, and note that "metro income uses BEA's MSA level (current delineation)", with the access date.

- [ ] **Step 8: Commit.**

```bash
git add us_housing_crisis_analysis tests Claude
git commit -m "Add BEA per capita income source for states and metros

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Hand-collected state income (Klein 1880–1910, Easterlin 1880/1900/1920)

**Files:**
- Create: `references/manual_data/state_income_historical.csv`, `references/manual_data/README.md`, `us_housing_crisis_analysis/sources/manual.py`, `tests/test_manual.py`
- Modify: `sources/__init__.py` (append `"manual"`), `Claude/research/sources.md`

**Interfaces:**
- Consumes: `schema.validate_long`, `config.MANUAL_DATA_DIR`
- Produces:
  - `manual.parse_state_income(path: Path) -> pd.DataFrame`: long format; `geo_id="state:SS"`, variables `income_pc_klein` and `income_pc_easterlin`, with the unit taken from the CSV (one per variable)
  - `manual.download(force=False) -> list[Path]` (returns the committed file; nothing to download)
  - `manual.load() -> pd.DataFrame`

- [ ] **Step 1: Write the failing tests** in `tests/test_manual.py`:

```python
import numpy as np
import pandas as pd
import pytest

from us_housing_crisis_analysis.config import MANUAL_DATA_DIR
from us_housing_crisis_analysis.schema import SchemaError, validate_long
from us_housing_crisis_analysis.sources import manual

HEADER = "state_fips,state_name,year,value,unit,source,table_ref\n"


def write(tmp_path, body):
    p = tmp_path / "s.csv"
    p.write_text(HEADER + body)
    return p


def test_parse_maps_sources_to_variables(tmp_path):
    p = write(tmp_path, "24,Maryland,1880,120,usd_current,klein_2013,Table 1\n"
                        "24,Maryland,1920,600,usd_current,easterlin_1960,Table A-1\n")
    df = validate_long(manual.parse_state_income(p))
    assert set(df.variable) == {"income_pc_klein", "income_pc_easterlin"}
    assert set(df.geo_id) == {"state:24"}


def test_unknown_source_rejected(tmp_path):
    p = write(tmp_path, "24,Maryland,1880,120,usd_current,someone_else,Table 1\n")
    with pytest.raises(ValueError, match="unknown source"):
        manual.parse_state_income(p)


def test_mixed_units_within_a_source_rejected(tmp_path):
    p = write(tmp_path, "24,Maryland,1880,120,usd_current,klein_2013,T1\n"
                        "25,Massachusetts,1880,140,index_us=100,klein_2013,T1\n")
    with pytest.raises(SchemaError, match="more than one unit"):
        validate_long(manual.parse_state_income(p))


# --- checks on the committed, transcribed file ---

def committed() -> pd.DataFrame:
    return pd.read_csv(MANUAL_DATA_DIR / "state_income_historical.csv", dtype={"state_fips": str})


def test_committed_coverage():
    df = committed()
    counts = df.groupby(["source", "year"]).state_fips.nunique()
    for year in (1880, 1890, 1900, 1910):
        assert counts[("klein_2013", year)] >= 38, year
    for year in (1880, 1900, 1920):
        assert counts[("easterlin_1960", year)] >= 38, year
    assert not df.duplicated(["source", "year", "state_fips"]).any()


def test_klein_and_easterlin_agree_where_they_overlap():
    """Two independent estimates of the same quantity: a transcription error shows up as a gap."""
    df = committed()
    for year in (1880, 1900):
        w = df[df.year == year].pivot(index="state_fips", columns="source", values="value").dropna()
        rel = np.log(w / w.mean())  # relative to the cross-state mean, so units can differ
        assert rel.corr().iloc[0, 1] > 0.9, year
        assert (rel.klein_2013 - rel.easterlin_1960).abs().median() < 0.10, year
```

- [ ] **Step 2: Run the tests and confirm they fail.** Run: `venv/bin/python -m pytest tests/test_manual.py -q`. Expected: collection error.

- [ ] **Step 3: Implement `sources/manual.py`:**

```python
"""Hand-collected inputs committed under references/manual_data/ (see its README)."""

from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import MANUAL_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long

STATE_INCOME_PATH = MANUAL_DATA_DIR / "state_income_historical.csv"
VARIABLE_BY_SOURCE = {"klein_2013": "income_pc_klein", "easterlin_1960": "income_pc_easterlin"}


def download(force: bool = False) -> list[Path]:
    return [STATE_INCOME_PATH]  # committed file; nothing to fetch


def parse_state_income(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, dtype={"state_fips": str})
    unknown = set(raw.source) - set(VARIABLE_BY_SOURCE)
    if unknown:
        raise ValueError(f"unknown source in {path.name}: {sorted(unknown)}")
    df = pd.DataFrame(
        {
            "geo_id": "state:" + raw.state_fips.str.zfill(2), "geo_name": raw.state_name,
            "geo_level": "state", "country_iso3": "USA", "year": raw.year.astype("int64"),
            "variable": raw.source.map(VARIABLE_BY_SOURCE), "value": raw.value.astype("float64"),
            "unit": raw.unit, "source": "manual",
        }
    )
    return df


def load() -> pd.DataFrame:
    return validate_long(parse_state_income(STATE_INCOME_PATH))
```

Append `"manual"` to `SOURCE_NAMES`.

- [ ] **Step 4: Run the parser tests and confirm they pass.** Run: `venv/bin/python -m pytest tests/test_manual.py -q -k "parse or unknown or mixed"`. Expected: `3 passed`. The two committed-file tests still fail until Step 5.

- [ ] **Step 5: Transcribe the tables into `references/manual_data/state_income_historical.csv`.** Use the header `state_fips,state_name,year,value,unit,source,table_ref`. This is data entry. If the PDFs can't be read programmatically, stop and ask the user to transcribe or supply the tables.
  - **Klein:** Klein, A. (2009), *Personal Income of U.S. States: Estimates for the Period 1880–1910*, Warwick Economic Research Papers No. 916 (https://wrap.warwick.ac.uk/id/eprint/3551). Transcribe per capita personal income by state for 1880, 1890, 1900 and 1910 with `source=klein_2013`. Prefer the published version (*Research in Economic History* 29, 2013) if it is accessible and its figures differ.
  - **Easterlin:** Easterlin, R. A. (1960), "Interregional Differences in Per Capita Income, Population, and Total Income, 1840–1950", NBER (https://www.nber.org/chapters/c2475.pdf). Transcribe per capita personal income by state for 1880, 1900 and 1920 with `source=easterlin_1960`. Easterlin's "1920" figure is the 1919–21 average.
  - Use the unit exactly as the table reports it: `usd_current` for dollars, or `index_us=100` for relative values. Relative values are fine for RQ0b because decade fixed effects absorb the level. Each source must use one unit throughout.
  - Put the table number and page in `table_ref` for every row.
  - Territories are included when the table lists them. Use the FIPS code of the state they became (e.g., Dakota Territory → leave out, since it splits into 38 and 46; Washington Territory → 53).
  - After transcribing, re-check every fifth row against the PDF.

- [ ] **Step 6: Write `references/manual_data/README.md`** with one section per file: source, citation, URL, table and page, date transcribed, who transcribed it, units, and the territory rule from Step 5.

- [ ] **Step 7: Run all the manual tests.** Run: `venv/bin/python -m pytest tests/test_manual.py -q`. Expected: `5 passed`. If the agreement test fails, the largest gaps are the rows to recheck against the PDFs. Print them with `rel.klein_2013 - rel.easterlin_1960` sorted. Do not loosen the threshold before rechecking.

- [ ] **Step 8: Update the docs.** In `sources.md`, set the Klein and Easterlin rows to `active`, with the transcription date and the table references.

- [ ] **Step 9: Commit.**

```bash
git add references/manual_data us_housing_crisis_analysis tests Claude
git commit -m "Add hand-collected Klein and Easterlin state income tables

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: IPUMS 1940 full-count wage income by county

**Files:**
- Create: `us_housing_crisis_analysis/sources/ipums.py`, `tests/test_ipums.py`
- Modify: `sources/__init__.py` (append `"ipums"`)

**Interfaces:**
- Consumes: `_ipums.run_extract`, `geography.fips_from_nhgis_code`, `schema.validate_long`
- Produces:
  - `ipums.INCWAGE_TOPCODE = 5001`
  - `ipums.aggregate_wages(chunks: Iterable[pd.DataFrame]) -> pd.DataFrame` with columns `COUNTYNHG, STATEFIP, wage_total, persons, missing_wage` (one row per county)
  - `ipums.to_long(agg: pd.DataFrame) -> pd.DataFrame`: long format; `geo_level="county"`, `year=1940`; variables `wage_income_total` (`usd_current`), `persons_ipums` (`persons`) and `wage_missing_share` (`share`)
  - `ipums.download(force=False) -> list[Path]`
  - `ipums.load() -> pd.DataFrame`

- [ ] **Step 1: Write the failing tests** in `tests/test_ipums.py`:

```python
import pandas as pd

from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import ipums


def chunks():
    # Baltimore city (NHGIS 2405100) appears in both chunks; one historical county has no FIPS
    yield pd.DataFrame({"STATEFIP": [24, 24, 24], "COUNTYNHG": [2405100, 2405100, 2400050],
                        "INCWAGE": [1000, 5001, 999999]})
    yield pd.DataFrame({"STATEFIP": [24, 46], "COUNTYNHG": [2405100, 4650015],
                        "INCWAGE": [999998, 200]})


def test_aggregate_combines_chunks_and_codes():
    agg = ipums.aggregate_wages(chunks()).set_index("COUNTYNHG")
    balt = agg.loc[2405100]
    assert balt.wage_total == 6001  # 1000 + topcoded 5001; 999998 (missing) adds 0
    assert balt.persons == 3
    assert balt.missing_wage == 1  # 999998 counted as missing; 999999 (N/A) is not
    assert agg.loc[2400050].wage_total == 0  # child / N/A contributes 0 but counts as a person


def test_to_long_ids_and_schema():
    df = validate_long(ipums.to_long(ipums.aggregate_wages(chunks())))
    assert {"county:24510", "county:24005", "county:nhgis-4650015"} <= set(df.geo_id)
    assert set(df.variable) == {"wage_income_total", "persons_ipums", "wage_missing_share"}
    assert set(df.year) == {1940}


def test_download_skips_when_files_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(ipums, "RAW_DIR", tmp_path)
    (tmp_path / "usa_00001.xml").write_text("x")
    (tmp_path / "usa_00001.dat.gz").write_text("x")
    monkeypatch.setattr(ipums, "run_extract", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    assert len(ipums.download()) == 2
```

- [ ] **Step 2: Run the tests and confirm they fail.** Run: `venv/bin/python -m pytest tests/test_ipums.py -q`. Expected: collection error.

- [ ] **Step 3: Implement `sources/ipums.py`:**

```python
"""IPUMS USA 1940 full-count census: wage and salary income summed by county.
INCWAGE in 1940 covers wages only (no business or farm income) and is top-coded at $5,000
(code 5001). 999998 = missing, 999999 = N/A (e.g., children)."""

from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import RAW_DATA_DIR
from us_housing_crisis_analysis.geography import fips_from_nhgis_code
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._ipums import run_extract

RAW_DIR = RAW_DATA_DIR / "ipums"
SAMPLE = "us1940b"  # 1940 100% (full count)
VARIABLES = ["STATEFIP", "COUNTYNHG", "INCWAGE"]
INCWAGE_TOPCODE = 5001
INCWAGE_MISSING = 999998
CHUNKSIZE = 2_000_000


def _files() -> list[Path]:
    return sorted(RAW_DIR.glob("usa_*.xml")) + sorted(RAW_DIR.glob("usa_*.dat.gz"))


def download(force: bool = False) -> list[Path]:
    if len(_files()) >= 2 and not force:
        return _files()
    from ipumspy import MicrodataExtract

    extract = MicrodataExtract(
        collection="usa", description="1940 full count: county wage income",
        samples=[SAMPLE], variables=VARIABLES,
    )
    run_extract(extract, RAW_DIR)
    return _files()


def aggregate_wages(chunks: Iterable[pd.DataFrame]) -> pd.DataFrame:
    parts = []
    for ch in chunks:
        inc = ch["INCWAGE"]
        valid = inc.between(0, INCWAGE_TOPCODE)
        ch = ch.assign(wage=inc.where(valid, 0), missing=(inc == INCWAGE_MISSING).astype("int64"))
        parts.append(
            ch.groupby(["COUNTYNHG", "STATEFIP"]).agg(
                wage_total=("wage", "sum"), persons=("INCWAGE", "size"), missing_wage=("missing", "sum")
            )
        )
    return pd.concat(parts).groupby(level=[0, 1]).sum().reset_index()


def to_long(agg: pd.DataFrame) -> pd.DataFrame:
    codes = agg.COUNTYNHG.astype("int64").map(lambda c: f"{c:07d}")
    fips = codes.map(fips_from_nhgis_code)
    ids = ("county:" + fips.fillna("")).where(fips.notna(), "county:nhgis-" + codes)
    base = {"geo_id": ids, "geo_name": "NHGIS county " + codes, "geo_level": "county",
            "country_iso3": "USA", "year": 1940, "source": "ipums"}
    frames = [
        pd.DataFrame({**base, "variable": "wage_income_total", "value": agg.wage_total, "unit": "usd_current"}),
        pd.DataFrame({**base, "variable": "persons_ipums", "value": agg.persons, "unit": "persons"}),
        pd.DataFrame({**base, "variable": "wage_missing_share", "value": agg.missing_wage / agg.persons, "unit": "share"}),
    ]
    out = pd.concat(frames, ignore_index=True)
    return out.astype({"year": "int64", "value": "float64"})


def load() -> pd.DataFrame:
    from ipumspy import readers

    ddi_path = next(RAW_DIR.glob("usa_*.xml"))
    ddi = readers.read_ipums_ddi(ddi_path)
    chunks = readers.read_microdata_chunked(ddi, ddi_path.with_suffix(".dat.gz"), chunksize=CHUNKSIZE)
    agg = aggregate_wages(ch[VARIABLES] for ch in chunks)
    return validate_long(to_long(agg))
```

Append `"ipums"` to `SOURCE_NAMES`.

- [ ] **Step 4: Run the tests and confirm they pass.** Run: `venv/bin/python -m pytest tests/test_ipums.py -q`. Expected: `3 passed`.

- [ ] **Step 5: Check the sample ID and variable before submitting (it's a large extract).**

```bash
venv/bin/python -c "
from us_housing_crisis_analysis.sources._ipums import client
info = client().get_all_sample_info('usa'); print('us1940b ->', info.get('us1940b'))"
```

Expected: the description reads as the 1940 100% / full-count database. If not, find the right ID in the printed dictionary and update `SAMPLE`. Then check that `COUNTYNHG` exists for that sample on the IPUMS USA variable page (https://usa.ipums.org/usa-action/variables/COUNTYNHG). If it doesn't, stop and ask the user. The alternative, `COUNTYICP`, needs a separate ICPSR → FIPS crosswalk.

- [ ] **Step 6: Download and load.** Run: `venv/bin/python -m us_housing_crisis_analysis.dataset download --source ipums && venv/bin/python -m us_housing_crisis_analysis.dataset load --source ipums`. The extract may take hours, and load reads about 130M rows in chunks. If `read_microdata_chunked` rejects the positional data-file argument, check `help(readers.read_microdata_chunked)` and pass it by the keyword the installed version uses. Expected: about 3,100 counties per variable.

- [ ] **Step 7: Check that the NHGIS codes convert.** Run: `venv/bin/python -c "import pandas as pd; d=pd.read_parquet('data/interim/ipums.parquet'); p=d[d.variable=='persons_ipums']; print(p.geo_id.str.startswith('county:nhgis-').mean(), p[p.geo_id=='county:24510'].value.tolist())"`. Expected: the share of non-FIPS IDs is below 0.01, and Baltimore city (24510) has about 859,000 persons. If Baltimore is missing, `COUNTYNHG` is not the 7-digit format assumed here. Inspect the codes, and fix `to_long` and the tests.

- [ ] **Step 8: Update the docs.** In `sources.md`, set the IPUMS 1940 row to `active`, with the sample ID, variables and access date. In `Claude/methods/analysis-methods.md` under RQ0b, add the 1940 income definition: wage income summed over everyone in the county ÷ all persons. Missing wages count as 0, and the missing share is recorded.

- [ ] **Step 9: Commit.**

```bash
git add us_housing_crisis_analysis tests Claude
git commit -m "Add IPUMS 1940 full-count county wage income source

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: ICPSR 2896 county median family income, 1950 and 1960

> **Rewritten 2026-10-11 (D-21).** NHGIS has a county income table for 1950 (`1950_cPHA`, NT39) but none for 1960; its 1960 county dataset has population tables only. The source is now ICPSR study 2896 (Haines, *Historical, Demographic, Economic, and Social Data: The United States, 1790–2002*), County Data Book parts for 1952 (1949 income) and 1962 (1959 income). ICPSR has no API, and its terms forbid redistribution, so the user downloads the files by hand into `data/raw/icpsr/` (gitignored). NHGIS NT39 is used once, as a cross-check on 1950.

**Files:**
- Create: `us_housing_crisis_analysis/sources/icpsr.py`, `tests/fixtures/icpsr/` (layout copied from the real files), `tests/test_icpsr.py`
- Modify: `sources/__init__.py` (append `"icpsr"`), `config.py` (`ICPSR_INCOME_FILES`), `Claude/research/sources.md`, `Claude/methods/analysis-methods.md`

**Interfaces:**
- Consumes: `schema.validate_long`, `config.RAW_DATA_DIR`
- Produces:
  - `config.ICPSR_INCOME_FILES: dict[int, dict[str, str]]`, keyed by census year (1950, 1960), each with `file` (name under `data/raw/icpsr/`), `state_col`, `county_col` and `income_col`
  - `icpsr.MissingManualDownloadError(RuntimeError)`
  - `icpsr.download(force=False) -> list[Path]`: downloads nothing; returns the files if present, otherwise raises `MissingManualDownloadError` with step-by-step download instructions
  - `icpsr.parse_income(path: Path, year: int, spec: dict[str, str]) -> pd.DataFrame`: long format; county rows; `geo_id="county:SSCCC"`; `variable="median_family_income"`; `unit="usd_current"`; `source="icpsr"`; state and US summary rows dropped
  - `icpsr.load() -> pd.DataFrame`
  - Task 10 reads 1950–1960 income with `county_series(icpsr, "median_family_income", [1950, 1960])` (was `nhgis`).

- [ ] **Step 1: User downloads the files** (prerequisite). On https://www.icpsr.umich.edu/web/ICPSR/studies/2896, log in with a free account, open **Data & Documentation**, and download the parts for the **County Data Book 1952** and **County Data Book 1962** (the County Data Book parts are numbered from about 70 upward; check the part titles). Choose a delimited (tab or CSV) or Stata format, plus the codebook PDF. Put everything in `data/raw/icpsr/`.

- [ ] **Step 2: Inspect the real files.** For each part, print the header and find, in the codebook: the state and county code variables (are they FIPS or ICPSR codes?), the median family income variable and its exact concept (1949 data may be "families and unrelated individuals"), its units (dollars or tens of dollars), and how summary rows (US, states) are coded. If the county codes are ICPSR state codes rather than FIPS, add an ICPSR-state → FIPS mapping (`STATEICP` codes are documented by IPUMS) to `icpsr.py` with its own test. **If a part has no county median family income, stop and ask the user.**

- [ ] **Step 3: Record what you found in `config.py`:**

```python
# ICPSR 2896 county median family income for RQ0b metro income (found in Plan 1, Task 9, Step 2)
ICPSR_INCOME_FILES: dict[int, dict[str, str]] = {
    1950: {"file": "<file name>", "state_col": "<var>", "county_col": "<var>", "income_col": "<var>"},
    1960: {"file": "<file name>", "state_col": "<var>", "county_col": "<var>", "income_col": "<var>"},
}
```

Don't commit while any angle-bracket value remains.

- [ ] **Step 4: Create the fixtures** in `tests/fixtures/icpsr/`, one per year: the real header, a US summary row, a state summary row, Baltimore city (24510), Baltimore County (24005), and one county with a blank or suppressed income, all in the real file's format.

- [ ] **Step 5: Write the failing tests** in `tests/test_icpsr.py`:

```python
import pytest

from us_housing_crisis_analysis.config import ICPSR_INCOME_FILES
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import icpsr


@pytest.mark.parametrize("year", [1950, 1960])
def test_parse_income_counties_only(fixtures_dir, year):
    spec = ICPSR_INCOME_FILES[year]
    df = validate_long(icpsr.parse_income(fixtures_dir / "icpsr" / spec["file"], year, spec))
    assert {"county:24510", "county:24005"} <= set(df.geo_id)
    assert df.geo_id.str.fullmatch(r"county:\d{5}").all()  # US and state summary rows dropped
    assert set(df.variable) == {"median_family_income"} and set(df.year) == {year}
    assert df.value.gt(0).all()  # blank or suppressed values dropped, never zero-filled


def test_missing_files_explain_the_manual_download(tmp_path, monkeypatch):
    monkeypatch.setattr(icpsr, "RAW_DIR", tmp_path)
    with pytest.raises(icpsr.MissingManualDownloadError, match="icpsr.umich.edu.*2896"):
        icpsr.download()
```

Add one assertion per fixture year pinning Baltimore city's income to the fixture value, after converting units if the file stores tens of dollars.

Run: `venv/bin/python -m pytest tests/test_icpsr.py -q`. Expected: collection error (module missing).

- [ ] **Step 6: Implement `sources/icpsr.py`**: `RAW_DIR = RAW_DATA_DIR / "icpsr"`; `download()` returns `[RAW_DIR / spec["file"] for spec in ICPSR_INCOME_FILES.values()]` when all exist, else raises `MissingManualDownloadError` naming the study URL, the two parts and the target directory; `parse_income()` reads the file (by extension: `.dta` with `pd.read_stata`, delimited with `pd.read_csv(dtype=str)`), builds 5-digit FIPS from the state and county columns, drops summary rows (county code 0 or blank) and non-positive or missing income, converts units to dollars, and returns the long format; `load()` concatenates both years and validates. Append `"icpsr"` to `SOURCE_NAMES`.

- [ ] **Step 7: Run the tests and confirm they pass.** Run: `venv/bin/python -m pytest tests/test_icpsr.py -q`. Expected: all pass.

- [ ] **Step 8: Load and check.** Run: `venv/bin/python -m us_housing_crisis_analysis.dataset load --source icpsr`, then count counties per year. Expected: about 3,000 each, and the US median family income in the summary row matches the census figure (1949: about $3,083 for families; 1959: $5,660).

- [ ] **Step 9: Cross-check 1950 against NHGIS NT39 (one time).** Request a small NHGIS extract of dataset `1950_cPHA`, table `NT39`, county level, into the scratchpad (not `data/raw`). Merge on FIPS and report the correlation of log income and the median absolute difference. Expected: correlation > 0.95. Record the result in `analysis-methods.md`. A low correlation means the two concepts differ (families vs. families and unrelated individuals) or a column is wrong; investigate before continuing.

- [ ] **Step 10: Update the docs.** `sources.md`: add an ICPSR 2896 row (parts used, access terms, access date) and remove "median family income" from the NHGIS row. `analysis-methods.md` RQ0b: the exact 1950 and 1960 income concepts and variable names, and the cross-check result.

- [ ] **Step 11: Commit.**

```bash
git add us_housing_crisis_analysis tests Claude
git commit -m "Add ICPSR 2896 county median family income for 1950 and 1960

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Build the `us_state_longrun` and `us_metro_longrun` panels and the data checks

**Files:**
- Modify: `us_housing_crisis_analysis/features.py` (replace the template)
- Create: `tests/test_features.py`, `tests/data/__init__.py`, `tests/data/test_us_longrun.py`, `references/known_values.csv`, `references/crosswalks/growth_allowlist.csv`

**Interfaces:**
- Consumes: interim long frames from `nhgis`, `bea`, `manual`, `ipums`, `census_pep`; `geography.county_to_cbsa`, `geography.harmonize_county_fips`
- Produces:
  - `features.build_us_state_longrun(nhgis: pd.DataFrame, bea: pd.DataFrame, manual: pd.DataFrame) -> pd.DataFrame` with columns `geo_id, geo_name, year, population, income_pc, income_source`, for decade years 1880–2020
  - `features.county_series(nhgis_or_ipums: pd.DataFrame, variable: str, years) -> pd.DataFrame` with columns `county_fips, year, value` (harmonized and summed)
  - `features.build_us_metro_longrun(nhgis: pd.DataFrame, ipums: pd.DataFrame, icpsr: pd.DataFrame, bea: pd.DataFrame, crosswalk: pd.DataFrame) -> pd.DataFrame` with columns `geo_id, geo_name, year, population, income_pc, income_source`, for decade years 1900–2020
  - `features.unmatched_county_report(nhgis: pd.DataFrame) -> pd.DataFrame` with columns `year, county_id, population, share_of_us`
  - CLI: `python -m us_housing_crisis_analysis.features` writes `data/processed/us_state_longrun.parquet` and `us_metro_longrun.parquet`
  - `income_source` values:
    - `klein`, `easterlin` and `bea` (states);
    - `ipums_1940_wages`, `census_median_family_income` and `bea` (metros).

- [ ] **Step 1: Write the failing unit tests** in `tests/test_features.py`:

```python
import numpy as np
import pandas as pd

from us_housing_crisis_analysis import features


def long(rows, source):
    df = pd.DataFrame(rows, columns=["geo_id", "geo_level", "year", "variable", "value"])
    return df.assign(geo_name=df.geo_id, country_iso3="USA", unit="x", source=source,
                     year=df.year.astype("int64"), value=df.value.astype("float64"))


def test_state_panel_chains_income_sources_and_keeps_gaps_as_nan():
    nhgis = long([("state:24", "state", y, "population", 1e6) for y in (1880, 1920, 1930)]
                 + [("state:nhgis-G465", "state", 1880, "population", 1e5)], "nhgis")
    manual = long([("state:24", "state", 1880, "income_pc_klein", 100),
                   ("state:24", "state", 1880, "income_pc_easterlin", 999),  # cross-check only
                   ("state:24", "state", 1920, "income_pc_easterlin", 500)], "manual")
    bea = long([("state:24", "state", 1930, "income_pc", 700),
                ("state:24", "state", 1931, "income_pc", 650)], "bea")
    p = features.build_us_state_longrun(nhgis, bea, manual).set_index(["geo_id", "year"])
    assert p.loc[("state:24", 1880), "income_pc"] == 100  # Klein, not Easterlin, for 1880
    assert p.loc[("state:24", 1920), "income_source"] == "easterlin"
    assert p.loc[("state:24", 1930), "income_source"] == "bea"
    assert np.isnan(p.loc[("state:nhgis-G465", 1880), "income_pc"])  # territory: NaN, not 0
    assert 1931 not in p.index.get_level_values("year")


def test_metro_panel_sums_counties_and_weights_medians():
    crosswalk = pd.DataFrame({"county_fips": ["24510", "24005"], "cbsa_code": ["12580"] * 2,
                              "cbsa_title": ["Baltimore"] * 2, "area_type": ["metro"] * 2})
    nhgis = long([("county:24510", "county", 1940, "population", 800),
                  ("county:24005", "county", 1940, "population", 200),
                  ("county:24510", "county", 1950, "population", 900),
                  ("county:24005", "county", 1950, "population", 100)], "nhgis")
    icpsr = long([("county:24510", "county", 1950, "median_family_income", 3000),
                  ("county:24005", "county", 1950, "median_family_income", 4000)], "icpsr")
    ipums = long([("county:24510", "county", 1940, "wage_income_total", 400_000),
                  ("county:24510", "county", 1940, "persons_ipums", 800),
                  ("county:24005", "county", 1940, "wage_income_total", 100_000),
                  ("county:24005", "county", 1940, "persons_ipums", 200)], "ipums")
    nhgis = pd.concat([nhgis, long([("county:24510", "county", 1970, "population", 900),
                                    ("county:24005", "county", 1970, "population", 100)], "nhgis")])
    bea = long([("county:24510", "county", 1970, "personal_income", 3_000_000),
                ("county:24510", "county", 1970, "population_bea", 900),
                ("county:24005", "county", 1970, "personal_income", 1_000_000),
                ("county:24005", "county", 1970, "population_bea", 100)], "bea")
    p = features.build_us_metro_longrun(nhgis, ipums, icpsr, bea, crosswalk).set_index(["geo_id", "year"])
    assert p.loc[("cbsa:12580", 1940), "population"] == 1000
    assert p.loc[("cbsa:12580", 1940), "income_pc"] == 500  # 500,000 wages / 1,000 persons
    assert p.loc[("cbsa:12580", 1950), "income_pc"] == 3100  # 0.9*3000 + 0.1*4000
    assert p.loc[("cbsa:12580", 1950), "income_source"] == "census_median_family_income"
    assert p.loc[("cbsa:12580", 1970), "income_pc"] == 4000  # 4,000,000 / 1,000 (BEA counties summed)


def test_unmatched_report_flags_counties_missing_from_2020():
    nhgis = long([("county:24510", "county", 2020, "population", 10),
                  ("county:24510", "county", 1900, "population", 90),
                  ("county:nhgis-G4650015", "county", 1900, "population", 10)], "nhgis")
    r = features.unmatched_county_report(nhgis)
    assert list(r.county_id) == ["nhgis-G4650015"]
    assert r.share_of_us.iloc[0] == 0.1
```

- [ ] **Step 2: Run the tests and confirm they fail.** Run: `venv/bin/python -m pytest tests/test_features.py -q`. Expected: `AttributeError` on `build_us_state_longrun`.

- [ ] **Step 3: Implement `features.py`:**

```python
"""Build processed analysis panels from data/interim (spec §4, processed panels)."""

import pandas as pd
from loguru import logger
import typer

from us_housing_crisis_analysis.config import (
    INTERIM_DATA_DIR, METRO_LONGRUN_START, PROCESSED_DATA_DIR, RQ0B_END, RQ0B_STATE_START,
)
from us_housing_crisis_analysis.geography import county_to_cbsa, harmonize_county_fips

app = typer.Typer()
PANEL_COLUMNS = ["geo_id", "geo_name", "year", "population", "income_pc", "income_source"]


def _decades(start: int, end: int = RQ0B_END) -> list[int]:
    return list(range(start, end + 1, 10))


def _pick(df: pd.DataFrame, variable: str, years, level: str | None = None) -> pd.DataFrame:
    m = (df.variable == variable) & df.year.isin(list(years))
    if level:
        m &= df.geo_level == level
    return df[m]


def _assemble(pop: pd.DataFrame, income: pd.DataFrame) -> pd.DataFrame:
    """Left join income onto population, so missing income stays NaN (never 0)."""
    out = pop.merge(income, on=["geo_id", "year"], how="left")
    return out[PANEL_COLUMNS].sort_values(["geo_id", "year"]).reset_index(drop=True)


def build_us_state_longrun(nhgis: pd.DataFrame, bea: pd.DataFrame, manual: pd.DataFrame) -> pd.DataFrame:
    years = _decades(RQ0B_STATE_START)
    pop = _pick(nhgis, "population", years, "state")[["geo_id", "geo_name", "year", "value"]]
    pop = pop.rename(columns={"value": "population"})
    income = pd.concat(
        [
            _pick(manual, "income_pc_klein", range(1880, 1911, 10)).assign(income_source="klein"),
            _pick(manual, "income_pc_easterlin", [1920]).assign(income_source="easterlin"),
            _pick(bea, "income_pc", [y for y in years if y >= 1930], "state").assign(income_source="bea"),
        ]
    )[["geo_id", "year", "value", "income_source"]].rename(columns={"value": "income_pc"})
    return _assemble(pop, income)


def county_series(df: pd.DataFrame, variable: str, years) -> pd.DataFrame:
    """County values with historical codes mapped to successors and summed."""
    c = _pick(df, variable, years, "county")
    c = c[~c.geo_id.str.startswith("county:nhgis-")]
    c = pd.DataFrame({"county_fips": c.geo_id.str.removeprefix("county:"), "year": c.year, "value": c.value})
    return harmonize_county_fips(c).groupby(["county_fips", "year"], as_index=False)["value"].sum()


def build_us_metro_longrun(
    nhgis: pd.DataFrame, ipums: pd.DataFrame, icpsr: pd.DataFrame, bea: pd.DataFrame,
    crosswalk: pd.DataFrame,
) -> pd.DataFrame:
    years = _decades(METRO_LONGRUN_START)
    cw = crosswalk[["county_fips", "cbsa_code", "cbsa_title"]]

    def to_cbsa(series: pd.DataFrame) -> pd.DataFrame:
        return series.merge(cw, on="county_fips", how="inner")

    pop_c = to_cbsa(county_series(nhgis, "population", years))
    pop = pop_c.groupby(["cbsa_code", "cbsa_title", "year"], as_index=False)["value"].sum()
    pop = pd.DataFrame({"geo_id": "cbsa:" + pop.cbsa_code, "geo_name": pop.cbsa_title,
                        "year": pop.year, "population": pop.value})

    # 1940: total wages / total persons across the metro's counties
    wages = to_cbsa(county_series(ipums, "wage_income_total", [1940])).groupby("cbsa_code")["value"].sum()
    persons = to_cbsa(county_series(ipums, "persons_ipums", [1940])).groupby("cbsa_code")["value"].sum()
    inc1940 = (wages / persons).rename("income_pc").reset_index().assign(year=1940, income_source="ipums_1940_wages")

    # 1950-1960: county medians cannot be summed; use the population-weighted mean (approximation)
    med = to_cbsa(county_series(icpsr, "median_family_income", [1950, 1960]))
    med = med.merge(pop_c[["county_fips", "year", "value"]].rename(columns={"value": "w"}), on=["county_fips", "year"])
    med = (med.assign(vw=med.value * med.w).groupby(["cbsa_code", "year"])[["vw", "w"]].sum())
    inc5060 = (med.vw / med.w).rename("income_pc").reset_index().assign(income_source="census_median_family_income")

    # 1970+: BEA county personal income / BEA county population, summed over the metro's counties
    # (BEA's own MSA level fails in the API, D-23; this also keeps every year on the same counties)
    bea_years = [y for y in years if y >= 1970]
    pi = to_cbsa(county_series(bea, "personal_income", bea_years)).groupby(["cbsa_code", "year"])["value"].sum()
    bpop = to_cbsa(county_series(bea, "population_bea", bea_years)).groupby(["cbsa_code", "year"])["value"].sum()
    inc_bea = (pi / bpop).rename("income_pc").reset_index().assign(income_source="bea")

    income = pd.concat([inc1940, inc5060, inc_bea], ignore_index=True)
    income = income.assign(geo_id="cbsa:" + income.cbsa_code)[["geo_id", "year", "income_pc", "income_source"]]
    return _assemble(pop, income)


def unmatched_county_report(nhgis: pd.DataFrame) -> pd.DataFrame:
    """County rows whose (harmonized) code is not a 2020 county: the population that a
    county-based metro build cannot place. Review the largest and extend county_fixes.csv."""
    c = nhgis[(nhgis.geo_level == "county") & (nhgis.variable == "population")]
    c = pd.DataFrame({"county_fips": c.geo_id.str.removeprefix("county:"), "year": c.year, "population": c.value})
    c = harmonize_county_fips(c)
    modern = set(c.loc[c.year == 2020, "county_fips"])
    totals = c.groupby("year").population.sum()
    bad = c[~c.county_fips.isin(modern)]
    return pd.DataFrame(
        {"year": bad.year, "county_id": bad.county_fips, "population": bad.population,
         "share_of_us": bad.population / bad.year.map(totals)}
    ).sort_values(["year", "population"], ascending=[True, False]).reset_index(drop=True)


@app.command()
def main():
    read = lambda s: pd.read_parquet(INTERIM_DATA_DIR / f"{s}.parquet")  # noqa: E731
    nhgis, bea, manual, ipums, icpsr = (read(s) for s in ("nhgis", "bea", "manual", "ipums", "icpsr"))
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    panels = {
        "us_state_longrun": build_us_state_longrun(nhgis, bea, manual),
        "us_metro_longrun": build_us_metro_longrun(nhgis, ipums, icpsr, bea, county_to_cbsa()),
    }
    for name, df in panels.items():
        if df.duplicated(["geo_id", "year"]).any():
            raise ValueError(f"{name}: duplicate (geo_id, year) rows")
        df.to_parquet(PROCESSED_DATA_DIR / f"{name}.parquet", index=False)
        logger.success(f"{name}: {len(df):,} rows, {df.geo_id.nunique()} units")


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Run the unit tests and confirm they pass.** Run: `venv/bin/python -m pytest tests/test_features.py -q`. Expected: `3 passed`.

- [ ] **Step 5: Create `references/known_values.csv`.** Look up the San Francisco value on data.census.gov (2020 Decennial, P1, "San Francisco-Oakland-Fremont, CA Metro Area") before committing. Correct it if it differs, and record the URL in `note`.

```csv
dataset,geo_id,year,variable,value,rel_tol,note
us_metro_longrun,cbsa:41860,2020,population,4749008,0.001,2020 Census count; verify at data.census.gov
```

Create `references/crosswalks/growth_allowlist.csv` with the header `geo_id,year,reason`, where `year` is the decade start.

- [ ] **Step 6: Write the data tests** in `tests/data/test_us_longrun.py` (and an empty `tests/data/__init__.py`):

```python
import numpy as np
import pandas as pd
import pytest

from us_housing_crisis_analysis.config import CROSSWALKS_DIR, RAW_DATA_DIR, REFERENCES_DIR
from us_housing_crisis_analysis import features, geography
from us_housing_crisis_analysis.sources import census_pep

pytestmark = pytest.mark.data


def state_pop(interim, year):
    d = interim("nhgis")
    return d[(d.geo_level == "state") & (d.variable == "population") & (d.year == year)]


def test_us_population_2020(interim):
    s = state_pop(interim, 2020)
    assert s[s.geo_id != "state:72"].value.sum() == 331_449_281


def test_us_population_1880(interim):
    assert state_pop(interim, 1880).value.sum() == pytest.approx(50_189_209, rel=1e-3)


@pytest.mark.parametrize("row", pd.read_csv(REFERENCES_DIR / "known_values.csv").to_dict("records"))
def test_known_values(processed, row):
    p = processed(row["dataset"]).set_index(["geo_id", "year"])
    assert p.loc[(row["geo_id"], row["year"]), row["variable"]] == pytest.approx(row["value"], rel=row["rel_tol"])


def ct_cbsas() -> set[str]:
    cw = geography.county_to_cbsa()
    return set("cbsa:" + cw[cw.county_fips.str.startswith("09")].cbsa_code)


def test_cbsa_2020_population_matches_census_base(interim, processed):
    ours = processed("us_metro_longrun").query("year == 2020").set_index("geo_id").population
    base = interim("census_pep").set_index("geo_id").value
    rel = ((ours - base) / base).drop(ct_cbsas(), errors="ignore").dropna()
    assert len(rel) > 350
    assert rel.abs().max() < 0.01, rel.abs().sort_values().tail()
    assert rel.abs().median() < 0.001


def test_county_membership_matches_census():
    path = RAW_DATA_DIR / "census_pep" / "cbsa-est2023-alldata.csv"
    if not path.exists():
        pytest.skip("census_pep not downloaded")
    theirs = census_pep.parse_county_membership(path)
    ours = geography.county_to_cbsa()
    ours = ours[~ours.county_fips.str.startswith("09")]
    theirs = theirs[~theirs.county_fips.str.startswith("09")]
    merged = ours.merge(theirs, on="county_fips", how="outer", suffixes=("_ours", "_census"), indicator=True)
    assert (merged._merge == "both").all(), merged[merged._merge != "both"]
    assert (merged.cbsa_code_ours == merged.cbsa_code_census).all()


def test_unmatched_county_population_is_small(interim):
    r = features.unmatched_county_report(interim("nhgis"))
    by_year = r[r.year >= 1900].groupby("year").share_of_us.sum()
    assert (by_year <= 0.005).all(), r.groupby("year").head(5)


def test_metro_growth_is_plausible(processed):
    p = processed("us_metro_longrun").sort_values(["geo_id", "year"])
    assert (p.population > 0).all()
    ratio = p.groupby("geo_id").population.shift(-1) / p.population
    flagged = p.assign(ratio=ratio)[(ratio < 0.5) | (ratio > 3.0)]
    allow = pd.read_csv(CROSSWALKS_DIR / "growth_allowlist.csv", dtype={"year": "int64"})
    flagged = flagged.merge(allow, on=["geo_id", "year"], how="left", indicator=True)
    assert (flagged._merge == "both").all(), flagged[flagged._merge != "both"][["geo_id", "geo_name", "year", "ratio"]]


def test_income_series_has_no_gap_decades(processed):
    s = processed("us_state_longrun")
    assert (s[s.year >= 1880].groupby("year").income_pc.count() >= 38).all()
    m = processed("us_metro_longrun")
    m = m[m.year >= 1940]
    assert (m.groupby("year").income_pc.count() / m.groupby("year").geo_id.count() >= 0.9).all()


def test_ipums_1940_wages_track_bea_1940_income(interim):
    ip = interim("ipums")
    ip = ip[~ip.geo_id.str.startswith("county:nhgis-")]
    ip = ip.assign(state=ip.geo_id.str[7:9]).pivot_table(index="state", columns="variable", values="value", aggfunc="sum")
    wages_pc = ip.wage_income_total / ip.persons_ipums
    b = interim("bea")
    b = b[(b.geo_level == "state") & (b.year == 1940)]
    b = b.set_index(b.geo_id.str[6:8]).value
    both = pd.concat([np.log(wages_pc), np.log(b)], axis=1, join="inner").dropna()
    assert len(both) >= 45
    assert both.corr().iloc[0, 1] > 0.85
```

- [ ] **Step 7: Build the panels and run the data tests.**

Run: `venv/bin/python -m us_housing_crisis_analysis.features && venv/bin/python -m pytest tests/data -q`

Expected: all pass. Investigate failures instead of loosening thresholds:
- **Unmatched counties:** print `features.unmatched_county_report(...)`. For each large county with a clear successor, add a row to `county_fixes.csv` with a note. Counties split between successors stay unmatched and are documented in `geography.md`.
- **Growth flags:** check each one. Add genuine booms (e.g., Las Vegas, 1940s) to `growth_allowlist.csv` with a reason. Fix join errors at their source.
- **CBSA mismatch:** a large gap means missing counties. Compare the county lists for that CBSA.

- [ ] **Step 8: Update the docs.**
  - `Claude/methods/pipeline.md`: add `us_state_longrun` to the panels table.
  - `Claude/methods/geography.md`: list every added county fix and the final unmatched share by decade.
  - `analysis-methods.md`: record the 1950–60 population-weighted median approximation.

- [ ] **Step 9: Commit.**

```bash
git add us_housing_crisis_analysis tests references Claude
git commit -m "Build state and metro long-run panels with data validation tests

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Break estimation (`modeling/breaks.py`) with synthetic recovery tests

**Files:**
- Create: `us_housing_crisis_analysis/modeling/breaks.py`, `tests/test_breaks.py`
- Modify: `Claude/methods/analysis-methods.md`

**Interfaces:**
- Consumes: a panel with columns `geo_id, year, population, income_pc, income_source` (Task 10)
- Produces:
  - `breaks.prepare_decade_panel(panel: pd.DataFrame, start: int, end: int = 2020) -> pd.DataFrame` with columns `geo_id, decade, growth, log_income, income_source`
  - `breaks.decade_betas(dp: pd.DataFrame) -> pd.DataFrame` with columns `decade, beta, se, n`
  - `breaks.TestResult(statistic: float, p_value: float)` (frozen dataclass)
  - `breaks.chow_test(dp: pd.DataFrame, break_decade: int) -> TestResult`
  - `breaks.BreakSearch(breaks: tuple[int, ...], bic: dict[tuple[int, ...], float])`
  - `breaks.break_search(dp: pd.DataFrame, max_breaks: int = 3, min_segment: int = 2) -> BreakSearch`
  - `breaks.standardize_within_decade(dp: pd.DataFrame) -> pd.DataFrame`
  - `breaks.source_change_decades(dp: pd.DataFrame) -> list[int]`

- [ ] **Step 1: Write the failing tests** in `tests/test_breaks.py`:

```python
import numpy as np
import pandas as pd

from us_housing_crisis_analysis.modeling import breaks

DECADES = list(range(1880, 2020, 10))


def simulate(beta_for, n_units=200, noise=0.05, seed=0, shift_from=None, shift=1.0):
    """Decade panel where growth = 0.1 + beta(d) * true log income + noise. If shift_from is
    set, *measured* log income jumps by `shift` for every unit from that decade on, the way a
    change of income source would."""
    rng = np.random.default_rng(seed)
    rows = []
    for d in DECADES:
        x = rng.normal(0, 0.4, n_units)
        y = 0.1 + beta_for(d) * x + rng.normal(0, noise, n_units)
        measured = x + (shift if shift_from is not None and d >= shift_from else 0.0)
        rows.append(pd.DataFrame({"geo_id": [f"u{i}" for i in range(n_units)], "decade": d,
                                  "growth": y, "log_income": measured, "income_source": "s"}))
    return pd.concat(rows, ignore_index=True)


def test_prepare_decade_panel_drops_gaps_instead_of_filling():
    panel = pd.DataFrame({
        "geo_id": ["a"] * 3 + ["b"] * 3,
        "year": [1940, 1950, 1960] * 2,
        "population": [100.0, 200.0, 400.0, 100.0, np.nan, 100.0],
        "income_pc": [10.0, np.nan, 10.0, 10.0, 10.0, 10.0],
        "income_source": ["s"] * 6,
    })
    dp = breaks.prepare_decade_panel(panel, start=1940).set_index(["geo_id", "decade"])
    assert dp.loc[("a", 1940), "growth"] == np.log(2)
    assert ("a", 1950) not in dp.index  # income missing at the decade start
    assert ("b", 1940) not in dp.index and ("b", 1950) not in dp.index  # population gap


def test_decade_betas_recover_true_slope():
    b = breaks.decade_betas(simulate(lambda d: 0.3))
    assert np.allclose(b.beta, 0.3, atol=0.03)
    assert list(b.decade) == DECADES


def test_break_search_finds_planted_1980_break():
    dp = simulate(lambda d: 0.3 if d < 1980 else 0.0)
    assert breaks.break_search(dp).breaks == (1980,)


def test_break_search_finds_no_break_when_none_planted():
    assert breaks.break_search(simulate(lambda d: 0.3)).breaks == ()


def test_chow_detects_planted_1950_break():
    dp = simulate(lambda d: 0.3 if d < 1950 else 0.1)
    assert breaks.chow_test(dp, 1950).p_value < 0.01


def test_chow_does_not_reject_without_break():
    assert breaks.chow_test(simulate(lambda d: 0.3), 1950).p_value > 0.01


def test_source_level_shift_is_not_a_break():
    dp = simulate(lambda d: 0.3, shift_from=1930)
    assert breaks.break_search(dp).breaks == ()
    assert breaks.chow_test(dp, 1930).p_value > 0.01


def test_standardize_within_decade():
    z = breaks.standardize_within_decade(simulate(lambda d: 0.3))
    stats = z.groupby("decade").log_income.agg(["mean", "std"])
    assert np.allclose(stats["mean"], 0, atol=1e-9) and np.allclose(stats["std"], 1)


def test_source_change_decades():
    dp = pd.DataFrame({"decade": [1900, 1910, 1920, 1930, 1930],
                       "income_source": ["klein", "klein", "easterlin", "bea", "bea"]})
    assert breaks.source_change_decades(dp) == [1920, 1930]
```

- [ ] **Step 2: Run the tests and confirm they fail.** Run: `venv/bin/python -m pytest tests/test_breaks.py -q`. Expected: collection error.

- [ ] **Step 3: Implement `modeling/breaks.py`:**

```python
"""RQ0b: decade-by-decade income coefficients and structural break tests (spec §5).

Model, for unit i (state or metro) and decade d:
    growth_{i,d} = alpha_d + beta_d * log_income_{i,d} + e_{i,d}
where growth = ln pop(d+10) - ln pop(d). Break tests pool all decades, keep decade fixed
effects, and let the income slope differ between segments."""

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd
import statsmodels.api as sm


@dataclass(frozen=True)
class TestResult:
    statistic: float
    p_value: float


@dataclass(frozen=True)
class BreakSearch:
    breaks: tuple[int, ...]
    bic: dict[tuple[int, ...], float]


def prepare_decade_panel(panel: pd.DataFrame, start: int, end: int = 2020) -> pd.DataFrame:
    """One row per unit-decade with population at both ends and income at the start. Units
    missing either drop out of that decade only (spec: no interpolation)."""
    p = panel[["geo_id", "year", "population", "income_pc", "income_source"]]
    nxt = p[["geo_id", "year", "population"]].assign(year=p.year - 10)
    m = p.merge(nxt.rename(columns={"population": "population_next"}), on=["geo_id", "year"])
    m = m[(m.year >= start) & (m.year + 10 <= end)]
    m = m[(m.population > 0) & (m.population_next > 0) & (m.income_pc > 0)]
    return pd.DataFrame(
        {
            "geo_id": m.geo_id, "decade": m.year.astype("int64"),
            "growth": np.log(m.population_next / m.population), "log_income": np.log(m.income_pc),
            "income_source": m.income_source,
        }
    ).sort_values(["decade", "geo_id"]).reset_index(drop=True)


def decade_betas(dp: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for d, g in dp.groupby("decade"):
        fit = sm.OLS(g.growth, sm.add_constant(g.log_income)).fit(cov_type="HC1")
        rows.append({"decade": int(d), "beta": fit.params["log_income"],
                     "se": fit.bse["log_income"], "n": len(g)})
    return pd.DataFrame(rows)


def _design(dp: pd.DataFrame, break_decades) -> pd.DataFrame:
    """Decade fixed effects plus one income slope per segment. Segment k starts at the k-th break."""
    fe = pd.get_dummies(dp.decade, prefix="d", dtype=float)
    segment = np.searchsorted(sorted(break_decades), dp.decade.to_numpy(), side="right")
    slopes = {f"slope_{k}": dp.log_income.to_numpy() * (segment == k) for k in range(len(break_decades) + 1)}
    return pd.concat([fe, pd.DataFrame(slopes, index=dp.index)], axis=1)


def chow_test(dp: pd.DataFrame, break_decade: int) -> TestResult:
    """Wald test that the income slope is equal before and after break_decade, with standard
    errors clustered by unit (a Chow test robust to heteroskedasticity and serial correlation)."""
    fit = sm.OLS(dp.growth, _design(dp, [break_decade])).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(dp.geo_id)[0]}
    )
    w = fit.wald_test("slope_0 = slope_1", scalar=True)
    return TestResult(float(w.statistic), float(w.pvalue))


def break_search(dp: pd.DataFrame, max_breaks: int = 3, min_segment: int = 2) -> BreakSearch:
    """Bai-Perron-style global search: every set of up to max_breaks decade boundaries with at
    least min_segment decades per segment; choose the set with the lowest BIC."""
    decades = sorted(dp.decade.unique())
    candidates = decades[min_segment : len(decades) - min_segment + 1]
    n = len(dp)
    bic: dict[tuple[int, ...], float] = {}
    for k in range(max_breaks + 1):
        for combo in combinations(candidates, k):
            edges = [decades[0], *combo, decades[-1] + 10]
            sizes = [sum(lo <= d < hi for d in decades) for lo, hi in zip(edges[:-1], edges[1:])]
            if min(sizes) < min_segment:
                continue
            X = _design(dp, combo)
            ssr = sm.OLS(dp.growth, X).fit().ssr
            bic[tuple(int(c) for c in combo)] = n * np.log(ssr / n) + X.shape[1] * np.log(n)
    return BreakSearch(breaks=min(bic, key=bic.get), bic=bic)


def standardize_within_decade(dp: pd.DataFrame) -> pd.DataFrame:
    """Robustness: z-score log income within each decade, so sources with different spreads
    (e.g., 1940 wages vs. later total income) are comparable."""
    g = dp.groupby("decade").log_income
    return dp.assign(log_income=(dp.log_income - g.transform("mean")) / g.transform("std"))


def source_change_decades(dp: pd.DataFrame) -> list[int]:
    """Decades whose income source differs from the previous decade's."""
    src = dp.groupby("decade").income_source.first().sort_index()
    return [int(d) for d, changed in (src != src.shift()).iloc[1:].items() if changed]
```

- [ ] **Step 4: Run the tests and confirm they pass.** Run: `venv/bin/python -m pytest tests/test_breaks.py -q`. Expected: `9 passed`. If `wald_test` rejects the string constraint in the installed statsmodels, build the restriction matrix instead: `R = np.zeros(X.shape[1]); R[cols.index("slope_0")] = 1; R[cols.index("slope_1")] = -1` and pass `R`.

- [ ] **Step 5: Update the docs.** In `analysis-methods.md` RQ0b, describe the pooled design (decade fixed effects plus segment slopes), the clustered Wald/Chow test, and the BIC global search (max 3 breaks, at least 2 decades per segment). Also add the two robustness checks: within-decade standardization, and dropping `source_change_decades`. Replace the old "source indicator" line with the collinearity explanation (decision D-20).

- [ ] **Step 6: Commit.**

```bash
git add us_housing_crisis_analysis/modeling tests Claude
git commit -m "Add RQ0b break estimation with synthetic recovery tests

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: Figure style and the RQ0b notebook

**Files:**
- Modify: `us_housing_crisis_analysis/plots.py` (replace the template)
- Create: `notebooks/1.1-lr-us-structural-break.ipynb` (generated from a percent-format script), `tests/test_plots.py`

**Interfaces:**
- Consumes: `breaks.*` (Task 11), processed panels (Task 10), `config.FIGURES_DIR`, `config.TABLES_DIR`
- Produces:
  - `plots.apply_style() -> None`
  - `plots.save_figure(fig, name: str) -> Path` (writes `reports/figures/<name>.png` at 200 dpi)
  - `reports/figures/rq0b_betas.png`
  - `reports/tables/rq0b_tests.csv` with columns `version, spec, test, statistic, p_value, breaks`

- [ ] **Step 1: Write the failing test** in `tests/test_plots.py`:

```python
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from us_housing_crisis_analysis import plots


def test_save_figure_writes_png(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "FIGURES_DIR", tmp_path)
    plots.apply_style()
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    path = plots.save_figure(fig, "smoke")
    assert path == tmp_path / "smoke.png" and path.stat().st_size > 0
```

Run: `venv/bin/python -m pytest tests/test_plots.py -q`. Expected: FAIL (`apply_style` missing).

- [ ] **Step 2: Replace `plots.py`:**

```python
"""Shared matplotlib style for paper figures."""

from pathlib import Path

import matplotlib.pyplot as plt

from us_housing_crisis_analysis.config import FIGURES_DIR


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.figsize": (8, 4.5), "figure.dpi": 100, "axes.spines.top": False,
            "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3, "font.size": 11,
        }
    )


def save_figure(fig, name: str) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    return path
```

Run: `venv/bin/python -m pytest tests/test_plots.py -q`. Expected: `1 passed`.

- [ ] **Step 3: Write the notebook source** to the scratch file `notebooks/1.1-lr-us-structural-break.py`. It is only used to generate the `.ipynb`; delete it in Step 4.

```python
# %% [markdown]
# # 1.1 — RQ0b: Is there a structural break in how US population growth responds to income?
#
# For each decade d: Δln(pop)_{i,d} = α_d + β_d · ln(income per capita)_{i,d}.
# States 1880–2020 (Klein, Easterlin, BEA); metros 1940–2020 (IPUMS 1940 wages, Census medians, BEA).
# Break tests pool all decades with decade fixed effects (see Claude/methods/analysis-methods.md).
# Findings are descriptive and associational.

# %%
import matplotlib.pyplot as plt
import pandas as pd

from us_housing_crisis_analysis.config import PROCESSED_DATA_DIR, RQ0B_METRO_START, RQ0B_STATE_START, TABLES_DIR
from us_housing_crisis_analysis.modeling import breaks
from us_housing_crisis_analysis.plots import apply_style, save_figure

apply_style()
panels = {
    "states": breaks.prepare_decade_panel(pd.read_parquet(PROCESSED_DATA_DIR / "us_state_longrun.parquet"), RQ0B_STATE_START),
    "metros": breaks.prepare_decade_panel(pd.read_parquet(PROCESSED_DATA_DIR / "us_metro_longrun.parquet"), RQ0B_METRO_START),
}
{k: (v.decade.min(), v.decade.max(), v.geo_id.nunique(), len(v)) for k, v in panels.items()}

# %% [markdown]
# ## β_d by decade

# %%
betas = {k: breaks.decade_betas(v) for k, v in panels.items()}
fig, ax = plt.subplots()
for (name, b), offset in zip(betas.items(), (-1, 1)):
    ax.errorbar(b.decade + offset, b.beta, yerr=1.96 * b.se, marker="o", capsize=3, label=name)
ax.axhline(0, color="black", lw=0.8)
for d in (1950, 1980):
    ax.axvline(d, color="grey", ls="--", lw=0.8)
ax.set(xlabel="Decade start", ylabel="β (growth on log income)", title="Population growth toward richer places, by decade")
ax.legend()
save_figure(fig, "rq0b_betas")
pd.concat(betas, names=["version"]).round(4)

# %% [markdown]
# ## Break tests: main specification and robustness

# %%
rows = []
for name, dp in panels.items():
    specs = {
        "main": dp,
        "standardized income": breaks.standardize_within_decade(dp),
        "drop source-change decades": dp[~dp.decade.isin(breaks.source_change_decades(dp))],
    }
    for spec, d in specs.items():
        for year in (1950, 1980):
            if d.decade.min() < year <= d.decade.max():
                r = breaks.chow_test(d, year)
                rows.append({"version": name, "spec": spec, "test": f"chow_{year}",
                             "statistic": r.statistic, "p_value": r.p_value, "breaks": ""})
        s = breaks.break_search(d)
        rows.append({"version": name, "spec": spec, "test": "break_search_bic",
                     "statistic": s.bic[s.breaks], "p_value": float("nan"),
                     "breaks": " ".join(map(str, s.breaks))})
tests = pd.DataFrame(rows)
TABLES_DIR.mkdir(parents=True, exist_ok=True)
tests.to_csv(TABLES_DIR / "rq0b_tests.csv", index=False)
tests.round(4)

# %% [markdown]
# ## Sanity check against Ganong & Shoag (2017)
#
# Ganong & Shoag find that population flowed toward high-income states from 1880 until about
# 1980, and that this weakened afterwards. The state-level β_d above should show the same
# pattern (positive and fairly stable before 1980, lower after). If it does not, check the
# pipeline before interpreting the results.
#
# **Finding (fill in after running):** write two or three sentences on the β_d pattern, which
# Chow tests reject, where the break search puts the breaks, whether robustness changes this,
# and the main limitations (1940 wages only; 1950–60 medians; metro panel starts 1940).
```

- [ ] **Step 4: Generate, execute and check the notebook.**

```bash
venv/bin/python -m jupytext --to notebook notebooks/1.1-lr-us-structural-break.py
rm notebooks/1.1-lr-us-structural-break.py
venv/bin/python -m jupyter nbconvert --to notebook --execute --inplace notebooks/1.1-lr-us-structural-break.ipynb
ls reports/figures/rq0b_betas.png reports/tables/rq0b_tests.csv
```

Expected: the notebook runs without errors and both files exist. Look at the figure. **Then replace the "Finding" placeholder in the last cell with the actual finding** in the notebook (2–3 plain sentences), and execute it again. A notebook still containing "(fill in after running)" is not finished.

- [ ] **Step 5: Run the full test suite.** Run: `make test`. Expected: everything passes; no data tests are skipped now that the data is built.

- [ ] **Step 6: Update the docs.**
  - `Claude/methods/analysis-methods.md`: add a "Results log" line for RQ0b with the date, the breaks found and the Chow p-values.
  - `Claude/methods/decisions.md`: add an entry for any judgment calls made during Tasks 3–12, e.g. county fixes added, allowlist entries, Easterlin unit choice.
  - Update "Open items": Plan 1 done, next is Plan 2 (RQ0a).

- [ ] **Step 7: Commit.**

```bash
git add us_housing_crisis_analysis/plots.py notebooks tests reports/figures/rq0b_betas.png reports/tables Claude
git commit -m "Add RQ0b notebook with decade coefficients and break tests

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Spec coverage (Plan 1)

| Spec item | Task |
|---|---|
| §4 architecture, source contract, long format | 1, 2 |
| §4 `geography.py` county → CBSA (2023) | 3 |
| §3 Tier 0: state population 1880+, county 1900+ | 4 |
| §3 Tier 0: income — Klein, Easterlin, BEA state; IPUMS 1940, NHGIS 1950–60, BEA metro | 6, 7, 8, 9 |
| §4 panels `us_state_longrun`, `us_metro_longrun` (population and income) | 10 |
| §5 RQ0b model, Chow 1950/1980, break search, robustness | 11, 12 |
| §6 notebook `1.1-lr-us-structural-break` | 12 |
| §7 schema, crosswalk, panel uniqueness, fast and data tiers | 1, 3, 10 |
| §7 CBSA vs. Census check; Connecticut, Virginia, Miami-Dade cases | 3, 5, 10 |
| §7 known values (US 2020, US 1880, SF CBSA); Klein vs. Easterlin; IPUMS vs. BEA | 7, 10 |
| §7 synthetic estimator recovery (`breaks.py`) | 11 |
| §7 plausibility bounds and allowlist | 10 |
| §4 build targets `data`, `features`, `notebooks`, `test` | 1 |

Deferred to later plans:
- **Plan 2:** RQ0a and city-proper population, including the Detroit 1950 known value.
- **Later plans:**
  - housing units 1940+ (RQ3);
  - all of Tiers 0-global, 1 and 2;
  - RQ5;
  - featured cities;
  - paper and dashboard;
  - the unit-conversion and peer-group tests, which belong with the sources that need them.
