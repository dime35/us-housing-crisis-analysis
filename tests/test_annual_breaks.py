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
