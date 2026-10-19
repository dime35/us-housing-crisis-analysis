import pandas as pd
import pytest

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


def test_state_divisions():
    d = geo.state_divisions()
    assert len(d) == 51 and set(d) == set(range(1, 10))
    assert d["06"] == 9 and d["36"] == 2 and d["48"] == 7 and d["11"] == 5



def test_central_flag(delineation_xlsx):
    d = geo.parse_delineation(delineation_xlsx).set_index("county_fips")
    assert d.loc["24510", "central"] and not d.loc["51019", "central"]
    cw = geo.county_to_cbsa(geo.parse_delineation(delineation_xlsx)).set_index("county_fips")
    assert cw.loc["09003", "central"]  # Connecticut legacy county: every CT planning region in a metro is central


def test_parse_place_counties(tmp_path):
    p = tmp_path / "pbc.txt"
    p.write_text("STATE|STATEFP|COUNTYFP|COUNTYNAME|PLACEFP|PLACENS|PLACENAME|TYPE|CLASSFP|FUNCSTAT\n"
                 "MI|26|163|Wayne County|22000|01626181|Detroit city|INCORPORATED PLACE|C1|A\n")
    out = geo.parse_place_counties(p)
    assert out.to_dict("records") == [{"place_fips": "2622000", "county_fips": "26163"}]


def cesta_long(rows):
    """rows: (place_fips, 'City, ST', year, population)"""
    return pd.DataFrame({"geo_id": ["place:" + r[0] for r in rows], "geo_name": [r[1] for r in rows],
                         "geo_level": "city", "year": [r[2] for r in rows], "variable": "population",
                         "value": [float(r[3]) for r in rows]})


def test_old_cities_mark_each_metros_largest_1950_city():
    wp27 = cesta_long([("5157000", "Norfolk city, VA", 1950, 213_513), ("5182000", "Virginia Beach city, VA", 1950, 5_390),
                       ("3651000", "New York city, NY", 1950, 7_891_957), ("3451000", "Newark city, NJ", 1950, 438_776)])
    pc = pd.DataFrame({"place_fips": ["5157000", "5182000", "3651000", "3451000"],
                       "cbsa_code": ["47260", "47260", "35620", "35620"]})
    old = geo.build_old_cities(wp27, pc, cesta_ids={"5157000", "3651000", "3451000"}).set_index("place_fips")
    assert old.loc["3651000", "rank_1950"] == 1 and old.loc["3651000", "main_city"]
    assert not old.loc["3451000", "main_city"] and old.loc["5157000", "main_city"]
    assert not old.loc["5182000", "in_cesta"]
    with pytest.raises(ValueError, match="more than one metro"):
        geo.build_old_cities(wp27, pd.concat([pc, pd.DataFrame({"place_fips": ["5157000"], "cbsa_code": ["99999"]})]), set())


def main_city_inputs():
    cw = pd.DataFrame({
        "county_fips": ["37067", "16055", "47037", "36061", "51810", "72127", "25001"],
        "cbsa_code": ["49180", "17660", "34980", "35620", "47260", "41980", "12700"],
        "cbsa_title": ["Winston-Salem, NC", "Coeur d'Alene, ID", "Nashville-Davidson--Murfreesboro--Franklin, TN",
                       "New York-Newark-Jersey City, NY-NJ", "Virginia Beach-Chesapeake-Norfolk, VA-NC",
                       "San Juan-Bayamón-Caguas, PR", "Barnstable Town, MA"]})
    names = pd.DataFrame({"place_fips": ["3774440", "3775000", "1616750", "4752006", "3651000", "5182000", "5157000"],
                          "city": ["Winston", "Winston-Salem", "Coeur D'Alene", "Nashville", "New York City",
                                   "Virginia Beach", "Norfolk"],
                          "state": ["NC", "NC", "ID", "TN", "NY", "VA", "VA"]})
    names["geo_name"] = names.city + ", " + names.state
    old = pd.DataFrame({"rank_1950": [1, 48], "place_fips": ["3651000", "5157000"], "city_name": ["x", "y"],
                        "population_1950": [7.9e6, 213_513.0], "cbsa_code": ["35620", "47260"],
                        "main_city": [True, True], "in_cesta": [True, True]})
    overrides = pd.DataFrame({"cbsa_code": ["35620", "12700"], "place_fips": ["3651000", None],
                              "note": ["CESTA: New York City", "not in CESTA"]})
    return cw, names, old, overrides


def test_main_city_matching_rules():
    m = geo.build_metro_main_city(*main_city_inputs()).set_index("cbsa_code")
    assert m.loc["49180", "place_fips"] == "3775000"  # longest name that starts the title
    assert m.loc["17660", "place_fips"] == "1616750"  # case ignored
    assert m.loc["34980", "place_fips"] == "4752006"
    assert "41980" not in m.index  # Puerto Rico left out
    assert pd.isna(m.loc["12700", "place_fips"]) and m.loc["12700", "city_name"] == "Barnstable Town"
    assert m.loc["35620", "headline"] and m.loc["35620", "top100_1950_rank"] == 1
    assert m.loc["47260", "place_fips"] == "5157000"  # headline: largest 1950 city, not first-named
    assert m.loc["47260", "city_name"] == "Norfolk, VA"
    assert "first-named" in m.loc["47260", "note"]
    assert not m.loc["49180", "headline"]


def test_main_city_unmatched_title_raises():
    cw, names, old, overrides = main_city_inputs()
    with pytest.raises(ValueError, match="no CESTA city"):
        geo.build_metro_main_city(cw, names[~names.city.str.startswith("Winston")], old, overrides)


def test_committed_tables_load():
    changes = geo.load_place_code_changes()
    assert set(changes.columns) >= {"place_fips", "year", "source_fips"}
    lou = changes[(changes.place_fips == "2148006") & (changes.year == 2020)]
    assert set(lou.source_fips) == {"2148006", "2148000"}
    cons = geo.load_consolidations().set_index("place_fips").year
    assert cons["4752006"] == 1963 and cons["2148006"] == 2003
