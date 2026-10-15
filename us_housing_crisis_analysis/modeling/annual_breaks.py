"""RQ0b with annual data: rolling-window betas and dating the break (Plan 1b spec §4).

Annual model, for unit i (state or metro) and year t:
    growth_{i,t} = ln pop(t+1) - ln pop(t) = alpha_t + beta_seg(t) * log_income_{i,t} + e_{i,t}
Year fixed effects are removed by demeaning growth and log income within year once. That is exact
(Frisch-Waugh-Lovell): every year lies wholly inside one segment, so the segment slopes are
estimated on the demeaned data, and each candidate break is a closed-form fit."""

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
