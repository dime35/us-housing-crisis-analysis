import numpy as np
import pandas as pd
import pytest

from us_housing_crisis_analysis.modeling import city_metro as cm

US = {(1950, 1970): 0.343, (1970, 1990): 0.224, (1990, 2020): 0.333}


def test_us_growth_uses_listed_states_only():
    s = pd.DataFrame({"geo_id": ["state:01", "state:72", "state:01", "state:72"], "year": [1950, 1950, 1970, 1970],
                      "population": [100.0, 50.0, 150.0, 999.0]})
    assert cm.us_growth(s, ["01"], [(1950, 1970)]) == {(1950, 1970): pytest.approx(0.5)}


def test_bars():
    assert cm.keep_up_bar(1950, 1970, "relative", US) == pytest.approx(0.1715)
    assert cm.keep_up_bar(1990, 2020, "absolute", US) == pytest.approx(0.157625)
    assert cm.keep_up_bar(1950, 1970, "relative", US, fraction=1 / 3) == pytest.approx(0.343 / 3)
    with pytest.raises(ValueError):
        cm.keep_up_bar(1950, 1970, "other", US)


def test_keeps_up_at_the_bar_and_missing():
    g = pd.Series([1.1 / 1.0 - 1, 0.0999, np.nan])  # 0.10000000000000009, just below, missing
    out = cm.keeps_up(g, 0.1)
    assert out.iloc[0] == 1.0 and out.iloc[1] == 0.0 and np.isnan(out.iloc[2])
    assert cm.keeps_up(pd.Series([0.3 - 1e-12]), 0.3).iloc[0] == 1.0  # equal up to rounding


def panel_rows(geo, city, metro, core=None, comparable=None, years=(1950, 1970, 1990, 2020), headline=True,
               fips="x", area=None):
    n = len(years)
    return pd.DataFrame({"geo_id": geo, "geo_name": f"{geo}, OH", "year": list(years), "city_fips": fips,
                         "headline": headline, "city_population": city, "metro_population": metro,
                         "core_population": core or [np.nan] * n,
                         "metro_central_population": [m / 2 for m in metro],
                         "city_land_sqmi": area or [np.nan] * n, "growth_comparable": comparable or [True] * n,
                         "central_growth_comparable": [True] * n})


def test_period_growth_and_the_d27_flag():
    p = panel_rows("cbsa:1", [100, 90, 90, 120], [200, 300, 300, 450], comparable=[True, True, False, True])
    g = cm.period_growth(p).set_index("start")
    assert g.loc[1950, "city"] == pytest.approx(-0.1) and g.loc[1950, "metro"] == pytest.approx(0.5)
    assert g.loc[1950, "suburb"] == pytest.approx(210 / 100 - 1)
    assert np.isnan(g.loc[1990, "metro"]) and np.isnan(g.loc[1990, "suburb"])  # split in the 1990s
    assert g.loc[1990, "city"] == pytest.approx(120 / 90 - 1)  # city growth kept
    assert g.loc[1970, "metro"] == pytest.approx(0.0)  # other periods untouched
    c = cm.period_growth(p, central=True).set_index("start")
    assert c.loc[1950, "metro"] == pytest.approx(0.5) and c.loc[1990, "metro"] == pytest.approx(0.5)


def test_four_classes_and_missing_class():
    g = pd.DataFrame({"geo_id": ["a", "b", "c", "d", "e"], "start": [1950] * 5, "end": [1970] * 5,
                      "city": [0.3, -0.1, -0.1, 0.3, np.nan], "metro": [0.3, 0.3, 0.0, 0.0, 0.2]})
    c = cm.classify(g, US)
    assert c["class"].iloc[:4].tolist() == ["growing", "suburbanizing", "stagnant", "city-led"]
    assert pd.isna(c["class"].iloc[4])  # city missing -> no class
    assert cm.classify(g, US, "absolute").city_keeps.tolist()[:4] == [1, 0, 0, 1]


def test_core_recovery():
    g = pd.DataFrame({"geo_id": ["b", "b", "b", "z"], "start": [1950, 1970, 1990, 1950],
                      "end": [1970, 1990, 2020, 1970], "city": [-0.1, 0.3, 0.3, 0.3], "metro": [0.3] * 4})
    assert cm.core_recovery(cm.classify(g, US)).tolist() == [False, True, True, False]


def area(rows):
    """rows: {place: {year: sq mi}}"""
    return pd.DataFrame(rows).T


def test_annexing_exact_threshold_and_consolidation():
    a = area({"up": {1950: 100, 1970: 125}, "flat": {1950: 100, 1970: 120}, "cons": {1950: 22, 1970: 22}})
    cons = pd.DataFrame({"place_fips": ["cons"], "year": [1963]})
    f = cm.annexing(a, 1950, 1970, consolidations=cons)
    assert f.to_dict() == {"up": "annexing", "flat": "fixed", "cons": "annexing"}
    assert cm.annexing(a, 1950, 1970, threshold=0.1)["flat"] == "annexing"
    assert cm.annexing(a, 1970, 1990, consolidations=cons)["cons"] == "unknown"  # merger outside, no 1990 area


def test_annexing_bracket_rule():
    a = area({"small": {1950: 100, 2000: 105}, "big": {1950: 100, 2000: 300}, "none": {1950: 100},
              "wide": {1940: 100, 1950: 101, 1970: 150}})
    f = cm.annexing(a, 1950, 1970)
    assert f["small"] == "fixed"  # at most +5% over 1950-2000, so not more than 20% in 1950-70
    assert f["big"] == "unknown"  # the gain could fall outside 1950-70
    assert f["none"] == "unknown"
    assert f["wide"] == "annexing"  # the tightest span (1950 to 1970) is used


def test_units_frame():
    p = pd.concat([
        panel_rows("cbsa:1", [100, 90, 90, 120], [200, 300, 300, 450], core=[150, 140, 140, 160], fips="p1",
                   area=[50, 50, 50, 50]),
        panel_rows("cbsa:2", [100, 200, 220, 300], [150, 250, 260, 400], fips="p2", area=[30, 90, np.nan, 200]),
        panel_rows("cbsa:3", [1, 1, 1, 1], [9, 9, 9, 9], headline=False),
    ])
    u = cm.units(p, US).set_index("geo_id")
    assert list(u.index) == ["cbsa:1", "cbsa:2"]
    assert u.loc["cbsa:1", "city_1950"] == 0 and u.loc["cbsa:1", "metro_1950"] == 1
    assert u.loc["cbsa:1", "annex_1950"] == "fixed" and u.loc["cbsa:2", "annex_1950"] == "annexing"
    assert u.loc["cbsa:2", "annex_1970"] == "unknown"  # 1990 area missing, 1970-2020 gain over 20%
    assert u.loc["cbsa:1", "city_pop_1950"] == 100 and u.loc["cbsa:1", "region"] == "Northeast + Midwest"
    core = cm.units(p, US, core=True).set_index("geo_id")
    assert core.loc["cbsa:1", "city_1950"] == 0 and np.isnan(core.loc["cbsa:2", "city_1950"])  # no core figure


def test_regions():
    p = pd.DataFrame({"geo_id": ["cbsa:1", "cbsa:2"], "geo_name": ["Detroit, MI", "Houston, TX"]})
    assert cm.regions(p).to_dict() == {"cbsa:1": "Northeast + Midwest", "cbsa:2": "South + West"}
