import numpy as np
import pandas as pd
import pytest

from us_housing_crisis_analysis import features


def long(rows, source):
    df = pd.DataFrame(rows, columns=["geo_id", "geo_level", "year", "variable", "value"])
    return df.assign(geo_name=df.geo_id, country_iso3="USA", unit="x", source=source,
                     year=df.year.astype("int64"), value=df.value.astype("float64"))


def test_state_panel_chains_income_sources_and_keeps_gaps_as_nan():
    nhgis = long([("state:24", "state", y, "population", 1e6) for y in (1880, 1920, 1930)]
                 + [("state:nhgis-G465", "state", 1880, "population", 1e5)], "nhgis")
    manual = long([("state:24", "state", 1880, "income_pc_klein", 100),
                   ("state:24", "state", 1880, "income_pc_easterlin", 999),  # cross-check only
                   ("state:24", "state", 1920, "income_pc_easterlin", 500)], "manual")
    bea = long([("state:24", "state", 1930, "income_pc", 700),
                ("state:24", "state", 1931, "income_pc", 650)], "bea")
    p = features.build_us_state_longrun(nhgis, bea, manual).set_index(["geo_id", "year"])
    assert p.loc[("state:24", 1880), "income_pc"] == 100  # Klein, not Easterlin, for 1880
    assert p.loc[("state:24", 1920), "income_source"] == "easterlin"
    assert p.loc[("state:24", 1930), "income_source"] == "bea"
    assert np.isnan(p.loc[("state:nhgis-G465", 1880), "income_pc"])  # territory: NaN, not 0
    assert 1931 not in p.index.get_level_values("year")


def test_state_panel_maps_territories_to_their_later_states():
    nhgis = long([("state:nhgis-G495", "state", 1880, "population", 144_000),  # Utah Territory
                  ("state:nhgis-G405", "state", 1890, "population", 62_000),   # Oklahoma Territory
                  ("state:nhgis-G405", "state", 1900, "population", 398_331),
                  ("state:nhgis-G178", "state", 1900, "population", 392_060),  # Indian Territory
                  ("state:nhgis-G095", "state", 1880, "population", 135_000),  # Dakota: split
                  ("state:nhgis-G999", "state", 1900, "population", 91_219)], "nhgis")  # military abroad
    manual = long([("state:49", "state", 1880, "income_pc_klein", 135),
                   ("state:40", "state", 1900, "income_pc_klein", 94)], "manual")
    p = features.build_us_state_longrun(nhgis, long([], "bea"), manual).set_index(["geo_id", "year"])
    assert p.loc[("state:49", 1880), "income_pc"] == 135
    assert p.loc[("state:40", 1900), "population"] == 790_391  # both territories = the 1907 state
    assert ("state:nhgis-G405", 1890) in p.index  # 1890 Indian Territory uncounted: not mapped
    assert ("state:nhgis-G095", 1880) in p.index  # Dakota split into two states: not mapped
    assert not p.index.get_level_values("geo_id").isin(["state:nhgis-G495", "state:nhgis-G178", "state:nhgis-G999"]).any()


def test_metro_panel_sums_counties_and_weights_medians():
    crosswalk = pd.DataFrame({"county_fips": ["24510", "24005"], "cbsa_code": ["12580"] * 2,
                              "cbsa_title": ["Baltimore"] * 2, "area_type": ["metro"] * 2})
    nhgis = long([("county:24510", "county", 1940, "population", 800),
                  ("county:24005", "county", 1940, "population", 200),
                  ("county:24510", "county", 1950, "population", 900),
                  ("county:24005", "county", 1950, "population", 100)], "nhgis")
    icpsr = long([("county:24510", "county", 1950, "median_family_income", 3000),
                  ("county:24005", "county", 1950, "median_family_income", 4000)], "icpsr")
    ipums = long([("county:24510", "county", 1940, "wage_income_total", 400_000),
                  ("county:24510", "county", 1940, "persons_ipums", 800),
                  ("county:24005", "county", 1940, "wage_income_total", 100_000),
                  ("county:24005", "county", 1940, "persons_ipums", 200)], "ipums")
    nhgis = pd.concat([nhgis, long([("county:24510", "county", 1970, "population", 900),
                                    ("county:24005", "county", 1970, "population", 100)], "nhgis")])
    bea = long([("county:24510", "county", 1970, "personal_income", 3_000_000),
                ("county:24510", "county", 1970, "population_bea", 900),
                ("county:24005", "county", 1970, "personal_income", 1_000_000),
                ("county:24005", "county", 1970, "population_bea", 100)], "bea")
    p = features.build_us_metro_longrun(nhgis, ipums, icpsr, bea, crosswalk).set_index(["geo_id", "year"])
    assert p.loc[("cbsa:12580", 1940), "population"] == 1000
    assert p.loc[("cbsa:12580", 1940), "income_pc"] == 500  # 500,000 wages / 1,000 persons
    assert p.loc[("cbsa:12580", 1950), "income_pc"] == 3100  # 0.9*3000 + 0.1*4000
    assert p.loc[("cbsa:12580", 1950), "income_source"] == "census_median_family_income"
    assert p.loc[("cbsa:12580", 1970), "income_pc"] == 4000  # 4,000,000 / 1,000 (BEA counties summed)


def test_unmatched_report_flags_counties_missing_from_2020():
    nhgis = long([("county:24510", "county", 2020, "population", 10),
                  ("county:24510", "county", 1900, "population", 90),
                  ("county:nhgis-G4650015", "county", 1900, "population", 10)], "nhgis")
    r = features.unmatched_county_report(nhgis)
    assert list(r.county_id) == ["nhgis-G4650015"]
    assert r.share_of_us.iloc[0] == 0.1


def test_metro_years_with_uncounted_indian_territory_are_dropped():
    crosswalk = pd.DataFrame({"county_fips": ["40143", "40037"], "cbsa_code": ["46140"] * 2,
                              "cbsa_title": ["Tulsa"] * 2, "area_type": ["metro"] * 2})
    nhgis = long([("county:40037", "county", 1900, "population", 100),  # Tulsa County: no 1900 row
                  ("county:40143", "county", 1910, "population", 900),
                  ("county:40037", "county", 1910, "population", 100)], "nhgis")
    empty = long([], "x")
    p = features.build_us_metro_longrun(nhgis, empty, empty, empty, crosswalk)
    assert list(p.year) == [1910]


def test_metro_1940_income_variant_leaves_out_missing_wages():
    crosswalk = pd.DataFrame({"county_fips": ["24510", "24005"], "cbsa_code": ["12580"] * 2,
                              "cbsa_title": ["Baltimore"] * 2, "area_type": ["metro"] * 2})
    nhgis = long([("county:24510", "county", 1940, "population", 800),
                  ("county:24005", "county", 1940, "population", 200)], "nhgis")
    ipums = long([("county:24510", "county", 1940, "wage_income_total", 400_000),
                  ("county:24510", "county", 1940, "persons_ipums", 800),
                  ("county:24510", "county", 1940, "wage_missing_share", 0.25),  # 200 missing
                  ("county:24005", "county", 1940, "wage_income_total", 100_000),
                  ("county:24005", "county", 1940, "persons_ipums", 200),
                  ("county:24005", "county", 1940, "wage_missing_share", 0.0)], "ipums")
    empty = long([], "x")
    p = features.build_us_metro_longrun(nhgis, ipums, empty, empty, crosswalk).set_index(["geo_id", "year"])
    assert p.loc[("cbsa:12580", 1940), "income_pc"] == 500  # missing wages count as 0
    assert p.loc[("cbsa:12580", 1940), "income_pc_wages_reported"] == 625  # 500,000 / 800 reported


def test_metro_decade_with_a_county_split_is_flagged_not_comparable(tmp_path, monkeypatch):
    # Broomfield (08014) split from Boulder (08013) in 2001: Boulder's and Denver's 2000-2010 growth
    # compare different areas, so that decade is flagged; other decades are not
    splits = tmp_path / "county_splits.csv"
    splits.write_text("new_fips,parent_fips,split_year,note\n08014,08013,2001,x\n")
    monkeypatch.setattr(features, "COUNTY_SPLITS_PATH", splits)
    crosswalk = pd.DataFrame({"county_fips": ["08013", "08014", "08031"], "cbsa_code": ["14500", "19740", "19740"],
                              "cbsa_title": ["Boulder", "Denver", "Denver"], "area_type": ["metro"] * 3})
    nhgis = long([("county:08013", "county", y, "population", 100) for y in (1990, 2000, 2010)]
                 + [("county:08031", "county", y, "population", 500) for y in (1990, 2000, 2010)], "nhgis")
    empty = long([], "x")
    p = features.build_us_metro_longrun(nhgis, empty, empty, empty, crosswalk).set_index(["geo_id", "year"])
    assert not p.loc[("cbsa:14500", 2000), "growth_comparable"]
    assert not p.loc[("cbsa:19740", 2000), "growth_comparable"]
    assert p.loc[("cbsa:14500", 1990), "growth_comparable"] and p.loc[("cbsa:14500", 2010), "growth_comparable"]


def test_state_annual_panel_joins_population_and_income():
    bea = long([("state:24", "state", 1929, "population_bea", 1.6e6),
                ("state:24", "state", 1929, "income_pc", 900),
                ("state:24", "state", 1930, "population_bea", 1.63e6),  # income missing: NaN
                ("state:24", "state", 2025, "income_pc", 80_000)], "bea")  # past the panel end
    p = features.build_us_state_annual(bea).set_index(["geo_id", "year"])
    assert p.loc[("state:24", 1929), "income_pc"] == 900
    assert np.isnan(p.loc[("state:24", 1930), "income_pc"])
    assert list(p.index.get_level_values("year")) == [1929, 1930]
    assert set(p.income_source.dropna()) == {"bea"}


def _split_crosswalk():
    # Broomfield (08014) and Adams (08001) in Denver, Boulder (08013) in its own metro
    return pd.DataFrame({"county_fips": ["08014", "08001", "08013"], "cbsa_code": ["19740", "19740", "14500"],
                         "cbsa_title": ["Denver, CO", "Denver, CO", "Boulder, CO"], "area_type": ["metro"] * 3})


def test_metro_annual_panel_sums_counties_and_flags_split_growth_years():
    rows = []
    for y in (2000, 2001, 2002):
        rows += [("county:08001", "county", y, "population_bea", 300.0), ("county:08001", "county", y, "personal_income", 3000.0),
                 ("county:08013", "county", y, "population_bea", 200.0), ("county:08013", "county", y, "personal_income", 4000.0)]
    rows += [("county:08014", "county", 2002, "population_bea", 40.0), ("county:08014", "county", 2002, "personal_income", 800.0)]
    p = features.build_us_metro_annual(long(rows, "bea"), _split_crosswalk()).set_index(["geo_id", "year"])
    assert p.loc[("cbsa:19740", 2002), "population"] == 340.0
    assert p.loc[("cbsa:19740", 2002), "income_pc"] == 3800.0 / 340.0
    # Broomfield first appears in 2002, so the 2001 -> 2002 step compares different areas
    assert not p.loc[("cbsa:19740", 2001), "growth_comparable"]
    assert not p.loc[("cbsa:14500", 2001), "growth_comparable"]
    assert p.loc[("cbsa:19740", 2000), "growth_comparable"] and p.loc[("cbsa:19740", 2002), "growth_comparable"]


def test_split_growth_years_ignores_splits_before_the_panel_starts():
    first_year = pd.Series({"08014": 2002, "35028": 1969})  # Los Alamos (1949) is in place by 1969
    cw = pd.concat([_split_crosswalk(), pd.DataFrame({"county_fips": ["35028", "35043"], "cbsa_code": ["31060", "10740"],
                                                      "cbsa_title": ["Los Alamos, NM", "Albuquerque, NM"], "area_type": ["metro"] * 2})])
    flagged = features.split_growth_years(cw, first_year, start=1969)
    assert flagged == {("19740", 2001), ("14500", 2001)}  # 08014's other parents aren't in this crosswalk


def test_energy_states_rule():
    bea = long([("state:56", "state", 1980, "earnings_total", 100.0), ("state:56", "state", 1980, "earnings_mining", 30.0),
                ("state:24", "state", 1980, "earnings_total", 900.0), ("state:24", "state", 1980, "earnings_mining", 0.5),
                ("state:11", "state", 1980, "earnings_total", 50.0)], "bea")  # mining suppressed: not energy
    e = features.energy_states(bea).set_index("state_fips")
    national = 30.5 / 1000.0  # states with both values
    assert e.loc["56", "ratio"] == pytest.approx(0.3 / national)
    assert e.energy.to_dict() == {"56": True, "24": False, "11": False}
    assert e.index[0] == "56"


def test_drop_states_for_states_and_metros():
    states = pd.DataFrame({"geo_id": ["state:48", "state:24"], "geo_name": ["Texas", "Maryland"]})
    metros = pd.DataFrame({"geo_id": ["cbsa:19100", "cbsa:12580"],
                           "geo_name": ["Dallas-Fort Worth-Arlington, TX", "Baltimore-Columbia-Towson, MD"]})
    assert features.drop_states(states, {"48"}).geo_id.tolist() == ["state:24"]
    assert features.drop_states(metros, {"48"}).geo_id.tolist() == ["cbsa:12580"]
