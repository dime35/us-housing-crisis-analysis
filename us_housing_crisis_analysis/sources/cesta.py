"""Stanford CESTA, Historical U.S. City Populations (US Census Bureau and Erik Steiner): decennial
city populations 1790-2010, keyed by each place's 2010 state+place FIPS code."""

from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file

# Pinned to the repository's last commit (2018-03-22), so the file can't change under us
COMMIT = "9b267baf1a7a662ca2076cc966166662346f80bc"
URL = (f"https://raw.githubusercontent.com/cestastanford/historical-us-city-populations/{COMMIT}/"
       "data/1790-2010_MASTER.csv")
RAW_DIR = RAW_DATA_DIR / "cesta"
PATH = RAW_DIR / "1790-2010_MASTER.csv"
YEARS = range(1790, 2011, 10)


def download(force: bool = False) -> list[Path]:
    return [download_file(URL, PATH, force=force)]


def parse(path: Path) -> pd.DataFrame:
    """The file has old-Mac (CR) line ends, which pandas reads. Missing counts are stored as 0 or
    left blank and are dropped here, never read as zero people. Places without a 2010 code ("0" or
    blank: places that no longer exist, or Arlington CDP, VA) are dropped."""
    raw = pd.read_csv(path, dtype=str)
    fips = raw["STPLFIPS_2010"].fillna("").str.strip()
    raw = raw.assign(STPLFIPS_2010=fips)[fips.str.fullmatch(r"\d{7}")]
    raw = raw.assign(name=raw["CityST"].fillna(raw["City"] + ", " + raw["ST"]))
    long = raw.melt(id_vars=["STPLFIPS_2010", "name"], value_vars=[str(y) for y in YEARS],
                    var_name="year", value_name="value")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long[long["value"] > 0]
    df = pd.DataFrame(
        {
            "geo_id": "place:" + long["STPLFIPS_2010"], "geo_name": long["name"], "geo_level": "city",
            "country_iso3": "USA", "year": long["year"].astype("int64"), "variable": "population",
            "value": long["value"].astype("float64"), "unit": "persons", "source": "cesta",
        }
    )
    return validate_long(df.reset_index(drop=True))


def load() -> pd.DataFrame:
    return parse(PATH)
