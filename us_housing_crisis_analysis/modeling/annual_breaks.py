"""RQ0b with annual data: rolling-window betas and dating the break (Plan 1b spec §4).

Annual model, for unit i (state or metro) and year t:
    growth_{i,t} = ln pop(t+1) - ln pop(t) = alpha_t + beta_seg(t) * log_income_{i,t} + e_{i,t}
Year fixed effects are removed by demeaning growth and log income within year once. That is exact
(Frisch-Waugh-Lovell): every year lies wholly inside one segment, so the segment slopes are
estimated on the demeaned data, and each candidate break is a closed-form fit."""

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations

import numpy as np
import pandas as pd

from us_housing_crisis_analysis.modeling import breaks


def _ok(panel: pd.DataFrame) -> pd.Series:
    """growth_comparable (metro panel): False where the step t -> t+1 crosses a county split."""
    if "growth_comparable" in panel:
        return panel["growth_comparable"].astype(bool)
    return pd.Series(True, index=panel.index)


def annual_growth_panel(panel: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    """One row per unit-year t with population at t and t+1 and income at t, for start <= t and
    t+1 <= end. Gaps and flagged steps drop out; nothing is filled."""
    p = panel[["geo_id", "year", "population", "income_pc"]].assign(ok=_ok(panel))
    nxt = p[["geo_id", "year", "population"]].assign(year=p.year - 1)
    m = p.merge(nxt.rename(columns={"population": "population_next"}), on=["geo_id", "year"])
    m = m[m.ok & (m.year >= start) & (m.year + 1 <= end)]
    m = m[(m.population > 0) & (m.population_next > 0) & (m.income_pc > 0)]
    return pd.DataFrame(
        {"geo_id": m.geo_id, "year": m.year.astype("int64"),
         "growth": np.log(m.population_next / m.population), "log_income": np.log(m.income_pc)}
    ).sort_values(["year", "geo_id"]).reset_index(drop=True)


def window_panel(panel: pd.DataFrame, horizon: int, start: int, end: int) -> pd.DataFrame:
    """One row per unit and window start t: growth ln pop(t+horizon) - ln pop(t), income at t.
    A window is dropped if any one-year step inside it is flagged (county split)."""
    p = panel[["geo_id", "year", "population", "income_pc"]]
    nxt = p[["geo_id", "year", "population"]].assign(year=p.year - horizon)
    m = p.merge(nxt.rename(columns={"population": "population_end"}), on=["geo_id", "year"])
    m = m[(m.year >= start) & (m.year + horizon <= end)]
    bad = panel.loc[~_ok(panel), ["geo_id", "year"]].rename(columns={"year": "bad"})
    hits = m[["geo_id", "year"]].merge(bad, on="geo_id")
    hits = hits[(hits.year <= hits.bad) & (hits.bad < hits.year + horizon)][["geo_id", "year"]]
    m = m.merge(hits.drop_duplicates().assign(hit=True), on=["geo_id", "year"], how="left")
    m = m[m.hit.isna() & (m.population > 0) & (m.population_end > 0) & (m.income_pc > 0)]
    return pd.DataFrame(
        {"geo_id": m.geo_id, "start": m.year.astype("int64"),
         "growth": np.log(m.population_end / m.population), "log_income": np.log(m.income_pc)}
    ).sort_values(["start", "geo_id"]).reset_index(drop=True)


def rolling_betas(panel: pd.DataFrame, horizon: int, start: int, end: int) -> pd.DataFrame:
    """beta for every window start (one cross-section per start, HC1), as in the decade model."""
    return breaks.decade_betas(window_panel(panel, horizon, start, end), period="start")


@lru_cache
def andrews_critical_value(trim: float, level: float = 0.05) -> float:
    """Andrews (1993) critical value for sup-Wald with one restriction: the (1 - level) quantile
    of sup over pi in [trim, 1 - trim] of (W(pi) - pi W(1))^2 / (pi (1 - pi)), W a Brownian
    motion, simulated on a grid of 10,000 steps with 20,000 draws (fixed seed)."""
    grid, reps, chunk = 10_000, 20_000, 500
    rng = np.random.default_rng(0)
    pi = np.arange(1, grid + 1) / grid
    inside = (pi >= trim) & (pi <= 1 - trim)
    sups = []
    for _ in range(reps // chunk):
        w = np.cumsum(rng.standard_normal((chunk, grid)), axis=1) / np.sqrt(grid)
        bridge = w[:, inside] - pi[inside] * w[:, [-1]]
        sups.append((bridge**2 / (pi[inside] * (1 - pi[inside]))).max(axis=1))
    return float(np.quantile(np.concatenate(sups), 1 - level))


def candidate_positions(n_periods: int, trim: float) -> np.ndarray:
    """Positions of the first after-break period allowed: at least floor(trim * n) periods on
    each side."""
    k = max(1, int(np.floor(trim * n_periods)))
    return np.arange(k, n_periods - k + 1)


def _arrays(dp: pd.DataFrame, period: str = "year"):
    """Sorted periods, each row's period position, unit codes, log income and growth."""
    periods = np.sort(dp[period].unique())
    t = np.searchsorted(periods, dp[period].to_numpy())
    g = pd.factorize(dp.geo_id)[0]
    return periods, t, g, dp.log_income.to_numpy(float), dp.growth.to_numpy(float)


def _demean(t, x, y, w, nt):
    """Weighted within-period demeaning (w = how many times each row is drawn; 1 = no resampling).
    A period with no weight gets mean 0, and its rows contribute nothing downstream."""
    wt = np.bincount(t, w, nt)
    mx = np.divide(np.bincount(t, w * x, nt), wt, out=np.zeros(nt), where=wt > 0)
    my = np.divide(np.bincount(t, w * y, nt), wt, out=np.zeros(nt), where=wt > 0)
    return x - mx[t], y - my[t]


def _sums(t, xd, yd, w, nt):
    """Per-period sums of x'x, x'y and y'y on demeaned data."""
    return (np.bincount(t, w * xd * xd, nt), np.bincount(t, w * xd * yd, nt), np.bincount(t, w * yd * yd, nt))


def _ssr_candidates(sxx, sxy, syy, cand):
    """SSR and the two slopes for every candidate break position, from cumulative sums."""
    cxx, cxy = np.cumsum(sxx), np.cumsum(sxy)
    bxx, bxy = cxx[cand - 1], cxy[cand - 1]
    axx, axy = cxx[-1] - bxx, cxy[-1] - bxy
    with np.errstate(divide="ignore", invalid="ignore"):
        return syy.sum() - bxy**2 / bxx - axy**2 / axx, bxy / bxx, axy / axx


def _cluster_wald(t, g, xd, yd, c, b1, b2, n_periods) -> float:
    """Wald statistic for slope before = slope after, clustered by unit, with statsmodels'
    small-sample factor G/(G-1) * (N-1)/(N-K), K counting the period dummies."""
    before = t < c
    e = yd - np.where(before, b1, b2) * xd
    n_units, n, k = g.max() + 1, len(t), n_periods + 2
    u1 = np.bincount(g, np.where(before, xd * e, 0.0), n_units)
    u2 = np.bincount(g, np.where(before, 0.0, xd * e), n_units)
    s1, s2 = (xd[before] ** 2).sum(), (xd[~before] ** 2).sum()
    factor = n_units / (n_units - 1) * (n - 1) / (n - k)
    var = factor * ((u1 @ u1) / s1**2 + (u2 @ u2) / s2**2 - 2 * (u1 @ u2) / (s1 * s2))
    return float((b1 - b2) ** 2 / var)


def wald_statistic(dp: pd.DataFrame, break_year: int) -> float:
    """Clustered Wald statistic for a break starting in break_year (equal to breaks.chow_test
    with period="year")."""
    periods, t, g, x, y = _arrays(dp)
    xd, yd = _demean(t, x, y, np.ones(len(t)), len(periods))
    c = int(np.searchsorted(periods, break_year))
    sxx, sxy, _ = _sums(t, xd, yd, np.ones(len(t)), len(periods))
    b1, b2 = sxy[:c].sum() / sxx[:c].sum(), sxy[c:].sum() / sxx[c:].sum()
    return _cluster_wald(t, g, xd, yd, c, b1, b2, len(periods))


@dataclass(frozen=True)
class SingleBreak:
    break_year: int  # first year of the "after" segment (growth from break_year to break_year+1)
    at_edge: bool  # estimate on the first candidate: read as "at or before break_year"
    sup_wald: float
    critical_value: float  # Andrews 5%, one restriction, at this trim
    beta_before: float  # one-year growth slopes; x10 to compare with decade betas
    beta_after: float
    trim: float
    first_candidate: int
    last_candidate: int
    n_units: int
    first_year: int
    last_year: int


def sup_wald_break(dp: pd.DataFrame, trim: float = 0.15) -> SingleBreak:
    """Break year = lowest SSR over candidates (Bai-Perron); significance = the largest clustered
    Wald statistic over the same candidates, against Andrews' critical value."""
    periods, t, g, x, y = _arrays(dp)
    nt, ones = len(periods), np.ones(len(t))
    xd, yd = _demean(t, x, y, ones, nt)
    cand = candidate_positions(nt, trim)
    ssr, b1, b2 = _ssr_candidates(*_sums(t, xd, yd, ones, nt), cand)
    wald = [_cluster_wald(t, g, xd, yd, c, s1, s2, nt) for c, s1, s2 in zip(cand, b1, b2)]
    j = int(np.argmin(ssr))
    return SingleBreak(
        break_year=int(periods[cand[j]]), at_edge=j == 0, sup_wald=float(max(wald)),
        critical_value=andrews_critical_value(trim), beta_before=float(b1[j]), beta_after=float(b2[j]),
        trim=trim, first_candidate=int(periods[cand[0]]), last_candidate=int(periods[cand[-1]]),
        n_units=int(g.max() + 1), first_year=int(periods[0]), last_year=int(periods[-1]),
    )


# Bai (1997): quantiles of the break-date limiting distribution (symmetric case), by coverage
BAI_CRITICAL = {0.90: 7.7, 0.95: 11.0}
# Coverage rule for the bootstrap range (Plan 1b spec §6, as amended): at least COVERAGE_MIN of
# synthetic panels must have the planted year inside the 90% range. Above COVERAGE_MAX the range
# is conservative (common with sharp breaks, since years are whole numbers) but still used.
COVERAGE_MIN, COVERAGE_MAX = 0.80, 0.97


@dataclass(frozen=True)
class BreakRange:
    low: int
    high: int
    estimates: np.ndarray


def _estimate(t, x, y, w, nt, cand) -> int:
    """Position of the best-fitting break with rows weighted by w."""
    xd, yd = _demean(t, x, y, w, nt)
    ssr, _, _ = _ssr_candidates(*_sums(t, xd, yd, w, nt), cand)
    return int(cand[int(np.nanargmin(ssr))])


def bootstrap_break_year(dp: pd.DataFrame, trim: float = 0.15, draws: int = 999,
                         level: float = 0.90, seed: int = 0) -> BreakRange:
    """Resample whole units with replacement (keeping each unit's years together), re-estimate
    the break year each time, and return the middle `level` share of the estimates."""
    periods, t, g, x, y = _arrays(dp)
    nt, n_units = len(periods), g.max() + 1
    cand = candidate_positions(nt, trim)
    rng = np.random.default_rng(seed)
    est = np.empty(draws, dtype=int)
    for d in range(draws):
        w = np.bincount(rng.integers(0, n_units, n_units), minlength=n_units)[g].astype(float)
        est[d] = periods[_estimate(t, x, y, w, nt, cand)]
    a = (1 - level) / 2
    return BreakRange(int(np.floor(np.quantile(est, a))), int(np.ceil(np.quantile(est, 1 - a))), est)


def bai_interval(dp: pd.DataFrame, result: SingleBreak, level: float = 0.90) -> tuple[int, int]:
    """Bai (1997) interval for the break year: break_year +/- ceil(c / L), with
    L = delta^2 * Q^2 / Omega, delta the slope change, Q the mean per-year sum of demeaned x^2 and
    Omega the mean per-year sum of (x e)^2 (heteroskedasticity-robust across units; it ignores
    serial correlation, which the bootstrap keeps). Clipped to the sample years."""
    periods, t, _, x, y = _arrays(dp)
    nt, ones = len(periods), np.ones(len(t))
    xd, yd = _demean(t, x, y, ones, nt)
    c = int(np.searchsorted(periods, result.break_year))
    e = yd - np.where(t < c, result.beta_before, result.beta_after) * xd
    q = np.bincount(t, xd * xd, nt).mean()
    omega = np.bincount(t, (xd * e) ** 2, nt).mean()
    half = int(np.ceil(BAI_CRITICAL[level] / ((result.beta_after - result.beta_before) ** 2 * q**2 / omega)))
    return max(int(periods[0]), result.break_year - half), min(int(periods[-1]), result.break_year + half)


def range_coverage(dp: pd.DataFrame, result: SingleBreak, sims: int = 200, draws: int = 199,
                   level: float = 0.90, seed: int = 0) -> dict[str, float]:
    """Share of synthetic panels whose range contains the planted break. Each panel keeps the
    real units, years and incomes, plants the estimated break and slopes, and reuses the fitted
    residuals with a random sign per unit (keeping each unit's serial correlation)."""
    periods, t, g, x, y = _arrays(dp)
    nt, ones = len(periods), np.ones(len(t))
    xd, yd = _demean(t, x, y, ones, nt)
    c = int(np.searchsorted(periods, result.break_year))
    slope = np.where(t < c, result.beta_before, result.beta_after)
    resid = yd - slope * xd
    rng = np.random.default_rng(seed)
    hits = {"bootstrap": 0, "bai": 0}
    for s in range(sims):
        fake = dp.assign(growth=slope * xd + resid * rng.choice([-1.0, 1.0], g.max() + 1)[g])
        r = sup_wald_break(fake, result.trim)
        b = bootstrap_break_year(fake, result.trim, draws, level, seed=s)
        lo, hi = bai_interval(fake, r, level)
        hits["bootstrap"] += b.low <= result.break_year <= b.high
        hits["bai"] += lo <= result.break_year <= hi
    return {k: v / sims for k, v in hits.items()}


def demeaned_break_search(dp: pd.DataFrame, max_breaks: int = 3, min_segment: int = 5) -> breaks.BreakSearch:
    """breaks.break_search on annual data without the year dummies: demean once, then each set of
    breaks costs a few cumulative-sum lookups (about 100,000 sets for states in under a second).
    Same candidates, segment rule and BIC (the year effects still count as parameters)."""
    periods, t, _, x, y = _arrays(dp)
    nt, ones, n = len(periods), np.ones(len(t)), len(t)
    xd, yd = _demean(t, x, y, ones, nt)
    sxx, sxy, syy = _sums(t, xd, yd, ones, nt)
    cxx, cxy = np.concatenate([[0.0], np.cumsum(sxx)]), np.concatenate([[0.0], np.cumsum(sxy)])
    bic: dict[tuple[int, ...], float] = {}
    for k in range(max_breaks + 1):
        for combo in combinations(range(min_segment, nt - min_segment + 1), k):
            edges = [0, *combo, nt]
            if min(b - a for a, b in zip(edges[:-1], edges[1:])) < min_segment:
                continue
            ssr = syy.sum() - sum((cxy[b] - cxy[a]) ** 2 / (cxx[b] - cxx[a]) for a, b in zip(edges[:-1], edges[1:]))
            # parameters: year effects + one slope per segment + the break dates (Yao 1988)
            bic[tuple(int(periods[c]) for c in combo)] = n * np.log(ssr / n) + (nt + 2 * k + 1) * np.log(n)
    return breaks.BreakSearch(breaks=min(bic, key=bic.get), bic=bic)
