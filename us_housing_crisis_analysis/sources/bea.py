"""BEA Regional API: per capita personal income and population for states (SAINC1, 1929+), 1980
mining and total earnings for states (SAINC5S, SIC basis, 1958-2001; energy-state rule), and
county personal income and population (CAINC1, 1969+), which features.py sums to 2023 CBSAs like
every other metro year. (CAINC1 at MSA level returns BEA error 101 "Unknown error".)"""

import json
from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import BEA_API_KEY_ENV, CROSSWALKS_DIR, RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file, require_env

API_URL = "https://apps.bea.gov/api/data"
RAW_DIR = RAW_DATA_DIR / "bea"
# file stem -> (table, line code, GeoFips scope, geo_level, variable, unit).
# SAINC1/CAINC1: line 1 = personal income, 2 = population, 3 = per capita personal income.
# SAINC5S: line 35 = earnings by place of work, 200 = mining earnings (SIC division B).
REQUESTS = {
    "sainc1_state_pcpi": ("SAINC1", 3, "STATE", "state", "income_pc", "usd_current"),
    "sainc1_state_pop": ("SAINC1", 2, "STATE", "state", "population_bea", "persons"),
    "sainc5s_state_earnings_total": ("SAINC5S", 35, "STATE", "state", "earnings_total", "usd_current"),
    "sainc5s_state_earnings_mining": ("SAINC5S", 200, "STATE", "state", "earnings_mining", "usd_current"),
    "cainc1_county_pi": ("CAINC1", 1, "COUNTY", "county", "personal_income", "usd_current"),
    "cainc1_county_pop": ("CAINC1", 2, "COUNTY", "county", "population_bea", "persons"),
}
# Connecticut planning regions (09110-09190). The panels use the 8 old counties, which BEA also
# reports, so the regions are dropped to avoid counting the same people twice.
CT_PLANNING_REGIONS = {f"091{i}0" for i in range(1, 10)}


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
    for stem, (table, line, scope, *_) in REQUESTS.items():
        dest = RAW_DIR / f"{stem}.json"
        params = {
            "UserID": key, "method": "GetData", "datasetname": "Regional", "TableName": table,
            "LineCode": line, "GeoFips": scope, "Year": "ALL", "ResultFormat": "json",
        }
        existed = dest.exists() and not force
        download_file(API_URL, dest, force=force, params=params)
        if not existed:
            try:
                payload = json.loads(dest.read_text())
                _results(payload)
            except BeaApiError:
                dest.unlink()  # never cache an error payload
                raise
            # BEA echoes the request, including the UserID (API key); never keep it on disk
            payload["BEAAPI"].pop("Request", None)
            dest.write_text(json.dumps(payload))
        paths.append(dest)
    return paths


def _combine_county_combos(df: pd.DataFrame, fips: pd.Series) -> pd.DataFrame:
    """BEA folds some Virginia independent cities (and Kalawao HI, Menominee WI) into combo areas
    with codes like 51901. Each combo is assigned to its main county; every component shares that
    county's 2023 CBSA (checked in references/crosswalks/bea_county_combos.csv)."""
    combos = pd.read_csv(CROSSWALKS_DIR / "bea_county_combos.csv", dtype=str)
    seen = set(zip(fips, df.year))
    for c in combos.itertuples():
        for year in {y for f, y in seen if f == c.bea_fips}:
            overlap = [p for p in c.components.split("+") if (p, year) in seen]
            if overlap:
                raise ValueError(f"BEA combo {c.bea_fips} and components {overlap} both reported for {year}")
    fips = fips.replace(dict(zip(combos.bea_fips, combos.county_fips)))
    return df.assign(geo_id="county:" + fips)


def parse_bea_json(path: Path, geo_level: str, variable: str = "income_pc", unit: str = "usd_current") -> pd.DataFrame:
    data = pd.DataFrame(_results(json.loads(Path(path).read_text()))["Data"])
    fips = data.GeoFips.str.zfill(5)
    # "(NA)", "(D)" and similar suppression codes become NaN and are dropped
    value = pd.to_numeric(data.DataValue.str.replace(",", "", regex=False), errors="coerce")
    value = value * 10.0 ** pd.to_numeric(data.UNIT_MULT, errors="coerce").fillna(0)
    if geo_level == "state":
        keep = fips.str.endswith("000") & fips.str[:2].between("01", "56")
    else:
        keep = ~fips.str.endswith("000") & ~fips.isin(CT_PLANNING_REGIONS)
    # 0 is BEA's placeholder for an area without data that year (Alaska and Hawaii before 1950,
    # old Alaska divisions, Broomfield CO before 2001, Connecticut planning regions), never a real value
    keep = keep & (value != 0)
    df = pd.DataFrame(
        {
            "geo_id": "state:" + fips.str[:2], "geo_name": data.GeoName.str.rstrip(" *"),
            "geo_level": geo_level, "country_iso3": "USA", "year": data.TimePeriod.astype("int64"),
            "variable": variable, "value": value.astype("float64"), "unit": unit, "source": "bea",
        }
    )
    keep = keep & value.notna()
    df, fips = df[keep], fips[keep]
    if geo_level == "county":
        df = _combine_county_combos(df, fips)
    return df.reset_index(drop=True)


def load() -> pd.DataFrame:
    frames = [
        parse_bea_json(RAW_DIR / f"{stem}.json", level, variable, unit)
        for stem, (*_, level, variable, unit) in REQUESTS.items()
    ]
    return validate_long(pd.concat(frames, ignore_index=True))
