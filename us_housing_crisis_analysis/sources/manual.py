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
