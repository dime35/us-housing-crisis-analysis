import numpy as np
import pandas as pd

from us_housing_crisis_analysis.modeling import breaks

DECADES = list(range(1880, 2020, 10))


def simulate(beta_for, n_units=200, noise=0.05, seed=0, shift_from=None, shift=1.0):
    """Decade panel where growth = 0.1 + beta(d) * true log income + noise. If shift_from is
    set, *measured* log income jumps by `shift` for every unit from that decade on, the way a
    change of income source would."""
    rng = np.random.default_rng(seed)
    rows = []
    for d in DECADES:
        x = rng.normal(0, 0.4, n_units)
        y = 0.1 + beta_for(d) * x + rng.normal(0, noise, n_units)
        measured = x + (shift if shift_from is not None and d >= shift_from else 0.0)
        rows.append(pd.DataFrame({"geo_id": [f"u{i}" for i in range(n_units)], "decade": d,
                                  "growth": y, "log_income": measured, "income_source": "s"}))
    return pd.concat(rows, ignore_index=True)


def test_prepare_decade_panel_drops_gaps_instead_of_filling():
    panel = pd.DataFrame({
        "geo_id": ["a"] * 3 + ["b"] * 3,
        "year": [1940, 1950, 1960] * 2,
        "population": [100.0, 200.0, 400.0, 100.0, np.nan, 100.0],
        "income_pc": [10.0, np.nan, 10.0, 10.0, 10.0, 10.0],
        "income_source": ["s"] * 6,
    })
    dp = breaks.prepare_decade_panel(panel, start=1940).set_index(["geo_id", "decade"])
    assert dp.loc[("a", 1940), "growth"] == np.log(2)
    assert ("a", 1950) not in dp.index  # income missing at the decade start
    assert ("b", 1940) not in dp.index and ("b", 1950) not in dp.index  # population gap


def test_decade_betas_recover_true_slope():
    b = breaks.decade_betas(simulate(lambda d: 0.3))
    assert np.allclose(b.beta, 0.3, atol=0.03)
    assert list(b.decade) == DECADES


def test_break_search_finds_planted_1980_break():
    dp = simulate(lambda d: 0.3 if d < 1980 else 0.0)
    assert breaks.break_search(dp).breaks == (1980,)


def test_break_search_finds_no_break_when_none_planted():
    assert breaks.break_search(simulate(lambda d: 0.3)).breaks == ()


def test_chow_detects_planted_1950_break():
    dp = simulate(lambda d: 0.3 if d < 1950 else 0.1)
    assert breaks.chow_test(dp, 1950).p_value < 0.01


def test_chow_does_not_reject_without_break():
    assert breaks.chow_test(simulate(lambda d: 0.3), 1950).p_value > 0.01


def test_source_level_shift_is_not_a_break():
    dp = simulate(lambda d: 0.3, shift_from=1930)
    assert breaks.break_search(dp).breaks == ()
    assert breaks.chow_test(dp, 1930).p_value > 0.01


def test_standardize_within_decade():
    z = breaks.standardize_within_decade(simulate(lambda d: 0.3))
    stats = z.groupby("decade").log_income.agg(["mean", "std"])
    assert np.allclose(stats["mean"], 0, atol=1e-9) and np.allclose(stats["std"], 1)


def test_source_change_decades():
    dp = pd.DataFrame({"decade": [1900, 1910, 1920, 1930, 1930],
                       "income_source": ["klein", "klein", "easterlin", "bea", "bea"]})
    assert breaks.source_change_decades(dp) == [1920, 1930]
