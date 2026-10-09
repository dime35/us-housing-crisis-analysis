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
