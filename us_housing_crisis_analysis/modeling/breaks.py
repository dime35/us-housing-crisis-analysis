"""RQ0b: decade-by-decade income coefficients and structural break tests (spec §5).

Model, for unit i (state or metro) and decade d:
    growth_{i,d} = alpha_d + beta_d * log_income_{i,d} + e_{i,d}
where growth = ln pop(d+10) - ln pop(d). Break tests pool all decades, keep decade fixed
effects, and let the income slope differ between segments."""

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd
import statsmodels.api as sm


@dataclass(frozen=True)
class TestResult:
    statistic: float
    p_value: float


@dataclass(frozen=True)
class BreakSearch:
    breaks: tuple[int, ...]
    bic: dict[tuple[int, ...], float]


def prepare_decade_panel(panel: pd.DataFrame, start: int, end: int = 2020) -> pd.DataFrame:
    """One row per unit-decade with population at both ends and income at the start. Units
    missing either drop out of that decade only (spec: no interpolation)."""
    # growth_comparable (metro panel): False where a county split makes the decade's growth
    # compare different areas; that decade is dropped, the neighboring decades are kept
    ok = panel["growth_comparable"].astype(bool) if "growth_comparable" in panel else True
    p = panel[["geo_id", "year", "population", "income_pc", "income_source"]].assign(ok=ok)
    nxt = p[["geo_id", "year", "population"]].assign(year=p.year - 10)
    m = p.merge(nxt.rename(columns={"population": "population_next"}), on=["geo_id", "year"])
    m = m[m.ok]
    m = m[(m.year >= start) & (m.year + 10 <= end)]
    m = m[(m.population > 0) & (m.population_next > 0) & (m.income_pc > 0)]
    return pd.DataFrame(
        {
            "geo_id": m.geo_id, "decade": m.year.astype("int64"),
            "growth": np.log(m.population_next / m.population), "log_income": np.log(m.income_pc),
            "income_source": m.income_source,
        }
    ).sort_values(["decade", "geo_id"]).reset_index(drop=True)


def decade_betas(dp: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for d, g in dp.groupby("decade"):
        fit = sm.OLS(g.growth, sm.add_constant(g.log_income)).fit(cov_type="HC1")
        rows.append({"decade": int(d), "beta": fit.params["log_income"],
                     "se": fit.bse["log_income"], "n": len(g)})
    return pd.DataFrame(rows)


def _design(dp: pd.DataFrame, break_decades) -> pd.DataFrame:
    """Decade fixed effects plus one income slope per segment. Segment k starts at the k-th break."""
    fe = pd.get_dummies(dp.decade, prefix="d", dtype=float)
    segment = np.searchsorted(sorted(break_decades), dp.decade.to_numpy(), side="right")
    slopes = {f"slope_{k}": dp.log_income.to_numpy() * (segment == k) for k in range(len(break_decades) + 1)}
    return pd.concat([fe, pd.DataFrame(slopes, index=dp.index)], axis=1)


def chow_test(dp: pd.DataFrame, break_decade: int) -> TestResult:
    """Wald test that the income slope is equal before and after break_decade, with standard
    errors clustered by unit (a Chow test robust to heteroskedasticity and serial correlation)."""
    fit = sm.OLS(dp.growth, _design(dp, [break_decade])).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(dp.geo_id)[0]}
    )
    w = fit.wald_test("slope_0 = slope_1", scalar=True)
    return TestResult(float(w.statistic), float(w.pvalue))


def break_search(dp: pd.DataFrame, max_breaks: int = 3, min_segment: int = 2) -> BreakSearch:
    """Bai-Perron-style global search: every set of up to max_breaks decade boundaries with at
    least min_segment decades per segment; choose the set with the lowest BIC."""
    decades = sorted(dp.decade.unique())
    candidates = decades[min_segment : len(decades) - min_segment + 1]
    n = len(dp)
    bic: dict[tuple[int, ...], float] = {}
    for k in range(max_breaks + 1):
        for combo in combinations(candidates, k):
            edges = [decades[0], *combo, decades[-1] + 10]
            sizes = [sum(lo <= d < hi for d in decades) for lo, hi in zip(edges[:-1], edges[1:])]
            if min(sizes) < min_segment:
                continue
            X = _design(dp, combo)
            ssr = sm.OLS(dp.growth, X).fit().ssr
            # parameters = coefficients plus the break dates themselves (Yao 1988)
            bic[tuple(int(c) for c in combo)] = n * np.log(ssr / n) + (X.shape[1] + len(combo)) * np.log(n)
    return BreakSearch(breaks=min(bic, key=bic.get), bic=bic)


def standardize_within_decade(dp: pd.DataFrame) -> pd.DataFrame:
    """Robustness: z-score log income within each decade, so sources with different spreads
    (e.g., 1940 wages vs. later total income) are comparable."""
    g = dp.groupby("decade").log_income
    return dp.assign(log_income=(dp.log_income - g.transform("mean")) / g.transform("std"))


def source_change_decades(dp: pd.DataFrame) -> list[int]:
    """Decades whose income source differs from the previous decade's."""
    src = dp.groupby("decade").income_source.first().sort_index()
    return [int(d) for d, changed in (src != src.shift()).iloc[1:].items() if changed]
