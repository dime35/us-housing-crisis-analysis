import numpy as np
import pandas as pd
import pytest

from us_housing_crisis_analysis.config import MANUAL_DATA_DIR
from us_housing_crisis_analysis.schema import SchemaError, validate_long
from us_housing_crisis_analysis.sources import manual

HEADER = "state_fips,state_name,year,value,unit,source,table_ref\n"


def write(tmp_path, body):
    p = tmp_path / "s.csv"
    p.write_text(HEADER + body)
    return p


def test_parse_maps_sources_to_variables(tmp_path):
    p = write(tmp_path, "24,Maryland,1880,120,usd_current,klein_2013,Table 1\n"
                        "24,Maryland,1920,600,usd_current,easterlin_1960,Table A-1\n")
    df = validate_long(manual.parse_state_income(p))
    assert set(df.variable) == {"income_pc_klein", "income_pc_easterlin"}
    assert set(df.geo_id) == {"state:24"}


def test_unknown_source_rejected(tmp_path):
    p = write(tmp_path, "24,Maryland,1880,120,usd_current,someone_else,Table 1\n")
    with pytest.raises(ValueError, match="unknown source"):
        manual.parse_state_income(p)


def test_mixed_units_within_a_source_rejected(tmp_path):
    p = write(tmp_path, "24,Maryland,1880,120,usd_current,klein_2013,T1\n"
                        "25,Massachusetts,1880,140,index_us=100,klein_2013,T1\n")
    with pytest.raises(SchemaError, match="more than one unit"):
        validate_long(manual.parse_state_income(p))


# --- checks on the committed, transcribed file ---

def committed() -> pd.DataFrame:
    return pd.read_csv(MANUAL_DATA_DIR / "state_income_historical.csv", dtype={"state_fips": str})


def test_committed_coverage():
    df = committed()
    counts = df.groupby(["source", "year"]).state_fips.nunique()
    for year in (1880, 1890, 1900, 1910):
        assert counts[("klein_2013", year)] >= 38, year
    for year in (1880, 1900):
        assert counts[("easterlin_1960", year)] >= 38, year
    assert not df.duplicated(["source", "year", "state_fips"]).any()


@pytest.mark.xfail(
    strict=True,
    reason="Easterlin 1919-21 state figures (Easterlin 1957, Table Y-1) not yet transcribed; "
    "the source is a borrow-only book. Remove this marker once the rows are added.",
)
def test_committed_coverage_easterlin_1920():
    counts = committed().groupby(["source", "year"]).state_fips.nunique()
    assert counts.get(("easterlin_1960", 1920), 0) >= 38


def test_klein_and_easterlin_agree_where_they_overlap():
    """Two independent estimates of the same quantity: a transcription error shows up as a gap."""
    df = committed()
    for year in (1880, 1900):
        w = df[df.year == year].pivot(index="state_fips", columns="source", values="value").dropna()
        rel = np.log(w / w.mean())  # relative to the cross-state mean, so units can differ
        assert rel.corr().iloc[0, 1] > 0.9, year
        assert (rel.klein_2013 - rel.easterlin_1960).abs().median() < 0.10, year
