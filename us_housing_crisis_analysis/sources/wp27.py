"""Census Working Paper 27 (Gibson 1998), "Population of the 100 Largest Cities and Other Urban
Places in the United States: 1790 to 1990", tables 18-22 (1950-1990): population and land area of
each year's 100 largest urban places."""

from pathlib import Path
import re

import pandas as pd

from us_housing_crisis_analysis.config import CROSSWALKS_DIR, RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file

URL = "https://www2.census.gov/library/working-papers/1998/demographics/pop-twps0027/tab{n}.txt"
TABLES = {1950: 18, 1960: 19, 1970: 20, 1980: 21, 1990: 22}
RAW_DIR = RAW_DATA_DIR / "wp27"
PLACE_FIPS_PATH = CROSSWALKS_DIR / "wp27_place_fips.csv"

# A data row: rank (ties print as "97-T"), place and state, an optional " *" (see the paper's notes
# for individual places) and leader dots, then population, land area in sq mi (can carry a
# thousands comma: Anchorage 1,697.6) and density
ROW = re.compile(r"^\s*(\d+)(?:-T)?\s+(.+?)(\s\*)?\.*\s+([\d,]+)\s+([\d,.]+)\s+([\d,]+)\s*$")
# "Detroit city, MI", and in two rows "Spokane city WA" (no comma)
PLACE = re.compile(r"^(.*?),?\s([A-Z]{2})$")
# Place-type words dropped before matching names to CESTA
SUFFIX = r" (city|town|village|borough|CDP|municipality)$"


def download(force: bool = False) -> list[Path]:
    return [download_file(URL.format(n=n), RAW_DIR / f"tab{n}.txt", force=force) for n in TABLES.values()]


def parse_table(path: Path, year: int) -> pd.DataFrame:
    """One row per place: year, rank, wp27_name, state, population, land_sqmi, note ("*")."""
    rows = []
    for line in Path(path).read_text(encoding="latin-1").splitlines():
        m = ROW.match(line)
        if not m:
            continue
        rank, place, star, pop, area, _ = m.groups()
        p = PLACE.match(place.strip())
        if p is None:
            raise ValueError(f"{Path(path).name}: no state in {place!r}")
        rows.append({"year": year, "rank": int(rank), "wp27_name": p.group(1), "state": p.group(2),
                     "population": float(pop.replace(",", "")),
                     "land_sqmi": float(area.replace(",", "")), "note": star is not None})
    return pd.DataFrame(rows)


def parse_all(raw_dir: Path = RAW_DIR, tables: dict[int, int] = TABLES) -> pd.DataFrame:
    parts = [parse_table(Path(raw_dir) / f"tab{n}.txt", year) for year, n in tables.items()]
    for year, part in zip(tables, parts):
        if len(part) != 100:
            raise ValueError(f"WP27 {year}: {len(part)} places, expected 100")
    return pd.concat(parts, ignore_index=True)


def load_place_fips() -> pd.DataFrame:
    return pd.read_csv(PLACE_FIPS_PATH, dtype=str)


def to_long(rows: pd.DataFrame, place_fips: pd.DataFrame) -> pd.DataFrame:
    m = rows.merge(place_fips, on=["wp27_name", "state"], how="left")
    missing = m[m.place_fips.isna()]
    if len(missing):
        raise ValueError(f"no place code for {sorted(set(missing.wp27_name + ', ' + missing.state))}")
    base = pd.DataFrame({"geo_id": "place:" + m.place_fips, "geo_name": m.wp27_name + ", " + m.state,
                         "geo_level": "city", "country_iso3": "USA", "year": m.year.astype("int64"),
                         "source": "wp27"})
    out = pd.concat([
        base.assign(variable="population", value=m.population.astype("float64"), unit="persons"),
        base.assign(variable="land_area", value=m.land_sqmi.astype("float64"), unit="sq_mi"),
    ], ignore_index=True)
    return validate_long(out)


def load() -> pd.DataFrame:
    return to_long(parse_all(RAW_DIR), load_place_fips())
