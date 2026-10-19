import pandas as pd
import pytest

from us_housing_crisis_analysis import features, geography
from us_housing_crisis_analysis.config import RAW_DATA_DIR, RQ0A_OVERLAP_TOLERANCE, RQ0A_PERIODS

pytestmark = pytest.mark.data

# Headline cities where CESTA and Working Paper 27 differ by more than 0.5% (found 2026-10-19;
# CESTA stays the population source). Jacksonville 1970: WP27 has all of Duval County.
CESTA_WP27_EXCEPTIONS = {
    ("0150000", 1960), ("1235000", 1970), ("4159000", 1970), ("0664000", 1970), ("4805000", 1970),
    ("3988000", 1970), ("2270000", 1980), ("3921000", 1980),
}
# CBSA codes of the featured US metros (master spec §2)
FEATURED = {"35620", "31080", "14460", "41860", "47900", "12580", "40060", "26420", "12420"}
# Main cities the 2020 place-to-county file can't place in their own metro: Waterbury (old CT county
# maps to New Haven), Macon (its 2010 code was replaced in 2014)
NOT_PLACED = {"0980000", "1349000"}


def headline(processed):
    p = processed("us_city_metro")
    return p[p.headline]


def test_headline_metros(processed):
    h = headline(processed)
    assert h.geo_id.nunique() == 81
    assert h.groupby("geo_id").city_fips.nunique().eq(1).all() and h.city_fips.notna().all()
    assert FEATURED <= set(h.geo_id.str.removeprefix("cbsa:"))


def test_headline_cities_have_every_count_and_area(processed):
    h = headline(processed)
    assert h.city_population.notna().all(), h[h.city_population.isna()][["geo_name", "year"]]
    for y in (1950, 1990, 2000, 2010, 2020):
        missing = h[(h.year == y) & h.city_land_sqmi.isna()]
        assert missing.empty, (y, missing.geo_name.tolist())


def test_city_never_exceeds_metro(processed):
    p = processed("us_city_metro").dropna(subset=["city_population", "metro_population"])
    bad = p[p.city_population > p.metro_population]
    assert bad.empty, bad[["geo_name", "year", "city_population", "metro_population"]]
    c = p.dropna(subset=["core_population"])
    assert (c.core_population <= c.metro_population).all() and (c.core_population >= c.city_population).all()


def test_cesta_matches_nhgis_2010_for_headline_cities(interim, processed):
    ids = ["place:" + f for f in set(headline(processed).city_fips)]
    c = interim("cesta").query("year == 2010").set_index("geo_id").value
    n = interim("nhgis").query("geo_level == 'city' and year == 2010").set_index("geo_id").value
    rel = (n.reindex(ids) / c.reindex(ids) - 1).abs()
    assert (rel <= RQ0A_OVERLAP_TOLERANCE).all(), rel[~(rel <= RQ0A_OVERLAP_TOLERANCE)]


def test_cesta_vs_wp27_only_known_exceptions(interim, processed):
    fips = set(headline(processed).city_fips)
    c = interim("cesta").set_index(["geo_id", "year"]).value
    w = interim("wp27").query("variable == 'population'")
    w = w[w.geo_id.str.removeprefix("place:").isin(fips)]
    rel = c.reindex(list(zip(w.geo_id, w.year))).to_numpy() / w.value.to_numpy() - 1
    off = {(g.removeprefix("place:"), y) for g, y, r in zip(w.geo_id, w.year, rel) if abs(r) > 0.005}
    assert off == CESTA_WP27_EXCEPTIONS


def test_wp27_1990_area_matches_gazetteer_1990(interim):
    changes = geography.load_place_code_changes()
    pw = features._places(interim("wp27"), "land_area", [1990])
    pg = features.apply_place_code_changes(features._places(interim("gazetteer"), "land_area", [1990]), changes)
    m = pw.merge(pg, on=["place_fips", "year"], suffixes=("_wp27", "_gaz"))
    assert len(m) >= 95
    assert ((m.value_gaz / m.value_wp27 - 1).abs() < 0.005).all()


def test_us_totals_50_states_and_dc(processed):
    s = processed("us_state_longrun")
    s = s[s.geo_id.str.removeprefix("state:").isin(set(geography.state_divisions().index))]
    t = s.groupby("year").population.sum()
    for year, total in {1950: 151.326e6, 1970: 203.212e6, 1990: 248.710e6, 2020: 331.449e6}.items():
        assert t[year] == pytest.approx(total, rel=1e-4)


def test_crosswalks_rebuild_to_the_committed_files(interim):
    path = RAW_DATA_DIR / "geography" / "national_place_by_county2020.txt"
    if not path.exists():
        pytest.skip("place-to-county file not downloaded")
    cesta, wp27 = interim("cesta"), interim("wp27")
    cw = geography.county_to_cbsa()
    pc = geography.place_cbsas(geography.parse_place_counties(path), cw)
    old = geography.build_old_cities(wp27, pc, set(cesta.geo_id.str.removeprefix("place:")))
    pd.testing.assert_frame_equal(old, geography.load_old_cities(), check_dtype=False)
    main = geography.build_metro_main_city(cw, geography.cesta_names(cesta), old, geography.load_main_city_overrides())
    committed = geography.load_metro_main_city()
    for frame in (main, committed):
        frame["place_fips"] = frame.place_fips.astype(object).where(frame.place_fips.notna(), None)
        frame["note"] = frame.note.fillna("")
    pd.testing.assert_frame_equal(main, committed, check_dtype=False)
    # every main city lies in its metro, except the two the 2020 file can't place
    pairs = set(zip(pc.place_fips, pc.cbsa_code))
    misplaced = {f for f, c in zip(main.place_fips, main.cbsa_code) if f is not None and (f, c) not in pairs}
    assert misplaced == NOT_PLACED


def test_annexing_unknowns_stay_within_the_spec_limit(processed):
    # Spec §3.4: more than 5 unknown headline cities in a period would call for ICPSR 7735
    from us_housing_crisis_analysis.modeling import city_metro as cm

    h = headline(processed)
    for start, end in RQ0A_PERIODS:
        flags = cm.annexing_by_metro(h, start, end, consolidations=geography.load_consolidations())
        assert (flags == "unknown").sum() <= 5, (start, flags[flags == "unknown"])
