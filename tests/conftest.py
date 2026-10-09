from pathlib import Path

import pandas as pd
import pytest

from us_housing_crisis_analysis.config import INTERIM_DATA_DIR, PROCESSED_DATA_DIR

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


def _read_or_skip(path: Path) -> pd.DataFrame:
    if not path.exists():
        pytest.skip(f"{path.name} is not built; run `make data` and `make features`")
    return pd.read_parquet(path)


@pytest.fixture
def interim():
    """interim("nhgis") -> data/interim/nhgis.parquet, or skip the test if it is absent."""
    return lambda source: _read_or_skip(INTERIM_DATA_DIR / f"{source}.parquet")


@pytest.fixture
def processed():
    """processed("us_state_longrun") -> data/processed/<panel>.parquet, or skip."""
    return lambda panel: _read_or_skip(PROCESSED_DATA_DIR / f"{panel}.parquet")


DELINEATION_HEADER = [
    "CBSA Code", "Metropolitan Division Code", "CSA Code", "CBSA Title",
    "Metropolitan/Micropolitan Statistical Area", "Metropolitan Division Title", "CSA Title",
    "County/County Equivalent", "State Name", "FIPS State Code", "FIPS County Code",
    "Central/Outlying County",
]
METRO, MICRO = "Metropolitan Statistical Area", "Micropolitan Statistical Area"
DELINEATION_ROWS = [
    ["12580", "", "548", "Baltimore-Columbia-Towson, MD", METRO, "", "", "Baltimore city", "Maryland", "24", "510", "Central"],
    ["12580", "", "548", "Baltimore-Columbia-Towson, MD", METRO, "", "", "Baltimore County", "Maryland", "24", "005", "Central"],
    ["33100", "", "370", "Miami-Fort Lauderdale-West Palm Beach, FL", METRO, "", "", "Miami-Dade County", "Florida", "12", "086", "Central"],
    ["25540", "", "278", "Hartford-West Hartford-East Hartford, CT", METRO, "", "", "Capitol Planning Region", "Connecticut", "09", "110", "Central"],
    ["14860", "", "408", "Bridgeport-Stamford-Danbury, CT", METRO, "", "", "Western Connecticut Planning Region", "Connecticut", "09", "190", "Central"],
    ["45860", "", "278", "Torrington, CT", MICRO, "", "", "Northwest Hills Planning Region", "Connecticut", "09", "160", "Central"],
    ["31340", "", "", "Lynchburg, VA", METRO, "", "", "Bedford County", "Virginia", "51", "019", "Outlying"],
]


@pytest.fixture
def delineation_xlsx(tmp_path) -> Path:
    blank = [""] * len(DELINEATION_HEADER)
    rows = (
        [["List 1. CORE BASED STATISTICAL AREAS (CBSAs) ..."] + blank[1:], ["July 2023"] + blank[1:]]
        + [DELINEATION_HEADER]
        + DELINEATION_ROWS
        + [blank, ["Note: footnote text"] + blank[1:]]
    )
    path = tmp_path / "list1_2023.xlsx"
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    return path
