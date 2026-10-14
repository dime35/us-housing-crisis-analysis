"""Build processed analysis panels from data/interim (spec §4, processed panels)."""

import pandas as pd
from loguru import logger
import typer

from us_housing_crisis_analysis.config import (
    CROSSWALKS_DIR, INTERIM_DATA_DIR, METRO_LONGRUN_START, PROCESSED_DATA_DIR, RQ0B_END,
    RQ0B_STATE_START,
)
from us_housing_crisis_analysis.geography import county_to_cbsa, harmonize_county_fips

app = typer.Typer()
PANEL_COLUMNS = ["geo_id", "geo_name", "year", "population", "income_pc", "income_source"]


def _decades(start: int, end: int = RQ0B_END) -> list[int]:
    return list(range(start, end + 1, 10))


def _pick(df: pd.DataFrame, variable: str, years, level: str | None = None) -> pd.DataFrame:
    m = (df.variable == variable) & df.year.isin(list(years))
    if level:
        m &= df.geo_level == level
    return df[m]


def _assemble(pop: pd.DataFrame, income: pd.DataFrame) -> pd.DataFrame:
    """Left join income onto population, so missing income stays NaN (never 0)."""
    out = pop.merge(income, on=["geo_id", "year"], how="left")
    return out[PANEL_COLUMNS].sort_values(["geo_id", "year"]).reset_index(drop=True)


def map_territories(pop: pd.DataFrame) -> pd.DataFrame:
    """Give NHGIS territory rows (state:nhgis-G...) their later state's ID where the boundary
    already matched, from territory_to_state.csv, and sum (Oklahoma 1900 = two territories)."""
    t = pd.read_csv(CROSSWALKS_DIR / "territory_to_state.csv", dtype={"state_fips": str})
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
    income = income.assign(geo_id="cbsa:" + income.cbsa_code)[["geo_id", "year", "income_pc", "income_source"]]
    return _assemble(pop, income)


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


@app.command()
def main():
    read = lambda s: pd.read_parquet(INTERIM_DATA_DIR / f"{s}.parquet")  # noqa: E731
    nhgis, bea, manual, ipums, icpsr = (read(s) for s in ("nhgis", "bea", "manual", "ipums", "icpsr"))
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    panels = {
        "us_state_longrun": build_us_state_longrun(nhgis, bea, manual),
        "us_metro_longrun": build_us_metro_longrun(nhgis, ipums, icpsr, bea, county_to_cbsa()),
    }
    for name, df in panels.items():
        if df.duplicated(["geo_id", "year"]).any():
            raise ValueError(f"{name}: duplicate (geo_id, year) rows")
        df.to_parquet(PROCESSED_DATA_DIR / f"{name}.parquet", index=False)
        logger.success(f"{name}: {len(df):,} rows, {df.geo_id.nunique()} units")


if __name__ == "__main__":
    app()
