import numpy as np
import pandas as pd
import pytest

from us_housing_crisis_analysis import features, geography
from us_housing_crisis_analysis.modeling import annual_breaks, breaks

pytestmark = pytest.mark.data

AK_HI = ["state:02", "state:15"]


@pytest.mark.parametrize("name", ["us_state_annual", "us_metro_annual"])
def test_panels_unique_and_income_positive(processed, name):
    p = processed(name)
    assert not p.duplicated(["geo_id", "year"]).any()
    assert (p.income_pc.dropna() > 0).all() and (p.population > 0).all()


def test_state_annual_years_and_no_alaska_hawaii_before_1950(processed):
    p = processed("us_state_annual")
    assert p.year.min() == 1929 and p.year.max() == 2024
    assert p[p.geo_id.isin(AK_HI) & (p.year < 1950)].empty
    assert (p.groupby("year").geo_id.count().loc[1950:] == 51).all()


@pytest.mark.parametrize("year", range(1930, 2021, 10))
def test_state_population_matches_census(processed, interim, year):
    # BEA is mid-year, the census is April 1; Alaska and Hawaii left out of both sides before 1950
    bea = processed("us_state_annual").query("year == @year")
    n = interim("nhgis")
    n = n[(n.geo_level == "state") & (n.variable == "population") & (n.year == year)]
    n = n[n.geo_id.str.match(r"state:\d\d$") & (n.geo_id != "state:72")]
    if year < 1950:
        bea, n = bea[~bea.geo_id.isin(AK_HI)], n[~n.geo_id.isin(AK_HI)]
    assert bea.population.sum() == pytest.approx(n.value.sum(), rel=0.01)


def test_metro_2020_population_matches_census_base(processed, interim):
    # BEA's July 2020 estimates dip in college towns (students away during COVID: Amherst -8%,
    # Ithaca -6%), so each metro must be within 1% of the April 2020 base in July 2019 or 2020
    p = processed("us_metro_annual").pivot(index="geo_id", columns="year", values="population")
    base = interim("census_pep").set_index("geo_id").value
    cw = geography.county_to_cbsa()
    ct = list(set("cbsa:" + cw[cw.county_fips.str.startswith("09")].cbsa_code))
    rel = {y: ((p[y] - base) / base).drop(ct, errors="ignore").dropna() for y in (2019, 2020)}
    assert len(rel[2020]) > 350
    closer = pd.concat([rel[2019].abs(), rel[2020].abs()], axis=1).min(axis=1)
    assert closer.max() < 0.01, closer.sort_values().tail()
    assert rel[2020].abs().median() < 0.002


def test_split_growth_years_are_exactly_the_known_ones(processed):
    p = processed("us_metro_annual")
    flagged = set(zip(p.loc[~p.growth_comparable, "geo_id"], p.loc[~p.growth_comparable, "year"]))
    assert flagged == {("cbsa:19740", 2001), ("cbsa:14500", 2001), ("cbsa:24540", 2001),
                       ("cbsa:49740", 1982), ("cbsa:10740", 1981)}


def test_energy_states_1980(interim):
    e = features.energy_states(interim("bea"))
    assert set(e.loc[e.energy, "state_fips"]) == {"56", "54", "40", "35", "22", "21", "48", "02"}
    assert e.set_index("state_fips").loc["38", "ratio"] < 3  # North Dakota: why the hand list also runs


@pytest.mark.parametrize("annual, longrun, first", [("us_state_annual", "us_state_longrun", 1930),
                                                    ("us_metro_annual", "us_metro_longrun", 1970)])
def test_rolling_beta_matches_decade_beta(processed, annual, longrun, first):
    roll = annual_breaks.rolling_betas(processed(annual), 10, first, 2020).set_index("start")
    dec = breaks.decade_betas(breaks.prepare_decade_panel(processed(longrun), first)).set_index("decade")
    for d in range(first, 2011, 10):
        lo, hi = dec.beta[d] - 1.96 * dec.se[d], dec.beta[d] + 1.96 * dec.se[d]
        assert lo <= roll.beta[d] <= hi, (d, roll.beta[d], dec.beta[d], dec.se[d])
