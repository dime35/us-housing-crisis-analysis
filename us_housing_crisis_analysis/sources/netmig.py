"""County net migration by decade: the UW-Madison Applied Population Laboratory series (Winkler,
Johnson, Curtis and others), archived at ICPSR as the "United States County-Specific Net
Migration Rates Series" (collection 2760). The 2010s file downloads from netmigration.wisc.edu;
the 1950s-2000s files need a free ICPSR login and no redistribution, so they are downloaded by
hand into data/raw/netmig/ (like ICPSR 2896) and read straight from the zips. Net migration is
the residual method's estimate: population change minus births plus deaths."""

import io
from pathlib import Path
import zipfile

import pandas as pd

from us_housing_crisis_analysis.config import NETMIG_FILES, RAW_DATA_DIR
from us_housing_crisis_analysis.geography import STATE_ABBR_TO_FIPS
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file
from us_housing_crisis_analysis.sources.icpsr import MissingManualDownloadError

RAW_DIR = RAW_DATA_DIR / "netmig"
APL_URLS = {2010: "https://netmigration.wisc.edu/documents/NME_1020_data.zip"}
SERIES_URL = "https://www.icpsr.umich.edu/sites/icpsr/view/collections/2760"

__all__ = ["MissingManualDownloadError", "download", "load", "parse_net_migration"]


def download(force: bool = False) -> list[Path]:
    paths = []
    for decade, spec in NETMIG_FILES.items():
        dest = RAW_DIR / spec["file"]
        if decade in APL_URLS:
            download_file(APL_URLS[decade], dest, force=force)
        paths.append(dest)
    missing = [p.name for p in paths if not p.exists()]
    if missing:
        raise MissingManualDownloadError(
            f"missing {missing} in {RAW_DIR}. The ICPSR decades need a free login:\n"
            f"  1. Open {SERIES_URL} and log in.\n"
            "  2. For each decade, download the county file (Stata or fixed-width ASCII)"
            " with its codebook.\n"
            f"  3. Save the zips, unopened, in {RAW_DIR} under the names in config.NETMIG_FILES."
        )
    return paths


# State codes 2-52 of the Bowles / Tarver / Beale / Lee files (ICPSR 8493; "UGA" codes, ICPSR 8697
# codebook Table 1) number the 50 states and DC alphabetically, which is also the FIPS order.
UGA_STATE_FIPS = dict(zip(range(2, 53), sorted(set(STATE_ABBR_TO_FIPS.values()) - {"72"})))


def _read(path: Path, member: str, colspecs: str | None = None) -> pd.DataFrame:
    """colspecs reads a fixed-width member: "name:start-end,..." with 0-based, half-open positions."""
    with zipfile.ZipFile(path) as zf:
        raw = zf.read(member)
    if colspecs:
        fields = [item.split(":") for item in colspecs.split(",")]
        spans = [tuple(int(x) for x in span.split("-")) for _, span in fields]
        return pd.read_fwf(
            io.BytesIO(raw), colspecs=spans, names=[n for n, _ in fields], header=None, dtype=str
        )
    suffix = Path(member).suffix.lower()
    if suffix == ".dta":
        return pd.read_stata(io.BytesIO(raw), convert_categoricals=False)
    return pd.read_csv(
        io.BytesIO(raw), sep="\t" if suffix in (".tsv", ".tab", ".txt") else ",", dtype=str
    )


def _code(col: pd.Series) -> pd.Series:
    """Numeric code as a digit string ("" if missing); Stata stores codes as numbers, maybe floats."""
    return col.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).where(col.notna(), "")


def _county_fips(raw: pd.DataFrame, spec: dict[str, str]) -> pd.Series:
    """5-digit county code: one fips_col, or state_col + county_col (state_codes="uga" maps UGA codes)."""
    if "fips_col" in spec:
        return _code(raw[spec["fips_col"]]).str.zfill(5)
    state = _code(raw[spec["state_col"]])
    if spec.get("state_codes") == "uga":
        state = state.map(lambda c: UGA_STATE_FIPS.get(int(c), "") if c.isdigit() else "")
    county = _code(raw[spec["county_col"]])
    # A missing part stays empty (not zero-padded), so the row fails the 5-digit check and drops
    return state.str.zfill(2).where(state != "", "") + county.str.zfill(3).where(county != "", "")


def parse_net_migration(path: Path, decade: int, spec: dict[str, str]) -> pd.DataFrame:
    raw = _read(path, spec["member"], spec.get("colspecs"))
    fips = _county_fips(raw, spec)
    cols = spec["total_col"].split("+")
    value = raw[cols].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=len(cols))
    # County rows only: xx000 rows are state totals and 00000 the US; never add them to counties
    keep = fips.str.fullmatch(r"\d{5}") & ~fips.str.endswith("000") & value.notna()
    name = raw[spec["name_col"]].astype(str).str.strip() if "name_col" in spec else fips
    return (
        pd.DataFrame(
            {
                "geo_id": "county:" + fips[keep],
                "geo_name": name[keep],
                "geo_level": "county",
                "country_iso3": "USA",
                "year": decade,
                "variable": "net_migration",
                "value": value[keep].astype("float64"),
                "unit": "persons",
                "source": "netmig",
            }
        )
        .astype({"year": "int64"})
        .reset_index(drop=True)
    )


def load() -> pd.DataFrame:
    paths = download()
    frames = [parse_net_migration(p, d, spec) for p, (d, spec) in zip(paths, NETMIG_FILES.items())]
    return validate_long(pd.concat(frames, ignore_index=True))
