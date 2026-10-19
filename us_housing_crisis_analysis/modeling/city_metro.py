"""RQ0a (Plan 2): did US cities stall, or did their metros? Growth by period, keep-up classes,
annexing flags, and the three preset answers with unit-resampling ranges (spec 2026-10-18 §4).
Class names describe growth patterns, not moves (D-29)."""

import numpy as np
import pandas as pd

from us_housing_crisis_analysis.config import (
    RQ0A_ABSOLUTE_RATE,
    RQ0A_ANNEX_THRESHOLD,
    RQ0A_BAR_FRACTION,
    RQ0A_PERIODS,
)
from us_housing_crisis_analysis.geography import first_listed_state_fips, state_divisions

# A value equal to a bar up to floating-point noise counts as reaching it (spec §4.1)
EPS = 1e-9
CLASSES = {(1.0, 1.0): "growing", (0.0, 1.0): "suburbanizing", (0.0, 0.0): "stagnant",
           (1.0, 0.0): "city-led"}


def us_growth(state_longrun: pd.DataFrame, states, periods=RQ0A_PERIODS) -> dict[tuple[int, int], float]:
    """US population growth over each period, summing only `states` (FIPS codes: 50 states + DC)."""
    s = state_longrun[state_longrun.geo_id.str.removeprefix("state:").isin(set(states))]
    total = s.groupby("year").population.sum()
    return {(a, b): float(total[b] / total[a] - 1) for a, b in periods}


def keep_up_bar(start: int, end: int, yardstick: str, us: dict, fraction: float = RQ0A_BAR_FRACTION) -> float:
    if yardstick == "relative":
        return fraction * us[(start, end)]
    if yardstick == "absolute":
        return (1 + RQ0A_ABSOLUTE_RATE) ** ((end - start) / 10) - 1
    raise ValueError(f"unknown yardstick {yardstick!r}")


def keeps_up(growth: pd.Series, bar) -> pd.Series:
    """1.0 = keeps up (growth at or above the bar), 0.0 = falls behind, NaN = no growth figure."""
    return (growth >= bar - EPS).astype(float).where(growth.notna())


def period_growth(panel: pd.DataFrame, periods=RQ0A_PERIODS, central: bool = False) -> pd.DataFrame:
    """One row per metro x period: growth (end / start - 1) of the city, the metro, the suburbs and
    the core. Metro and suburb growth are NaN when a county split crosses the metro's line in any
    decade of the period (D-27). central=True uses the metro's central counties."""
    metro_col, flag_col = (("metro_central_population", "central_growth_comparable") if central
                           else ("metro_population", "growth_comparable"))
    p = panel.assign(city=panel.city_population, metro=panel[metro_col],
                     suburb=panel[metro_col] - panel.city_population, core=panel.core_population)
    parts = []
    for start, end in periods:
        a = p[p.year == start].set_index("geo_id")
        b = p[p.year == end].set_index("geo_id").reindex(a.index)
        g = pd.DataFrame(index=a.index)
        for col in ("city", "metro", "suburb", "core"):
            g[col] = b[col] / a[col].where(a[col] > 0) - 1
        inside = p[(p.year >= start) & (p.year < end)]
        ok = inside.groupby("geo_id")[flag_col].all().reindex(a.index, fill_value=False).astype(bool)
        g.loc[~ok, ["metro", "suburb"]] = np.nan
        parts.append(g.assign(start=start, end=end).reset_index())
    return pd.concat(parts, ignore_index=True)


def classify(growth: pd.DataFrame, us: dict, yardstick: str = "relative",
             fraction: float = RQ0A_BAR_FRACTION, city_col: str = "city") -> pd.DataFrame:
    """Adds city_keeps and metro_keeps (1 / 0 / NaN) and the class (missing unless both are known)."""
    bar = pd.Series([keep_up_bar(s, e, yardstick, us, fraction) for s, e in zip(growth.start, growth.end)],
                    index=growth.index)
    out = growth.assign(city_keeps=keeps_up(growth[city_col], bar), metro_keeps=keeps_up(growth.metro, bar))
    out["class"] = [CLASSES.get((c, m)) for c, m in zip(out.city_keeps, out.metro_keeps)]
    return out


def core_recovery(classes: pd.DataFrame) -> pd.Series:
    """True where the city keeps up in a period after falling behind in an earlier one."""
    c = classes.sort_values(["geo_id", "start"])
    fell = c.city_keeps.eq(0.0)
    earlier = fell.groupby(c.geo_id).transform(lambda s: s.shift(fill_value=False).cummax()).astype(bool)
    return (c.city_keeps.eq(1.0) & earlier).reindex(classes.index)


def annexing(area: pd.DataFrame, start: int, end: int, threshold: float = RQ0A_ANNEX_THRESHOLD,
             consolidations: pd.DataFrame | None = None) -> pd.Series:
    """Per city (rows of `area`, columns = census years, sq mi): "annexing" if the area at `end` is
    more than `threshold` above `start`, or the city consolidated with its county in (start, end].
    Area is taken never to shrink materially (spec §3.4), so with the latest known area at or before
    `start` and the earliest at or after `end`: growth no larger than the threshold over that span
    means "fixed"; a larger gain means "annexing" only if the span is exactly the period, and
    "unknown" otherwise (it could fall outside the period). No area on either side: "unknown"."""
    merged = set()
    if consolidations is not None:
        c = consolidations
        merged = set(c.loc[(c.year > start) & (c.year <= end), "place_fips"])
    area = area.reindex(columns=sorted(area.columns))
    out = {}
    for place, a in area.iterrows():
        a = a.dropna()
        before, after = a[a.index <= start], a[a.index >= end]
        if place in merged:
            out[place] = "annexing"
        elif before.empty or after.empty:
            out[place] = "unknown"
        elif after.iloc[0] <= before.iloc[-1] * (1 + threshold):
            out[place] = "fixed"
        elif before.index[-1] == start and after.index[0] == end:
            out[place] = "annexing"
        else:
            out[place] = "unknown"
    return pd.Series(out, name="annexing", dtype=object)


def annexing_by_metro(panel: pd.DataFrame, start: int, end: int, threshold: float = RQ0A_ANNEX_THRESHOLD,
                      consolidations: pd.DataFrame | None = None) -> pd.Series:
    """annexing() for each metro's main city, indexed by geo_id."""
    p = panel.dropna(subset=["city_fips"]).drop_duplicates(["city_fips", "year"])
    area = p.pivot(index="city_fips", columns="year", values="city_land_sqmi")
    flags = annexing(area, start, end, threshold, consolidations)
    return panel.drop_duplicates("geo_id").set_index("geo_id").city_fips.map(flags)


def regions(panel: pd.DataFrame) -> pd.Series:
    """geo_id -> "Northeast + Midwest" (census divisions 1-4) or "South + West", by the metro's
    first-listed state."""
    names = panel.drop_duplicates("geo_id").set_index("geo_id").geo_name
    division = first_listed_state_fips(names).map(state_divisions())
    return pd.Series(np.where(division <= 4, "Northeast + Midwest", "South + West"),
                     index=names.index).where(division.notna())


def units(panel: pd.DataFrame, us: dict, *, yardstick: str = "relative", fraction: float = RQ0A_BAR_FRACTION,
          threshold: float = RQ0A_ANNEX_THRESHOLD, core: bool = False, central: bool = False,
          consolidations: pd.DataFrame | None = None, periods=RQ0A_PERIODS) -> pd.DataFrame:
    """One row per headline metro with, for each period start s: city_s and metro_s (1 keeps up,
    0 falls behind, NaN unknown) and annex_s. core=True puts all the metro's old cities in place of
    the main city; central=True uses central counties for the metro. One row carries every period,
    so resampling rows keeps the same metros in all periods."""
    hp = panel[panel.headline.astype(bool)]
    c = classify(period_growth(hp, periods, central=central), us, yardstick, fraction,
                 city_col="core" if core else "city")
    out = pd.DataFrame(index=pd.Index(sorted(hp.geo_id.unique()), name="geo_id"))
    for start, end in periods:
        k = c[c.start == start].set_index("geo_id")
        out[f"city_{start}"] = k.city_keeps
        out[f"metro_{start}"] = k.metro_keeps
        out[f"annex_{start}"] = annexing_by_metro(hp, start, end, threshold, consolidations)
    out["city_pop_1950"] = hp[hp.year == 1950].set_index("geo_id").city_population
    out["region"] = regions(hp)
    return out.reset_index()
