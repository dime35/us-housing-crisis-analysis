import pandas as pd
import pytest

from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import wp27


def table(fixtures_dir, n, year):
    return wp27.parse_table(fixtures_dir / "wp27" / f"tab{n}.txt", year)


def test_notes_and_missing_commas(fixtures_dir):
    t = table(fixtures_dir, 18, 1950).set_index("wp27_name")
    assert len(t) == 5  # header lines are not rows
    assert t.loc["Spokane city", "state"] == "WA" and t.loc["Spokane city", "land_sqmi"] == 41.5
    assert t.loc["Arlington CDP", "note"] and t.loc["Arlington CDP", "population"] == 135_449
    assert not t.loc["Detroit city", "note"]
    assert t.loc["Detroit city", "population"] == 1_849_568 and t.loc["Detroit city", "land_sqmi"] == 139.6
    assert t.loc["Houston city", "land_sqmi"] == 160.0


def test_tied_ranks_and_area_with_a_thousands_comma(fixtures_dir):
    assert "Madison city" in set(table(fixtures_dir, 19, 1960).wp27_name)  # rank "97-T"
    t = table(fixtures_dir, 22, 1990).set_index("wp27_name")
    assert t.loc["Anchorage city", "land_sqmi"] == 1697.6
    assert t.loc["Anchorage city", "note"]  # "*" with no leader dots after it
    assert t.loc["Houston city", "land_sqmi"] == 539.9


def test_parse_all_needs_100_places_a_year(fixtures_dir):
    with pytest.raises(ValueError, match="expected 100"):
        wp27.parse_all(fixtures_dir / "wp27", tables={1950: 18})


def test_to_long_needs_a_code_for_every_place(fixtures_dir):
    t = table(fixtures_dir, 18, 1950)
    codes = pd.DataFrame({"wp27_name": ["Detroit city"], "state": ["MI"], "place_fips": ["2622000"]})
    with pytest.raises(ValueError, match="no place code"):
        wp27.to_long(t, codes)
    out = validate_long(wp27.to_long(t[t.wp27_name == "Detroit city"], codes))
    assert set(out.variable) == {"population", "land_area"}
    assert set(out.geo_id) == {"place:2622000"}


def test_crosswalk_names_are_unique():
    c = wp27.load_place_fips()
    # A code can serve two names in different years ("Nashville city" 1950-60, "Nashville-Davidson"
    # from 1970); to_long rejects two names claiming one code in the same year
    assert not c.duplicated(["wp27_name", "state"]).any()
    assert c.place_fips.str.fullmatch(r"\d{7}").all()
