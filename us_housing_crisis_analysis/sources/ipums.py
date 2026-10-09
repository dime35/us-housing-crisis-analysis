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
