import pytest

from us_housing_crisis_analysis.config import ICPSR_INCOME_FILES
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import icpsr

# Baltimore city's median family income in the fixtures (copied from the real files, in dollars)
BALTIMORE_CITY = {1950: 3275.0, 1960: 5659.0}


def parse(fixtures_dir, year):
    spec = ICPSR_INCOME_FILES[year]
    return validate_long(icpsr.parse_income(fixtures_dir / "icpsr" / spec["file"], year, spec))


@pytest.mark.parametrize("year", [1950, 1960])
def test_parse_income_counties_only(fixtures_dir, year):
    df = parse(fixtures_dir, year)
    assert {"county:24510", "county:24005"} <= set(df.geo_id)
    assert df.geo_id.str.fullmatch(r"county:\d{5}").all()  # US and state summary rows dropped
    assert not df.geo_id.str.endswith("000").any()
    assert set(df.variable) == {"median_family_income"} and set(df.year) == {year}
    assert df.value.gt(0).all()  # blank or suppressed values dropped, never zero-filled


@pytest.mark.parametrize("year", [1950, 1960])
def test_baltimore_city_income_in_dollars(fixtures_dir, year):
    df = parse(fixtures_dir, year).set_index("geo_id")
    assert df.at["county:24510", "value"] == BALTIMORE_CITY[year]
    assert df.at["county:24510", "unit"] == "usd_current"


@pytest.mark.parametrize("year", [1950, 1960])
def test_dc_appears_once_under_its_fips(fixtures_dir, year):
    # 1952 codes DC's county row 11010; 1962 has a duplicate row coded 11000
    df = parse(fixtures_dir, year)
    assert df.geo_id.str.startswith("county:110").sum() == 1
    assert "county:11001" in set(df.geo_id)


def test_missing_files_explain_the_manual_download(tmp_path, monkeypatch):
    monkeypatch.setattr(icpsr, "RAW_DIR", tmp_path)
    with pytest.raises(icpsr.MissingManualDownloadError, match="icpsr.umich.edu.*2896"):
        icpsr.download()
