import numpy as np
import pandas as pd

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
