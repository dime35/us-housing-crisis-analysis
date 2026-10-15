from functools import cache

import pandas as pd
import pytest

from us_housing_crisis_analysis.config import MANUAL_DATA_DIR, NETMIG_DECADES, NETMIG_FILES
from us_housing_crisis_analysis.sources import netmig

pytestmark = pytest.mark.data


def test_every_decade_covers_the_states(processed):
    p = processed("us_state_net_migration")
    assert sorted(p.decade.unique()) == list(NETMIG_DECADES)
    counts = p.groupby("decade").geo_id.nunique()
    assert (counts == 51).all(), counts  # 50 states + DC in every decade


def test_national_net_migration_is_positive(processed):
    # domestic moves cancel out across states, so the US sum is net international migration
    assert (processed("us_state_net_migration").groupby("decade").net_migration.sum() > 0).all()


# natural_rate is a residual: census growth minus net migration. If the census at the end of a
# decade counted more (or less) completely than the one at its start, measured growth includes
# that coverage change, and since net migration is held fixed it lands in the residual. The
# Census Bureau's demographic-analysis (DA) net undercount was 5.5M (2.7%) in 1970, 2.8M (1.2%)
# in 1980 and 4.7M (1.8%) in 1990 (National Academies, Modernizing the U.S. Census, 1995, ch. 2,
# citing Robinson et al. 1993: https://www.nationalacademies.org/read/4805/chapter/4), and
# 338,000 (0.12%) in 2000 (revised DA, October 2001:
# https://www.census.gov/programs-surveys/decennial-census/about/coverage-measurement/da.2000_Demographic_Analysis.html).
# So coverage improved in 1970-80 (+2.7M, residual too high), worsened in 1980-90 (-1.9M, too
# low) and improved in 1990-2000 (+4.4M, too high). Those decades are held to that direction
# and a 25% bound instead of the 5% match.
COVERAGE_SHIFT = {1970: +1, 1980: -1, 1990: +1}


def test_natural_increase_matches_nchs(processed):
    path = MANUAL_DATA_DIR / "us_natural_increase.csv"
    if not path.exists():
        pytest.skip("us_natural_increase.csv not entered")
    ref = pd.read_csv(path).set_index("decade")
    p = processed("us_state_net_migration")
    ours = (p.natural_rate * p.population).groupby(p.decade).sum()
    for decade, row in ref.iterrows():
        nchs = row.births - row.deaths
        if decade in COVERAGE_SHIFT:
            ratio = ours[decade] / nchs
            assert (ratio - 1) * COVERAGE_SHIFT[decade] > 0 and abs(ratio - 1) < 0.25, (decade, ratio)
        else:
            assert ours[decade] == pytest.approx(nchs, rel=0.05), decade


# US sums of county net migration in data/interim/netmig.parquet, recorded from the
# Plan 1c Task 4 build (rounded to the nearest thousand). The 1970s file is adjusted
# for census undercount (Census Bureau total 6.08M).
US_NET_MIGRATION = {1950: 2_665_000, 1960: 3_214_000, 1970: 6_062_000, 1980: 6_738_000,
                    1990: 12_061_000, 2000: 10_770_000, 2010: 10_529_000}


def test_netmig_us_totals_match_the_recorded_values(interim):
    nm = interim("netmig")
    nm = nm[(nm.variable == "net_migration") & (nm.geo_level == "county")]
    totals = nm.groupby("year").value.sum()
    assert sorted(totals.index) == sorted(US_NET_MIGRATION)
    for decade, expected in US_NET_MIGRATION.items():
        assert totals[decade] == pytest.approx(expected, rel=0.01), decade


# Base populations in the APL files (spec §6, "population agrees" and "coverage"). Each check sums
# a population column over the counties the parser kept (data/interim/netmig.parquet), so a parser
# or source change that loses counties shows up as a population shortfall.
#
# Fixed-width columns not in config.NETMIG_FILES, as 0-based half-open spans. ICPSR 8697 codebook
# §3.2: begin column - 1, width 9 (f9.0). ICPSR 4171: the field ends found for NETMIG_FILES;
# P90_TT_T and P00_TT_T are fields 301 and 586 of 1726, the all-ages totals of the P90/P00 blocks.
EXTRA_SPANS = {
    1970: "LEVEL:0-3,PTOT70:234-243,PTOT80:855-864,AWTOT70:180-189,ANWTOT70:189-198,ATOT80:2241-2250",
    1990: "P90_TT_T:1669-1676,P00_TT_T:3229-3236",
}


def _age_groups(top: int) -> list[str]:
    """ICPSR 26761 population age groups: 04, 59, 1014, ..., then the open group (75UP, 85UP)."""
    return ["04", "59"] + [f"{a}{a + 4}" for a in range(10, top, 5)] + [f"{top}UP"]


# (decade, census year) -> the columns summed. Unadjusted census counts, from each codebook:
# 8493 V19/V199 "1950 [1960] POPULATION ALL AGES TOTAL" and "1960 [1970] ...", 8697 PTOT70/PTOT80
# "1970 [1980] total pop" (enumerated), APL f1tttt "Population 2020, total".
CENSUS_BASES = {
    (1950, 1950): ["V19"], (1950, 1960): ["V199"],
    (1960, 1960): ["V19"], (1960, 1970): ["V199"],
    (1970, 1970): ["PTOT70"], (1970, 1980): ["PTOT80"],
    (2010, 2020): ["f1tttt"],
}
# Undercount-adjusted bases, on which each file's net migration is computed: 8697 "1970 adjusted
# white [non white] total pop" and "1980 total adjusted pop"; 26761 "Adjusted population 1980
# [1990]" by sex and age; 4171 P90/P00 (US P00 281.76M against the census's 281.42M); 34638
# "Starting [Final] population count in 2000 [2010]", adjusted for undercount and overcount
# (documentation, "Census 2000: The Starting Population").
ADJUSTED_BASES = {
    (1970, 1970): ["AWTOT70", "ANWTOT70"], (1970, 1980): ["ATOT80"],
    (1980, 1980): [f"AJ{a}{s}8" for s in "MF" for a in _age_groups(75)],
    (1980, 1990): [f"AJ{a}{s}9" for s in "MF" for a in _age_groups(85)],
    (1990, 1990): ["P90_TT_T"], (1990, 2000): ["P00_TT_T"],
    (2000, 2000): [f"P0TTT{a}" for a in range(0, 90, 5)],
    (2000, 2010): [f"F0TTT{a}" for a in range(0, 90, 5)],
}
# Rows that are state totals, where a file has them. In 8493 and 8697 division and region rows can
# also look like xx000 state codes, so the level field tells them apart.
STATE_LEVEL = {1950: ("LEVELNO", 1), 1960: ("LEVELNO", 1), 1970: ("LEVEL", 2), 2000: None, 2010: None}
STATES = set(netmig.UGA_STATE_FIPS.values())


@cache
def _apl(decade: int) -> tuple[pd.DataFrame, pd.Series]:
    """The decade's raw APL file and each row's 5-digit code, as the parser reads them."""
    spec = NETMIG_FILES[decade]
    path = netmig.RAW_DIR / spec["file"]
    if not path.exists():
        pytest.skip(f"{spec['file']} not downloaded")
    colspecs = ",".join(filter(None, [spec.get("colspecs"), EXTRA_SPANS.get(decade)])) or None
    raw = netmig._read(path, spec["member"], colspecs)
    return raw, netmig._county_fips(raw, spec)


def _total(raw: pd.DataFrame, columns: list[str]) -> pd.Series:
    return raw[columns].apply(pd.to_numeric).sum(axis=1)


def _county_sums(interim, decade: int, columns: list[str]) -> pd.Series:
    """`columns` summed over the counties the parser kept, by state FIPS."""
    raw, fips = _apl(decade)
    nm = interim("netmig")
    kept = ("county:" + fips).isin(set(nm.loc[nm.year == decade, "geo_id"]))
    return _total(raw[kept], columns).groupby(fips[kept].str[:2]).sum()


def _census(processed, year: int) -> pd.Series:
    """Census counts by state FIPS, 50 states and DC (us_state_longrun adds Puerto Rico from 2010)."""
    p = processed("us_state_longrun").query("year == @year")
    p = p.assign(fips=p.geo_id.str[6:8]).query("fips in @STATES")
    return p.set_index("fips").population


# The 1960s and 1970s files take their 1970 counts from Bowles, Beale and Lee (1975). They are
# 89,330 (0.04%) above the NHGIS count nationally and differ in 42 states. Only Alaska is off by
# more than 0.5% (302,419 against 300,382, +0.68%), so it is held to 1%.
CENSUS_TOLERANCE = {(1970, "02"): 0.01}


@pytest.mark.parametrize(("decade", "year"), list(CENSUS_BASES))
def test_census_bases_in_the_apl_files_match_us_state_longrun(interim, processed, decade, year):
    apl = _county_sums(interim, decade, CENSUS_BASES[decade, year])
    ours = _census(processed, year)
    assert sorted(apl.index) == sorted(ours.index)
    rel = (apl / ours - 1).abs()
    tol = pd.Series([CENSUS_TOLERANCE.get((year, f), 0.005) for f in rel.index], index=rel.index)
    assert (rel < tol).all(), rel[rel >= tol]


# The DA net undercounts cited above. The 1970s-1990s files add an undercount by age, sex and race
# to every county (8697 used the Census Bureau's 1985 estimates: 3.0% in 1970, 1.5% in 1980), so
# their national base minus the census count lands near these, not on them: within 15%.
DA_NET_UNDERCOUNT = {1970: 5_500_000, 1980: 2_800_000, 1990: 4_700_000, 2000: 338_000}


@pytest.mark.parametrize(("decade", "year"), list(ADJUSTED_BASES))
def test_adjusted_bases_carry_the_documented_undercount(interim, processed, decade, year):
    columns = ADJUSTED_BASES[decade, year]
    apl = _county_sums(interim, decade, columns)
    assert len(apl) == 51
    added = apl.sum() - _census(processed, year).sum()
    if decade == 2000:
        # 34638 adjusts the Census Bureau's estimates base with ACE Revision II (ages 10+) and DA
        # (under 10), with no published national total: hold it to the sign and under 0.5%
        assert 0 < added < 0.005 * apl.sum(), added
    else:
        assert added / DA_NET_UNDERCOUNT[year] == pytest.approx(1, abs=0.15), added


@pytest.mark.parametrize("decade", list(STATE_LEVEL))
def test_county_sums_equal_the_files_state_rows(interim, decade):
    """Coverage: the kept counties add up to the file's own state rows, for net migration and for
    each base population the file carries. The 2000s file estimated its state rows separately
    (net migration up to 470 apart, North Carolina; 2010 population up to 2,108, Texas): 0.1%
    of the state's population there, 0.001% (10 persons or fewer) elsewhere."""
    raw, fips = _apl(decade)
    state = fips.str.fullmatch(r"\d\d000") & fips.str[:2].isin(STATES)
    if STATE_LEVEL[decade]:
        col, level = STATE_LEVEL[decade]
        state &= pd.to_numeric(raw[col]) == level
    assert state.sum() == 51
    rows = raw[state].set_index(fips[state].str[:2])
    bases = [cs for bases in (CENSUS_BASES, ADJUSTED_BASES) for (d, _), cs in bases.items() if d == decade]
    tol = (1e-3 if decade == 2000 else 1e-5) * _total(rows, bases[0])
    for cols in [NETMIG_FILES[decade]["total_col"].split("+"), *bases]:
        gap = (_county_sums(interim, decade, cols) - _total(rows, cols)).abs()
        assert (gap <= tol).all(), (cols[:2], gap[gap > tol])


def test_1980s_natural_increase_from_the_adjusted_bases_matches_nchs(interim):
    """The 1980s file's own adjusted populations give a natural increase free of census coverage
    change: adjusted 1990 - adjusted 1980 - net migration. Nationally it must match NCHS births
    minus deaths within 1%, so the 1980s gap in the residual (ratio 0.91) is coverage."""
    path = MANUAL_DATA_DIR / "us_natural_increase.csv"
    if not path.exists():
        pytest.skip("us_natural_increase.csv not entered")
    nchs = pd.read_csv(path).set_index("decade").loc[1980]
    growth = (_county_sums(interim, 1980, ADJUSTED_BASES[1980, 1990])
              - _county_sums(interim, 1980, ADJUSTED_BASES[1980, 1980])).sum()
    nm = interim("netmig")
    migration = nm.loc[(nm.year == 1980) & (nm.variable == "net_migration"), "value"].sum()
    assert growth - migration == pytest.approx(nchs.births - nchs.deaths, rel=0.01)
