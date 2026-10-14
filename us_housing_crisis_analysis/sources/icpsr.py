"""ICPSR 2896 (Haines) County Data Books: county median family income for 1950 and 1960.

ICPSR has no API and its terms forbid redistribution, so the files are downloaded by hand
into data/raw/icpsr/ and read straight from the zips.
"""

import io
import zipfile
from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import ICPSR_INCOME_FILES, RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long

RAW_DIR = RAW_DATA_DIR / "icpsr"
STUDY_URL = "https://doi.org/10.3886/ICPSR02896.v3"
COUNTY_LEVEL = 1  # `level`: County=1 State=2 USA=3
# 1952 codes DC's county row 11010 rather than its FIPS 11001
FIPS_FIXES = {11010: 11001}


class MissingManualDownloadError(RuntimeError):
    """Raised when the hand-downloaded ICPSR files are not in data/raw/icpsr/."""


def download(force: bool = False) -> list[Path]:
    paths = [RAW_DIR / spec["file"] for spec in ICPSR_INCOME_FILES.values()]
    missing = [p.name for p in paths if not p.exists()]
    if missing:
        raise MissingManualDownloadError(
            f"missing {missing} in {RAW_DIR}. ICPSR has no API; download by hand:\n"
            f"  1. Open {STUDY_URL} (https://www.icpsr.umich.edu/web/ICPSR/studies/2896) and log in.\n"
            "  2. Download Part 72 (1952 County Data Book) and Part 74 (1962 County Data Book),\n"
            "     Stata format, with the codebook.\n"
            f"  3. Save the zips, unopened, in {RAW_DIR} under the names above."
        )
    return paths


def _read(path: Path, member: str) -> pd.DataFrame:
    with zipfile.ZipFile(path) as zf:
        return pd.read_stata(io.BytesIO(zf.read(member)), convert_categoricals=False)


def parse_income(path: Path, year: int, spec: dict[str, str]) -> pd.DataFrame:
    raw = _read(path, spec["member"])
    fips = raw[spec["fips_col"]]
    income = raw[spec["income_col"]].astype("float64")
    # County rows with a whole-number county FIPS (Alaska districts are 2900.1 etc.; xx000 is a
    # duplicate state-level row) and a reported income (blank or 0 means suppressed)
    keep = (
        raw["level"].eq(COUNTY_LEVEL) & fips.notna() & fips.mod(1).eq(0) & fips.mod(1000).ne(0)
        & income.gt(0)
    )
    raw, fips, income = raw[keep], fips[keep].astype("int64").replace(FIPS_FIXES), income[keep]
    return pd.DataFrame(
        {
            "geo_id": "county:" + fips.astype(str).str.zfill(5), "geo_name": raw["name"].str.title(),
            "geo_level": "county", "country_iso3": "USA", "year": year,
            "variable": "median_family_income", "value": income, "unit": "usd_current",
            "source": "icpsr",
        }
    ).astype({"year": "int64"}).reset_index(drop=True)


def load() -> pd.DataFrame:
    paths = download()
    frames = [parse_income(p, year, spec) for p, (year, spec) in zip(paths, ICPSR_INCOME_FILES.items())]
    return validate_long(pd.concat(frames, ignore_index=True))
