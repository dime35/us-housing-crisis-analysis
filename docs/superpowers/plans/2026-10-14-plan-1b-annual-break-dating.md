# Plan 1b: Dating the RQ0b Break with Annual Data — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Use annual BEA data (states 1929–2024, metros 1969–2024) to estimate *when* US population growth stopped following income. The outputs are a rolling-window β picture, a single break year with a significance test and a range, an oil-cycle check, and an updated RQ0b finding.

**Architecture:**
- `sources/bea.py` gains three requests: state population, plus 1980 mining and total earnings.
- `features.py` builds two panels, `us_state_annual` and `us_metro_annual`, and the energy-state list.
- `modeling/breaks.py` is generalized from decades to any period column.
- A new `modeling/annual_breaks.py` does the annual work: rolling β, the sup-Wald single-break test, the bootstrap and Bai ranges, and the multi-break search.
  - **Shared trick:** the year fixed effects are removed by demeaning within year once. This is exact (each year lies wholly inside one segment), so every candidate break year becomes a closed-form fit.
- Notebook `1.1` gains a section that writes one figure and two tables.

**Tech Stack:** Python 3.12, pandas, numpy, statsmodels (only as the reference that tests compare against), matplotlib, pytest, jupytext and nbconvert.

**Spec:** `docs/superpowers/specs/2026-10-14-rq0b-annual-break-dating-design.md` (approved 2026-10-14). Master spec: `docs/superpowers/specs/2026-10-08-housing-growth-mismatch-design.md`.

## Global Constraints

- **Branch:** work on `plan-1b-annual-breaks`, which comes off `plan-1-rq0b`.
- **Running tools:** the venv is `venv/`, so run tools as `venv/bin/python -m ...`. `make test-fast` runs tests that need no data; `make test` runs everything.
- **One source:** BEA only, for both population and income, in every annual year. No interpolation. Units missing a value drop out of that year only.
- **Geography:** same rules as Plan 1. Metros are 2023 CBSAs (metropolitan only) built from counties; Connecticut uses its 8 old counties; BEA combo areas and zero placeholders are handled as in D-23 and D-24.
- **County splits (D-27):** a metro-year whose one-year growth crosses a county split is flagged `growth_comparable = False` and left out of every growth calculation.
- **Trimming:** 15% for the main result; 5% as a check for metros and the 1969+ states. With n growth years, the first candidate break year is position `floor(trim · n)`. An estimate on the first candidate year is reported as "at or before".
- **Significance:** sup-Wald with standard errors clustered by unit, compared with Andrews (1993) critical values for one restriction at the trimming used. The critical values are simulated in code, never copied from a table, and an ordinary p-value is never reported for the chosen year.
- **Break-year range:** a bootstrap that resamples units (999 draws), giving the middle 90% of estimates. Bai's (1997) 90% interval is reported next to it. The bootstrap range is checked by simulation over at least 200 synthetic panels (see the coverage rule below).
- **Two scales for β:** one-year coefficients are named `*_annual`. Wherever they sit next to decade results they are also shown ×10, as `*_10y`.
- **Energy states:** 1980 mining earnings ÷ total earnings at least 3× the national share (BEA SAINC5S lines 200 and 35). The hand-picked list (TX, OK, LA, WY, AK, NM, WV, ND) is also run, because the rule leaves out North Dakota (see the Execution notes).
- **Docs:** every task that adds a source, method or decision updates `Claude/research/sources.md`, `Claude/methods/*.md` or `Claude/methods/decisions.md` in the same commit.
- **Commits:** commit after every task. Messages end with:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01WK1JcWFMpphC1KeQcaYjNr
  ```

## Execution notes (found while writing this plan, 2026-10-14)

- **The energy rule's list, checked against the live BEA API:**
  - In 1980 the national mining share was 2.03% of earnings.
  - At 3× or more: WY 11.9×, WV 7.8×, OK 4.9×, NM 4.7×, LA 4.0×, KY 3.8×, TX 3.1×, AK 3.02×.
  - Just below: ND 2.7×, UT 2.6×, CO 2.6×, MT 2.4×.
  - The rule adds Kentucky (coal) and leaves out North Dakota, so under spec §8.2 the hand-picked list is run as a robustness check.
  - Alaska sits just above the cutoff. The data test pins the eight states, so any BEA revision that moves Alaska is caught.
- **County-split growth years come from the data, not the legal dates.** BEA county data first shows the new counties in these years: Broomfield 2002, La Paz 1983, Cibola 1982. So the growth steps that cross a split start in 2001, 1982 and 1981. The spec's "La Paz 1983" was the legal split year, and the data-driven year replaces it. The flagged metro-years are:
  - Denver (19740), Boulder (14500) and Greeley (24540): 2001;
  - Yuma (49740): 1982;
  - Albuquerque (10740): 1981.
- **Coverage rule: owner decision needed before Task 5.** In a prototype with a sharp planted break, the bootstrap range had 100% coverage. That's legitimate: break years are whole numbers, so a sharp break gives a one-year range that always contains the truth. The spec's 80–97% band would wrongly reject that range. This plan implements **"at least 80%; above 97% is reported as conservative"**. If the owner keeps the spec's band instead, change `COVERAGE_MIN`/`COVERAGE_MAX` in Task 5 and the notebook's selection line.
- **Metro population check, adapted from spec §6.** In BEA's July 2020 estimates, five college-town metros are 1.6–8.5% below the April 2020 census base: Amherst, Ithaca, Tuscaloosa, Greenville NC and Corvallis. Students were away during COVID. Their July 2019 values are within 0.5%. So the data test requires each metro to be within 1% in July 2019 **or** July 2020, and the median 2020 gap to be under 0.2%. This was checked on the real data in a scratch run; every other Task 2–3 data test passed there unchanged, including the decade cross-check.
- **Prototype checks (scratch code, 2026-10-14):**
  - The demeaned multi-break search gives identical breaks and BIC values (difference < 1e-12) to the existing brute-force search with year dummies. A full 3-break search over 95 years took 0.6 s.
  - The closed-form clustered Wald statistic equals statsmodels' value with year dummies to 10 digits.
  - Simulated Andrews critical values (grid 10,000, 20,000 draws): 8.81 at 15% trimming (table: 8.85) and 9.84 at 5% (table: 9.84).
- **Columns beyond the spec's list:** the results table adds `sup_wald_cv5` (the critical value), `at_edge`, `multi_breaks` and `reported_range`. Without them the table can't be read on its own.

## Review Focus

1. **A metro whose growth crosses a county split** must never enter a growth calculation: not the one-year panel, and not any rolling window that contains the flagged year. Tested in Task 2 (flags) and Task 3 (annual panel and windows).
2. **A unit missing a year in the middle of the series** (a BEA suppression, or a county that appears late) must drop out of the growth for that year only. It must never be zero-filled, and a growth rate must never span the gap. Tested in Task 3 (`annual_growth_panel`, `window_panel`).
3. **A bootstrap draw that, by chance, leaves a year with no units** must not crash or produce NaN break years. Tested in Task 5 (an unbalanced panel where one year has a single unit).
4. **A break estimated on the first candidate year** must be flagged `at_edge` so the notebook writes "at or before". Tested in Task 4 (a break planted in 1972 with 15% trimming on 1969+ data).
5. **The Alaska and Hawaii zeros before 1950** must not leak into the state panel or the population-sum test. Tested in Task 2 (the panel has no AK/HI rows before 1950) and the Task 2 data test.

---

## File structure

| File | Responsibility | Task |
|---|---|---|
| `us_housing_crisis_analysis/config.py` | Annual year range, energy rule constants, WWII years | 1 |
| `us_housing_crisis_analysis/sources/bea.py` | + SAINC1 line 2 (state population), SAINC5S lines 35 and 200 (earnings) | 1 |
| `us_housing_crisis_analysis/geography.py` | + `STATE_ABBR_TO_FIPS`, `first_listed_state_fips` | 2 |
| `us_housing_crisis_analysis/features.py` | + `build_us_state_annual`, `build_us_metro_annual`, `split_growth_years`, `energy_states`, `drop_states` | 2 |
| `us_housing_crisis_analysis/modeling/breaks.py` | Generalize to a `period` column (defaults unchanged) | 3 |
| `us_housing_crisis_analysis/modeling/annual_breaks.py` (new) | Growth and window panels, rolling β, sup-Wald, bootstrap, Bai, coverage, demeaned search | 3–6 |
| `tests/test_annual_breaks.py` (new) | Synthetic recovery tests | 3–6 |
| `tests/test_features.py`, `tests/test_bea.py`, `tests/test_geography.py` | New unit tests | 1–2 |
| `tests/data/test_us_annual.py` (new) | Data tests on the built panels | 2, 3 |
| `pyproject.toml`, `Makefile` | `slow` pytest marker, excluded from `make test-fast` | 5 |
| `notebooks/1.1-lr-us-structural-break.ipynb` | New section "Annual data: when did the break happen?" | 7 |
| `reports/figures/rq0b_annual_betas.png`, `reports/tables/rq0b_annual_tests.csv`, `reports/tables/rq0b_annual_range_coverage.csv` | Outputs | 7 |
| `Claude/…`, master spec | Docs | every task, 7 |

**Order and parallelism:** Tasks 1 → 2 → 3 → 4 run in sequence. **Tasks 5 (break-year range) and 6 (multi-break search) are independent and can run in parallel** once Task 4 is done: both use only Task 4's private helpers and touch different functions. If they run on separate branches or worktrees, each adds functions to the end of `annual_breaks.py` and tests to the end of `test_annual_breaks.py`, so expect a trivial merge. Task 7 needs everything before it.

---

### Task 1: BEA requests for state population and 1980 earnings by industry

**Files:**
- Modify: `us_housing_crisis_analysis/config.py`, `us_housing_crisis_analysis/sources/bea.py`, `tests/test_bea.py`, `tests/data/test_us_longrun.py`, `Claude/research/sources.md`

**Interfaces:**
- Consumes: the existing `bea.REQUESTS`, `bea.parse_bea_json`, `bea.download`.
- Produces:
  - `config.RQ0B_ANNUAL_STATE_START = 1929`, `RQ0B_ANNUAL_METRO_START = 1969`, `RQ0B_ANNUAL_END = 2024`
  - `config.ENERGY_SHARE_YEAR = 1980`, `ENERGY_SHARE_MULTIPLE = 3.0`, `ENERGY_STATES_HAND: tuple[str, ...]` (state FIPS)
  - `config.WWII_GROWTH_YEARS = range(1940, 1947)`
  - Interim `bea` rows with `geo_level="state"`: `population_bea` (persons, 1929+), `earnings_total` and `earnings_mining` (usd_current, 1958–2001).

- [ ] **Step 1: Write the failing tests** (append to `tests/test_bea.py`):

```python
def _payload(rows, unit_mult="0"):
    data = [{"GeoFips": f, "GeoName": n, "TimePeriod": y, "DataValue": v, "UNIT_MULT": unit_mult}
            for f, n, y, v in rows]
    return {"BEAAPI": {"Results": {"Data": data}}}


def test_new_requests_are_registered():
    assert bea.REQUESTS["sainc1_state_pop"] == ("SAINC1", 2, "STATE", "state", "population_bea", "persons")
    assert bea.REQUESTS["sainc5s_state_earnings_total"][:2] == ("SAINC5S", 35)
    assert bea.REQUESTS["sainc5s_state_earnings_mining"][:2] == ("SAINC5S", 200)


def test_state_population_drops_alaska_zero_placeholder(tmp_path):
    p = tmp_path / "pop.json"
    p.write_text(json.dumps(_payload([("02000", "Alaska *", "1940", "0"), ("02000", "Alaska *", "1950", "135,000"),
                                      ("00000", "United States", "1950", "151,000,000")])))
    df = validate_long(bea.parse_bea_json(p, "state", "population_bea", "persons"))
    assert df[["geo_id", "year", "value"]].values.tolist() == [["state:02", 1950, 135000.0]]


def test_earnings_in_thousands_become_dollars(tmp_path):
    p = tmp_path / "earn.json"
    p.write_text(json.dumps(_payload([("56000", "Wyoming", "1980", "1,234")], unit_mult="3")))
    df = bea.parse_bea_json(p, "state", "earnings_mining", "usd_current")
    assert df.value.tolist() == [1_234_000.0]
```

Run: `venv/bin/python -m pytest tests/test_bea.py -q`. Expected: `test_new_requests_are_registered` FAILS (KeyError); the other two pass already. They pin parser behavior the new requests rely on.

- [ ] **Step 2: Add the requests and constants.** In `sources/bea.py`, replace the module docstring's first sentence and `REQUESTS`:

```python
"""BEA Regional API: per capita personal income and population for states (SAINC1, 1929+), 1980
mining and total earnings for states (SAINC5S, SIC basis, 1958-2001; energy-state rule), and
county personal income and population (CAINC1, 1969+), which features.py sums to 2023 CBSAs like
every other metro year. (CAINC1 at MSA level returns BEA error 101 "Unknown error".)"""
```

```python
# file stem -> (table, line code, GeoFips scope, geo_level, variable, unit).
# SAINC1/CAINC1: line 1 = personal income, 2 = population, 3 = per capita personal income.
# SAINC5S: line 35 = earnings by place of work, 200 = mining earnings (SIC division B).
REQUESTS = {
    "sainc1_state_pcpi": ("SAINC1", 3, "STATE", "state", "income_pc", "usd_current"),
    "sainc1_state_pop": ("SAINC1", 2, "STATE", "state", "population_bea", "persons"),
    "sainc5s_state_earnings_total": ("SAINC5S", 35, "STATE", "state", "earnings_total", "usd_current"),
    "sainc5s_state_earnings_mining": ("SAINC5S", 200, "STATE", "state", "earnings_mining", "usd_current"),
    "cainc1_county_pi": ("CAINC1", 1, "COUNTY", "county", "personal_income", "usd_current"),
    "cainc1_county_pop": ("CAINC1", 2, "COUNTY", "county", "population_bea", "persons"),
}
```

In `config.py`, after `METRO_LONGRUN_START = 1900`:

```python
# RQ0b annual break dating (Plan 1b): BEA state data from 1929, county data from 1969. Annual
# growth runs t -> t+1, so the last growth year is RQ0B_ANNUAL_END - 1.
RQ0B_ANNUAL_STATE_START = 1929
RQ0B_ANNUAL_METRO_START = 1969
RQ0B_ANNUAL_END = 2024
# Energy states (Plan 1b spec §4.3, §8.2): 1980 mining share of earnings >= 3x the national share.
# The hand-picked list is the robustness check (TX, OK, LA, WY, AK, NM, WV, ND).
ENERGY_SHARE_YEAR = 1980
ENERGY_SHARE_MULTIPLE = 3.0
ENERGY_STATES_HAND = ("48", "40", "22", "56", "02", "35", "54", "38")
# Growth years left out in the WWII robustness check (troop moves and war industry)
WWII_GROWTH_YEARS = range(1940, 1947)
```

Run: `venv/bin/python -m pytest tests/test_bea.py -q`. Expected: all pass.

- [ ] **Step 3: Download and load the real data.** The download skips the three existing files and fetches the three new ones.

```bash
venv/bin/python -m us_housing_crisis_analysis.dataset download --source bea
venv/bin/python -m us_housing_crisis_analysis.dataset load --source bea
venv/bin/python -c "
import pandas as pd; b = pd.read_parquet('data/interim/bea.parquet')
print(b[b.geo_level == 'state'].groupby('variable').year.agg(['min', 'max', 'count']))"
```

Expected: `population_bea` 1929–2024 (2025 if BEA has published it; the panels stop at 2024); `earnings_total` and `earnings_mining` 1958–2001; `income_pc` 1929–2025. If BEA returns an error, stop and report it. Don't change the line codes without checking them with `GetParameterValuesFiltered`.

- [ ] **Step 4: Keep the existing 1940 data test working.** `tests/data/test_us_longrun.py::test_ipums_1940_wages_track_bea_1940_income` selects BEA state rows for 1940 without filtering on the variable. With state population now loaded, it would pick up two rows per state. In that test, change

```python
    b = b[(b.geo_level == "state") & (b.year == 1940)]
```

to

```python
    b = b[(b.geo_level == "state") & (b.year == 1940) & (b.variable == "income_pc")]
```

Run: `venv/bin/python -m pytest tests/data/test_us_longrun.py -q`. Expected: all pass.

- [ ] **Step 5: Update `Claude/research/sources.md`.** In the BEA row's status cell, add: "SAINC1 line 2 state population 1929+ and SAINC5S lines 35/200 (earnings, mining) 1958–2001 for the energy-state rule (Plan 1b)". Set the last-checked date to the current day.

- [ ] **Step 6: Run the fast suite and commit.**

```bash
make test-fast
git add us_housing_crisis_analysis/config.py us_housing_crisis_analysis/sources/bea.py tests/test_bea.py tests/data/test_us_longrun.py Claude/research/sources.md
git commit -m "Add BEA state population and 1980 earnings by industry (Plan 1b)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WK1JcWFMpphC1KeQcaYjNr"
```

---

### Task 2: Annual panels, county-split growth years and the energy-state list

**Files:**
- Modify: `us_housing_crisis_analysis/geography.py`, `us_housing_crisis_analysis/features.py`, `tests/test_geography.py`, `tests/test_features.py`, `Claude/methods/pipeline.md`
- Create: `tests/data/test_us_annual.py`

**Interfaces:**
- Consumes: Task 1 constants and interim `bea` variables; the existing `features._pick`, `_assemble`, `county_series`, `COUNTY_SPLITS_PATH`, `PANEL_COLUMNS`; `geography.county_to_cbsa`.
- Produces:
  - `geography.STATE_ABBR_TO_FIPS: dict[str, str]`
  - `geography.first_listed_state_fips(cbsa_title: pd.Series) -> pd.Series` (FIPS of the first state in the title)
  - `features.build_us_state_annual(bea) -> DataFrame[PANEL_COLUMNS]`
  - `features.build_us_metro_annual(bea, crosswalk) -> DataFrame[PANEL_COLUMNS + ["growth_comparable"]]`, where `growth_comparable` at year t refers to the growth t → t+1
  - `features.split_growth_years(cw, first_year: pd.Series, start: int) -> set[tuple[str, int]]`
  - `features.energy_states(bea) -> DataFrame[state_fips, state_name, mining_share, ratio, energy]`, sorted by ratio, descending
  - `features.drop_states(panel, fips: set[str]) -> DataFrame` (states: by `geo_id`; metros: by the first listed state in `geo_name`)
  - Processed files `data/processed/us_state_annual.parquet` and `us_metro_annual.parquet`.

- [ ] **Step 1: Write the failing unit tests.** Append to `tests/test_geography.py`:

```python
def test_first_listed_state_fips():
    titles = pd.Series(["Dallas-Fort Worth-Arlington, TX", "New York-Newark-Jersey City, NY-NJ",
                        "Cheyenne, WY", "Aguadilla, PR"])
    assert geo.first_listed_state_fips(titles).tolist() == ["48", "36", "56", "72"]
```

(`tests/test_geography.py` imports the module as `geo`; add `import pandas as pd` at the top if it isn't there.) Append to `tests/test_features.py`:

```python
def test_state_annual_panel_joins_population_and_income():
    bea = long([("state:24", "state", 1929, "population_bea", 1.6e6),
                ("state:24", "state", 1929, "income_pc", 900),
                ("state:24", "state", 1930, "population_bea", 1.63e6),  # income missing: NaN
                ("state:24", "state", 2025, "income_pc", 80_000)], "bea")  # past the panel end
    p = features.build_us_state_annual(bea).set_index(["geo_id", "year"])
    assert p.loc[("state:24", 1929), "income_pc"] == 900
    assert np.isnan(p.loc[("state:24", 1930), "income_pc"])
    assert list(p.index.get_level_values("year")) == [1929, 1930]
    assert set(p.income_source.dropna()) == {"bea"}


def _split_crosswalk():
    # Broomfield (08014) and Adams (08001) in Denver, Boulder (08013) in its own metro
    return pd.DataFrame({"county_fips": ["08014", "08001", "08013"], "cbsa_code": ["19740", "19740", "14500"],
                         "cbsa_title": ["Denver, CO", "Denver, CO", "Boulder, CO"], "area_type": ["metro"] * 3})


def test_metro_annual_panel_sums_counties_and_flags_split_growth_years():
    rows = []
    for y in (2000, 2001, 2002):
        rows += [("county:08001", "county", y, "population_bea", 300.0), ("county:08001", "county", y, "personal_income", 3000.0),
                 ("county:08013", "county", y, "population_bea", 200.0), ("county:08013", "county", y, "personal_income", 4000.0)]
    rows += [("county:08014", "county", 2002, "population_bea", 40.0), ("county:08014", "county", 2002, "personal_income", 800.0)]
    p = features.build_us_metro_annual(long(rows, "bea"), _split_crosswalk()).set_index(["geo_id", "year"])
    assert p.loc[("cbsa:19740", 2002), "population"] == 340.0
    assert p.loc[("cbsa:19740", 2002), "income_pc"] == 3800.0 / 340.0
    # Broomfield first appears in 2002, so the 2001 -> 2002 step compares different areas
    assert not p.loc[("cbsa:19740", 2001), "growth_comparable"]
    assert not p.loc[("cbsa:14500", 2001), "growth_comparable"]
    assert p.loc[("cbsa:19740", 2000), "growth_comparable"] and p.loc[("cbsa:19740", 2002), "growth_comparable"]


def test_split_growth_years_ignores_splits_before_the_panel_starts():
    first_year = pd.Series({"08014": 2002, "35028": 1969})  # Los Alamos (1949) is in place by 1969
    cw = pd.concat([_split_crosswalk(), pd.DataFrame({"county_fips": ["35028", "35043"], "cbsa_code": ["31060", "10740"],
                                                      "cbsa_title": ["Los Alamos, NM", "Albuquerque, NM"], "area_type": ["metro"] * 2})])
    flagged = features.split_growth_years(cw, first_year, start=1969)
    assert flagged == {("19740", 2001), ("14500", 2001)}  # 08014's other parents aren't in this crosswalk


def test_energy_states_rule():
    bea = long([("state:56", "state", 1980, "earnings_total", 100.0), ("state:56", "state", 1980, "earnings_mining", 30.0),
                ("state:24", "state", 1980, "earnings_total", 900.0), ("state:24", "state", 1980, "earnings_mining", 0.5),
                ("state:11", "state", 1980, "earnings_total", 50.0)], "bea")  # mining suppressed: not energy
    e = features.energy_states(bea).set_index("state_fips")
    national = 30.5 / 1000.0  # states with both values
    assert e.loc["56", "ratio"] == pytest.approx(0.3 / national)
    assert e.energy.to_dict() == {"56": True, "24": False, "11": False}
    assert e.index[0] == "56"


def test_drop_states_for_states_and_metros():
    states = pd.DataFrame({"geo_id": ["state:48", "state:24"], "geo_name": ["Texas", "Maryland"]})
    metros = pd.DataFrame({"geo_id": ["cbsa:19100", "cbsa:12580"],
                           "geo_name": ["Dallas-Fort Worth-Arlington, TX", "Baltimore-Columbia-Towson, MD"]})
    assert features.drop_states(states, {"48"}).geo_id.tolist() == ["state:24"]
    assert features.drop_states(metros, {"48"}).geo_id.tolist() == ["cbsa:12580"]
```

(Add `import pytest` at the top of `tests/test_features.py` if it isn't there.)

Run: `venv/bin/python -m pytest tests/test_geography.py tests/test_features.py -q`. Expected: the new tests FAIL with AttributeError.

- [ ] **Step 2: Add the state abbreviations** to `geography.py`, after `harmonize_county_fips`:

```python
STATE_ABBR_TO_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10",
    "DC": "11", "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27",
    "MS": "28", "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35",
    "NY": "36", "NC": "37", "ND": "38", "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44",
    "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53",
    "WV": "54", "WI": "55", "WY": "56", "PR": "72",
}


def first_listed_state_fips(cbsa_title: pd.Series) -> pd.Series:
    """FIPS of the first state named in a CBSA title ("New York-Newark-Jersey City, NY-NJ" -> 36)."""
    return cbsa_title.str.extract(r", ([A-Z]{2})", expand=False).map(STATE_ABBR_TO_FIPS)
```

- [ ] **Step 3: Add the builders to `features.py`.** Extend the config import with `ENERGY_SHARE_MULTIPLE, ENERGY_SHARE_YEAR, RQ0B_ANNUAL_END, RQ0B_ANNUAL_METRO_START, RQ0B_ANNUAL_STATE_START`, and the geography import with `first_listed_state_fips`. Add after `build_us_metro_longrun`:

```python
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
    """Plan 1b spec §4.3: a state is an energy state if its mining share of earnings in
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
```

Add both panels to `main()`:

```python
    panels = {
        "us_state_longrun": build_us_state_longrun(nhgis, bea, manual),
        "us_metro_longrun": build_us_metro_longrun(nhgis, ipums, icpsr, bea, county_to_cbsa()),
        "us_state_annual": build_us_state_annual(bea),
        "us_metro_annual": build_us_metro_annual(bea, county_to_cbsa()),
    }
```

Run: `venv/bin/python -m pytest tests/test_geography.py tests/test_features.py -q`. Expected: all pass.

- [ ] **Step 4: Write the data tests** in `tests/data/test_us_annual.py`:

```python
import numpy as np
import pandas as pd
import pytest

from us_housing_crisis_analysis import features, geography

pytestmark = pytest.mark.data

AK_HI = ["state:02", "state:15"]


@pytest.mark.parametrize("name", ["us_state_annual", "us_metro_annual"])
def test_panels_unique_and_income_positive(processed, name):
    p = processed(name)
    assert not p.duplicated(["geo_id", "year"]).any()
    assert (p.income_pc.dropna() > 0).all() and (p.population > 0).all()


def test_state_annual_years_and_no_alaska_hawaii_before_1950(processed):
    p = processed("us_state_annual")
    assert p.year.min() == 1929 and p.year.max() == 2024
    assert p[p.geo_id.isin(AK_HI) & (p.year < 1950)].empty
    assert (p.groupby("year").geo_id.count().loc[1950:] == 51).all()


@pytest.mark.parametrize("year", range(1930, 2021, 10))
def test_state_population_matches_census(processed, interim, year):
    # BEA is mid-year, the census is April 1; Alaska and Hawaii left out of both sides before 1950
    bea = processed("us_state_annual").query("year == @year")
    n = interim("nhgis")
    n = n[(n.geo_level == "state") & (n.variable == "population") & (n.year == year)]
    n = n[n.geo_id.str.match(r"state:\d\d$") & (n.geo_id != "state:72")]
    if year < 1950:
        bea, n = bea[~bea.geo_id.isin(AK_HI)], n[~n.geo_id.isin(AK_HI)]
    assert bea.population.sum() == pytest.approx(n.value.sum(), rel=0.01)


def test_metro_2020_population_matches_census_base(processed, interim):
    # BEA's July 2020 estimates dip in college towns (students away during COVID: Amherst -8%,
    # Ithaca -6%), so each metro must be within 1% of the April 2020 base in July 2019 or 2020
    p = processed("us_metro_annual").pivot(index="geo_id", columns="year", values="population")
    base = interim("census_pep").set_index("geo_id").value
    cw = geography.county_to_cbsa()
    ct = list(set("cbsa:" + cw[cw.county_fips.str.startswith("09")].cbsa_code))
    rel = {y: ((p[y] - base) / base).drop(ct, errors="ignore").dropna() for y in (2019, 2020)}
    assert len(rel[2020]) > 350
    closer = pd.concat([rel[2019].abs(), rel[2020].abs()], axis=1).min(axis=1)
    assert closer.max() < 0.01, closer.sort_values().tail()
    assert rel[2020].abs().median() < 0.002


def test_split_growth_years_are_exactly_the_known_ones(processed):
    p = processed("us_metro_annual")
    flagged = set(zip(p.loc[~p.growth_comparable, "geo_id"], p.loc[~p.growth_comparable, "year"]))
    assert flagged == {("cbsa:19740", 2001), ("cbsa:14500", 2001), ("cbsa:24540", 2001),
                       ("cbsa:49740", 1982), ("cbsa:10740", 1981)}


def test_energy_states_1980(interim):
    e = features.energy_states(interim("bea"))
    assert set(e.loc[e.energy, "state_fips"]) == {"56", "54", "40", "35", "22", "21", "48", "02"}
    assert e.set_index("state_fips").loc["38", "ratio"] < 3  # North Dakota: why the hand list also runs
```

- [ ] **Step 5: Build and run the data tests.**

```bash
make features
venv/bin/python -m pytest tests/data/test_us_annual.py -v
```

Expected: all pass. If the census comparison fails for a year, print the gap by state and look for a cause (a missing state, a unit error). Don't loosen the 1% tolerance without recording why in `decisions.md`. If the metro 2020 check fails for a few metros only by just over 1%, report them. BEA's July 2020 estimate and the April 2020 base can differ by a few months of growth, and that's an owner call.

- [ ] **Step 6: Update `Claude/methods/pipeline.md`** (the "Processed panels" section). Add `us_state_annual` (state × year, 1929–2024, BEA population and income) and `us_metro_annual` (2023 CBSA × year, 1969–2024, BEA county sums; `growth_comparable` refers to growth t → t+1). Note that build step 5 adds housing columns to `us_metro_annual`.

- [ ] **Step 7: Commit.**

```bash
make test-fast
git add us_housing_crisis_analysis/geography.py us_housing_crisis_analysis/features.py tests Claude/methods/pipeline.md
git commit -m "Build annual state and metro panels and the energy-state list (Plan 1b)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WK1JcWFMpphC1KeQcaYjNr"
```

---

### Task 3: Generalize `breaks.py` to any period; annual growth panel and rolling β

**Files:**
- Modify: `us_housing_crisis_analysis/modeling/breaks.py`, `tests/data/test_us_annual.py`
- Create: `us_housing_crisis_analysis/modeling/annual_breaks.py`, `tests/test_annual_breaks.py`

**Interfaces:**
- Consumes: Task 2 panels (columns `geo_id, year, population, income_pc` and optionally `growth_comparable`).
- Produces:
  - `breaks.decade_betas(dp, period="decade")`, `breaks.chow_test(dp, break_period, period="decade")`, `breaks.break_search(dp, max_breaks=3, min_segment=2, period="decade")`, `breaks.standardize_within_decade(dp, period="decade")`. The defaults reproduce Plan 1 exactly; `decade_betas` names its first output column after `period`.
  - `annual_breaks.annual_growth_panel(panel, start, end) -> DataFrame[geo_id, year, growth, log_income]`
  - `annual_breaks.window_panel(panel, horizon, start, end) -> DataFrame[geo_id, start, growth, log_income]`
  - `annual_breaks.rolling_betas(panel, horizon, start, end) -> DataFrame[start, beta, se, n]`

- [ ] **Step 1: Write the failing tests** in a new `tests/test_annual_breaks.py`:

```python
import numpy as np
import pandas as pd
import pytest

from us_housing_crisis_analysis.modeling import annual_breaks as ab
from us_housing_crisis_analysis.modeling import breaks


def simulate(beta_for, n_units=50, years=range(1929, 2024), noise=0.01, seed=0):
    """Annual growth panel: persistent unit income plus small yearly noise; growth = a year
    effect + beta(year) * log income + noise."""
    rng = np.random.default_rng(seed)
    base = rng.normal(0, 0.3, n_units)
    rows = []
    for y in years:
        x = base + rng.normal(0, 0.05, n_units)
        g = 0.01 * np.sin(y) + beta_for(y) * x + rng.normal(0, noise, n_units)
        rows.append(pd.DataFrame({"geo_id": [f"u{i}" for i in range(n_units)], "year": y,
                                  "log_income": x, "growth": g}))
    return pd.concat(rows, ignore_index=True)


def levels(beta=0.02, n_units=40, years=range(1969, 2025), seed=0):
    """Panel in levels (population, income_pc) whose one-year growth = 0.01 + beta * log income."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 0.3, n_units)
    rows, logpop = [], np.zeros(n_units)
    for y in years:
        rows.append(pd.DataFrame({"geo_id": [f"u{i}" for i in range(n_units)], "year": y,
                                  "population": np.exp(logpop) * 1000, "income_pc": np.exp(x) * 1e4}))
        logpop = logpop + 0.01 + beta * x + rng.normal(0, 0.002, n_units)
    return pd.concat(rows, ignore_index=True)


def test_breaks_defaults_unchanged_and_period_column_works():
    dp = simulate(lambda y: 0.03 if y < 1978 else 0.0, years=range(1960, 1990))
    b = breaks.decade_betas(dp, period="year")
    assert list(b.columns[:1]) == ["year"] and len(b) == 30
    s = breaks.break_search(dp, max_breaks=1, min_segment=5, period="year")
    assert s.breaks == (1978,)
    decade = dp.rename(columns={"year": "decade"})
    assert breaks.decade_betas(decade).columns[0] == "decade"


def test_annual_growth_panel_drops_gaps_and_flagged_years():
    panel = pd.DataFrame({
        "geo_id": ["a"] * 5, "year": [2000, 2001, 2003, 2004, 2005],  # 2002 missing
        "population": [100.0, 110.0, 121.0, 133.1, 146.41], "income_pc": [10.0, 10.0, 10.0, np.nan, 10.0],
        "growth_comparable": [True, True, True, True, False],
    })
    g = ab.annual_growth_panel(panel, 2000, 2024)
    assert g.year.tolist() == [2000, 2003]  # 2001->2002 gap; 2004 no income; 2005 flagged (and no 2006)
    assert g.growth.iloc[0] == pytest.approx(np.log(1.1))


def test_annual_growth_panel_respects_start_and_end():
    g = ab.annual_growth_panel(levels(), 1970, 2000)
    assert g.year.min() == 1970 and g.year.max() == 1999


def test_rolling_betas_recover_slope_times_horizon():
    p = levels(beta=0.02)
    for h in (10, 5):
        r = ab.rolling_betas(p, h, 1969, 2024)
        assert r.start.min() == 1969 and r.start.max() == 2024 - h
        assert np.allclose(r.beta, 0.02 * h, atol=0.01 * h / 10 + 0.002)


def test_window_panel_skips_windows_containing_a_flagged_step():
    p = levels(n_units=3, years=range(1990, 2011))
    p["growth_comparable"] = ~((p.geo_id == "u0") & (p.year == 2001))
    w = ab.window_panel(p, 10, 1990, 2010)
    starts_u0 = set(w.loc[w.geo_id == "u0", "start"])
    assert starts_u0 == {1990, 1991}  # windows starting 1992-2000 contain the 2001 step
    assert set(w.loc[w.geo_id == "u1", "start"]) == set(range(1990, 2001))
```

Run: `venv/bin/python -m pytest tests/test_annual_breaks.py -q`. Expected: FAIL (`annual_breaks` missing).

- [ ] **Step 2: Generalize `breaks.py`.** Replace `decade_betas`, `_design`, `chow_test`, `break_search` and `standardize_within_decade` with the versions below. Keep the module docstring, add one line to it ("Every function takes a `period` column, "decade" by default; Plan 1b passes "year"."), and leave the other functions unchanged.

```python
def decade_betas(dp: pd.DataFrame, period: str = "decade") -> pd.DataFrame:
    rows = []
    for d, g in dp.groupby(period):
        fit = sm.OLS(g.growth, sm.add_constant(g.log_income)).fit(cov_type="HC1")
        rows.append({period: int(d), "beta": fit.params["log_income"],
                     "se": fit.bse["log_income"], "n": len(g)})
    return pd.DataFrame(rows)


def _design(dp: pd.DataFrame, break_periods, period: str = "decade") -> pd.DataFrame:
    """Period fixed effects plus one income slope per segment. Segment k starts at the k-th break."""
    fe = pd.get_dummies(dp[period], prefix="d", dtype=float)
    segment = np.searchsorted(sorted(break_periods), dp[period].to_numpy(), side="right")
    slopes = {f"slope_{k}": dp.log_income.to_numpy() * (segment == k) for k in range(len(break_periods) + 1)}
    return pd.concat([fe, pd.DataFrame(slopes, index=dp.index)], axis=1)


def chow_test(dp: pd.DataFrame, break_period: int, period: str = "decade") -> TestResult:
    """Wald test that the income slope is equal before and after break_period, with standard
    errors clustered by unit (a Chow test robust to heteroskedasticity and serial correlation)."""
    fit = sm.OLS(dp.growth, _design(dp, [break_period], period)).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(dp.geo_id)[0]}
    )
    w = fit.wald_test("slope_0 = slope_1", scalar=True)
    return TestResult(float(w.statistic), float(w.pvalue))


def break_search(dp: pd.DataFrame, max_breaks: int = 3, min_segment: int = 2, period: str = "decade") -> BreakSearch:
    """Bai-Perron-style global search: every set of up to max_breaks period boundaries with at
    least min_segment periods per segment; choose the set with the lowest BIC."""
    periods = sorted(dp[period].unique())
    candidates = periods[min_segment : len(periods) - min_segment + 1]
    n = len(dp)
    bic: dict[tuple[int, ...], float] = {}
    for k in range(max_breaks + 1):
        for combo in combinations(candidates, k):
            edges = [periods[0], *combo, periods[-1] + 1]
            sizes = [sum(lo <= d < hi for d in periods) for lo, hi in zip(edges[:-1], edges[1:])]
            if min(sizes) < min_segment:
                continue
            X = _design(dp, combo, period)
            ssr = sm.OLS(dp.growth, X).fit().ssr
            # parameters = coefficients plus the break dates themselves (Yao 1988)
            bic[tuple(int(c) for c in combo)] = n * np.log(ssr / n) + (X.shape[1] + len(combo)) * np.log(n)
    return BreakSearch(breaks=min(bic, key=bic.get), bic=bic)


def standardize_within_decade(dp: pd.DataFrame, period: str = "decade") -> pd.DataFrame:
    """Robustness: z-score log income within each period, so sources with different spreads
    (e.g., 1940 wages vs. later total income) are comparable."""
    g = dp.groupby(period).log_income
    return dp.assign(log_income=(dp.log_income - g.transform("mean")) / g.transform("std"))
```

(The last segment edge changes from `+ 10` to `+ 1`. That only marks "after the last period", so decade results are identical.)

- [ ] **Step 3: Create `modeling/annual_breaks.py`** with its first three functions:

```python
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
```

Run: `venv/bin/python -m pytest tests/test_annual_breaks.py tests/test_breaks.py -q`. Expected: all pass, and the Plan 1 tests are unchanged.

- [ ] **Step 4: Add the decade cross-check data test** (spec §6) to `tests/data/test_us_annual.py`:

```python
from us_housing_crisis_analysis.modeling import annual_breaks, breaks


@pytest.mark.parametrize("annual, longrun, first", [("us_state_annual", "us_state_longrun", 1930),
                                                    ("us_metro_annual", "us_metro_longrun", 1970)])
def test_rolling_beta_matches_decade_beta(processed, annual, longrun, first):
    roll = annual_breaks.rolling_betas(processed(annual), 10, first, 2020).set_index("start")
    dec = breaks.decade_betas(breaks.prepare_decade_panel(processed(longrun), first)).set_index("decade")
    for d in range(first, 2011, 10):
        lo, hi = dec.beta[d] - 1.96 * dec.se[d], dec.beta[d] + 1.96 * dec.se[d]
        assert lo <= roll.beta[d] <= hi, (d, roll.beta[d], dec.beta[d], dec.se[d])
```

Run: `venv/bin/python -m pytest tests/data/test_us_annual.py -v`. Expected: pass. A failure means the annual and decade data disagree for that decade (spec: "a data problem, not a finding"). Investigate (population timing, the unit set, income definition) and report. Don't widen the interval.

- [ ] **Step 5: Commit.**

```bash
make test-fast
git add us_housing_crisis_analysis/modeling tests
git commit -m "Annual growth panel and rolling-window betas; breaks.py takes any period (Plan 1b)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WK1JcWFMpphC1KeQcaYjNr"
```

---

### Task 4: Single break: sup-Wald, Andrews critical values, break year

**Files:**
- Modify: `us_housing_crisis_analysis/modeling/annual_breaks.py`, `tests/test_annual_breaks.py`

**Interfaces:**
- Consumes: Task 3 (`annual_growth_panel` output: `geo_id, year, growth, log_income`); `breaks.chow_test(..., period="year")` as the reference in tests.
- Produces, used by Tasks 5–7:
  - `annual_breaks.andrews_critical_value(trim: float, level: float = 0.05) -> float` (cached)
  - `annual_breaks.candidate_positions(n_periods: int, trim: float) -> np.ndarray`
  - `annual_breaks.wald_statistic(dp, break_year: int) -> float`
  - `annual_breaks.sup_wald_break(dp, trim=0.15) -> SingleBreak`, with fields `break_year, at_edge, sup_wald, critical_value, beta_before, beta_after, trim, first_candidate, last_candidate, n_units, first_year, last_year`
  - Private helpers for Tasks 5 and 6: `_arrays(dp, period)`, `_demean(t, x, y, w, nt)`, `_sums(t, xd, yd, w, nt)`, `_ssr_candidates(sxx, sxy, syy, cand)`

- [ ] **Step 1: Write the failing tests** (append to `tests/test_annual_breaks.py`):

```python
def test_andrews_critical_values_match_the_published_table():
    # Andrews (1993) Table 1, one restriction, 5% level
    assert ab.andrews_critical_value(0.15) == pytest.approx(8.85, abs=0.15)
    assert ab.andrews_critical_value(0.05) == pytest.approx(9.84, abs=0.15)


def test_candidate_years_follow_the_trimming():
    states, metros = list(range(1929, 2024)), list(range(1969, 2024))
    assert states[ab.candidate_positions(len(states), 0.15)[0]] == 1943
    assert metros[ab.candidate_positions(len(metros), 0.15)[0]] == 1977
    assert metros[ab.candidate_positions(len(metros), 0.05)[0]] == 1971


def test_wald_matches_statsmodels_with_year_dummies():
    dp = simulate(lambda y: 0.03 if y < 1978 else 0.0, n_units=30, years=range(1960, 1995), noise=0.02)
    assert ab.wald_statistic(dp, 1978) == pytest.approx(breaks.chow_test(dp, 1978, period="year").statistic, rel=1e-8)


def test_planted_1978_break_is_found_and_significant():
    r = ab.sup_wald_break(simulate(lambda y: 0.03 if y < 1978 else 0.0, noise=0.02))
    assert abs(r.break_year - 1978) <= 2
    assert r.sup_wald > r.critical_value
    assert r.beta_before == pytest.approx(0.03, abs=0.01) and r.beta_after == pytest.approx(0.0, abs=0.01)
    assert not r.at_edge and r.first_candidate == 1943


def test_no_planted_break_is_not_significant():
    r = ab.sup_wald_break(simulate(lambda y: 0.02, noise=0.05))
    assert r.sup_wald < r.critical_value


def test_break_before_the_first_candidate_is_flagged_at_edge():
    r = ab.sup_wald_break(simulate(lambda y: 0.03 if y < 1972 else 0.0, years=range(1969, 2024)))
    assert r.break_year == 1977 and r.at_edge


def oil_cycle(n_units=50, n_energy=10, seed=0, noise=0.01):
    """No change in behavior; energy units get an income boom (1973-81) and bust (1982-90) with
    growth following oil jobs rather than income."""
    rng = np.random.default_rng(seed)
    base = rng.normal(0, 0.3, n_units)
    energy = np.arange(n_units) < n_energy
    rows = []
    for y in range(1969, 2024):
        cycle = 0.3 if 1973 <= y <= 1981 else (-0.3 if 1982 <= y <= 1990 else 0.0)
        x = base + rng.normal(0, 0.05, n_units) + energy * cycle
        g = 0.02 * x + energy * np.sign(cycle) * 0.03 + rng.normal(0, noise, n_units)
        rows.append(pd.DataFrame({"geo_id": [f"u{i}" for i in range(n_units)], "year": y,
                                  "log_income": x, "growth": g, "energy": energy}))
    return pd.concat(rows, ignore_index=True)


def test_oil_cycle_breaks_the_full_panel_but_not_the_one_without_energy_units():
    dp = oil_cycle()
    assert ab.sup_wald_break(dp).sup_wald > ab.andrews_critical_value(0.15)
    without = ab.sup_wald_break(dp[~dp.energy])
    assert without.sup_wald < without.critical_value
```

Run: `venv/bin/python -m pytest tests/test_annual_breaks.py -q`. Expected: the new tests FAIL (AttributeError).

- [ ] **Step 2: Implement.** Add to `annual_breaks.py`. Put the imports at the top of the file, sorted (`from dataclasses import dataclass`, `from functools import lru_cache`), and add the functions after `rolling_betas`:

```python
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
```

Run: `venv/bin/python -m pytest tests/test_annual_breaks.py -q`. Expected: all pass. The first call simulates the critical value, which takes about 5 s; later calls hit the cache.

- [ ] **Step 3: Commit.**

```bash
make test-fast
git add us_housing_crisis_analysis/modeling/annual_breaks.py tests/test_annual_breaks.py
git commit -m "Single-break test on annual data: sup-Wald, Andrews critical values (Plan 1b)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WK1JcWFMpphC1KeQcaYjNr"
```

---

### Task 5: Range for the break year: bootstrap, Bai interval, coverage check

*Can run in parallel with Task 6.* **Before starting, confirm the coverage rule with the owner** (see the Execution notes). The code below implements "at least 80%".

**Files:**
- Modify: `us_housing_crisis_analysis/modeling/annual_breaks.py`, `tests/test_annual_breaks.py`, `pyproject.toml`, `Makefile`

**Interfaces:**
- Consumes: Task 4 (`sup_wald_break`, `SingleBreak`, `candidate_positions`, `_arrays`, `_demean`, `_sums`, `_ssr_candidates`).
- Produces:
  - `annual_breaks.bootstrap_break_year(dp, trim=0.15, draws=999, level=0.90, seed=0) -> BreakRange(low, high, estimates: np.ndarray)`
  - `annual_breaks.bai_interval(dp, result: SingleBreak, level=0.90) -> tuple[int, int]`
  - `annual_breaks.range_coverage(dp, result, sims=200, draws=199, level=0.90, seed=0) -> dict[str, float]`, with keys `bootstrap` and `bai`
  - `annual_breaks.COVERAGE_MIN = 0.80`, `COVERAGE_MAX = 0.97`
  - pytest marker `slow`

- [ ] **Step 1: Add the `slow` marker.** In `pyproject.toml`, set the markers to:

```toml
markers = [
  "data: needs built data in data/; skipped when it is absent",
  "slow: simulation checks that take more than a few seconds",
]
```

In the `Makefile`'s `test-fast` target, change `-m "not data"` to `-m "not data and not slow"`, and change its `##` comment to "Run only tests that need no downloaded data and no long simulations".

- [ ] **Step 2: Write the failing tests** (append to `tests/test_annual_breaks.py`):

```python
def test_bootstrap_range_covers_planted_break():
    dp = simulate(lambda y: 0.03 if y < 1978 else 0.0, noise=0.02)
    r = ab.bootstrap_break_year(dp, draws=199)
    assert r.low <= 1978 <= r.high and r.high - r.low <= 10
    assert len(r.estimates) == 199


def test_bootstrap_survives_a_year_with_a_single_unit():
    dp = simulate(lambda y: 0.03 if y < 1978 else 0.0, n_units=20, years=range(1960, 2000), noise=0.05)
    dp = dp[(dp.year != 1990) | (dp.geo_id == "u0")]  # 1990 often has no unit in a draw
    r = ab.bootstrap_break_year(dp, draws=99)
    assert 1960 <= r.low <= r.high <= 1999 and not np.isnan(r.estimates).any()


def test_bai_interval_contains_break_and_narrows_with_signal():
    weak = simulate(lambda y: 0.03 if y < 1978 else 0.0, noise=0.03)
    strong = simulate(lambda y: 0.03 if y < 1978 else 0.0, noise=0.01)
    lo_w, hi_w = ab.bai_interval(weak, ab.sup_wald_break(weak))
    lo_s, hi_s = ab.bai_interval(strong, ab.sup_wald_break(strong))
    assert lo_w <= 1978 <= hi_w and lo_s <= 1978 <= hi_s
    assert hi_s - lo_s < hi_w - lo_w


def test_range_coverage_returns_fractions():
    dp = simulate(lambda y: 0.03 if y < 1978 else 0.0, noise=0.05, years=range(1969, 2024))
    cov = ab.range_coverage(dp, ab.sup_wald_break(dp), sims=10, draws=49)
    assert set(cov) == {"bootstrap", "bai"} and all(0 <= v <= 1 for v in cov.values())


@pytest.mark.slow
def test_bootstrap_range_coverage_meets_the_rule():
    # Plan 1b spec §6: >= 200 synthetic panels; the 90% range must contain the planted year
    # at least COVERAGE_MIN of the time (the prototype gave 0.945). The noise is high on purpose,
    # so the range is wide and coverage is a real test.
    dp = simulate(lambda y: 0.03 if y < 1978 else 0.0, noise=0.05)
    cov = ab.range_coverage(dp, ab.sup_wald_break(dp), sims=200, draws=199)
    assert cov["bootstrap"] >= ab.COVERAGE_MIN, cov
```

Run: `venv/bin/python -m pytest tests/test_annual_breaks.py -q`. Expected: the new tests FAIL (AttributeError).

- [ ] **Step 3: Implement** (append to `annual_breaks.py`):

```python
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
```

Run: `venv/bin/python -m pytest tests/test_annual_breaks.py -q -m "not slow"`, then `venv/bin/python -m pytest tests/test_annual_breaks.py -q -m slow`. Expected: all pass. The slow test takes about 10–20 s. If the slow test fails, **don't tune it**: report the coverage numbers to the owner. Under the spec, a failure means Bai's interval becomes the reported range.

- [ ] **Step 4: Commit.**

```bash
make test-fast
git add us_housing_crisis_analysis/modeling/annual_breaks.py tests/test_annual_breaks.py pyproject.toml Makefile
git commit -m "Break-year range: unit bootstrap, Bai interval, coverage check (Plan 1b)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WK1JcWFMpphC1KeQcaYjNr"
```

---

### Task 6: Multi-break cross-check with year effects removed once

*Can run in parallel with Task 5.*

**Files:**
- Modify: `us_housing_crisis_analysis/modeling/annual_breaks.py`, `tests/test_annual_breaks.py`

**Interfaces:**
- Consumes: Task 4 (`_arrays`, `_demean`, `_sums`); `breaks.break_search(..., period="year")` and `breaks.BreakSearch` (Task 3).
- Produces: `annual_breaks.demeaned_break_search(dp, max_breaks=3, min_segment=5) -> breaks.BreakSearch`. It has the same candidates, segment rule and BIC as `breaks.break_search(dp, max_breaks, min_segment, period="year")`, but no dummies.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_annual_breaks.py`):

```python
def test_demeaned_search_matches_brute_force_with_year_dummies():
    dp = simulate(lambda y: 0.03 if y < 1968 else 0.0, n_units=20, years=range(1960, 1978))
    fast = ab.demeaned_break_search(dp, max_breaks=2, min_segment=3)
    slow = breaks.break_search(dp, max_breaks=2, min_segment=3, period="year")
    assert fast.breaks == slow.breaks == (1968,)
    assert set(fast.bic) == set(slow.bic)
    assert all(fast.bic[k] == pytest.approx(slow.bic[k], abs=1e-6) for k in slow.bic)


def test_demeaned_search_finds_planted_break_and_none_when_absent():
    assert ab.demeaned_break_search(simulate(lambda y: 0.03 if y < 1978 else 0.0)).breaks == (1978,)
    assert ab.demeaned_break_search(simulate(lambda y: 0.02)).breaks == ()
```

Run: `venv/bin/python -m pytest tests/test_annual_breaks.py -q -m "not slow"`. Expected: the new tests FAIL (AttributeError).

- [ ] **Step 2: Implement.** Append to `annual_breaks.py`, and add `from itertools import combinations` to the imports:

```python
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
```

Run: `venv/bin/python -m pytest tests/test_annual_breaks.py -q -m "not slow"`. Expected: all pass.

- [ ] **Step 3: Commit.**

```bash
make test-fast
git add us_housing_crisis_analysis/modeling/annual_breaks.py tests/test_annual_breaks.py
git commit -m "Multi-break cross-check on annual data, year effects removed once (Plan 1b)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WK1JcWFMpphC1KeQcaYjNr"
```

---

### Task 7: Notebook section, outputs, finding and docs

**Files:**
- Modify: `notebooks/1.1-lr-us-structural-break.ipynb`, `Claude/methods/analysis-methods.md`, `Claude/methods/decisions.md`, `docs/superpowers/specs/2026-10-08-housing-growth-mismatch-design.md`
- Create: `reports/figures/rq0b_annual_betas.png`, `reports/tables/rq0b_annual_tests.csv`, `reports/tables/rq0b_annual_range_coverage.csv`

**Interfaces:**
- Consumes: everything above.
- Produces: the outputs listed above. The `rq0b_annual_tests.csv` columns are `version, spec, trim, break_year, at_edge, range_low, range_high, bai_low, bai_high, reported_range, sup_wald, sup_wald_cv5, beta_before_annual, beta_after_annual, beta_before_10y, beta_after_10y, multi_breaks, n_units, years`.

- [ ] **Step 1: Export the notebook to a scratch percent script.**

```bash
venv/bin/python -m jupytext --to py:percent notebooks/1.1-lr-us-structural-break.ipynb -o notebooks/1.1-lr-us-structural-break.py
```

- [ ] **Step 2: Append the new section** to the end of `notebooks/1.1-lr-us-structural-break.py`:

```python
# %% [markdown]
# ## Annual data: when did the break happen? (Plan 1b)
#
# BEA only, every year: states 1929–2024, metros 1969–2024. Two views:
# - **Rolling β (the picture):** the decade model on ten-year windows starting every year
#   (and five-year windows as a check).
# - **Single break (the test):** one-year growth with year fixed effects and a slope that changes
#   in year T. sup-Wald (clustered by unit) against Andrews' critical value says whether there is a
#   break; T is the best-fitting year; the range comes from resampling units (checked by
#   simulation) with Bai's (1997) interval alongside.
#
# One-year slopes are about a tenth of the ten-year β; the ×10 columns put them on the decade scale.

# %%
from us_housing_crisis_analysis import features
from us_housing_crisis_analysis.config import (
    ENERGY_STATES_HAND, INTERIM_DATA_DIR, RQ0B_ANNUAL_END, RQ0B_ANNUAL_METRO_START,
    RQ0B_ANNUAL_STATE_START, WWII_GROWTH_YEARS,
)
from us_housing_crisis_analysis.modeling import annual_breaks as ab
from us_housing_crisis_analysis.plots import MUTED, SERIES_COLORS, SERIES_MARKERS

annual = {"states": pd.read_parquet(PROCESSED_DATA_DIR / "us_state_annual.parquet"),
          "metros": pd.read_parquet(PROCESSED_DATA_DIR / "us_metro_annual.parquet")}
energy = features.energy_states(pd.read_parquet(INTERIM_DATA_DIR / "bea.parquet"))
energy_rule = set(energy.loc[energy.energy, "state_fips"])
print("Energy states by the rule:", ", ".join(energy.loc[energy.energy, "state_name"]))
energy.head(12).round(3)

# %% [markdown]
# ### Rolling β by window start

# %%
starts = {"states": RQ0B_ANNUAL_STATE_START, "metros": RQ0B_ANNUAL_METRO_START}
rolling = {(name, h): ab.rolling_betas(p, h, starts[name], RQ0B_ANNUAL_END)
           for name, p in annual.items() for h in (10, 5)}

# %% [markdown]
# ### Single-break tests: main specification and robustness

# %%
def growth(name, start=None):
    return ab.annual_growth_panel(annual[name], start or starts[name], RQ0B_ANNUAL_END)

def growth_without(name, fips):
    return ab.annual_growth_panel(features.drop_states(annual[name], fips), starts[name], RQ0B_ANNUAL_END)

runs = [  # (version, spec, growth panel, trim)
    ("states", "main", growth("states"), 0.15),
    ("states", "without energy states (rule)", growth_without("states", energy_rule), 0.15),
    ("states", "without energy states (hand list)", growth_without("states", set(ENERGY_STATES_HAND)), 0.15),
    ("states", "standardized income", breaks.standardize_within_decade(growth("states"), period="year"), 0.15),
    ("states", "without WWII years", growth("states")[lambda d: ~d.year.isin(WWII_GROWTH_YEARS)], 0.15),
    ("states", "1969-2024 only", growth("states", RQ0B_ANNUAL_METRO_START), 0.15),
    ("states", "1969-2024 only", growth("states", RQ0B_ANNUAL_METRO_START), 0.05),
    ("metros", "main", growth("metros"), 0.15),
    ("metros", "main", growth("metros"), 0.05),
    ("metros", "without energy states (rule)", growth_without("metros", energy_rule), 0.15),
    ("metros", "without energy states (hand list)", growth_without("metros", set(ENERGY_STATES_HAND)), 0.15),
    ("metros", "standardized income", breaks.standardize_within_decade(growth("metros"), period="year"), 0.15),
]

# The bootstrap range is used where its simulated coverage meets the rule; otherwise Bai's interval
coverage = []
for version in ("states", "metros"):
    dp = next(d for v, s, d, tr in runs if v == version and s == "main" and tr == 0.15)
    cov = ab.range_coverage(dp, ab.sup_wald_break(dp))
    coverage.append({"version": version, **cov})
coverage = pd.DataFrame(coverage).set_index("version")
use_bootstrap = coverage.bootstrap >= ab.COVERAGE_MIN

rows = []
for version, spec, dp, trim in runs:
    r = ab.sup_wald_break(dp, trim)
    boot = ab.bootstrap_break_year(dp, trim)
    bai = ab.bai_interval(dp, r)
    multi = ab.demeaned_break_search(dp)
    rows.append({
        "version": version, "spec": spec, "trim": trim, "break_year": r.break_year, "at_edge": r.at_edge,
        "range_low": boot.low, "range_high": boot.high, "bai_low": bai[0], "bai_high": bai[1],
        "reported_range": "bootstrap" if use_bootstrap[version] else "bai",
        "sup_wald": r.sup_wald, "sup_wald_cv5": r.critical_value,
        "beta_before_annual": r.beta_before, "beta_after_annual": r.beta_after,
        "beta_before_10y": 10 * r.beta_before, "beta_after_10y": 10 * r.beta_after,
        "multi_breaks": " ".join(map(str, multi.breaks)), "n_units": r.n_units,
        "years": f"{r.first_year}-{r.last_year}",
    })
annual_tests = pd.DataFrame(rows)
annual_tests.to_csv(TABLES_DIR / "rq0b_annual_tests.csv", index=False)
coverage.to_csv(TABLES_DIR / "rq0b_annual_range_coverage.csv")
display(coverage.round(3))
annual_tests.round(4)

# %% [markdown]
# ### Figure: rolling β with the estimated break and its range

# %%
main = annual_tests[(annual_tests.spec == "main") & (annual_tests.trim == 0.15)].set_index("version")
fig, axes = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
for ax, h in zip(axes, (10, 5)):
    for i, name in enumerate(("states", "metros")):
        b, color = rolling[(name, h)], SERIES_COLORS[i]
        ax.plot(b.start, b.beta, color=color, marker=SERIES_MARKERS[i], markevery=5, label=name)
        ax.fill_between(b.start, b.beta - 1.96 * b.se, b.beta + 1.96 * b.se, color=color, alpha=0.12, lw=0)
        m = main.loc[name]
        lo, hi = (m.range_low, m.range_high) if m.reported_range == "bootstrap" else (m.bai_low, m.bai_high)
        ax.axvspan(lo, hi + 1, color=color, alpha=0.10, lw=0)
        ax.axvline(m.break_year, color=color, ls="--", lw=1)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set(ylabel=f"β, {h}-year growth on log income")
    ax.set_title(f"{h}-year windows by start year", loc="left", fontsize=11)
for i, (name, b) in enumerate(betas.items()):  # decade β from Plan 1, ten-year panel only
    b = b[b.decade >= starts[name]]
    axes[0].scatter(b.decade, b.beta, edgecolors=SERIES_COLORS[i], marker=SERIES_MARKERS[i], s=40,
                    facecolors="none", zorder=3, label=f"{name}, decade β")
axes[0].legend(ncols=2)
axes[1].set(xlabel="Window start year")
fig.suptitle("When did population stop flowing toward richer places? (dashed: estimated break; shaded: range)",
             x=0.01, ha="left", fontsize=11)
save_figure(fig, "rq0b_annual_betas")

# %% [markdown]
# **Annual finding (fill in after running):** two to four plain sentences. Say whether sup-Wald
# exceeds the critical value (states, metros); the break year and reported range (write "at or
# before" where `at_edge`); whether it holds without the energy states (both lists), without the
# WWII years and with 5% trimming; what the multi-break search adds; and β before/after on the
# ten-year scale. Close with the sentence for the paper: "The break most likely happened around
# year X (range Y–Z); it holds up without the energy states", or say plainly that annual data
# can't pin it down, and why.
```

- [ ] **Step 3: Regenerate, execute and look at the outputs.**

```bash
venv/bin/python -m jupytext --to notebook notebooks/1.1-lr-us-structural-break.py -o notebooks/1.1-lr-us-structural-break.ipynb
rm notebooks/1.1-lr-us-structural-break.py
make notebooks
ls reports/figures/rq0b_annual_betas.png reports/tables/rq0b_annual_tests.csv reports/tables/rq0b_annual_range_coverage.csv
```

Expected: the notebook runs without errors (the coverage cell takes about a minute), and all three files exist. Open the figure and the table. Check the following, and report anything odd instead of adjusting it:
- The decade points sit on the ten-year curve.
- The ×10 β values are on the decade β's scale.
- The energy list printed matches the eight states in the Execution notes.

- [ ] **Step 4: Write the finding.** Replace the "(fill in after running)" cell with the actual finding, in plain language and following the cell's own instructions. Re-execute with `make notebooks`. A notebook that still contains "(fill in after running)" isn't finished.

- [ ] **Step 5: Run the full suite.** Run: `make test` and `venv/bin/python -m pytest -m slow`. Expected: all pass, with no data tests skipped.

- [ ] **Step 6: Update the docs.**
  - **`Claude/methods/analysis-methods.md`:**
    - Add a section "RQ0b — annual break dating (states 1929–2024, metros 1969–2024)" after the decennial RQ0b section. Cover the model, the demeaning, the trimming and candidate years, sup-Wald with simulated Andrews values, the bootstrap with the coverage rule, the Bai interval, the multi-break search, the energy rule with its list, the robustness rows and the two β scales.
    - Add a Results log entry with the date and the main numbers from `rq0b_annual_tests.csv`.
  - **`Claude/methods/decisions.md`:** add D-28, "Plan 1b judgment calls". It covers:
    - the energy list (the rule picks KY over ND, so the hand list runs too);
    - data-driven split growth years (2001, 1982, 1981; the spec's "La Paz 1983" was the legal year);
    - the coverage rule as the owner decided it;
    - candidate positions by floor(trim · n);
    - the extra table columns.
    - Mark the owner's decisions "user" and the rest "Claude". Update "Open items": Plan 1b done, next is Plan 2 (RQ0a), and RQ0c is in design.
  - **Master spec** (`2026-10-08-housing-growth-mismatch-design.md`): apply the Plan 1b spec's §10 "Spec changes on approval":
    - §2 RQ0b years;
    - §4 panels (`us_state_annual`; `us_metro_annual` from 1969);
    - §5 the annual method (a short paragraph pointing to the Plan 1b spec);
    - §8 risks (the oil cycle, intercensal smoothing);
    - §10 build step 2b.

- [ ] **Step 7: Commit.**

```bash
git add notebooks reports/figures/rq0b_annual_betas.png reports/tables Claude docs/superpowers/specs/2026-10-08-housing-growth-mismatch-design.md
git commit -m "Date the RQ0b break with annual data: notebook section, outputs, finding (Plan 1b)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WK1JcWFMpphC1KeQcaYjNr"
```

---

## Spec coverage (Plan 1b)

| Spec item | Task |
|---|---|
| §3 `us_state_annual` (SAINC1 lines 2 and 3), `us_metro_annual` (CAINC1 county sums, D-23), energy classification (SAINC5S) | 1, 2 |
| §3 one source; geography rules; county splits dropped (D-27) | 2, 3 |
| §4.1 rolling-window β, states 1929–2014 and metros 1969–2014 starts, HC1 | 3 |
| §4.2 pooled annual model with year FE; break year by SSR; trimming 15%, 5% check; "at or before" | 4, 7 |
| §4.2 sup-Wald, clustered by unit, Andrews values simulated | 4 |
| §4.2 bootstrap range (999 draws), Bai (1997) interval, coverage check | 5 |
| §4.2 multi-break cross-check (up to 3, segments ≥ 5 years), year effects removed once | 6 |
| §4.2 two scales for β | 4, 7 |
| §4.3 without energy states (rule and hand list), five-year windows, standardized income, states 1969+, without WWII years, 5% trimming, decade cross-check | 3, 7 |
| §5 components and outputs (figure, table with `trim` column) | 1–7 |
| §6 synthetic recovery (planted 1978, no break, oil cycle), rolling β, range coverage, demeaned = brute force | 3–6 |
| §6 data tests (population sums 1930–2020 without AK/HI before 1950; metro 2020; positive income; uniqueness; decade cross-check; D-27 years) | 2, 3 |
| §8 decisions (order, energy rule, notebook 1.1, trimming) | Global Constraints, 7 |
| §10 master spec changes | 7 |
