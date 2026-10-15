import zipfile

import pandas as pd
import pytest

from us_housing_crisis_analysis.config import MANUAL_DATA_DIR, NETMIG_DECADES, RAW_DATA_DIR

pytestmark = pytest.mark.data


def test_every_decade_covers_the_states(processed):
    p = processed("us_state_net_migration")
    assert sorted(p.decade.unique()) == list(NETMIG_DECADES)
    counts = p.groupby("decade").geo_id.nunique()
    assert (counts >= 49).all(), counts  # 48 contiguous states + DC at least; AK/HI where estimated


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
# and a 25% bound instead of the 5% match (Plan 1c Task 4 report).
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


def test_2020_population_in_the_apl_file_matches_the_census(processed):
    path = RAW_DATA_DIR / "netmig" / "NME_1020_data.zip"
    if not path.exists():
        pytest.skip("2010s net migration file not downloaded")
    with zipfile.ZipFile(path) as z:
        raw = pd.read_csv(z.open("NME_1020_data.csv"), dtype={"fips_str2020": str})
    states = raw[raw.fips_str2020.str.endswith("000")]
    apl = pd.Series(states.f1tttt.to_numpy(float), index=states.fips_str2020.str[:2].to_numpy())
    ours = processed("us_state_longrun").query("year == 2020").set_index("geo_id").population
    ours.index = ours.index.str[6:8]
    rel = ((apl - ours) / ours).dropna()
    assert len(rel) >= 51 and rel.abs().max() < 0.005, rel.abs().sort_values().tail()


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
