"""Build processed analysis panels from data/interim (spec §4, processed panels)."""

import pandas as pd
from loguru import logger
import typer

from us_housing_crisis_analysis.config import (
    CROSSWALKS_DIR, ENERGY_SHARE_MULTIPLE, ENERGY_SHARE_YEAR, INTERIM_DATA_DIR, METRO_LONGRUN_START,
    NETMIG_DECADES, PROCESSED_DATA_DIR, RQ0B_ANNUAL_END, RQ0B_ANNUAL_METRO_START,
    RQ0A_CITY_START, RQ0A_METRO_START, RQ0A_OVERLAP_TOLERANCE, RQ0B_ANNUAL_STATE_START, RQ0B_END,
    RQ0B_STATE_START,
)
from us_housing_crisis_analysis.geography import (
    county_to_cbsa, first_listed_state_fips, harmonize_county_fips, load_metro_main_city,
    load_old_cities, load_place_code_changes,
)

app = typer.Typer()
PANEL_COLUMNS = ["geo_id", "geo_name", "year", "population", "income_pc", "income_source"]


def _decades(start: int, end: int = RQ0B_END) -> list[int]:
    return list(range(start, end + 1, 10))


def _pick(df: pd.DataFrame, variable: str, years, level: str | None = None) -> pd.DataFrame:
    m = (df.variable == variable) & df.year.isin(list(years))
    if level:
        m &= df.geo_level == level
    return df[m]


def _assemble(pop: pd.DataFrame, income: pd.DataFrame, columns: list[str] = PANEL_COLUMNS) -> pd.DataFrame:
    """Left join income onto population, so missing income stays NaN (never 0)."""
    out = pop.merge(income, on=["geo_id", "year"], how="left")
    return out[columns].sort_values(["geo_id", "year"]).reset_index(drop=True)


# Counties created by splitting others (new county, parent, year); see geography.md
COUNTY_SPLITS_PATH = CROSSWALKS_DIR / "county_splits.csv"
METRO_COLUMNS = PANEL_COLUMNS + ["income_pc_wages_reported", "growth_comparable"]


def split_decades(cw: pd.DataFrame) -> set[tuple[str, int]]:
    """(cbsa_code, decade start) pairs whose growth to the next decade compares different areas:
    a county split off from a parent, and the two pieces are in different metros (or one is in
    none). Both metros are flagged for the decade containing the split."""
    splits = pd.read_csv(COUNTY_SPLITS_PATH, dtype={"new_fips": str, "parent_fips": str})
    cbsa = cw.set_index("county_fips").cbsa_code
    flagged = set()
    for s in splits.itertuples():
        new_area, parent_area = cbsa.get(s.new_fips), cbsa.get(s.parent_fips)  # None = no metro
        if new_area != parent_area:
            decade = s.split_year // 10 * 10  # the split falls between this census and the next
            flagged |= {(a, decade) for a in (new_area, parent_area) if a is not None}
    return flagged


# NHGIS 1900 "Persons in the Military" abroad: not a place, so not a panel unit
MILITARY_GEO_ID = "state:nhgis-G999"


def map_territories(pop: pd.DataFrame) -> pd.DataFrame:
    """Give NHGIS territory rows (state:nhgis-G...) their later state's ID where the boundary
    already matched, from territory_to_state.csv, and sum (Oklahoma 1900 = two territories)."""
    t = pd.read_csv(CROSSWALKS_DIR / "territory_to_state.csv", dtype={"state_fips": str})
    pop = pop[pop.geo_id != MILITARY_GEO_ID]
    code = pop.geo_id.str.removeprefix("state:nhgis-")
    m = pop.assign(nhgis_code=code).merge(t[["nhgis_code", "state_fips", "from_year"]], on="nhgis_code", how="left")
    mapped = m.state_fips.notna() & (m.year >= m.from_year)
    m.loc[mapped, "geo_id"] = "state:" + m.loc[mapped, "state_fips"]
    names = pop[~pop.geo_id.str.startswith("state:nhgis-")].groupby("geo_id").geo_name.first()
    m.loc[mapped, "geo_name"] = m.loc[mapped, "geo_id"].map(names).fillna(m.loc[mapped, "geo_name"])
    return m.groupby(["geo_id", "year"], as_index=False).agg(geo_name=("geo_name", "first"), population=("population", "sum"))


def build_us_state_longrun(nhgis: pd.DataFrame, bea: pd.DataFrame, manual: pd.DataFrame) -> pd.DataFrame:
    years = _decades(RQ0B_STATE_START)
    pop = _pick(nhgis, "population", years, "state")[["geo_id", "geo_name", "year", "value"]]
    pop = map_territories(pop.rename(columns={"value": "population"}))
    income = pd.concat(
        [
            _pick(manual, "income_pc_klein", range(1880, 1911, 10)).assign(income_source="klein"),
            _pick(manual, "income_pc_easterlin", [1920]).assign(income_source="easterlin"),
            _pick(bea, "income_pc", [y for y in years if y >= 1930], "state").assign(income_source="bea"),
        ]
    )[["geo_id", "year", "value", "income_source"]].rename(columns={"value": "income_pc"})
    return _assemble(pop, income)


def _counties(df: pd.DataFrame, variable: str, years) -> pd.DataFrame:
    c = _pick(df, variable, years, "county")
    return pd.DataFrame({"county_fips": c.geo_id.str.removeprefix("county:"), "year": c.year, "value": c.value})


def _drop_unplaced(c: pd.DataFrame) -> pd.DataFrame:
    """Drop codes still without a FIPS successor after harmonizing (see unmatched_county_report)."""
    return c[~c.county_fips.str.startswith("nhgis-")]


def county_series(df: pd.DataFrame, variable: str, years) -> pd.DataFrame:
    """County values with historical codes (including NHGIS-only territory counties) mapped to
    successors and summed (counts only)."""
    c = _drop_unplaced(harmonize_county_fips(_counties(df, variable, years)))
    return c.groupby(["county_fips", "year"], as_index=False)["value"].sum()


# State-years where a large population had no county geography, so metros there can't be built
# from counties: Indian Territory's nations (1900; Oklahoma's 1907 counties cut across them).
INCOMPLETE_STATE_YEARS = [("40", 1900)]


def _drop_incomplete(pop: pd.DataFrame, pop_c: pd.DataFrame, cw: pd.DataFrame) -> pd.DataFrame:
    """Drop metro-years (state-years in INCOMPLETE_STATE_YEARS) where any of the metro's counties
    in that state has no count, rather than report a partial population."""
    drop = set()
    for state, year in INCOMPLETE_STATE_YEARS:
        counted = set(pop_c.loc[pop_c.year == year, "county_fips"])
        missing = cw[cw.county_fips.str.startswith(state) & ~cw.county_fips.isin(counted)]
        drop |= {(code, year) for code in missing.cbsa_code}
    keep = [(c, y) not in drop for c, y in zip(pop.cbsa_code, pop.year)]
    return pop[keep]


def build_us_metro_longrun(
    nhgis: pd.DataFrame, ipums: pd.DataFrame, icpsr: pd.DataFrame, bea: pd.DataFrame,
    crosswalk: pd.DataFrame,
) -> pd.DataFrame:
    years = _decades(METRO_LONGRUN_START)
    cw = crosswalk[["county_fips", "cbsa_code", "cbsa_title"]]

    def to_cbsa(series: pd.DataFrame) -> pd.DataFrame:
        return series.merge(cw, on="county_fips", how="inner")

    pop_c = to_cbsa(county_series(nhgis, "population", years))
    pop = pop_c.groupby(["cbsa_code", "cbsa_title", "year"], as_index=False)["value"].sum()
    pop = _drop_incomplete(pop, pop_c, cw)
    pop = pd.DataFrame({"geo_id": "cbsa:" + pop.cbsa_code, "geo_name": pop.cbsa_title,
                        "year": pop.year, "population": pop.value})

    # 1940: total wages / total persons across the metro's counties
    wages = to_cbsa(county_series(ipums, "wage_income_total", [1940])).groupby("cbsa_code")["value"].sum()
    persons = to_cbsa(county_series(ipums, "persons_ipums", [1940])).groupby("cbsa_code")["value"].sum()
    inc1940 = (wages / persons).rename("income_pc").reset_index().assign(year=1940, income_source="ipums_1940_wages")
    # Robustness variant: people with a missing wage (999998) left out of the denominator instead
    # of counted as earning 0. Missing counts are built per county (share x persons) before summing.
    miss = _counties(ipums, "wage_missing_share", [1940]).merge(
        _counties(ipums, "persons_ipums", [1940]), on=["county_fips", "year"], suffixes=("_share", "_persons"))
    miss = _drop_unplaced(harmonize_county_fips(miss.assign(value=miss.value_share * miss.value_persons)))
    missing = to_cbsa(miss[["county_fips", "year", "value"]]).groupby("cbsa_code")["value"].sum()
    reported = persons.sub(missing, fill_value=0)
    inc1940 = inc1940.merge((wages / reported).rename("income_pc_wages_reported").reset_index(), on="cbsa_code")

    # 1950-1960: county medians cannot be summed; use the population-weighted mean (approximation).
    # Weight at the original county code, before harmonizing, so merged counties average
    # rather than add their medians.
    med = _counties(icpsr, "median_family_income", [1950, 1960])
    w = _counties(nhgis, "population", [1950, 1960]).rename(columns={"value": "w"})
    med = med.merge(w, on=["county_fips", "year"])
    med = _drop_unplaced(harmonize_county_fips(med.assign(vw=med.value * med.w)))
    med = to_cbsa(med).groupby(["cbsa_code", "year"])[["vw", "w"]].sum()
    inc5060 = (med.vw / med.w).rename("income_pc").reset_index().assign(income_source="census_median_family_income")

    # 1970+: BEA county personal income / BEA county population, summed over the metro's counties
    # (BEA's own MSA level fails in the API, D-23; this also keeps every year on the same counties)
    bea_years = [y for y in years if y >= 1970]
    pi = to_cbsa(county_series(bea, "personal_income", bea_years)).groupby(["cbsa_code", "year"])["value"].sum()
    bpop = to_cbsa(county_series(bea, "population_bea", bea_years)).groupby(["cbsa_code", "year"])["value"].sum()
    inc_bea = (pi / bpop).rename("income_pc").reset_index().assign(income_source="bea")

    income = pd.concat([inc1940, inc5060, inc_bea], ignore_index=True)
    # The variant differs from income_pc only in 1940
    income["income_pc_wages_reported"] = income.income_pc_wages_reported.fillna(income.income_pc)
    income = income.assign(geo_id="cbsa:" + income.cbsa_code)[
        ["geo_id", "year", "income_pc", "income_source", "income_pc_wages_reported"]]
    flagged = split_decades(cw)
    income_and_flags = income.merge(pop[["geo_id", "year"]], on=["geo_id", "year"], how="right")
    income_and_flags["growth_comparable"] = [
        (g.removeprefix("cbsa:"), y) not in flagged for g, y in zip(income_and_flags.geo_id, income_and_flags.year)]
    return _assemble(pop, income_and_flags, METRO_COLUMNS)


def unmatched_county_report(nhgis: pd.DataFrame) -> pd.DataFrame:
    """County rows whose (harmonized) code is not a 2020 county: the population that a
    county-based metro build cannot place. Review the largest and extend county_fixes.csv."""
    c = nhgis[(nhgis.geo_level == "county") & (nhgis.variable == "population")]
    c = pd.DataFrame({"county_fips": c.geo_id.str.removeprefix("county:"), "year": c.year, "population": c.value})
    c = harmonize_county_fips(c)
    modern = set(c.loc[c.year == 2020, "county_fips"])
    totals = c.groupby("year").population.sum()
    bad = c[~c.county_fips.isin(modern)]
    return pd.DataFrame(
        {"year": bad.year, "county_id": bad.county_fips, "population": bad.population,
         "share_of_us": bad.population / bad.year.map(totals)}
    ).sort_values(["year", "population"], ascending=[True, False]).reset_index(drop=True)


METRO_ANNUAL_COLUMNS = PANEL_COLUMNS + ["growth_comparable"]


def build_us_state_annual(bea: pd.DataFrame) -> pd.DataFrame:
    """State x year from BEA alone: SAINC1 population and per capita income, 1929-2024. Alaska and
    Hawaii start in 1950 (BEA's earlier zeros are dropped at parse time, D-24)."""
    years = range(RQ0B_ANNUAL_STATE_START, RQ0B_ANNUAL_END + 1)
    pop = _pick(bea, "population_bea", years, "state")[["geo_id", "geo_name", "year", "value"]]
    income = _pick(bea, "income_pc", years, "state")[["geo_id", "year", "value"]]
    return _assemble(pop.rename(columns={"value": "population"}),
                     income.rename(columns={"value": "income_pc"}).assign(income_source="bea"))


def split_growth_years(cw: pd.DataFrame, first_year: pd.Series, start: int) -> set[tuple[str, int]]:
    """(cbsa_code, t) pairs whose one-year growth t -> t+1 compares different areas: a county split
    off across a metro line first appears in the data in year t+1 (which can differ from the legal
    split date). Splits before `start` are already in place when the panel begins."""
    splits = pd.read_csv(COUNTY_SPLITS_PATH, dtype={"new_fips": str, "parent_fips": str})
    cbsa = cw.set_index("county_fips").cbsa_code
    flagged = set()
    for s in splits.itertuples():
        if s.split_year < start or s.new_fips not in first_year.index:
            continue
        new_area, parent_area = cbsa.get(s.new_fips), cbsa.get(s.parent_fips)  # None = no metro
        if new_area != parent_area:
            t = int(first_year[s.new_fips]) - 1
            flagged |= {(a, t) for a in (new_area, parent_area) if a is not None}
    return flagged


def build_us_metro_annual(bea: pd.DataFrame, crosswalk: pd.DataFrame) -> pd.DataFrame:
    """Metro (2023 CBSA) x year, 1969-2024: BEA county personal income and population summed over
    the metro's counties (D-23), income = sum of income / sum of population."""
    years = range(RQ0B_ANNUAL_METRO_START, RQ0B_ANNUAL_END + 1)
    cw = crosswalk[["county_fips", "cbsa_code", "cbsa_title"]]
    pop_c = county_series(bea, "population_bea", years)
    first_year = pop_c.groupby("county_fips").year.min()
    pop = pop_c.merge(cw, on="county_fips").groupby(["cbsa_code", "cbsa_title", "year"], as_index=False)["value"].sum()
    pi = county_series(bea, "personal_income", years).merge(cw, on="county_fips")
    pi = pi.groupby(["cbsa_code", "year"], as_index=False)["value"].sum().rename(columns={"value": "pi"})
    m = pop.merge(pi, on=["cbsa_code", "year"], how="left")
    flagged = split_growth_years(cw, first_year, RQ0B_ANNUAL_METRO_START)
    out = pd.DataFrame(
        {
            "geo_id": "cbsa:" + m.cbsa_code, "geo_name": m.cbsa_title, "year": m.year.astype("int64"),
            "population": m.value, "income_pc": m.pi / m.value, "income_source": "bea",
            "growth_comparable": [(c, y) not in flagged for c, y in zip(m.cbsa_code, m.year)],
        }
    )
    return out[METRO_ANNUAL_COLUMNS].sort_values(["geo_id", "year"]).reset_index(drop=True)


def energy_states(bea: pd.DataFrame) -> pd.DataFrame:
    """Plan 1b spec 4.3: a state is an energy state if its mining share of earnings in
    ENERGY_SHARE_YEAR is at least ENERGY_SHARE_MULTIPLE x the national share. The national share
    sums the states that report both values; a suppressed mining value means not an energy state."""
    total = _pick(bea, "earnings_total", [ENERGY_SHARE_YEAR], "state").set_index("geo_id")
    mining = _pick(bea, "earnings_mining", [ENERGY_SHARE_YEAR], "state").set_index("geo_id").value
    mining = mining.reindex(total.index)
    national = mining.sum() / total.value[mining.notna()].sum()
    share = mining / total.value
    out = pd.DataFrame({"state_fips": total.index.str.removeprefix("state:"), "state_name": total.geo_name,
                        "mining_share": share, "ratio": share / national})
    out["energy"] = (out.ratio >= ENERGY_SHARE_MULTIPLE).fillna(False).astype(bool)
    return out.sort_values("ratio", ascending=False).reset_index(drop=True)


def drop_states(panel: pd.DataFrame, fips: set[str]) -> pd.DataFrame:
    """Remove states in `fips`, or metros whose first listed state is in `fips`."""
    is_state = panel.geo_id.str.startswith("state:")
    state = panel.geo_id.str[6:8].where(is_state, first_listed_state_fips(panel.geo_name))
    return panel[~state.isin(fips)]


def build_us_state_net_migration(longrun: pd.DataFrame, netmig: pd.DataFrame) -> pd.DataFrame:
    """State x decade (Plan 1c): census population at both ends, income at the start, county net
    migration summed to the state. Rates are simple percent changes of the starting population,
    so total = migration + natural exactly. A state missing net migration for a decade drops out
    of that decade only.

    natural_rate is the residual (total - migration): natural increase plus any change in census
    coverage between the two counts. Nationally it is within 5% of NCHS births minus deaths except
    in the 1970s, 1980s and 1990s (ratios 1.23 / 0.91 / 1.20), when census coverage improved,
    worsened and improved again."""
    nm = netmig[(netmig.variable == "net_migration") & (netmig.geo_level == "county")]
    nm = (nm.assign(geo_id="state:" + nm.geo_id.str[7:9]).groupby(["geo_id", "year"], as_index=False)["value"].sum()
          .rename(columns={"value": "net_migration"}))
    p = longrun[["geo_id", "geo_name", "year", "population", "income_pc"]]
    nxt = p[["geo_id", "year", "population"]].assign(year=p.year - 10).rename(columns={"population": "population_next"})
    m = p.merge(nxt, on=["geo_id", "year"]).merge(nm, on=["geo_id", "year"])
    m = m[m.year.isin(list(NETMIG_DECADES)) & (m.population > 0)]
    total = (m.population_next - m.population) / m.population
    migration = m.net_migration / m.population
    out = m.rename(columns={"year": "decade"}).assign(
        total_rate=total, migration_rate=migration, natural_rate=total - migration)
    cols = ["geo_id", "geo_name", "decade", "population", "population_next", "income_pc", "net_migration",
            "total_rate", "migration_rate", "natural_rate"]
    return out[cols].sort_values(["geo_id", "decade"]).reset_index(drop=True)


# --- RQ0a (Plan 2): main city, metro and suburbs by decade ---
CITY_METRO_COLUMNS = [
    "geo_id", "geo_name", "year", "city_fips", "city_name", "headline", "city_population",
    "metro_population", "suburb_population", "core_population", "metro_central_population",
    "city_land_sqmi", "growth_comparable", "central_growth_comparable",
]


def _places(df: pd.DataFrame, variable: str, years) -> pd.DataFrame:
    c = _pick(df, variable, years, "city")
    return pd.DataFrame({"place_fips": c.geo_id.str.removeprefix("place:").to_numpy(),
                         "year": c.year.to_numpy(), "value": c.value.to_numpy()})


def apply_place_code_changes(places: pd.DataFrame, changes: pd.DataFrame) -> pd.DataFrame:
    """Put each value under its 2010 place code (CESTA's key). A row of place_code_changes.csv says
    that in `year` the value for `place_fips` is the sum of the listed `source_fips` (Louisville
    2020 = balance + old city). A place's own row in a listed year counts only if it is listed."""
    m = places.merge(changes[["place_fips", "year", "source_fips"]].rename(columns={"place_fips": "target"}),
                     left_on=["place_fips", "year"], right_on=["source_fips", "year"], how="left")
    listed = set(zip(changes.place_fips, changes.year))
    own = [(p, y) in listed and pd.isna(t) for p, y, t in zip(m.place_fips, m.year, m.target)]
    m = m[~pd.Series(own, index=m.index, dtype=bool)]
    m = m.assign(place_fips=m.target.fillna(m.place_fips))
    return m.groupby(["place_fips", "year"], as_index=False)["value"].sum()


def city_population(cesta: pd.DataFrame, nhgis: pd.DataFrame, changes: pd.DataFrame) -> pd.DataFrame:
    """CESTA 1900-2010; NHGIS AV0 for 2020, used only where AV0 and CESTA agree in 2010 within
    RQ0A_OVERLAP_TOLERANCE (both must measure the same place: the Honolulu CDP was redefined)."""
    c = _places(cesta, "population", _decades(RQ0A_CITY_START, 2010))
    a = apply_place_code_changes(_places(nhgis, "population", [2010, 2020]), changes)
    c10 = c[c.year == 2010].set_index("place_fips").value
    a10 = a[a.year == 2010].set_index("place_fips").value.reindex(c10.index)
    agree = set(c10.index[((a10 / c10) - 1).abs() <= RQ0A_OVERLAP_TOLERANCE])
    dropped = sorted((set(a.loc[a.year == 2020, "place_fips"]) & set(c10.index)) - agree)
    if dropped:
        logger.info(f"2020 city counts not used (2010 sources disagree): {dropped}")
    return pd.concat([c, a[(a.year == 2020) & a.place_fips.isin(agree)]], ignore_index=True)


def city_land_area(wp27: pd.DataFrame, gazetteer: pd.DataFrame, changes: pd.DataFrame) -> pd.DataFrame:
    """One source per year: Working Paper 27 for 1950-1980 (top-100 places only), Gazetteers for
    1990-2020 (every place; WP27's 1990 table is a check)."""
    w = _places(wp27, "land_area", [1950, 1960, 1970, 1980])
    g = apply_place_code_changes(_places(gazetteer, "land_area", [1990, 2000, 2010, 2020]), changes)
    return pd.concat([w, g], ignore_index=True)


def build_us_city_metro(
    cesta: pd.DataFrame, nhgis: pd.DataFrame, wp27: pd.DataFrame, gazetteer: pd.DataFrame,
    metro_longrun: pd.DataFrame, crosswalk: pd.DataFrame, main_city: pd.DataFrame,
    old_cities: pd.DataFrame, changes: pd.DataFrame,
) -> pd.DataFrame:
    """Metro x decade (RQ0a spec §2): the main city, the metro (from 1940), the suburbs (metro -
    city), the core (all the metro's 1950 top-100 cities with a CESTA series; missing if any of them
    is), the metro's central counties, and the city's land area. growth_comparable (and its
    central-counties twin) is False for a decade whose growth to the next compares different areas
    because a county split crosses the line (D-27)."""
    years = _decades(RQ0A_CITY_START)
    grid = main_city.rename(columns={"place_fips": "city_fips"}).merge(pd.DataFrame({"year": years}), how="cross")
    grid["geo_id"] = "cbsa:" + grid.cbsa_code
    pop = city_population(cesta, nhgis, changes).rename(columns={"place_fips": "city_fips", "value": "city_population"})
    area = city_land_area(wp27, gazetteer, changes).rename(columns={"place_fips": "city_fips", "value": "city_land_sqmi"})
    out = grid.merge(pop, on=["city_fips", "year"], how="left").merge(area, on=["city_fips", "year"], how="left")

    m = metro_longrun[metro_longrun.year >= RQ0A_METRO_START][["geo_id", "year", "population"]]
    out = out.merge(m.rename(columns={"population": "metro_population"}), on=["geo_id", "year"], how="left")
    out["suburb_population"] = out.metro_population - out.city_population

    old = old_cities[old_cities.in_cesta.astype(bool)][["place_fips", "cbsa_code"]]
    core = old.merge(pop.rename(columns={"city_fips": "place_fips"}), on="place_fips")
    n_old = old.groupby("cbsa_code").size()
    core = core.groupby(["cbsa_code", "year"]).city_population.agg(["sum", "size"]).reset_index()
    core = core[core["size"] == core.cbsa_code.map(n_old)]
    out = out.merge(core[["cbsa_code", "year", "sum"]].rename(columns={"sum": "core_population"}),
                    on=["cbsa_code", "year"], how="left")

    central = crosswalk[crosswalk.central.astype(bool)][["county_fips", "cbsa_code"]]
    cpop = county_series(nhgis, "population", _decades(RQ0A_METRO_START)).merge(central, on="county_fips")
    cpop = cpop.groupby(["cbsa_code", "year"], as_index=False)["value"].sum()
    out = out.merge(cpop.rename(columns={"value": "metro_central_population"}), on=["cbsa_code", "year"], how="left")

    flagged, flagged_central = split_decades(crosswalk), split_decades(central)
    out["growth_comparable"] = [(c, y) not in flagged for c, y in zip(out.cbsa_code, out.year)]
    out["central_growth_comparable"] = [(c, y) not in flagged_central for c, y in zip(out.cbsa_code, out.year)]
    out = out.rename(columns={"cbsa_title": "geo_name"})
    return out[CITY_METRO_COLUMNS].sort_values(["geo_id", "year"]).reset_index(drop=True)


@app.command()
def main():
    read = lambda s: pd.read_parquet(INTERIM_DATA_DIR / f"{s}.parquet")  # noqa: E731
    nhgis, bea, manual, ipums, icpsr, netmig = (read(s) for s in ("nhgis", "bea", "manual", "ipums", "icpsr", "netmig"))
    cesta, wp27, gaz = (read(s) for s in ("cesta", "wp27", "gazetteer"))
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    panels = {
        "us_state_longrun": build_us_state_longrun(nhgis, bea, manual),
        "us_metro_longrun": build_us_metro_longrun(nhgis, ipums, icpsr, bea, county_to_cbsa()),
        "us_state_annual": build_us_state_annual(bea),
        "us_metro_annual": build_us_metro_annual(bea, county_to_cbsa()),
    }
    panels["us_state_net_migration"] = build_us_state_net_migration(panels["us_state_longrun"], netmig)
    panels["us_city_metro"] = build_us_city_metro(
        cesta, nhgis, wp27, gaz, panels["us_metro_longrun"], county_to_cbsa(), load_metro_main_city(),
        load_old_cities(), load_place_code_changes())
    for name, df in panels.items():
        if df.duplicated(["geo_id", "decade" if "decade" in df else "year"]).any():
            raise ValueError(f"{name}: duplicate (geo_id, year) rows")
        df.to_parquet(PROCESSED_DATA_DIR / f"{name}.parquet", index=False)
        logger.success(f"{name}: {len(df):,} rows, {df.geo_id.nunique()} units")


if __name__ == "__main__":
    app()
