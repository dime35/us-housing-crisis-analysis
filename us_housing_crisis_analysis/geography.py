"""Constant 2023 CBSA boundaries built from counties, plus county code harmonization.
Decisions are documented in Claude/methods/geography.md."""

from pathlib import Path
import re

import pandas as pd

from us_housing_crisis_analysis.config import CROSSWALKS_DIR, RAW_DATA_DIR
from us_housing_crisis_analysis.sources._http import download_file

DELINEATION_URL = (
    "https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/"
    "2023/delineation-files/list1_2023.xlsx"
)
RAW_DIR = RAW_DATA_DIR / "geography"
DELINEATION_PATH = RAW_DIR / "list1_2023.xlsx"
PLACE_COUNTY_URL = "https://www2.census.gov/geo/docs/reference/codes2020/national_place_by_county2020.txt"
PLACE_COUNTY_PATH = RAW_DIR / "national_place_by_county2020.txt"
AREA_TYPES = {"Metropolitan Statistical Area": "metro", "Micropolitan Statistical Area": "micro"}


def download(force: bool = False) -> list[Path]:
    return [download_file(DELINEATION_URL, DELINEATION_PATH, force=force),
            download_file(PLACE_COUNTY_URL, PLACE_COUNTY_PATH, force=force)]


def parse_delineation(path: Path) -> pd.DataFrame:
    # Two title rows precede the header; footnote rows at the end have no county code.
    raw = pd.read_excel(path, skiprows=2, dtype=str).dropna(subset=["FIPS County Code"])
    return pd.DataFrame(
        {
            "county_fips": raw["FIPS State Code"].str.zfill(2) + raw["FIPS County Code"].str.zfill(3),
            "cbsa_code": raw["CBSA Code"].str.zfill(5),
            "cbsa_title": raw["CBSA Title"],
            "area_type": raw["Metropolitan/Micropolitan Statistical Area"].map(AREA_TYPES),
            "central": raw["Central/Outlying County"].eq("Central"),
        }
    ).reset_index(drop=True)


def county_to_cbsa(delineation: pd.DataFrame | None = None, metro_only: bool = True) -> pd.DataFrame:
    """One row per county FIPS -> 2023 CBSA. Adds Connecticut's 8 old counties, which
    historical data uses, mapped to the 2023 CBSA holding most of each county's population."""
    d = parse_delineation(DELINEATION_PATH) if delineation is None else delineation
    cbsas = d.drop_duplicates("cbsa_code").set_index("cbsa_code")[["cbsa_title", "area_type"]]
    ct = pd.read_csv(CROSSWALKS_DIR / "ct_legacy_counties.csv", dtype=str)
    # Every 2023 Connecticut planning region in a metro is a central county, so the legacy counties
    # are central too (used by the RQ0a central-counties check)
    ct = ct[ct.cbsa_code.isin(cbsas.index)].join(cbsas, on="cbsa_code").assign(central=True)
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


# --- RQ0a (Plan 2): cities and their metros. See geography.md "Secondary unit: city proper". ---
OLD_CITIES_PATH = CROSSWALKS_DIR / "old_cities_1950.csv"
MAIN_CITY_PATH = CROSSWALKS_DIR / "metro_main_city.csv"
MAIN_CITY_OVERRIDES_PATH = CROSSWALKS_DIR / "metro_main_city_overrides.csv"
PLACE_CODE_CHANGES_PATH = CROSSWALKS_DIR / "place_code_changes.csv"
CONSOLIDATIONS_PATH = CROSSWALKS_DIR / "city_county_consolidations.csv"


def parse_place_counties(path: Path = PLACE_COUNTY_PATH) -> pd.DataFrame:
    """2020 place -> county pairs (a place in several counties has several rows). Connecticut is on
    its old counties, which county_to_cbsa maps to metros."""
    d = pd.read_csv(path, sep="|", dtype=str)
    return pd.DataFrame({"place_fips": d.STATEFP + d.PLACEFP, "county_fips": d.STATEFP + d.COUNTYFP})


def place_cbsas(place_counties: pd.DataFrame, crosswalk: pd.DataFrame) -> pd.DataFrame:
    """Unique (place, metro) pairs, through the place's counties."""
    m = place_counties.merge(crosswalk[["county_fips", "cbsa_code"]], on="county_fips")
    return m[["place_fips", "cbsa_code"]].drop_duplicates().reset_index(drop=True)


def cesta_names(cesta: pd.DataFrame) -> pd.DataFrame:
    """place_fips, city, state and geo_name ("City, ST") of every CESTA place."""
    c = cesta.drop_duplicates("geo_id")
    split = c.geo_name.str.rsplit(", ", n=1)
    return pd.DataFrame({"place_fips": c.geo_id.str.removeprefix("place:").to_numpy(),
                         "city": split.str[0].to_numpy(), "state": split.str[1].to_numpy(),
                         "geo_name": c.geo_name.to_numpy()})


def build_old_cities(wp27: pd.DataFrame, place_cbsa: pd.DataFrame, cesta_ids: set[str]) -> pd.DataFrame:
    """The 1950 top 100 (Working Paper 27, table 18), ranked by 1950 population, each with its 2023
    metro. main_city marks the metro's largest 1950 city: "the city" of a headline metro (spec §3.2).
    in_cesta is False for a city with no CESTA series (Arlington CDP, VA), which the
    all-old-cities-as-core check leaves out."""
    p = wp27[(wp27.year == 1950) & (wp27.variable == "population")]
    old = pd.DataFrame({"place_fips": p.geo_id.str.removeprefix("place:").to_numpy(),
                        "city_name": p.geo_name.to_numpy(), "population_1950": p.value.to_numpy()})
    old = old.sort_values("population_1950", ascending=False, kind="stable").reset_index(drop=True)
    old.insert(0, "rank_1950", old.index + 1)
    metros = place_cbsa[place_cbsa.place_fips.isin(old.place_fips)].groupby("place_fips").cbsa_code.agg(list)
    multi = metros[metros.str.len() > 1]
    if len(multi):
        raise ValueError(f"old cities in more than one metro: {multi.to_dict()}")
    old["cbsa_code"] = old.place_fips.map(metros.str[0])
    old["main_city"] = old.cbsa_code.notna() & ~old.cbsa_code.duplicated()
    old["in_cesta"] = old.place_fips.isin(cesta_ids)
    return old


def first_listed_state(title: str) -> str | None:
    m = re.search(r", ([A-Z]{2})", title)
    return m.group(1) if m else None


def build_metro_main_city(crosswalk: pd.DataFrame, names: pd.DataFrame, old_cities: pd.DataFrame,
                          overrides: pd.DataFrame) -> pd.DataFrame:
    """One row per metro outside Puerto Rico (owner's choice A, spec §3.2):
    - headline metros (holding a 1950 top-100 city) take their largest 1950 city;
    - other metros take the first-named city of the CBSA title: the CESTA place in the title's
      first state with the longest name that starts the title (followed by "-", "," or "/"),
      ignoring case;
    - overrides (cbsa_code, place_fips, note) settle titles that don't match; a blank place_fips
      means the city isn't in CESTA, so the metro has no city series."""
    metros = crosswalk[~crosswalk.county_fips.str.startswith("72")].drop_duplicates("cbsa_code")
    names = names[~names.duplicated(["city", "state"], keep=False)]
    by_state = dict(tuple(names.groupby("state")))
    label = names.set_index("place_fips").geo_name
    ov = overrides.set_index("cbsa_code")
    rows, unmatched = [], []
    for code, title in zip(metros.cbsa_code, metros.cbsa_title):
        if code in ov.index:
            fips, note = ov.at[code, "place_fips"], ov.at[code, "note"]
        else:
            g = by_state.get(first_listed_state(title), names.iloc[:0])
            t = title.lower()
            hits = g[[any(t.startswith(c.lower() + sep) for sep in "-,/") for c in g.city]]
            if hits.empty:
                unmatched.append(title)
                continue
            fips, note = hits.loc[hits.city.str.len().idxmax(), "place_fips"], ""
        if isinstance(fips, str) and fips:
            city = label.get(fips, pd.NA)
        else:
            fips, city = pd.NA, title.split(",")[0].split("-")[0]
        rows.append({"cbsa_code": code, "cbsa_title": title, "city_name": city, "place_fips": fips,
                     "top100_1950_rank": pd.NA, "headline": False, "note": note})
    if unmatched:
        raise ValueError(f"no CESTA city for {unmatched}; add them to {MAIN_CITY_OVERRIDES_PATH.name}")
    out = pd.DataFrame(rows).set_index("cbsa_code")
    for o in old_cities[old_cities.main_city].itertuples():
        if o.cbsa_code not in out.index:
            continue
        if out.at[o.cbsa_code, "place_fips"] != o.place_fips:
            out.at[o.cbsa_code, "note"] = f"largest 1950 city; first-named is {out.at[o.cbsa_code, 'city_name']}"
        out.loc[o.cbsa_code, ["place_fips", "city_name", "top100_1950_rank", "headline"]] = [
            o.place_fips, label.get(o.place_fips, o.city_name), o.rank_1950, True]
    out["top100_1950_rank"] = out.top100_1950_rank.astype("Int64")
    out["headline"] = out.headline.astype(bool)
    return out.reset_index()


def _read_crosswalk(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"cbsa_code": str, "place_fips": str, "source_fips": str, "county_fips": str})


def load_old_cities() -> pd.DataFrame:
    return _read_crosswalk(OLD_CITIES_PATH)


def load_metro_main_city() -> pd.DataFrame:
    return _read_crosswalk(MAIN_CITY_PATH).astype({"top100_1950_rank": "Int64", "headline": bool})


def load_main_city_overrides() -> pd.DataFrame:
    return _read_crosswalk(MAIN_CITY_OVERRIDES_PATH)


def load_place_code_changes() -> pd.DataFrame:
    return _read_crosswalk(PLACE_CODE_CHANGES_PATH)


def load_consolidations() -> pd.DataFrame:
    return _read_crosswalk(CONSOLIDATIONS_PATH)
