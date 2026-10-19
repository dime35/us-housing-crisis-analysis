"""NHGIS (IPUMS): state and county population from time series table A00 (1790-2020), and place
population from table AV0 (1970-2020, nominal: each place within its boundary at each census)."""

from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._ipums import run_extract, unpack_csvs

RAW_DIR = RAW_DATA_DIR / "nhgis"
A00_DIR = RAW_DIR / "a00"
A00_FILES = {"*_ts_nominal_state.csv": "a00_state.csv", "*_ts_nominal_county.csv": "a00_county.csv"}
AV0_DIR = RAW_DIR / "av0"
AV0_FILES = {"*_ts_nominal_place.csv": "av0_place.csv"}
AV0_YEARS = ["1970", "1980", "1990", "2000", "2010", "2020"]


def download(force: bool = False) -> list[Path]:
    return _download_a00(force) + _download_av0(force)


def _download_a00(force: bool) -> list[Path]:
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


def _download_av0(force: bool) -> list[Path]:
    paths = [AV0_DIR / name for name in AV0_FILES.values()]
    if all(p.exists() for p in paths) and not force:
        return paths
    from ipumspy import AggregateDataExtract, TimeSeriesTable

    extract = AggregateDataExtract(
        collection="nhgis",
        description="Total population, places, 1970-2020 (nominal)",
        time_series_tables=[TimeSeriesTable("AV0", geog_levels=["place"], years=AV0_YEARS)],
        tst_layout="time_by_row_layout",
    )
    run_extract(extract, AV0_DIR)
    return unpack_csvs(AV0_DIR, AV0_FILES)


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


def parse_places(path: Path) -> pd.DataFrame:
    """AV0 places: one row per place and census year. YEAR also holds ACS ranges ("2016-2020"),
    which are dropped, as are places without a 5-digit FIPS place code (NHGIS gives some unofficial
    places 4-digit codes, e.g. Shemya Station, AK "3000", which padded would collide with Anchorage).
    The ID is the place's code in that year (codes change, for example Louisville after its 2003
    merger; features.apply_place_code_changes handles it)."""
    raw = _read(path)
    raw = raw[raw["YEAR"].str.fullmatch(r"\d{4}") & raw["PLACEA"].str.fullmatch(r"\d{5}")]
    value = pd.to_numeric(raw["AV0AA"], errors="coerce")
    df = pd.DataFrame(
        {
            "geo_id": "place:" + raw["STATEFP"].str.zfill(2) + raw["PLACEA"],
            "geo_name": raw["PLACE"] + ", " + raw["STATE"], "geo_level": "city", "country_iso3": "USA",
            "year": raw["YEAR"].astype("int64"), "variable": "population",
            "value": value.astype("float64"), "unit": "persons", "source": "nhgis",
        }
    )
    return validate_long(df[value.notna()].reset_index(drop=True))


def load() -> pd.DataFrame:
    counties = parse_population(A00_DIR / "a00_state.csv", A00_DIR / "a00_county.csv")
    return validate_long(pd.concat([counties, parse_places(AV0_DIR / "av0_place.csv")], ignore_index=True))
