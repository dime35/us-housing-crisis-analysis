import numpy as np
import pandas as pd
import pytest

from us_housing_crisis_analysis.modeling import annual_breaks as ab
from us_housing_crisis_analysis.modeling import breaks


def simulate(beta_for, n_units=50, years=range(1929, 2024), noise=0.01, seed=0):
    """Annual growth panel: persistent unit income plus small yearly noise; growth = a year
    effect + beta(year) * log income + noise."""
    rng = np.random.default_rng(seed)
    base = rng.normal(0, 0.3, n_units)
    rows = []
    for y in years:
        x = base + rng.normal(0, 0.05, n_units)
        g = 0.01 * np.sin(y) + beta_for(y) * x + rng.normal(0, noise, n_units)
        rows.append(pd.DataFrame({"geo_id": [f"u{i}" for i in range(n_units)], "year": y,
                                  "log_income": x, "growth": g}))
    return pd.concat(rows, ignore_index=True)


def levels(beta=0.02, n_units=40, years=range(1969, 2025), seed=0):
    """Panel in levels (population, income_pc) whose one-year growth = 0.01 + beta * log income."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 0.3, n_units)
    rows, logpop = [], np.zeros(n_units)
    for y in years:
        rows.append(pd.DataFrame({"geo_id": [f"u{i}" for i in range(n_units)], "year": y,
                                  "population": np.exp(logpop) * 1000, "income_pc": np.exp(x) * 1e4}))
        logpop = logpop + 0.01 + beta * x + rng.normal(0, 0.002, n_units)
    return pd.concat(rows, ignore_index=True)


def test_breaks_defaults_unchanged_and_period_column_works():
    dp = simulate(lambda y: 0.03 if y < 1978 else 0.0, years=range(1960, 1990))
    b = breaks.decade_betas(dp, period="year")
    assert list(b.columns[:1]) == ["year"] and len(b) == 30
    s = breaks.break_search(dp, max_breaks=1, min_segment=5, period="year")
    assert s.breaks == (1978,)
    decade = dp.rename(columns={"year": "decade"})
    assert breaks.decade_betas(decade).columns[0] == "decade"


def test_annual_growth_panel_drops_gaps_and_flagged_years():
    panel = pd.DataFrame({
        "geo_id": ["a"] * 5, "year": [2000, 2001, 2003, 2004, 2005],  # 2002 missing
        "population": [100.0, 110.0, 121.0, 133.1, 146.41], "income_pc": [10.0, 10.0, 10.0, np.nan, 10.0],
        "growth_comparable": [True, True, True, True, False],
    })
    g = ab.annual_growth_panel(panel, 2000, 2024)
    assert g.year.tolist() == [2000, 2003]  # 2001->2002 gap; 2004 no income; 2005 flagged (and no 2006)
    assert g.growth.iloc[0] == pytest.approx(np.log(1.1))


def test_annual_growth_panel_respects_start_and_end():
    g = ab.annual_growth_panel(levels(), 1970, 2000)
    assert g.year.min() == 1970 and g.year.max() == 1999


def test_rolling_betas_recover_slope_times_horizon():
    p = levels(beta=0.02)
    for h in (10, 5):
        r = ab.rolling_betas(p, h, 1969, 2024)
        assert r.start.min() == 1969 and r.start.max() == 2024 - h
        assert np.allclose(r.beta, 0.02 * h, atol=0.01 * h / 10 + 0.002)


def test_window_panel_skips_windows_containing_a_flagged_step():
    p = levels(n_units=3, years=range(1990, 2011))
    p["growth_comparable"] = ~((p.geo_id == "u0") & (p.year == 2001))
    w = ab.window_panel(p, 10, 1990, 2010)
    starts_u0 = set(w.loc[w.geo_id == "u0", "start"])
    assert starts_u0 == {1990, 1991}  # windows starting 1992-2000 contain the 2001 step
    assert set(w.loc[w.geo_id == "u1", "start"]) == set(range(1990, 2001))


def test_andrews_critical_values_match_the_published_table():
    # Andrews (1993) Table 1, one restriction, 5% level
    assert ab.andrews_critical_value(0.15) == pytest.approx(8.85, abs=0.15)
    assert ab.andrews_critical_value(0.05) == pytest.approx(9.84, abs=0.15)


def test_candidate_years_follow_the_trimming():
    states, metros = list(range(1929, 2024)), list(range(1969, 2024))
    assert states[ab.candidate_positions(len(states), 0.15)[0]] == 1943
    assert metros[ab.candidate_positions(len(metros), 0.15)[0]] == 1977
    assert metros[ab.candidate_positions(len(metros), 0.05)[0]] == 1971


def test_wald_matches_statsmodels_with_year_dummies():
    dp = simulate(lambda y: 0.03 if y < 1978 else 0.0, n_units=30, years=range(1960, 1995), noise=0.02)
    assert ab.wald_statistic(dp, 1978) == pytest.approx(breaks.chow_test(dp, 1978, period="year").statistic, rel=1e-8)


def test_planted_1978_break_is_found_and_significant():
    r = ab.sup_wald_break(simulate(lambda y: 0.03 if y < 1978 else 0.0, noise=0.02))
    assert abs(r.break_year - 1978) <= 2
    assert r.sup_wald > r.critical_value
    assert r.beta_before == pytest.approx(0.03, abs=0.01) and r.beta_after == pytest.approx(0.0, abs=0.01)
    assert not r.at_edge and r.first_candidate == 1943


def test_no_planted_break_is_not_significant():
    r = ab.sup_wald_break(simulate(lambda y: 0.02, noise=0.05))
    assert r.sup_wald < r.critical_value


def test_break_before_the_first_candidate_is_flagged_at_edge():
    r = ab.sup_wald_break(simulate(lambda y: 0.03 if y < 1972 else 0.0, years=range(1969, 2024)))
    assert r.break_year == 1977 and r.at_edge


def oil_cycle(n_units=50, n_energy=10, seed=0, noise=0.01):
    """No change in behavior; energy units get an income boom (1973-81) and bust (1982-90) with
    growth following oil jobs rather than income."""
    rng = np.random.default_rng(seed)
    base = rng.normal(0, 0.3, n_units)
    energy = np.arange(n_units) < n_energy
    rows = []
    for y in range(1969, 2024):
        cycle = 0.3 if 1973 <= y <= 1981 else (-0.3 if 1982 <= y <= 1990 else 0.0)
        x = base + rng.normal(0, 0.05, n_units) + energy * cycle
        g = 0.02 * x + energy * np.sign(cycle) * 0.03 + rng.normal(0, noise, n_units)
        rows.append(pd.DataFrame({"geo_id": [f"u{i}" for i in range(n_units)], "year": y,
                                  "log_income": x, "growth": g, "energy": energy}))
    return pd.concat(rows, ignore_index=True)


def test_oil_cycle_breaks_the_full_panel_but_not_the_one_without_energy_units():
    dp = oil_cycle()
    assert ab.sup_wald_break(dp).sup_wald > ab.andrews_critical_value(0.15)
    without = ab.sup_wald_break(dp[~dp.energy])
    assert without.sup_wald < without.critical_value


def test_bootstrap_range_covers_planted_break():
    dp = simulate(lambda y: 0.03 if y < 1978 else 0.0, noise=0.02)
    r = ab.bootstrap_break_year(dp, draws=199)
    assert r.low <= 1978 <= r.high and r.high - r.low <= 10
    assert len(r.estimates) == 199


def test_bootstrap_survives_a_year_with_a_single_unit():
    dp = simulate(lambda y: 0.03 if y < 1978 else 0.0, n_units=20, years=range(1960, 2000), noise=0.05)
    dp = dp[(dp.year != 1990) | (dp.geo_id == "u0")]  # 1990 often has no unit in a draw
    r = ab.bootstrap_break_year(dp, draws=99)
    assert 1960 <= r.low <= r.high <= 1999 and not np.isnan(r.estimates).any()


def test_bai_interval_contains_break_and_narrows_with_signal():
    weak = simulate(lambda y: 0.03 if y < 1978 else 0.0, noise=0.03)
    strong = simulate(lambda y: 0.03 if y < 1978 else 0.0, noise=0.01)
    lo_w, hi_w = ab.bai_interval(weak, ab.sup_wald_break(weak))
    lo_s, hi_s = ab.bai_interval(strong, ab.sup_wald_break(strong))
    assert lo_w <= 1978 <= hi_w and lo_s <= 1978 <= hi_s
    assert hi_s - lo_s < hi_w - lo_w


def test_range_coverage_returns_fractions():
    dp = simulate(lambda y: 0.03 if y < 1978 else 0.0, noise=0.05, years=range(1969, 2024))
    cov = ab.range_coverage(dp, ab.sup_wald_break(dp), sims=10, draws=49)
    assert set(cov) == {"bootstrap", "bai"} and all(0 <= v <= 1 for v in cov.values())


@pytest.mark.slow
def test_bootstrap_range_coverage_meets_the_rule():
    # Plan 1b spec §6: >= 200 synthetic panels; the 90% range must contain the planted year
    # at least COVERAGE_MIN of the time (the prototype gave 0.945). The noise is high on purpose,
    # so the range is wide and coverage is a real test.
    dp = simulate(lambda y: 0.03 if y < 1978 else 0.0, noise=0.05)
    cov = ab.range_coverage(dp, ab.sup_wald_break(dp), sims=200, draws=199)
    assert cov["bootstrap"] >= ab.COVERAGE_MIN, cov


def test_demeaned_search_matches_brute_force_with_year_dummies():
    dp = simulate(lambda y: 0.03 if y < 1968 else 0.0, n_units=20, years=range(1960, 1978))
    fast = ab.demeaned_break_search(dp, max_breaks=2, min_segment=3)
    slow = breaks.break_search(dp, max_breaks=2, min_segment=3, period="year")
    assert fast.breaks == slow.breaks == (1968,)
    assert set(fast.bic) == set(slow.bic)
    assert all(fast.bic[k] == pytest.approx(slow.bic[k], abs=1e-6) for k in slow.bic)


def test_demeaned_search_finds_planted_break_and_none_when_absent():
    assert ab.demeaned_break_search(simulate(lambda y: 0.03 if y < 1978 else 0.0)).breaks == (1978,)
    assert ab.demeaned_break_search(simulate(lambda y: 0.02)).breaks == ()
