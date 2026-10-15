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


STATE_ABBR_TO_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10",
    "DC": "11", "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27",
    "MS": "28", "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35",
    "NY": "36", "NC": "37", "ND": "38", "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44",
    "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53",
    "WV": "54", "WI": "55", "WY": "56", "PR": "72",
}


def first_listed_state_fips(cbsa_title: pd.Series) -> pd.Series:
    """FIPS of the first state named in a CBSA title ("New York-Newark-Jersey City, NY-NJ" -> 36)."""
    return cbsa_title.str.extract(r", ([A-Z]{2})", expand=False).map(STATE_ABBR_TO_FIPS)


def state_divisions() -> pd.Series:
    """State FIPS -> census division (1-9), from references/crosswalks/state_divisions.csv."""
    d = pd.read_csv(CROSSWALKS_DIR / "state_divisions.csv", dtype={"state_fips": str})
    return d.set_index("state_fips").division


def fips_from_nhgis_code(code: str) -> str | None:
    """NHGIS codes are 3-digit state + 4-digit county, each FIPS x 10 for counties that have a
    FIPS code. Historical counties without one use other final digits and return None."""
    code = (code or "").strip()
    if len(code) != 7 or not code.isdigit() or code[2] != "0" or code[6] != "0":
        return None
    return code[:2] + code[3:6]


def fips_from_gisjoin(gisjoin: str) -> str | None:
    return fips_from_nhgis_code((gisjoin or "")[1:])
