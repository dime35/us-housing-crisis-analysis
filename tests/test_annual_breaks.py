import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

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


def test_andrews_p_value_inverts_the_critical_value():
    assert ab.andrews_p_value(ab.andrews_critical_value(0.15), 0.15) == pytest.approx(0.05, abs=0.002)
    assert ab.andrews_p_value(ab.andrews_critical_value(0.15, 0.01), 0.15) == pytest.approx(0.01, abs=0.001)
    assert ab.andrews_p_value(0.0, 0.15) == 1.0


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


def state_panel(beta_for, n_units=48, years=range(1929, 2024), noise=0.02, seed=0, oil=False):
    """Like simulate(), with state-style IDs (state:01 ...) so oil and division cells apply. With
    oil=True, units 01-08 get an income boom 1973-81 and bust 1982-90, and growth follows oil jobs
    (+0.03 boom, -0.03 bust) rather than income."""
    rng = np.random.default_rng(seed)
    base = rng.normal(0, 0.3, n_units)
    energy = np.arange(n_units) < 8
    rows = []
    for y in years:
        cycle = (0.3 if 1973 <= y <= 1981 else -0.3 if 1982 <= y <= 1990 else 0.0) if oil else 0.0
        x = base + rng.normal(0, 0.05, n_units) + energy * cycle
        g = 0.01 * np.sin(y) + beta_for(y) * x + energy * np.sign(cycle) * 0.03 + rng.normal(0, noise, n_units)
        rows.append(pd.DataFrame({"geo_id": [f"state:{i + 1:02d}" for i in range(n_units)], "year": y,
                                  "log_income": x, "growth": g}))
    return pd.concat(rows, ignore_index=True)


ENERGY = {f"{i:02d}" for i in range(1, 9)}


def test_oil_cells_split_energy_states_in_oil_years_only():
    dp = ab.oil_cells(state_panel(lambda y: 0.02, years=range(1970, 1995)), ENERGY)
    row = dp.set_index(["geo_id", "year"]).cell
    assert row[("state:01", 1980)] == "1980E" and row[("state:20", 1980)] == "1980"
    assert row[("state:01", 1972)] == "1972" and row[("state:01", 1991)] == "1991"


def test_cells_spanning_two_periods_raise():
    dp = state_panel(lambda y: 0.02, years=range(1968, 1972)).assign(cell="all")
    with pytest.raises(ValueError, match="span"):
        ab.sup_wald_break(dp, cell="cell")


def test_sup_wald_with_cells_matches_statsmodels_cell_dummies():
    dp = ab.oil_cells(state_panel(lambda y: 0.03 if y < 1975 else 0.0, years=range(1960, 2000), oil=True), ENERGY)
    r = ab.sup_wald_break(dp, cell="cell")
    X = pd.get_dummies(dp.cell, prefix="c", dtype=float)
    X["s0"] = dp.log_income * (dp.year < r.break_year)
    X["s1"] = dp.log_income * (dp.year >= r.break_year)
    fit = sm.OLS(dp.growth, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(dp.geo_id)[0]})
    assert r.beta_before == pytest.approx(fit.params["s0"], rel=1e-8)
    assert r.beta_after == pytest.approx(fit.params["s1"], rel=1e-8)


def test_cell_none_unchanged():
    dp = state_panel(lambda y: 0.03 if y < 1978 else 0.0)
    a, b = ab.sup_wald_break(dp), ab.sup_wald_break(dp.assign(cell=dp.year), cell="cell")
    assert (a.break_year, a.sup_wald) == (b.break_year, pytest.approx(b.sup_wald, rel=1e-10))


def test_oil_cells_pull_the_break_back_to_1970():
    dp = state_panel(lambda y: 0.03 if y < 1970 else 0.0, oil=True)
    with_cells = ab.sup_wald_break(ab.oil_cells(dp, ENERGY), cell="cell")
    assert abs(with_cells.break_year - 1970) <= 2


def test_division_cells():
    divisions = pd.Series({f"{i:02d}": (i % 9) + 1 for i in range(1, 49)})
    dp = ab.division_cells(state_panel(lambda y: 0.02, years=range(2000, 2002)), divisions)
    assert dp.set_index(["geo_id", "year"]).cell[("state:09", 2000)] == "2000-1"


STEP_1970 = lambda y: 0.03 if y < 1970 else 0.0  # noqa: E731
STEP_1990 = lambda y: 0.03 if y < 1990 else 0.0  # noqa: E731
SLIDE = lambda y: 0.03 if y < 1970 else 0.0 if y >= 1990 else 0.03 * (1990 - y) / 20  # noqa: E731


def test_three_period_matches_statsmodels_with_cell_dummies():
    dp = ab.oil_cells(state_panel(STEP_1970, years=range(1960, 2000), oil=True), ENERGY)
    r = ab.three_period(dp, cell="cell")
    seg = np.searchsorted([1970, 1990], dp.year, side="right")
    X = pd.get_dummies(dp.cell, prefix="c", dtype=float)
    for s in range(3):
        X[f"s{s}"] = dp.log_income * (seg == s)
    fit = sm.OLS(dp.growth, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(dp.geo_id)[0]})
    assert [r.beta_pre, r.beta_mid, r.beta_post] == pytest.approx(list(fit.params[["s0", "s1", "s2"]]), rel=1e-10)
    assert [r.se_pre, r.se_mid, r.se_post] == pytest.approx(list(fit.bse[["s0", "s1", "s2"]]), rel=1e-8)
    for stat, p, constraint in [(r.wald_pre_post, r.p_pre_post, "s0 = s2"),
                                (r.wald_mid_pre, r.p_mid_pre, "s1 = s0"),
                                (r.wald_mid_post, r.p_mid_post, "s1 = s2")]:
        w = fit.wald_test(constraint, scalar=True, use_f=False)
        assert stat == pytest.approx(float(w.statistic), rel=1e-8)
        assert p == pytest.approx(float(w.pvalue), rel=1e-6, abs=1e-12)


@pytest.mark.parametrize("beta_for, answer", [(STEP_1970, "1970"), (STEP_1990, "1990"), (SLIDE, "gradual")])
def test_decision_rule_recovers_planted_pattern(beta_for, answer):
    dp = state_panel(beta_for)
    r = ab.three_period(dp)
    low, high, _ = ab.share_range(dp, draws=199)
    assert ab.decide(low, high, r.p_pre_post) == answer


def test_no_change_is_cant_tell():
    dp = state_panel(lambda y: 0.02)
    r = ab.three_period(dp)
    low, high, _ = ab.share_range(dp, draws=199)
    assert r.p_pre_post > 0.05 and ab.decide(low, high, r.p_pre_post) == "can't tell"


def test_guard_overrides_a_decisive_looking_range():
    assert ab.decide(0.9, 1.1, p_pre_post=0.2) == "can't tell"
    assert ab.decide(0.9, 1.1, p_pre_post=0.01) == "1970"


@pytest.mark.parametrize("low, high, answer", [(0.2, 1.3, "1970"), (1.1, 1.5, "1970"), (-0.4, 0.6, "1990"),
                                                (-0.9, -0.1, "1990"), (0.1, 0.8, "gradual"), (-0.2, 1.2, "can't tell")])
def test_decision_table(low, high, answer):
    assert ab.decide(low, high, p_pre_post=0.001) == answer


def test_oil_cells_turn_a_fake_gradual_into_1970():
    dp = state_panel(STEP_1970, oil=True)
    plain = ab.three_period(dp)
    lo0, hi0, _ = ab.share_range(dp, draws=199)
    cells = ab.oil_cells(dp, ENERGY)
    fixed = ab.three_period(cells, cell="cell")
    lo1, hi1, _ = ab.share_range(cells, cell="cell", draws=199)
    assert ab.decide(lo0, hi0, plain.p_pre_post) != "1970"
    assert ab.decide(lo1, hi1, fixed.p_pre_post) == "1970"


def test_betas_add_up_across_outcomes():
    # total = migration + natural increase; OLS is linear in y, so the betas add up exactly
    dp = state_panel(STEP_1970, years=range(1950, 2020, 10)).rename(columns={"year": "decade"})
    rng = np.random.default_rng(1)
    m = dp.assign(growth=dp.growth * 0.6 + rng.normal(0, 0.01, len(dp)))
    n = dp.assign(growth=dp.growth - m.growth)
    t, a, b = (ab.three_period(d, period="decade") for d in (dp, m, n))
    for f in ("beta_pre", "beta_mid", "beta_post"):
        assert getattr(t, f) == pytest.approx(getattr(a, f) + getattr(b, f), abs=1e-12)


def test_share_range_skips_degenerate_draws():
    # one unit only has years from 1990, so before 1990 a draw can contain a single distinct unit;
    # income then has no variation within year, the share is NaN and the range skips it
    dp = state_panel(STEP_1970, n_units=6, years=range(1960, 2000))
    dp = dp[~((dp.geo_id == "state:06") & (dp.year < 1990))]
    low, high, draws = ab.share_range(dp, draws=999)
    assert len(draws) == 999 and np.isnan(draws).any()
    assert np.isfinite(low) and np.isfinite(high)


def test_a_period_with_one_unit_drawn_several_times_gives_nan_not_a_finite_share():
    # Period 0 holds a single distinct unit, drawn 3 times. Demeaning leaves rounding residue
    # (3 * 0.1 / 3 != 0.1 in floating point), not exact zeros, so sxx is about 1e-33, not 0.
    t = np.array([0, 1, 1, 2, 2])
    x, y = np.array([0.1, 1.0, 2.0, 1.5, 3.0]), np.array([0.7, 2.0, 3.0, 4.0, 5.0])
    w = np.array([3.0, 1.0, 1.0, 1.0, 1.0])
    xd, yd = ab._demean(t, x, y, w, 3)
    assert xd[0] != 0  # the residue the guard has to catch
    b, _ = ab._three_betas(t, x, xd, yd, w)
    assert np.isnan(b[0]) and np.isfinite(b[1:]).all()
    assert np.isnan(ab._share(b))
