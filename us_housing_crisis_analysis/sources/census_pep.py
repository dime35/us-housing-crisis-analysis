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
