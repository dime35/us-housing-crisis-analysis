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
