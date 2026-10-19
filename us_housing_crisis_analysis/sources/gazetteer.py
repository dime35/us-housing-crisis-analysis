"""Census Gazetteer place files: land area of every place in 1990, 2000, 2010 and 2020, keyed by
that year's state+place FIPS code (codes can change between years; see
features.apply_place_code_changes)."""

import io
from pathlib import Path
import re
import zipfile

from loguru import logger
import pandas as pd

from us_housing_crisis_analysis.config import RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file

BASE = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
# year -> (path under BASE, member inside the zip)
FILES = {
    1990: ("places.zip", "places.txt"),
    2000: ("places2k.zip", "places2k.txt"),
    2010: ("Gaz_places_national.zip", "Gaz_places_national.txt"),
    2020: ("2020_Gazetteer/2020_Gaz_place_national.zip", "2020_Gaz_place_national.txt"),
}
RAW_DIR = RAW_DATA_DIR / "gazetteer"
SQ_M_PER_SQ_MI = 2_589_988.110336
# 1990: "SS PPPPP Name...   ST  pop  housing  land  water  lat  lon"; land and water areas are in
# thousands of square meters (Detroit 0000359284 -> 138.7 sq mi, as in Working Paper 27)
ROW_1990 = re.compile(
    r"^(\d{2}) (\d{5}) (.+?)\s+[A-Z]{2}\s+\d+\s+\d+\s+(\d{10})\s+\d{10}\s+[+-]\d+\s+[+-]\d+\s*$")
# 2000: fixed width (Census record layout); latitude and longitude can touch, so no splitting
COLSPECS_2000 = {"geoid": (2, 9), "name": (9, 73), "land_sqmi": (119, 131)}


def download(force: bool = False) -> list[Path]:
    return [download_file(BASE + path, RAW_DIR / f"gaz_{year}.zip", force=force)
            for year, (path, _) in FILES.items()]


def decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def read_text(year: int) -> str:
    with zipfile.ZipFile(RAW_DIR / f"gaz_{year}.zip") as z:
        return decode(z.read(FILES[year][1]))


def parse(year: int, text: str) -> pd.DataFrame:
    """geoid (that year's 7-digit place code), name, land_sqmi. Codes that appear twice in a file
    (two tiny places in 1990) are dropped."""
    if year == 1990:
        rows = [(m[1] + m[2], m[3], int(m[4]) * 1000 / SQ_M_PER_SQ_MI)
                for line in text.splitlines() if (m := ROW_1990.match(line))]
        df = pd.DataFrame(rows, columns=["geoid", "name", "land_sqmi"])
    elif year == 2000:
        df = pd.read_fwf(io.StringIO(text), colspecs=list(COLSPECS_2000.values()),
                         names=list(COLSPECS_2000), dtype={"geoid": str}, header=None)
    else:
        raw = pd.read_csv(io.StringIO(text), sep="\t", dtype=str)
        raw.columns = raw.columns.str.strip()
        df = pd.DataFrame({"geoid": raw.GEOID.str.strip(), "name": raw.NAME.str.strip(),
                           "land_sqmi": pd.to_numeric(raw.ALAND_SQMI.str.strip())})
    dupes = df.geoid.duplicated(keep=False)
    if dupes.any():
        logger.info(f"gazetteer {year}: dropped codes listed twice: {sorted(set(df.geoid[dupes]))}")
    return df[~dupes].astype({"land_sqmi": "float64"}).reset_index(drop=True)


def load() -> pd.DataFrame:
    parts = []
    for year in FILES:
        g = parse(year, read_text(year))
        parts.append(pd.DataFrame({
            "geo_id": "place:" + g.geoid, "geo_name": g.name, "geo_level": "city", "country_iso3": "USA",
            "year": year, "variable": "land_area", "value": g.land_sqmi, "unit": "sq_mi",
            "source": "gazetteer"}))
    out = pd.concat(parts, ignore_index=True)
    return validate_long(out.astype({"year": "int64"}))
