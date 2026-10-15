import pandas as pd

from us_housing_crisis_analysis import geography as geo


def test_parse_delineation_builds_padded_fips(delineation_xlsx):
    d = geo.parse_delineation(delineation_xlsx)
    assert len(d) == 7  # title, blank and footnote rows dropped
    assert "24510" in set(d.county_fips)
    assert d.set_index("county_fips").loc["09160", "area_type"] == "micro"


def test_each_county_maps_to_at_most_one_cbsa(delineation_xlsx):
    cw = geo.county_to_cbsa(geo.parse_delineation(delineation_xlsx), metro_only=False)
    assert not cw.county_fips.duplicated().any()


def test_legacy_ct_counties_map_to_2023_cbsas(delineation_xlsx):
    cw = geo.county_to_cbsa(geo.parse_delineation(delineation_xlsx)).set_index("county_fips")
    assert cw.loc["09003", "cbsa_code"] == "25540"  # Hartford County
    assert cw.loc["09001", "cbsa_title"] == "Bridgeport-Stamford-Danbury, CT"
    assert "09005" not in cw.index  # Litchfield -> Torrington is micropolitan


def test_metro_only_drops_micropolitan(delineation_xlsx):
    cw = geo.county_to_cbsa(geo.parse_delineation(delineation_xlsx))
    assert set(cw.area_type) == {"metro"}


def test_fixes_merge_bedford_city_into_bedford_county():
    df = pd.DataFrame({"county_fips": ["51515", "51019", "24510"], "population": [6222.0, 68676.0, 1.0]})
    out = geo.harmonize_county_fips(df).groupby("county_fips")["population"].sum()
    assert out["51019"] == 74898.0
    assert "51515" not in out.index


def test_fixes_are_not_chained():
    fixes = geo.load_county_fixes()
    assert not set(fixes.new_fips) & set(fixes.old_fips)
    assert not fixes.old_fips.duplicated().any()


def test_fips_from_nhgis_codes():
    assert geo.fips_from_nhgis_code("2405100") == "24510"
    assert geo.fips_from_gisjoin("G2405100") == "24510"
    assert geo.fips_from_nhgis_code("4600015") is None  # historical county, no FIPS
    assert geo.fips_from_nhgis_code("") is None


def test_first_listed_state_fips():
    titles = pd.Series(["Dallas-Fort Worth-Arlington, TX", "New York-Newark-Jersey City, NY-NJ",
                        "Cheyenne, WY", "Aguadilla, PR"])
    assert geo.first_listed_state_fips(titles).tolist() == ["48", "36", "56", "72"]
