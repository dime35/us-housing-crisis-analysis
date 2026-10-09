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
