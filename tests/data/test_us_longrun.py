import numpy as np
import pandas as pd
import pytest

from us_housing_crisis_analysis.config import CROSSWALKS_DIR, RAW_DATA_DIR, REFERENCES_DIR
from us_housing_crisis_analysis import features, geography
from us_housing_crisis_analysis.sources import census_pep

pytestmark = pytest.mark.data


def state_pop(interim, year):
    d = interim("nhgis")
    return d[(d.geo_level == "state") & (d.variable == "population") & (d.year == year)]


def test_us_population_2020(interim):
    s = state_pop(interim, 2020)
    assert s[s.geo_id != "state:72"].value.sum() == 331_449_281


def test_us_population_1880(interim):
    assert state_pop(interim, 1880).value.sum() == pytest.approx(50_189_209, rel=1e-3)


@pytest.mark.parametrize("row", pd.read_csv(REFERENCES_DIR / "known_values.csv").to_dict("records"))
def test_known_values(processed, row):
    p = processed(row["dataset"]).set_index(["geo_id", "year"])
    assert p.loc[(row["geo_id"], row["year"]), row["variable"]] == pytest.approx(row["value"], rel=row["rel_tol"])


def ct_cbsas() -> set[str]:
    cw = geography.county_to_cbsa()
    return set("cbsa:" + cw[cw.county_fips.str.startswith("09")].cbsa_code)


def test_cbsa_2020_population_matches_census_base(interim, processed):
    ours = processed("us_metro_longrun").query("year == 2020").set_index("geo_id").population
    base = interim("census_pep").set_index("geo_id").value
    rel = ((ours - base) / base).drop(ct_cbsas(), errors="ignore").dropna()
    assert len(rel) > 350
    assert rel.abs().max() < 0.01, rel.abs().sort_values().tail()
    assert rel.abs().median() < 0.001


def test_county_membership_matches_census():
    path = RAW_DATA_DIR / "census_pep" / "cbsa-est2023-alldata.csv"
    if not path.exists():
        pytest.skip("census_pep not downloaded")
    theirs = census_pep.parse_county_membership(path)
    # The Census file covers metros and micros but not Puerto Rico; Connecticut differs by design
    skip = lambda d: d[~d.county_fips.str[:2].isin(["09", "72"])]  # noqa: E731
    ours, theirs = skip(geography.county_to_cbsa(metro_only=False)), skip(theirs)
    merged = ours.merge(theirs, on="county_fips", how="outer", suffixes=("_ours", "_census"), indicator=True)
    assert (merged._merge == "both").all(), merged[merged._merge != "both"]
    assert (merged.cbsa_code_ours == merged.cbsa_code_census).all()


def test_unmatched_county_population_is_small(interim):
    r = features.unmatched_county_report(interim("nhgis"))
    # Indian Territory's nations (1900, 0.5% of the US) had no counties; the metro build drops
    # the affected Oklahoma metro-years instead (features.INCOMPLETE_STATE_YEARS)
    r = r[~r.county_id.str.startswith("nhgis-G178")]
    by_year = r[r.year >= 1900].groupby("year").share_of_us.sum()
    assert (by_year <= 0.002).all(), r.groupby("year").head(5)  # D-24: at most 0.14% per decade


def test_metro_growth_is_plausible(processed):
    p = processed("us_metro_longrun").sort_values(["geo_id", "year"])
    assert (p.population > 0).all()
    nxt = p.groupby("geo_id")[["year", "population"]].shift(-1)
    ratio = (nxt.population / p.population).where(nxt.year == p.year + 10)  # no ratios across gaps
    flagged = p.assign(ratio=ratio)[(ratio < 0.5) | (ratio > 3.0)]
    allow = pd.read_csv(CROSSWALKS_DIR / "growth_allowlist.csv", dtype={"year": "int64"})
    flagged = flagged.merge(allow, on=["geo_id", "year"], how="left", indicator=True)
    assert (flagged._merge == "both").all(), flagged[flagged._merge != "both"][["geo_id", "geo_name", "year", "ratio"]]


def test_income_series_has_no_gap_decades(processed):
    s = processed("us_state_longrun")
    assert (s[s.year >= 1880].groupby("year").income_pc.count() >= 38).all()
    m = processed("us_metro_longrun")
    m = m[m.year >= 1940]
    assert (m.groupby("year").income_pc.count() / m.groupby("year").geo_id.count() >= 0.9).all()


def test_ipums_1940_wages_track_bea_1940_income(interim):
    ip = interim("ipums")
    ip = ip[~ip.geo_id.str.startswith("county:nhgis-")]
    ip = ip.assign(state=ip.geo_id.str[7:9]).pivot_table(index="state", columns="variable", values="value", aggfunc="sum")
    wages_pc = ip.wage_income_total / ip.persons_ipums
    b = interim("bea")
    b = b[(b.geo_level == "state") & (b.year == 1940)]
    b = b.set_index(b.geo_id.str[6:8]).value
    both = pd.concat([np.log(wages_pc), np.log(b)], axis=1, join="inner").dropna()
    assert len(both) >= 45
    assert both.corr().iloc[0, 1] > 0.85


def test_ipums_1940_persons_match_nhgis_county_population(interim):
    # A county-code mapping error moves people between counties without changing state totals,
    # so check every county. Non-mapping gaps (enumeration revisions) are at most ~6%.
    ip = interim("ipums")
    ip = ip[ip.variable == "persons_ipums"].set_index("geo_id").value
    n = interim("nhgis")
    n = n[(n.geo_level == "county") & (n.year == 1940) & (n.variable == "population")].set_index("geo_id").value
    both = pd.concat([ip.rename("ipums"), n.rename("nhgis")], axis=1, join="inner")
    gap = (both.ipums - both.nhgis).abs()
    bad = both[gap > np.maximum(0.07 * both.nhgis, 100)]
    assert bad.empty, bad
    missing = n[(n > 1000) & ~n.index.isin(ip.index) & ~n.index.str.startswith("county:nhgis-")]
    assert missing.empty, missing
