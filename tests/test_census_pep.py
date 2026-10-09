from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import census_pep


def test_cbsa_base_keeps_metros_only(fixtures_dir):
    df = validate_long(census_pep.parse_cbsa_base(fixtures_dir / "census_pep/cbsa-est2023-alldata.csv"))
    assert list(df.geo_id) == ["cbsa:12580"]
    assert df.value.iloc[0] == 2844510.0


def test_county_membership(fixtures_dir):
    m = census_pep.parse_county_membership(fixtures_dir / "census_pep/cbsa-est2023-alldata.csv")
    assert set(m.county_fips) == {"24005", "24510"}
    assert set(m.cbsa_code) == {"12580"}
