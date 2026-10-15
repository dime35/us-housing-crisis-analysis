# Plan 3: RQ0c, Did Other Countries See the Same Change at the Same Time? — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run RQ0b's test inside other countries. Within each country and decade, did richer regions (and the cities in them) grow faster? Then compare the change in peers with the US change at 1970, 1980 and 1990, and fit the master spec's national-GDP model as labeled context.

**Architecture:**
- **New data sources:** five source modules (UN WUP, Maddison, World Bank, DOSE, Rosés-Wolf), plus a sixth for Japan's census population by prefecture (e-Stat).
- **`global_geography.py` (new):** builds two committed crosswalks.
  - `peer_groups.csv`: one fixed peer group per country.
  - `wup_to_region.csv`: each city matched to the region containing it (point-in-polygon on GISCO NUTS 2010 and GADM 4.1 level-1 boundaries).
- **`features.py`:** gains `global_regions` (region × decade) and `global_agglomerations` (agglomeration × 5 years).
- **`modeling/global_timing.py` (new):** reuses `breaks.py` unchanged. Country × decade constants are removed by demeaning first. The cluster-robust degrees of freedom are then corrected, which reproduces the explicit-dummy regression exactly (checked in a prototype).
- **Notebook `1.2-lr-global-timing`:** writes three figures and two tables.

**Tech Stack:** Python 3.12, pandas, numpy, statsmodels, scipy (via statsmodels), geopandas + pyogrio (used only to build the city→region crosswalk), xlrd (WUP 2018 `.xls`), python-calamine (the e-Stat file is "strict" OOXML, which openpyxl reads as an empty workbook), matplotlib, pytest, jupytext, nbconvert.

**Spec:** `docs/superpowers/specs/2026-10-14-rq0c-global-timing-design.md` (approved 2026-10-14, all eight §8 decisions as recommended). Master spec: `docs/superpowers/specs/2026-10-08-housing-growth-mismatch-design.md`. Executors read both.

## Global Constraints

- **Branch:** work on `rq0c-global-timing-design`, rebased onto `plan-1-rq0b` (Plan 1b is merged there at `c1df6ad`) in Task 1. Don't merge into `master`.
- **Where data lives:** `data/` is gitignored and exists only in the main checkout. Inside the worktree `.claude/worktrees/agent-a2ed2095526358eb2`, Task 1 links `data` to the main checkout's folder.
- **Running tools:** the worktree uses the main checkout's venv by absolute path. Every command below assumes `PY="/Users/lrubin/Documents/code/US Housing Crisis Analysis/venv/bin/python"`, so run tools as `"$PY" -m ...` and make targets with `PYTHON_INTERPRETER="$PY"`. `make test-fast` runs the tests that need no data.
- **One source per country for regional data:** Rosés-Wolf v7 covers its 16 countries. DOSE V2.11 covers every other country. Japan takes its population from the e-Stat census and its income from DOSE.
- **No invention (D-27):**
  - Nothing is interpolated.
  - A unit missing a value drops out of that decade only.
  - Agglomerations in countries without Maddison GDP for a period are dropped for that period, never filled from a parent country.
- **Decades:** region decades start 1950–2010, with growth to 2020. Cities run 1950–2015 in 5-year steps; values after 2015 are projections and are never loaded.
- **Comparisons are within a country:** every model has country × decade constants (`country_unit` × `decade`). East German (GDR) regions are their own `country_unit`, `DEU_EAST`, before 1990, and Berlin (DE30) is dropped before 1990 (see the Execution notes).
- **US break decades (spec §5.1 with Plan 1b's result, D-28):** `US_BREAK_DECADES = (1970, 1990)`. Plan 1b dated the state break at about 1970 or about 1990, so the range spans two decade boundaries and both rows are headlined. The spec's provisional "1980" no longer applies. All three of 1970, 1980 and 1990 are still computed and tabled.
- **Peer groups:** fixed for the whole period, by the rule in spec §3.5, five groups. The committed table is `references/crosswalks/peer_groups.csv`.
- **Docs:** every task that adds a source, method or decision updates `Claude/research/sources.md` or `Claude/methods/*.md` in the same commit. The decision entry is D-29 (Task 12).
- **Commits:** commit after every task. Messages end with:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  ```

## Execution notes (found while writing this plan, 2026-10-14; every file below was downloaded and read)

- **Japan (owner decided 2026-10-14):** DOSE has prefecture GDP per head from 1960 but **population only from 1975**. Population for 1950–1975 comes from the official census time series on e-Stat (`da01.xlsx`, statInfId 000001085925, CC BY), sheet `人口`, total columns for every census year 1920–2020. Its 1980 values equal DOSE's exactly (Tokyo 11,618,281; Okinawa 1,106,559), so census population is used for every Japanese year. Prefectures map to DOSE/GADM IDs through `references/crosswalks/jp_prefectures.csv`; its full content is in Task 4.
- **Australia** has almost no DOSE data before 1976 (population in 1953 only), so it shows only the period after 1980, like Canada (DOSE from 1981) and Korea (1985). Spec §3.3 said "sparse"; it is effectively absent before 1980.
- **Rosés-Wolf v7** (`RosesWolf_RegionalGDP_v7.xlsx`, downloaded by the owner into `data/raw/roses_wolf/`):
  - **Coverage:** 16 countries and 173 units, a mix of NUTS-2 units, merged NUTS-2 pairs (`AT12+AT13`) and NUTS-1 units (all of the UK, `IE0`).
  - **Sheets:** `A3 Population` (thousands), `A1b Regional GDP (2011PPP)` (millions) and `A1 Regional GDP` (1990 PPP, millions, to 2015). The header is on row 6 (`header=5`). Missing cells are `"."`.
  - **2020 is present**, so the region panel needs no "2010–2015 × 2" step (spec §4.1 fallback unused).
  - **One-region countries:** Ireland and Luxembourg have one unit each, so they drop out of every within-country comparison.
  - **East Germany is included from 1950.** Before 1990, migration between the two German states was blocked, so the GDR regions (DE40, DE80, DED2, DED4, DED5, DEE0, DEG0) form their own country unit, `DEU_EAST`. Berlin (DE30) combines East and West and is dropped before 1990. Flagged for the owner's review as D-29.
  - **The spec's 2% check against Maddison population** fails for known reasons: Portugal excludes Azores and Madeira (−3% to −6%), France excludes its overseas regions (−3.9% in 2020), Flevoland (NL23) didn't exist in 1950 (−2.6%), and Denmark 1980 is +5.1%. The data test uses per-country tolerances (Task 8).
- **DOSE V2.11:** income is `grp_pc_usd_2015` and population is `pop`. Only exact decade years are used (no nearest-year substitution). DOSE vs BEA US state population: equal in 1980 and 2000, and at most 1.09% apart in 1970. The spec's 1% check becomes "max 1.5%, median 0.5%" (Task 8).
- **DOSE region IDs match GADM 4.1 level 1** (checked for JPN, USA, CHN, BRA, MEX and IND; only IND.14_1 is missing from GADM 4.1). Boundaries: `https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_{ISO3}_1.json.zip`.
- **Rosés-Wolf boundaries:** the owner's download has no shapefile. The plan uses GISCO NUTS 2010 at 1:20M (all levels, `NUTS_RG_20M_2010_4326.geojson`, 18 MB), dissolving merged codes. Every Rosés-Wolf code part exists in NUTS 2010.
  - **Prototype matching:** 139 of 142 cities in the 16 countries fall inside a region. Venezia, Vigo and Bournemouth/Poole lie just off the generalized coastline, so they get the nearest region in their own country, flagged. London → UKI, Paris → FR10, Berlin → DE30, Hamburg → DE60, Madrid → ES30; all 33 Japanese cities match a prefecture.
- **WUP 2018:**
  - **File 12:** header row 17 (`skiprows=16`). Values are in thousands. Countries carry an M49 numeric code; ISO3 comes from the data-sources file. 1,860 agglomerations, 144 US; Tokyo 1950 = 11,274.641, New York–Newark 1950 = 12,338.471, Detroit 1950 = 2,769.254.
  - **Statistical concept** (data-sources file): 1,038 urban agglomeration, 644 city proper, 178 metropolitan area.
  - **File 21 (urban %)** uses the same header layout. The locations file `F00` (xlsx, `header=None, skiprows=17`) maps codes to ISO3, UN region and subregion; 233 countries have location type 4.
- **Agglomeration countries missing from Maddison:** ERI, MAC, PNG, SOM, SSD. They are dropped from the context model, and the notebook prints them. Maddison also has the aggregates SUN, CSK and YUG, which are not loaded.
- **WUP 2025 File 21** (Degree of Urbanisation cities): sheet `Data`, header on row 1, columns `ISO3_Code`, `City_Code`, `City_Name`, `PWCent_Longitude`, `PWCent_Latitude`, then years 1975–2050, in thousands.
- **World Bank `OGHIST.xlsx`:** sheet `Country Analytical History`. Data years are on row 6 (1987–2023) and countries start on row 12, with ISO3 in column A. Letter codes are L/LM/UM/H, and `..` means not classified.
- **WUP growth outliers:** 21 five-year steps in 14 agglomerations halve or more than triple. Shenzhen, Phnom Penh, Cancún, Port St. Lucie and 10 others are added to `growth_allowlist.csv` in Task 8.
- **Prototype checks (scratch code, 2026-10-14):**
  - **Demeaning check:** demeaning within country × decade, then `breaks.chow_test`, with the statistic rescaled by (N − K_true)/(N − K_demeaned), reproduces the explicit country × decade dummy regression to 12 significant digits at 1970, 1980 and 1990.
  - **Real data:** Rosés-Wolf + Japan pooled (17–18 country units, 171–220 regions per decade) gives β ≈ 0.17, 0.21, 0.11, 0.02, 0.08, 0.10, 0.08 for the 1950s–2010s, and BIC picks a break at 1970. Treat these as a smoke test of the pipeline, not results.

## Review Focus

1. **A region present in a decade but missing income** must drop out of that decade only, never be zero-filled, and never have its growth bridge a gap. Examples: Japan in 1950 (DOSE income starts in 1960), NL23 before 1970, Okinawa before 1972. Tested in Task 8 (`build_global_regions`) and Task 9 (`region_decades`).
2. **A country-decade with a single region** (Ireland, Luxembourg, or a country whose other regions lack income that decade) must not enter β, the tests or the counts. Demeaning makes its values exactly zero, but they would still inflate N and shrink standard errors. Tested in Task 9 (`demean_within`).
3. **GDR regions before 1990** must never share a country × decade constant with West German regions, and Berlin must not appear before 1990. Tested in Task 8.
4. **An agglomeration-period without national GDP** (former Soviet republics before 1973, Czechia before 1970, Slovakia before 1985, MAC/ERI/PNG/SOM/SSD always) must drop out of the context model and not be filled from another country. Tested in Task 11 (`five_year_panel`).
5. **A coastal city outside every generalized polygon** must get the nearest region in its own country, flagged `nearest`, and never a region across a border. Tested in Task 7 (`match_points`).

---

## File structure

| File | Responsibility | Task |
|---|---|---|
| `.gitignore`, `pyproject.toml` | `/data` ignored as a link too; new dependencies | 1 |
| `us_housing_crisis_analysis/schema.py` | `region` level (`nuts2:`, `gadm1:`); `dou:` agglomerations | 1 |
| `us_housing_crisis_analysis/config.py` | RQ0c constants | 1 |
| `us_housing_crisis_analysis/sources/un_wup.py` (new) | WUP 2018 Files 12, 21, F00 and data sources; WUP 2025 File 21 | 2 |
| `us_housing_crisis_analysis/sources/maddison.py` (new) | Maddison 2023 GDP per head and population | 3 |
| `us_housing_crisis_analysis/sources/worldbank.py` (new) | WDI GDP per head; OGHIST income groups | 3 |
| `us_housing_crisis_analysis/sources/dose.py` (new) | DOSE regional population and GDP per head | 4 |
| `us_housing_crisis_analysis/sources/estat_japan.py` (new) | Japan census population by prefecture | 4 |
| `references/crosswalks/jp_prefectures.csv` (new) | JIS prefecture code → GADM/DOSE `GID_1` | 4 |
| `us_housing_crisis_analysis/sources/roses_wolf.py` (new) | Rosés-Wolf v7 (manual download) | 5 |
| `us_housing_crisis_analysis/sources/__init__.py` | Append six names to `SOURCE_NAMES` | 2–5 |
| `us_housing_crisis_analysis/global_geography.py` (new) | Peer-group rule; boundaries; city → region matching; CLI writing both crosswalks | 6, 7 |
| `references/crosswalks/peer_groups.csv`, `wup_to_region.csv` (new) | Committed, reviewed crosswalks | 6, 7 |
| `us_housing_crisis_analysis/features.py` | `build_global_regions`, `build_global_agglomerations`, `main()` entries | 8 |
| `references/crosswalks/growth_allowlist.csv`, `references/known_values.csv` | WUP rows | 8 |
| `us_housing_crisis_analysis/modeling/global_timing.py` (new) | Within-country β, Chow, BIC, US-vs-peers, city panel, national model | 9–11 |
| `tests/test_un_wup.py`, `test_maddison.py`, `test_worldbank.py`, `test_dose.py`, `test_estat_japan.py`, `test_roses_wolf.py`, `test_global_geography.py`, `test_global_timing.py` (new); `test_schema.py`, `test_features.py` | Unit tests | 1–11 |
| `tests/data/test_global.py` (new) | Data tests on interim and processed data | 2–8 |
| `notebooks/1.2-lr-global-timing.ipynb` (new) | RQ0c notebook | 12 |
| `reports/figures/rq0c_*.png`, `reports/tables/rq0c_*.csv` | Outputs | 12 |
| `Claude/…`, master spec | Docs | every task, 12 |

**Order and parallelism:** Task 1 comes first. **Tasks 2–5 are independent source modules** and can run in parallel; each appends one or two names to `SOURCE_NAMES` and one row to `sources.md`, so expect trivial merges. Task 6 needs 2 and 3. Task 7 needs 2, 4 and 5. Task 8 needs 2–7. **Tasks 9 and 11 are independent of each other**; both need Task 8 only for data, and their unit tests are synthetic. Task 10 needs 9. Task 12 needs everything.

---

### Task 1: Branch, dependencies, schema and config

**Files:**
- Modify: `.gitignore`, `pyproject.toml`, `us_housing_crisis_analysis/schema.py`, `us_housing_crisis_analysis/config.py`
- Test: `tests/test_schema.py`

**Interfaces:**
- Produces: `GEO_PREFIXES["region"] == ("nuts2:", "gadm1:")`; `GEO_PREFIXES["agglomeration"] == ("wup:", "dou:")`; config names `RQ0C_START`, `RQ0C_END`, `RQ0C_CITY_END`, `RQ0C_COMPARE_YEARS`, `US_BREAK_DECADES`, `GDR_REGIONS`, `GDR_BERLIN`, `GDR_UNTIL`.

- [ ] **Step 1: Rebase the branch onto Plan 1b's result.** In the worktree:

```bash
cd "/Users/lrubin/Documents/code/US Housing Crisis Analysis/.claude/worktrees/agent-a2ed2095526358eb2"
git status --short            # must be clean
git rebase plan-1-rq0b
```

The branch holds three commits: the sources.md rows, the spec and the approval. If `Claude/research/sources.md` conflicts, keep both sides: Plan 1b changed the BEA row, and this branch changed the WUP, World Bank, Maddison, Rosés-Wolf, DOSE and OECD rows. Then run `git log --oneline -5` and expect `f06d030`'s message on top of `c1df6ad`.

- [ ] **Step 2: Make the data folder visible in the worktree.** In `.gitignore`, change the line `/data/` to `/data`. The trailing slash only matches real directories, so it wouldn't ignore a link. Then:

```bash
ln -s "/Users/lrubin/Documents/code/US Housing Crisis Analysis/data" data
git status --short   # shows only .gitignore modified; `data` must not appear
```

- [ ] **Step 3: Add dependencies.** In `pyproject.toml`, extend `dependencies` with `"xlrd>=2.0", "python-calamine>=0.2", "geopandas>=1.0", "pyogrio>=0.7"`, then install:

```bash
PY="/Users/lrubin/Documents/code/US Housing Crisis Analysis/venv/bin/python"
"$PY" -m pip install -e . 2>&1 | tail -1
"$PY" -c "import xlrd, python_calamine, geopandas, pyogrio; print('ok')"
```

Expected: `ok`.

- [ ] **Step 4: Write the failing schema tests.** Append to `tests/test_schema.py`:

```python
def region_frame(geo_id: str, level: str = "region") -> pd.DataFrame:
    df = good_frame().iloc[[0]].copy()
    df["geo_id"], df["geo_level"] = geo_id, level
    return df


@pytest.mark.parametrize("geo_id", ["nuts2:AT12+AT13", "nuts2:UKI", "gadm1:JPN.41_1"])
def test_region_level_accepts_roses_wolf_and_gadm_ids(geo_id):
    assert len(validate_long(region_frame(geo_id))) == 1


def test_region_level_rejects_other_prefixes():
    with pytest.raises(SchemaError, match="prefix"):
        validate_long(region_frame("state:24"))


def test_degree_of_urbanisation_cities_are_agglomerations():
    assert len(validate_long(region_frame("dou:4555", "agglomeration"))) == 1
```

- [ ] **Step 5: Run the tests and see them fail.**

Run: `"$PY" -m pytest tests/test_schema.py -q`
Expected: FAIL with `unknown geo_level values: ['region']`, and a prefix error for `dou:`.

- [ ] **Step 6: Implement.** In `schema.py`, set the `agglomeration` entry and add `region`:

```python
    "agglomeration": ("wup:", "dou:"),  # dou: = WUP 2025 Degree of Urbanisation cities
    "region": ("nuts2:", "gadm1:"),  # Rosés-Wolf units (NUTS 2010 codes, '+' if merged); GADM level 1
```

Append to `config.py`, after `WWII_GROWTH_YEARS`:

```python
# RQ0c (Plan 3): within-country pull of richer regions abroad. Region decades start 1950-2010
# (growth to 2020); cities stop at 2015, the last WUP 2018 estimate (later values are projections).
RQ0C_START = 1950
RQ0C_END = 2020
RQ0C_CITY_END = 2015
RQ0C_COMPARE_YEARS = (1970, 1980, 1990)
# Plan 1b (D-28) dated the US state break at about 1970 or about 1990; the range spans two decade
# boundaries, so both rows are headlined (RQ0c spec §5.1)
US_BREAK_DECADES = (1970, 1990)
# East Germany before reunification: its regions are their own country unit (migration between
# the two German states was blocked); Berlin (East and West together) is dropped before 1990
GDR_REGIONS = ("DE40", "DE80", "DED2", "DED4", "DED5", "DEE0", "DEG0")
GDR_BERLIN = "DE30"
GDR_UNTIL = 1990
```

- [ ] **Step 7: Run the tests and see them pass.**

Run: `"$PY" -m pytest tests/test_schema.py -q && make test-fast PYTHON_INTERPRETER="$PY"`
Expected: all pass.

- [ ] **Step 8: Commit.**

```bash
git add .gitignore pyproject.toml us_housing_crisis_analysis/schema.py us_housing_crisis_analysis/config.py tests/test_schema.py
git commit -m "RQ0c setup: region geo level, RQ0c constants, xlrd/calamine/geopandas (Plan 3)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: `sources/un_wup.py`, UN World Urbanization Prospects

**Files:**
- Create: `us_housing_crisis_analysis/sources/un_wup.py`, `tests/test_un_wup.py`, `tests/data/test_global.py`
- Modify: `us_housing_crisis_analysis/sources/__init__.py`, `Claude/research/sources.md`, `Claude/methods/pipeline.md`

**Interfaces:**
- Produces:
  - `un_wup.load() -> DataFrame` (long format), with three variables:
    - `population`: `wup:<City Code>`, persons, 1950–2015 every 5 years;
    - `urban_share`: `iso3:<ISO3>`, percent, annual 1950–2015;
    - `population_degurba`: `dou:<City_Code>`, persons, 1975–2015 every 5 years.
  - `un_wup.agglomeration_attributes() -> DataFrame` with columns `geo_id, geo_name, iso3, latitude, longitude, concept, capital, census_years`. `census_years` is a space-separated string, e.g. `"1950 1960 2010"`.
  - `un_wup.country_locations() -> DataFrame` with columns `code` (int M49), `iso3`, `name`, `region`, `subregion`, for the 233 countries.
  - `un_wup.census_years(text: str) -> list[int]`.

- [ ] **Step 1: Write the failing tests.** Create `tests/test_un_wup.py`:

```python
import numpy as np
import pandas as pd
import pytest

from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import un_wup

YEARS = list(range(1950, 2036, 5))


def f12() -> pd.DataFrame:
    head = ["Index", "Country Code", "Country or area", "City Code", "Urban Agglomeration", "Note",
            "Latitude", "Longitude"]
    rows = [[1, 392, "Japan", 21671, "Tokyo", 70.0, 35.69, 139.69] + [11274.641] + [30000.0] * 17,
            [2, 840, "United States of America", 23083, "New York-Newark", np.nan, 40.71, -74.01]
            + [12338.471] + [16000.0] * 17]
    return pd.DataFrame(rows, columns=head + YEARS)


def datasource() -> pd.DataFrame:
    return pd.DataFrame({
        "City Code": [21671, 23083], "ISO3 Alpha Code": ["JPN", "USA"],
        "Location name": ["Tokyo", "New York-Newark"], "Location type": ["Capital", "Non-Capital"],
        "Sources": ["Censuses of 1950, 1955 and 2015; Estimates for 1952.",
                    "Census of 1979; Estimates for 1950, 1966."],
        "Statistical Concept": ["Urban Agglomeration", "Urban Agglomeration"],
    })


def test_agglomerations_in_persons_with_iso3_and_no_projections():
    df = validate_long(un_wup.parse_agglomerations(f12(), datasource()))
    tokyo = df.set_index(["geo_id", "year"]).loc[("wup:21671", 1950)]
    assert tokyo.value == pytest.approx(11_274_641)
    assert tokyo.country_iso3 == "JPN" and tokyo.unit == "persons"
    assert df.year.max() == 2015 and df.year.min() == 1950  # 2020+ are projections


def test_census_years_ignore_estimates():
    assert un_wup.census_years("Census of 1979; Estimates for 1950, 1966, 1971, 2004 and 2016.") == [1979]
    assert un_wup.census_years("Censuses of 1950, 1960 and 2010.") == [1950, 1960, 2010]
    assert un_wup.census_years("Estimates for 1950.") == []


def test_attributes_keep_concept_capital_and_census_years():
    a = un_wup.parse_attributes(f12(), datasource()).set_index("geo_id")
    assert a.at["wup:21671", "concept"] == "Urban Agglomeration"
    assert a.at["wup:21671", "capital"] and not a.at["wup:23083", "capital"]
    assert a.at["wup:21671", "census_years"] == "1950 1955 2015"
    assert a.at["wup:23083", "latitude"] == 40.71


def locations_raw() -> pd.DataFrame:
    # F00 read with header=None, skiprows=17: positions 1 name, 3 code, 4 ISO3, 5 type, 8 subregion, 10 region
    rows = [[1, "WORLD", None, 900, "   ", 0, "Special groupings", None, None, None, None],
            [2, "Japan", None, 392, "JPN", 4, "Country/Area", 906, "Eastern Asia", 935, "Asia"],
            [3, "United States of America", None, 840, "USA", 4, "Country/Area", None, None, 918, "Northern America"]]
    return pd.DataFrame(rows)


def test_locations_keep_countries_only():
    loc = un_wup.parse_locations(locations_raw())
    assert list(loc.iso3) == ["JPN", "USA"] and list(loc.code) == [392, 840]
    assert loc.set_index("iso3").at["JPN", "subregion"] == "Eastern Asia"


def test_urban_share_for_countries_only():
    f21 = pd.DataFrame([[1, "WORLD", None, 900] + [29.6] * 101, [2, "Japan", None, 392] + [53.4] * 101],
                       columns=["Index", "Region, subregion, country or area", "Note", "Country\ncode"]
                       + list(range(1950, 2051)))
    df = validate_long(un_wup.parse_urban_share(f21, un_wup.parse_locations(locations_raw())))
    assert set(df.geo_id) == {"iso3:JPN"} and df.year.max() == 2015
    assert set(df.variable) == {"urban_share"} and set(df.unit) == {"percent"}


def test_degurba_cities_drop_missing_years():
    raw = pd.DataFrame([[1, "Afghanistan", None, 4, "AFG", "AF", 4555, "Charikar", 0, 69.17, 35.02]
                        + [82.727] + [np.nan] * 39 + [90.0] * 36],
                       columns=["Index", "Location", "Notes", "LocID", "ISO3_Code", "ISO2_Code", "City_Code",
                                "City_Name", "Capital", "PWCent_Longitude", "PWCent_Latitude"]
                       + [float(y) for y in range(1975, 2051)])
    df = validate_long(un_wup.parse_degurba(raw))
    assert list(df.year) == [1975] and df.value.iloc[0] == pytest.approx(82_727)
    assert df.geo_id.iloc[0] == "dou:4555" and df.geo_level.iloc[0] == "agglomeration"
```

- [ ] **Step 2: Run the tests and see them fail.**

Run: `"$PY" -m pytest tests/test_un_wup.py -q`
Expected: FAIL with `ImportError: cannot import name 'un_wup'`.

- [ ] **Step 3: Implement.** Create `us_housing_crisis_analysis/sources/un_wup.py`:

```python
"""UN World Urbanization Prospects. WUP 2018 (RQ0c main): File 12 agglomerations of 300k+ in 2018,
File 21 national % urban, F00 locations and the agglomeration data-sources file (ISO3, statistical
concept, census years). WUP 2025 File 21 (Degree of Urbanisation cities, 1975+) is an RQ0c check.
Values after 2015 are projections and are never loaded. See Claude/research/sources.md."""

import io
import re
import zipfile
from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import RAW_DATA_DIR, RQ0C_CITY_END, RQ0C_START
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file

ARCHIVE_URL = "https://population.un.org/wup/assets/Download/Archive/WUP2018-Excel-files.zip"
WUP2025_URL = "https://population.un.org/wup/assets/Download/Cities/WUP2025-F21-DEGURBA-Cities_Pop.xlsx"
RAW_DIR = RAW_DATA_DIR / "un_wup"
ZIP_PATH = RAW_DIR / "WUP2018-Excel-files.zip"
WUP2025_PATH = RAW_DIR / "WUP2025-F21-DEGURBA-Cities_Pop.xlsx"
F12 = "WUP2018-F12-Cities_Over_300K.xls"
F21 = "WUP2018-F21-Proportion_Urban_Annual.xls"
F00 = "WUP2018-F00-LOCATIONS.xlsx"
DATASOURCE = "WUP2018-DataSource-UrbanAgglomeration-and-CapitalCities.xls"
CITY_YEARS = list(range(RQ0C_START, RQ0C_CITY_END + 1, 5))
COUNTRY_TYPE = 4  # F00 "Location Type" code for a country or area


def download(force: bool = False) -> list[Path]:
    return [download_file(ARCHIVE_URL, ZIP_PATH, force=force),
            download_file(WUP2025_URL, WUP2025_PATH, force=force)]


def _member(name: str, **kwargs) -> pd.DataFrame:
    with zipfile.ZipFile(ZIP_PATH) as zf:
        data = io.BytesIO(zf.read(name))
    engine = "xlrd" if name.endswith(".xls") else None
    return pd.read_excel(data, engine=engine, **kwargs)


def _data_sheet(name: str) -> pd.DataFrame:
    # 16 title rows precede the header in every WUP 2018 data sheet
    return _member(name, sheet_name="Data", skiprows=16)


def _long(geo_id, geo_name, geo_level, iso3, year, variable, value, unit) -> pd.DataFrame:
    return pd.DataFrame({
        "geo_id": geo_id, "geo_name": geo_name, "geo_level": geo_level, "country_iso3": iso3,
        "year": year, "variable": variable, "value": value, "unit": unit, "source": "un_wup",
    }).astype({"year": "int64", "value": "float64"}).reset_index(drop=True)


def parse_agglomerations(f12: pd.DataFrame, ds: pd.DataFrame) -> pd.DataFrame:
    iso = ds.set_index("City Code")["ISO3 Alpha Code"]
    m = f12.melt(id_vars=["City Code", "Urban Agglomeration"], value_vars=CITY_YEARS,
                 var_name="year", value_name="value")
    return _long("wup:" + m["City Code"].astype(str), m["Urban Agglomeration"], "agglomeration",
                 m["City Code"].map(iso), m.year, "population", m.value * 1000, "persons")


def census_years(text: str) -> list[int]:
    """Years of the censuses named in a WUP 'Sources' cell; estimates and registers are ignored."""
    years: set[int] = set()
    for part in str(text).split(";"):
        if part.strip().lower().startswith("census"):
            years |= {int(y) for y in re.findall(r"\b(1[89]\d\d|20\d\d)\b", part)}
    return sorted(years)


def parse_attributes(f12: pd.DataFrame, ds: pd.DataFrame) -> pd.DataFrame:
    m = f12[["City Code", "Urban Agglomeration", "Latitude", "Longitude"]].merge(ds, on="City Code")
    return pd.DataFrame({
        "geo_id": "wup:" + m["City Code"].astype(str), "geo_name": m["Urban Agglomeration"],
        "iso3": m["ISO3 Alpha Code"], "latitude": m.Latitude, "longitude": m.Longitude,
        "concept": m["Statistical Concept"], "capital": m["Location type"].eq("Capital"),
        "census_years": [" ".join(map(str, census_years(s))) for s in m.Sources],
    }).reset_index(drop=True)


def parse_locations(raw: pd.DataFrame) -> pd.DataFrame:
    """F00 read with header=None, skiprows=17 (a two-row header)."""
    c = raw[raw[5] == COUNTRY_TYPE]
    return pd.DataFrame({"code": c[3].astype("int64"), "iso3": c[4].str.strip(), "name": c[1],
                         "region": c[10], "subregion": c[8]}).reset_index(drop=True)


def parse_urban_share(f21: pd.DataFrame, locations: pd.DataFrame) -> pd.DataFrame:
    iso = locations.set_index("code").iso3
    f = f21[f21["Country\ncode"].isin(iso.index)]
    years = list(range(RQ0C_START, RQ0C_CITY_END + 1))
    m = f.melt(id_vars=["Country\ncode", "Region, subregion, country or area"], value_vars=years,
               var_name="year", value_name="value")
    codes = m["Country\ncode"].map(iso)
    return _long("iso3:" + codes, m["Region, subregion, country or area"], "country", codes, m.year,
                 "urban_share", m.value, "percent")


def parse_degurba(raw: pd.DataFrame) -> pd.DataFrame:
    raw = raw.rename(columns=lambda c: c if isinstance(c, str) else int(c))  # years may read as floats
    m = raw.melt(id_vars=["City_Code", "City_Name", "ISO3_Code"], value_vars=CITY_YEARS[5:],
                 var_name="year", value_name="value").dropna(subset=["value"])  # 1975+
    return _long("dou:" + m.City_Code.astype(str), m.City_Name, "agglomeration", m.ISO3_Code, m.year,
                 "population_degurba", m.value * 1000, "persons")


def country_locations() -> pd.DataFrame:
    return parse_locations(_member(F00, sheet_name=0, header=None, skiprows=17))


def agglomeration_attributes() -> pd.DataFrame:
    return parse_attributes(_data_sheet(F12), _data_sheet(DATASOURCE))


def load() -> pd.DataFrame:
    download()
    frames = [
        parse_agglomerations(_data_sheet(F12), _data_sheet(DATASOURCE)),
        parse_urban_share(_data_sheet(F21), country_locations()),
        parse_degurba(pd.read_excel(WUP2025_PATH, sheet_name="Data")),
    ]
    return validate_long(pd.concat(frames, ignore_index=True))
```

Append `"un_wup"` to `SOURCE_NAMES` in `sources/__init__.py`.

- [ ] **Step 4: Run the tests and see them pass.**

Run: `"$PY" -m pytest tests/test_un_wup.py -q`
Expected: 6 passed.

- [ ] **Step 5: Load the real data and add data tests.** Run `"$PY" -m us_housing_crisis_analysis.dataset download --source un_wup && "$PY" -m us_housing_crisis_analysis.dataset load --source un_wup`. Then create `tests/data/test_global.py`:

```python
import pandas as pd
import pytest

from us_housing_crisis_analysis.sources import un_wup

pytestmark = pytest.mark.data


def test_wup_counts_and_known_values(interim):
    w = interim("un_wup")
    a = w[w.variable == "population"]
    assert a.geo_id.nunique() == 1860
    assert a[a.country_iso3 == "USA"].geo_id.nunique() == 144
    v = a.set_index(["geo_id", "year"]).value
    assert v[("wup:21671", 1950)] == pytest.approx(11_274_641)  # Tokyo
    assert v[("wup:23083", 1950)] == pytest.approx(12_338_471)  # New York-Newark
    assert a.year.max() == 2015


def test_wup_concepts_and_iso3():
    a = un_wup.agglomeration_attributes()
    assert len(a) == 1860 and a.iso3.notna().all()
    assert a.concept.value_counts().to_dict() == {
        "Urban Agglomeration": 1038, "City Proper": 644, "Metropolitan area": 178}
    assert len(un_wup.country_locations()) == 233
```

Run: `"$PY" -m pytest tests/data/test_global.py -q`. Expected: 2 passed.

- [ ] **Step 6: Docs.** In `Claude/research/sources.md`, change the WUP 2018 and WUP 2025 rows' status to `in use (Plan 3)` and the module to `sources/un_wup.py`. In `Claude/methods/pipeline.md`, add `un_wup` to the source list with its three variables and units.

- [ ] **Step 7: Commit.**

```bash
git add us_housing_crisis_analysis/sources tests/test_un_wup.py tests/data/test_global.py Claude
git commit -m "UN WUP source: 2018 agglomerations and % urban, 2025 Degree-of-Urbanisation cities (Plan 3)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: `sources/maddison.py` and `sources/worldbank.py`

**Files:**
- Create: `us_housing_crisis_analysis/sources/maddison.py`, `us_housing_crisis_analysis/sources/worldbank.py`, `tests/test_maddison.py`, `tests/test_worldbank.py`
- Modify: `us_housing_crisis_analysis/sources/__init__.py`, `tests/data/test_global.py`, `Claude/research/sources.md`, `Claude/methods/pipeline.md`

**Interfaces:**
- Produces:
  - `maddison.load()`: `iso3:` rows with `gdppc` (`usd_2011_ppp`) and `population_maddison` (persons), 1950–2022.
  - `worldbank.load()`: `iso3:` rows with `gdppc_wdi` (`usd_2015`, 1960–2025) and `wb_income_group` (1 = L, 2 = LM, 3 = UM, 4 = H, for data years 1987–2023).
  - `worldbank.latest_income_groups() -> pd.Series`: ISO3 → letter code (`"H"`, …) in the latest year.

- [ ] **Step 1: Write the failing tests.** Create `tests/test_maddison.py`:

```python
import numpy as np
import pandas as pd
import pytest

from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import maddison


def full() -> pd.DataFrame:
    return pd.DataFrame({
        "countrycode": ["USA", "USA", "USA", "SUN", "KAZ", "KAZ"],
        "country": ["United States", "United States", "United States", "Former USSR", "Kazakhstan", "Kazakhstan"],
        "region": ["Western Offshoots"] * 3 + ["Eastern Europe"] * 3,
        "year": [1940, 1950, 2022, 1950, 1950, 1973],
        "gdppc": [11000.0, 15240.0, 58487.5, 4000.0, np.nan, 6000.0],
        "pop": [132000.0, 152271.0, 333288.0, 180000.0, 6703.0, 13000.0],
    })


def test_gdp_and_population_from_1950_without_former_states():
    df = validate_long(maddison.parse(full())).set_index(["geo_id", "year", "variable"]).value
    assert df[("iso3:USA", 1950, "gdppc")] == 15240.0
    assert df[("iso3:USA", 1950, "population_maddison")] == pytest.approx(152_271_000)
    assert ("iso3:USA", 1940, "gdppc") not in df.index
    assert not df.index.get_level_values("geo_id").str.contains("SUN").any()  # no parent fill (D-27)
    assert ("iso3:KAZ", 1950, "gdppc") not in df.index  # missing stays missing
    assert ("iso3:KAZ", 1950, "population_maddison") in df.index
```

Create `tests/test_worldbank.py`:

```python
import pandas as pd
import pytest

from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import worldbank


def oghist() -> pd.DataFrame:
    # 'Country Analytical History' read with header=None: data years on row 5, countries from row 11
    rows = [[None] * 5 for _ in range(11)]
    rows[4] = [None, "Bank's fiscal year:", "FY89", "FY90", "FY25"]
    rows[5] = [None, "Data for calendar year :", 1987, 1988, 2023]
    rows += [["KOR", "Korea, Rep.", "UM", "UM", "H"], ["ALB", "Albania", "..", "LM*", "UM"]]
    return pd.DataFrame(rows)


def test_income_history_codes_and_unclassified_years():
    df = validate_long(worldbank.parse_income_history(oghist())).set_index(["geo_id", "year"]).value
    assert df[("iso3:KOR", 1987)] == 3 and df[("iso3:KOR", 2023)] == 4
    assert df[("iso3:ALB", 1988)] == 2  # footnote marker stripped
    assert ("iso3:ALB", 1987) not in df.index  # '..' = not classified


def test_latest_income_groups():
    assert worldbank.parse_latest_income_groups(oghist()).to_dict() == {"KOR": "H", "ALB": "UM"}


def test_wdi_keeps_countries_and_drops_nulls():
    payload = [{"page": 1, "pages": 1},
               [{"countryiso3code": "KOR", "country": {"value": "Korea, Rep."}, "date": "1960", "value": 1100.5},
                {"countryiso3code": "WLD", "country": {"value": "World"}, "date": "1960", "value": 3700.0},
                {"countryiso3code": "KOR", "country": {"value": "Korea, Rep."}, "date": "1961", "value": None}]]
    df = validate_long(worldbank.parse_wdi(payload, {"KOR"}))
    assert list(df.geo_id) == ["iso3:KOR"] and df.value.iloc[0] == 1100.5
    assert df.unit.iloc[0] == "usd_2015"
```

- [ ] **Step 2: Run the tests and see them fail.**

Run: `"$PY" -m pytest tests/test_maddison.py tests/test_worldbank.py -q`
Expected: FAIL with ImportError.

- [ ] **Step 3: Implement.** Create `us_housing_crisis_analysis/sources/maddison.py`:

```python
"""Maddison Project Database 2023: national GDP per head (2011 PPP $) and population (thousands).
Former-state aggregates (USSR, Czechoslovakia, Yugoslavia) are not loaded: agglomerations in their
successor states have no GDP until the successor's own series starts (D-27)."""

from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import RAW_DATA_DIR, RQ0C_START
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file

URL = "https://dataverse.nl/api/access/datafile/421302"
RAW_PATH = RAW_DATA_DIR / "maddison" / "mpd2023_web.xlsx"
FORMER_STATES = {"SUN", "CSK", "YUG"}


def download(force: bool = False) -> list[Path]:
    return [download_file(URL, RAW_PATH, force=force)]


def parse(full: pd.DataFrame) -> pd.DataFrame:
    f = full[(full.year >= RQ0C_START) & ~full.countrycode.isin(FORMER_STATES)]
    frames = []
    for column, variable, unit, scale in [("gdppc", "gdppc", "usd_2011_ppp", 1),
                                          ("pop", "population_maddison", "persons", 1000)]:
        g = f.dropna(subset=[column])
        frames.append(pd.DataFrame({
            "geo_id": "iso3:" + g.countrycode, "geo_name": g.country, "geo_level": "country",
            "country_iso3": g.countrycode, "year": g.year, "variable": variable,
            "value": g[column] * scale, "unit": unit, "source": "maddison",
        }))
    return pd.concat(frames, ignore_index=True).astype({"year": "int64", "value": "float64"})


def load() -> pd.DataFrame:
    download()
    return validate_long(parse(pd.read_excel(RAW_PATH, sheet_name="Full data")))
```

Create `us_housing_crisis_analysis/sources/worldbank.py`:

```python
"""World Bank: WDI GDP per head (constant 2015 US$, a 1960+ check on Maddison) and the historical
income classification (OGHIST.xlsx), used for peer group 2 and its time-varying check."""

import json
from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file

WDI_URL = "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.KD"
WDI_PARAMS = {"format": "json", "per_page": 20000, "date": "1960:2025"}
OGHIST_URL = "https://datacatalogfiles.worldbank.org/ddh-published/0037712/DR0090754/OGHIST.xlsx"
RAW_DIR = RAW_DATA_DIR / "worldbank"
WDI_PATH = RAW_DIR / "wdi_gdppc.json"
OGHIST_PATH = RAW_DIR / "OGHIST.xlsx"
OGHIST_SHEET = "Country Analytical History"
YEAR_ROW, FIRST_COUNTRY_ROW = 5, 11
GROUP_CODES = {"L": 1, "LM": 2, "UM": 3, "H": 4}


def download(force: bool = False) -> list[Path]:
    return [download_file(WDI_URL, WDI_PATH, force=force, params=WDI_PARAMS),
            download_file(OGHIST_URL, OGHIST_PATH, force=force)]


def _countries(raw: pd.DataFrame) -> pd.DataFrame:
    body = raw.iloc[FIRST_COUNTRY_ROW:]
    return body[body[0].astype(str).str.fullmatch(r"[A-Z]{3}")]


def _letters(cells: pd.Series) -> pd.Series:
    return cells.astype(str).str.replace(r"[^A-Z]", "", regex=True).where(lambda s: s.isin(GROUP_CODES))


def parse_income_history(raw: pd.DataFrame) -> pd.DataFrame:
    years = raw.iloc[YEAR_ROW, 2:]
    body = _countries(raw)
    frames = []
    for col, year in years.items():
        code = _letters(body[col]).map(GROUP_CODES)
        keep = code.notna()
        frames.append(pd.DataFrame({
            "geo_id": "iso3:" + body.loc[keep, 0], "geo_name": body.loc[keep, 1], "geo_level": "country",
            "country_iso3": body.loc[keep, 0], "year": int(year), "variable": "wb_income_group",
            "value": code[keep], "unit": "group_code_1L_2LM_3UM_4H", "source": "worldbank",
        }))
    return pd.concat(frames, ignore_index=True).astype({"year": "int64", "value": "float64"})


def parse_latest_income_groups(raw: pd.DataFrame) -> pd.Series:
    body = _countries(raw)
    return _letters(body[raw.columns[-1]]).set_axis(body[0]).dropna().rename_axis(None)


def parse_wdi(payload: list, countries: set[str]) -> pd.DataFrame:
    rows = [r for r in payload[1] if r["countryiso3code"] in countries and r["value"] is not None]
    return pd.DataFrame({
        "geo_id": ["iso3:" + r["countryiso3code"] for r in rows],
        "geo_name": [r["country"]["value"] for r in rows], "geo_level": "country",
        "country_iso3": [r["countryiso3code"] for r in rows], "year": [int(r["date"]) for r in rows],
        "variable": "gdppc_wdi", "value": [float(r["value"]) for r in rows], "unit": "usd_2015",
        "source": "worldbank",
    }).astype({"year": "int64", "value": "float64"})


def _oghist() -> pd.DataFrame:
    return pd.read_excel(OGHIST_PATH, sheet_name=OGHIST_SHEET, header=None)


def latest_income_groups() -> pd.Series:
    return parse_latest_income_groups(_oghist())


def load() -> pd.DataFrame:
    download()
    raw = _oghist()
    countries = set(_countries(raw)[0])
    wdi = parse_wdi(json.loads(WDI_PATH.read_text()), countries)
    return validate_long(pd.concat([wdi, parse_income_history(raw)], ignore_index=True))
```

Append `"maddison", "worldbank"` to `SOURCE_NAMES`.

- [ ] **Step 4: Run the tests and see them pass.**

Run: `"$PY" -m pytest tests/test_maddison.py tests/test_worldbank.py -q`
Expected: 4 passed.

- [ ] **Step 5: Load the real data, and pin the facts with data tests.** Run download and load for `maddison` and `worldbank`. Check that the WDI JSON has a single page: `payload[0]["pages"] == 1`. If it has more, raise `per_page` and record the change. Append to `tests/data/test_global.py`:

```python
def test_maddison_late_starts_are_the_documented_ones(interim):
    m = interim("maddison")
    first = m[m.variable == "gdppc"].groupby("country_iso3").year.min()
    late = first[first > 1950].to_dict()
    assert late["CZE"] == 1970 and late["SVK"] == 1985 and late["UKR"] == 1973 and late["SVN"] == 1952
    assert {"SUN", "CSK", "YUG"}.isdisjoint(m.country_iso3)
    assert m.set_index(["geo_id", "year", "variable"]).value[("iso3:USA", 1950, "gdppc")] == 15240


def test_world_bank_latest_groups(interim):
    from us_housing_crisis_analysis.sources import worldbank
    g = worldbank.latest_income_groups()
    assert g["KOR"] == "H" and g["TUR"] == "UM" and g["TWN"] == "H"
    w = interim("worldbank")
    assert w[w.variable == "gdppc_wdi"].year.min() == 1960
```

Run: `"$PY" -m pytest tests/data/test_global.py -q`. Expected: all pass.

- [ ] **Step 6: Docs.** Update the Maddison and World Bank rows in `sources.md` (status `in use (Plan 3)`). Update `pipeline.md` with the variables and units.

- [ ] **Step 7: Commit.**

```bash
git add us_housing_crisis_analysis/sources tests Claude
git commit -m "Maddison 2023 and World Bank sources: national GDP per head, income groups (Plan 3)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: `sources/dose.py` and `sources/estat_japan.py`

**Files:**
- Create: `us_housing_crisis_analysis/sources/dose.py`, `us_housing_crisis_analysis/sources/estat_japan.py`, `references/crosswalks/jp_prefectures.csv`, `tests/test_dose.py`, `tests/test_estat_japan.py`
- Modify: `us_housing_crisis_analysis/sources/__init__.py`, `tests/data/test_global.py`, `Claude/research/sources.md`, `Claude/methods/pipeline.md`

**Interfaces:**
- Produces:
  - `dose.load()`: `gadm1:<GID_1>` rows at geo level `region`, with `population` (persons) and `grp_pc` (`usd_2015`), for every DOSE year.
  - `estat_japan.load()`: `gadm1:JPN.*` rows with `population_census` (persons), census years 1920–2020.
  - `references/crosswalks/jp_prefectures.csv`, with columns `jis_code, name_en, gid_1`.

- [ ] **Step 1: Create the crosswalk.** Write `references/crosswalks/jp_prefectures.csv` exactly as below. The names match DOSE's `region` column and GADM 4.1's `NAME_1`, checked 2026-10-14:

```csv
jis_code,name_en,gid_1
01,Hokkaido,JPN.12_1
02,Aomori,JPN.3_1
03,Iwate,JPN.16_1
04,Miyagi,JPN.24_1
05,Akita,JPN.2_1
06,Yamagata,JPN.45_1
07,Fukushima,JPN.8_1
08,Ibaraki,JPN.14_1
09,Tochigi,JPN.39_1
10,Gunma,JPN.10_1
11,Saitama,JPN.35_1
12,Chiba,JPN.4_1
13,Tokyo,JPN.41_1
14,Kanagawa,JPN.19_1
15,Niigata,JPN.29_1
16,Toyama,JPN.43_1
17,Ishikawa,JPN.15_1
18,Fukui,JPN.6_1
19,Yamanashi,JPN.47_1
20,Nagano,JPN.26_1
21,Gifu,JPN.9_1
22,Shizuoka,JPN.38_1
23,Aichi,JPN.1_1
24,Mie,JPN.23_1
25,Shiga,JPN.36_1
26,Kyoto,JPN.22_1
27,Osaka,JPN.33_1
28,Hyogo,JPN.13_1
29,Nara,JPN.28_1
30,Wakayama,JPN.44_1
31,Tottori,JPN.42_1
32,Shimane,JPN.37_1
33,Okayama,JPN.31_1
34,Hiroshima,JPN.11_1
35,Yamaguchi,JPN.46_1
36,Tokushima,JPN.40_1
37,Kagawa,JPN.17_1
38,Ehime,JPN.5_1
39,Kochi,JPN.20_1
40,Fukuoka,JPN.7_1
41,Saga,JPN.34_1
42,Nagasaki,JPN.27_1
43,Kumamoto,JPN.21_1
44,Oita,JPN.30_1
45,Miyazaki,JPN.25_1
46,Kagoshima,JPN.18_1
47,Okinawa,JPN.32_1
```

- [ ] **Step 2: Write the failing tests.** Create `tests/test_dose.py`:

```python
import numpy as np
import pandas as pd

from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import dose


def raw() -> pd.DataFrame:
    return pd.DataFrame({
        "country": ["Japan", "Japan", "Kenya"], "region": ["Tokyo", "Tokyo", "South Nyanza"],
        "GID_0": ["JPN", "JPN", "KEN"], "GID_1": ["JPN.41_1", "JPN.41_1", np.nan],
        "year": [1960, 1980, 1970], "pop": [np.nan, 11618281.0, 1.0e6],
        "grp_pc_usd_2015": [12000.0, 30000.0, 500.0],
    })


def test_regions_with_separate_missing_values():
    df = validate_long(dose.parse(raw())).set_index(["geo_id", "year", "variable"]).value
    assert df[("gadm1:JPN.41_1", 1960, "grp_pc")] == 12000.0
    assert ("gadm1:JPN.41_1", 1960, "population") not in df.index  # missing population stays missing
    assert df[("gadm1:JPN.41_1", 1980, "population")] == 11618281.0
    assert not df.index.get_level_values("geo_id").str.contains("KEN").any()  # no GID_1: dropped
```

Create `tests/test_estat_japan.py`:

```python
import pandas as pd
import pytest

from us_housing_crisis_analysis.config import CROSSWALKS_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import estat_japan


def raw() -> pd.DataFrame:
    # sheet 人口 read with header=None: year labels on row 6, sexes on row 7, data from row 8
    width = 7
    rows = [[None] * width for _ in range(8)]
    rows[6] = ["地域", "1950年", "昭和25年", None, "1955年", "昭和30年", None]
    rows[7] = [None, "総数", "男", "女", "総数", "男", "女"]
    rows += [["00000_全国", 84114574, 1, 1, 90076594, 1, 1],
             ["00000_全国（人口集中地区）", "-", "-", "-", "-", "-", "-"],
             ["13000_東京都", 6277500, 1, 1, 8037084, 1, 1],
             ["47000_沖縄県", 914937, 1, 1, "-", 1, 1]]
    return pd.DataFrame(rows)


def test_prefecture_totals_mapped_to_gadm_ids():
    xw = pd.read_csv(CROSSWALKS_DIR / "jp_prefectures.csv", dtype=str)
    df = validate_long(estat_japan.parse(raw(), xw)).set_index(["geo_id", "year"])
    assert df.loc[("gadm1:JPN.41_1", 1950), "value"] == 6_277_500  # Tokyo, total not male
    assert df.loc[("gadm1:JPN.41_1", 1955), "value"] == 8_037_084
    assert ("gadm1:JPN.32_1", 1955) not in df.index  # '-' = no count
    assert set(df.variable) == {"population_census"} and not df.index.get_level_values(0).str.contains("00000").any()


def test_crosswalk_is_complete():
    xw = pd.read_csv(CROSSWALKS_DIR / "jp_prefectures.csv", dtype=str)
    assert len(xw) == 47 and xw.gid_1.is_unique and list(xw.jis_code) == [f"{i:02d}" for i in range(1, 48)]
```

- [ ] **Step 3: Run the tests and see them fail.**

Run: `"$PY" -m pytest tests/test_dose.py tests/test_estat_japan.py -q`
Expected: FAIL with ImportError.

- [ ] **Step 4: Implement.** Create `us_housing_crisis_analysis/sources/dose.py`:

```python
"""DOSE V2.11 (Wenz et al. 2023): GDP per head (2015 US$) and population for first-level regions
(GADM level 1) in 83 countries, 1953-2020, annual where reported. RQ0c regional income outside the
Rosés-Wolf countries, and the US calibration (spec §4.4). Nothing is interpolated."""

from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file

URL = "https://zenodo.org/records/16313760/files/DOSE_V2.11.csv?download=1"
RAW_PATH = RAW_DATA_DIR / "dose" / "DOSE_V2.11.csv"
VARIABLES = {"pop": ("population", "persons"), "grp_pc_usd_2015": ("grp_pc", "usd_2015")}


def download(force: bool = False) -> list[Path]:
    return [download_file(URL, RAW_PATH, force=force)]


def parse(raw: pd.DataFrame) -> pd.DataFrame:
    r = raw.dropna(subset=["GID_1"])
    frames = []
    for column, (variable, unit) in VARIABLES.items():
        g = r.dropna(subset=[column])
        frames.append(pd.DataFrame({
            "geo_id": "gadm1:" + g.GID_1, "geo_name": g.region, "geo_level": "region",
            "country_iso3": g.GID_0, "year": g.year, "variable": variable, "value": g[column],
            "unit": unit, "source": "dose",
        }))
    return pd.concat(frames, ignore_index=True).astype({"year": "int64", "value": "float64"})


def load() -> pd.DataFrame:
    download()
    return validate_long(parse(pd.read_csv(RAW_PATH, low_memory=False)))
```

Create `us_housing_crisis_analysis/sources/estat_japan.py`:

```python
"""Japan census population by prefecture, 1920-2020 (Statistics Bureau of Japan, census time
series table 1, via e-Stat; CC BY). DOSE has Japanese population only from 1975; this fills
1950-1970 and is used for every Japanese year (equal to DOSE in 1980). The file is 'strict' OOXML,
which only the calamine engine reads."""

import re
from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import CROSSWALKS_DIR, RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file

URL = "https://www.e-stat.go.jp/stat-search/file-download?statInfId=000001085925&fileKind=0"
RAW_PATH = RAW_DATA_DIR / "estat_japan" / "da01.xlsx"
SHEET = "人口"
YEAR_ROW, FIRST_ROW = 6, 8
PREFECTURE = r"^\d{2}000_"


def download(force: bool = False) -> list[Path]:
    return [download_file(URL, RAW_PATH, force=force)]


def parse(raw: pd.DataFrame, crosswalk: pd.DataFrame) -> pd.DataFrame:
    labels = raw.iloc[YEAR_ROW]
    year_cols = {int(v[:4]): c for c, v in labels.items() if isinstance(v, str) and re.fullmatch(r"\d{4}年", v)}
    body = raw.iloc[FIRST_ROW:]
    area = body[0].astype(str)
    body = body[area.str.match(PREFECTURE) & ~area.str.startswith("00")]
    xw = crosswalk.set_index("jis_code")
    jis = body[0].str[:2]
    frames = []
    for year, col in year_cols.items():
        value = pd.to_numeric(body[col], errors="coerce")  # '-' = no count
        frames.append(pd.DataFrame({
            "geo_id": "gadm1:" + jis.map(xw.gid_1), "geo_name": jis.map(xw.name_en), "geo_level": "region",
            "country_iso3": "JPN", "year": year, "variable": "population_census", "value": value,
            "unit": "persons", "source": "estat_japan",
        }).dropna(subset=["value"]))
    return pd.concat(frames, ignore_index=True).astype({"year": "int64", "value": "float64"})


def load() -> pd.DataFrame:
    download()
    raw = pd.read_excel(RAW_PATH, sheet_name=SHEET, header=None, engine="calamine")
    crosswalk = pd.read_csv(CROSSWALKS_DIR / "jp_prefectures.csv", dtype=str)
    return validate_long(parse(raw, crosswalk))
```

Append `"dose", "estat_japan"` to `SOURCE_NAMES`.

- [ ] **Step 5: Run the tests and see them pass.**

Run: `"$PY" -m pytest tests/test_dose.py tests/test_estat_japan.py -q`
Expected: 3 passed.

- [ ] **Step 6: Load the real data and add data tests.** Run download and load for `dose` and `estat_japan`. Append to `tests/data/test_global.py`:

```python
def test_japan_census_matches_dose_in_1980(interim):
    c = interim("estat_japan").set_index(["geo_id", "year"]).value
    d = interim("dose")
    d = d[(d.variable == "population") & (d.country_iso3 == "JPN")].set_index(["geo_id", "year"]).value
    assert c[("gadm1:JPN.41_1", 1980)] == 11_618_281
    both = (c.xs(1980, level="year") / d.xs(1980, level="year")).dropna()
    assert len(both) == 47 and (both - 1).abs().max() < 1e-6
    assert c.xs(1950, level="year").sum() == pytest.approx(84_114_574, rel=1e-6)


def test_dose_us_population_close_to_bea(interim):
    d = interim("dose")
    d = d[(d.variable == "population") & (d.country_iso3 == "USA")]
    b = interim("bea")
    b = b[(b.geo_level == "state") & (b.variable == "population_bea")]
    for year in (1970, 1980, 1990, 2000, 2010):
        m = d[d.year == year].merge(b[b.year == year], on="geo_name", suffixes=("_dose", "_bea"))
        rel = (m.value_dose / m.value_bea - 1).abs()
        assert len(m) == 51 and rel.max() < 0.015 and rel.median() < 0.005, (year, rel.max())
```

Run: `"$PY" -m pytest tests/data/test_global.py -q`. Expected: all pass.

- [ ] **Step 7: Docs.** Update the DOSE row in `sources.md`, and add a new row:

`| Census time series: population by prefecture, 1920–2020 (table 1, da01.xlsx) | Statistics Bureau of Japan (e-Stat) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000001085925&fileKind=0 (list: e-Stat toukei 00200521, tstat 000001011777) | 47 prefectures, census years 1920–2020 | CC BY (e-Stat terms); cite Statistics Bureau of Japan | sources/estat_japan.py | in use (Plan 3) | 2026-10-14 |`

In `pipeline.md`, note "Japan population = census for all years; income = DOSE".

- [ ] **Step 8: Commit.**

```bash
git add us_housing_crisis_analysis/sources references/crosswalks/jp_prefectures.csv tests Claude
git commit -m "DOSE regional GDP and Japan census population by prefecture (Plan 3)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: `sources/roses_wolf.py` (manual download)

**Files:**
- Create: `us_housing_crisis_analysis/sources/roses_wolf.py`, `tests/test_roses_wolf.py`
- Modify: `us_housing_crisis_analysis/sources/__init__.py`, `tests/data/test_global.py`, `Claude/research/sources.md`, `Claude/methods/pipeline.md`

**Interfaces:**
- Produces:
  - `roses_wolf.load()`: `nuts2:<code>` rows at geo level `region`, with `population` (persons), `gdp_pc` (`usd_2011_ppp`) and `gdp_pc_1990ppp` (`usd_1990_ppp`), years 1950+.
  - `roses_wolf.RW_COUNTRIES`: dict of NUTS prefix → ISO3.

- [ ] **Step 1: Write the failing tests.** Create `tests/test_roses_wolf.py`:

```python
import pandas as pd
import pytest

from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import roses_wolf

HEAD = ["Country (current borders)", "NUTS-Codes", "Region"]


def sheet(values: dict[str, list], years: list[int]) -> pd.DataFrame:
    rows = [["Austria", code, code] + v for code, v in values.items()]
    rows.append(["Note: A full description ...", None, None] + [None] * len(years))
    return pd.DataFrame(rows, columns=HEAD + years)


def sheets() -> dict[str, pd.DataFrame]:
    years = [1938, 1950, 2020]
    return {
        "population": sheet({"AT12+AT13": [3000.0, 3017.0, 3500.0], "NL23": [".", ".", 430.0]}, years),
        "gdp_2011ppp": sheet({"AT12+AT13": [1.0, 17158.6, 150000.0], "NL23": [".", ".", 20000.0]}, years),
        "gdp_1990ppp": sheet({"AT12+AT13": [1.0, 13945.7], "NL23": [".", "."]}, [1938, 1950]),
    }


def test_per_head_values_and_units():
    df = validate_long(roses_wolf.parse(sheets())).set_index(["geo_id", "year", "variable"])
    pop = df.loc[("nuts2:AT12+AT13", 1950, "population"), "value"]
    assert pop == pytest.approx(3_017_000)
    assert df.loc[("nuts2:AT12+AT13", 1950, "gdp_pc"), "value"] == pytest.approx(17158.6e6 / 3_017_000)
    assert df.loc[("nuts2:AT12+AT13", 1950, "gdp_pc_1990ppp"), "value"] == pytest.approx(13945.7e6 / 3_017_000)
    assert df.loc[("nuts2:AT12+AT13", 1950, "population"), "country_iso3"] == "AUT"
    assert 1938 not in df.index.get_level_values("year")


def test_dot_means_missing_and_note_row_is_dropped():
    df = validate_long(roses_wolf.parse(sheets()))
    nl = df[df.geo_id == "nuts2:NL23"]
    assert set(nl.year) == {2020}  # '.' before Flevoland existed
    assert not df.geo_id.str.contains("Note").any()


def test_missing_file_explains_the_manual_download(tmp_path, monkeypatch):
    monkeypatch.setattr(roses_wolf, "RAW_DIR", tmp_path)
    with pytest.raises(roses_wolf.MissingManualDownloadError, match="hu-berlin"):
        roses_wolf.download()
```

- [ ] **Step 2: Run the tests and see them fail.**

Run: `"$PY" -m pytest tests/test_roses_wolf.py -q`
Expected: FAIL with ImportError.

- [ ] **Step 3: Implement.** Create `us_housing_crisis_analysis/sources/roses_wolf.py`:

```python
"""Rosés-Wolf Database on Regional GDP, v7 (2025): population and GDP for European regions (NUTS
2010 units; '+' joins merged units; the UK is NUTS 1). The site is bot-protected, so the workbook
is downloaded by hand into data/raw/roses_wolf/, like ICPSR. '.' marks a missing cell."""

from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import RAW_DATA_DIR, RQ0C_START
from us_housing_crisis_analysis.schema import validate_long

RAW_DIR = RAW_DATA_DIR / "roses_wolf"
FILE = "RosesWolf_RegionalGDP_v7.xlsx"
PAGE = "https://www.wiwi.hu-berlin.de/de/professuren/vwl/wg/roses-wolf-database-on-regional-gdp"
SHEETS = {"population": "A3 Population", "gdp_2011ppp": "A1b Regional GDP (2011PPP)",
          "gdp_1990ppp": "A1 Regional GDP"}
HEADER_ROW = 5
RW_COUNTRIES = {"AT": "AUT", "BE": "BEL", "CH": "CHE", "DE": "DEU", "DK": "DNK", "ES": "ESP", "FI": "FIN",
                "FR": "FRA", "IE": "IRL", "IT": "ITA", "LU": "LUX", "NL": "NLD", "NO": "NOR", "PT": "PRT",
                "SE": "SWE", "UK": "GBR"}


class MissingManualDownloadError(RuntimeError):
    """Raised when the hand-downloaded Rosés-Wolf workbook is not in data/raw/roses_wolf/."""


def download(force: bool = False) -> list[Path]:
    path = RAW_DIR / FILE
    if not path.exists():
        raise MissingManualDownloadError(
            f"missing {FILE} in {RAW_DIR}. The site blocks scripts; download by hand:\n"
            f"  1. Open {PAGE}\n"
            "  2. Download the v7 (2025) Excel workbook.\n"
            f"  3. Save it, unopened and unrenamed, as {path}."
        )
    return [path]


def _long(sheet: pd.DataFrame) -> pd.DataFrame:
    s = sheet[sheet["NUTS-Codes"].notna()].rename(columns=lambda c: c if isinstance(c, str) else int(c))
    years = [c for c in s.columns if isinstance(c, int) and c >= RQ0C_START]
    m = s.melt(id_vars=["NUTS-Codes", "Region"], value_vars=years, var_name="year", value_name="value")
    m["value"] = pd.to_numeric(m.value, errors="coerce")
    return m.dropna(subset=["value"])


def _frame(m: pd.DataFrame, variable: str, value: pd.Series, unit: str) -> pd.DataFrame:
    return pd.DataFrame({
        "geo_id": "nuts2:" + m["NUTS-Codes"], "geo_name": m.Region, "geo_level": "region",
        "country_iso3": m["NUTS-Codes"].str[:2].map(RW_COUNTRIES), "year": m.year, "variable": variable,
        "value": value, "unit": unit, "source": "roses_wolf",
    })


def parse(sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    pop = _long(sheets["population"]).assign(value=lambda d: d.value * 1000)  # thousands -> persons
    frames = [_frame(pop, "population", pop.value, "persons")]
    for key, variable, unit in [("gdp_2011ppp", "gdp_pc", "usd_2011_ppp"),
                                ("gdp_1990ppp", "gdp_pc_1990ppp", "usd_1990_ppp")]:
        g = _long(sheets[key]).merge(pop, on=["NUTS-Codes", "Region", "year"], suffixes=("", "_pop"))
        frames.append(_frame(g, variable, g.value * 1e6 / g.value_pop, unit))  # millions -> per head
    return pd.concat(frames, ignore_index=True).astype({"year": "int64", "value": "float64"})


def load() -> pd.DataFrame:
    path = download()[0]
    sheets = {k: pd.read_excel(path, sheet_name=v, header=HEADER_ROW) for k, v in SHEETS.items()}
    return validate_long(parse(sheets))
```

Append `"roses_wolf"` to `SOURCE_NAMES`.

- [ ] **Step 4: Run the tests and see them pass.**

Run: `"$PY" -m pytest tests/test_roses_wolf.py -q`
Expected: 3 passed.

- [ ] **Step 5: Load the real data and add a data test.** Run `"$PY" -m us_housing_crisis_analysis.dataset load --source roses_wolf`. Append to `tests/data/test_global.py`:

```python
def test_roses_wolf_shape(interim):
    r = interim("roses_wolf")
    pop = r[r.variable == "population"]
    assert pop.geo_id.nunique() == 173 and pop.country_iso3.nunique() == 16
    assert {1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020} <= set(pop.year)
    assert r[r.variable == "gdp_pc"].country_iso3.notna().all()
```

Run: `"$PY" -m pytest tests/data/test_global.py -q`. Expected: all pass.

- [ ] **Step 6: Docs.** In `sources.md`, update the Rosés-Wolf row:
- status: `in use (Plan 3)`
- countries: AT, BE, CH, DE, DK, ES, FI, FR, IE, IT, LU, NL, NO, PT, SE, UK; 173 units; benchmark years to 2015, then annual 2016–2022
- URL: confirmed
- note: the file name, and that the workbook ships no shapefile

Remove "Confirm the Rosés-Wolf database URL" from the open items in `decisions.md`.

- [ ] **Step 7: Commit.**

```bash
git add us_housing_crisis_analysis/sources tests Claude
git commit -m "Rosés-Wolf v7 source: European regional population and GDP per head (Plan 3)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Peer groups, `global_geography.py` part 1

**Files:**
- Create: `us_housing_crisis_analysis/global_geography.py`, `tests/test_global_geography.py`, `references/crosswalks/peer_groups.csv` (generated, then committed)
- Modify: `tests/data/test_global.py`, `Claude/methods/geography.md`, `Claude/methods/analysis-methods.md` (new "Peer groups" section)

**Interfaces:**
- Consumes: `un_wup.country_locations()` (Task 2) and `worldbank.latest_income_groups()` (Task 3).
- Produces:
  - `global_geography.assign_peer_groups(locations: DataFrame, latest_income: Series) -> DataFrame[iso3, name, peer_group (int 1–5), reason]`;
  - `global_geography.PEER_GROUP_NAMES: dict[int, str]`;
  - `global_geography.load_peer_groups() -> DataFrame`;
  - the CLI command `peer-groups`, which writes the CSV.

- [ ] **Step 1: Write the failing tests.** Create `tests/test_global_geography.py`:

```python
import pandas as pd
import pytest

from us_housing_crisis_analysis import global_geography as gg


def locations() -> pd.DataFrame:
    rows = [("USA", "Northern America", None), ("JPN", "Asia", "Eastern Asia"),
            ("KOR", "Asia", "Eastern Asia"), ("POL", "Europe", "Eastern Europe"),
            ("VNM", "Asia", "South-Eastern Asia"), ("TUR", "Asia", "Western Asia"),
            ("BRA", "Latin America and the Caribbean", "South America"),
            ("EGY", "Africa", "Northern Africa"), ("NGA", "Africa", "Western Africa"),
            ("CHL", "Latin America and the Caribbean", "South America"), ("CZE", "Europe", "Eastern Europe"),
            ("GRC", "Europe", "Southern Europe"), ("SAU", "Asia", "Western Asia"), ("REU", "Africa", "Eastern Africa")]
    return pd.DataFrame(rows, columns=["iso3", "region", "subregion"]).assign(name=lambda d: d.iso3)


def income() -> pd.Series:
    return pd.Series({"USA": "H", "JPN": "H", "KOR": "H", "POL": "H", "VNM": "LM", "TUR": "UM", "BRA": "UM",
                      "EGY": "LM", "NGA": "LM", "CHL": "H", "CZE": "H", "GRC": "H", "SAU": "H"})


@pytest.mark.parametrize("iso3, group", [
    ("USA", 1), ("JPN", 1), ("GRC", 1), ("KOR", 2), ("CHL", 2), ("SAU", 2), ("POL", 3), ("CZE", 3),
    ("VNM", 4), ("TUR", 4), ("EGY", 4), ("BRA", 5), ("NGA", 5), ("REU", 5)])
def test_peer_group_rule(iso3, group):
    g = gg.assign_peer_groups(locations(), income()).set_index("iso3")
    assert g.at[iso3, "peer_group"] == group


def test_every_country_gets_exactly_one_group_with_a_reason():
    g = gg.assign_peer_groups(locations(), income())
    assert g.iso3.is_unique and len(g) == len(locations())
    assert g.reason.str.len().gt(0).all() and g.peer_group.between(1, 5).all()
```

- [ ] **Step 2: Run the tests and see them fail.**

Run: `"$PY" -m pytest tests/test_global_geography.py -q`
Expected: FAIL with ImportError.

- [ ] **Step 3: Implement.** Create `us_housing_crisis_analysis/global_geography.py`:

```python
"""RQ0c geography: the fixed peer-group table and the city -> region crosswalk, both committed under
references/crosswalks/ after review. Decisions are documented in Claude/methods/geography.md."""

import pandas as pd
import typer

from us_housing_crisis_analysis.config import CROSSWALKS_DIR

app = typer.Typer()
PEER_GROUPS_PATH = CROSSWALKS_DIR / "peer_groups.csv"
PEER_GROUP_NAMES = {1: "High-income mature", 2: "High-income newly developed", 3: "Transition",
                    4: "Developing Asia, Middle East and North Africa", 5: "Other developing"}
# OECD members by 1975 (Turkey excluded, D-17)
OECD_BY_1975 = {"AUS", "AUT", "BEL", "CAN", "DNK", "FIN", "FRA", "DEU", "GRC", "ISL", "IRL", "ITA", "JPN",
                "LUX", "NLD", "NZL", "NOR", "PRT", "ESP", "SWE", "CHE", "GBR", "USA"}
# Communist-ruled in Europe or the USSR in 1989 (successor states)
TRANSITION = {"ALB", "BGR", "CZE", "SVK", "HUN", "POL", "ROU",
              "ARM", "AZE", "BLR", "EST", "GEO", "KAZ", "KGZ", "LVA", "LTU", "MDA", "RUS", "TJK", "TKM",
              "UKR", "UZB", "BIH", "HRV", "MKD", "MNE", "SRB", "SVN"}


def _group(iso3: str, region: str, subregion: str, income: str | None) -> tuple[int, str]:
    if iso3 in OECD_BY_1975:
        return 1, "OECD member by 1975"
    if iso3 in TRANSITION:
        return 3, "communist-ruled in Europe or the USSR in 1989"
    if income == "H":
        return 2, "World Bank high income in the latest year"
    if iso3 == "TUR":
        return 4, "Turkey (D-17)"
    if region == "Asia" or subregion == "Northern Africa":
        return 4, f"UN region {region}" if region == "Asia" else "UN subregion Northern Africa"
    return 5, f"other: UN region {region}"


def assign_peer_groups(locations: pd.DataFrame, latest_income: pd.Series) -> pd.DataFrame:
    """Spec §3.5: one fixed group per country for the whole period, checked in rule order."""
    rows = [(r.iso3, r.name, *_group(r.iso3, r.region, r.subregion, latest_income.get(r.iso3)))
            for r in locations.itertuples()]
    return pd.DataFrame(rows, columns=["iso3", "name", "peer_group", "reason"]).sort_values("iso3").reset_index(drop=True)


def load_peer_groups() -> pd.DataFrame:
    return pd.read_csv(PEER_GROUPS_PATH)


@app.command("peer-groups")
def write_peer_groups():
    from us_housing_crisis_analysis.sources import un_wup, worldbank
    g = assign_peer_groups(un_wup.country_locations(), worldbank.latest_income_groups())
    g.to_csv(PEER_GROUPS_PATH, index=False)
    print(g.peer_group.value_counts().sort_index().to_string())


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Run the tests and see them pass.**

Run: `"$PY" -m pytest tests/test_global_geography.py -q`
Expected: 15 passed.

- [ ] **Step 5: Generate and review the table.** Run `"$PY" -m us_housing_crisis_analysis.global_geography peer-groups`. Expect 233 countries. Read the group-2 list: it should include KOR, ISR, SGP, TWN, HKG, MAC, CHL, URY, the Gulf states, and also PAN and GUY, which are high income in 2023 by the rule. Report the full group-2 list in the task report; don't hand-edit the CSV. Append to `tests/data/test_global.py`:

```python
def test_peer_groups_cover_every_agglomeration_country():
    from us_housing_crisis_analysis import global_geography as gg
    g = gg.load_peer_groups().set_index("iso3").peer_group
    a = un_wup.agglomeration_attributes()
    assert set(a.iso3) <= set(g.index) and len(g) == 233
    expected = {"USA": 1, "JPN": 1, "KOR": 2, "POL": 3, "VNM": 4, "TUR": 4, "BRA": 5}
    assert {k: g[k] for k in expected} == expected
```

Run: `"$PY" -m pytest tests/data/test_global.py -q`. Expected: all pass.

- [ ] **Step 6: Docs.** Add a "Peer groups (RQ0c)" section to `analysis-methods.md` with:
- the rule, in order;
- the group counts;
- the note that a membership fixed for the whole period avoids breaks created by a country moving between groups;
- the group-2 list.

In `geography.md`, describe `peer_groups.csv` and how it is regenerated.

- [ ] **Step 7: Commit.**

```bash
git add us_housing_crisis_analysis/global_geography.py references/crosswalks/peer_groups.csv tests Claude
git commit -m "Fixed peer groups for every country, by the RQ0c rule (Plan 3)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: City → region crosswalk, `global_geography.py` part 2

**Files:**
- Modify: `us_housing_crisis_analysis/global_geography.py`, `tests/test_global_geography.py`, `tests/data/test_global.py`, `Claude/methods/geography.md`, `Claude/research/sources.md`
- Create: `references/crosswalks/wup_to_region.csv` (generated, reviewed, committed)

**Interfaces:**
- Consumes: `un_wup.agglomeration_attributes()`; interim `roses_wolf` and `dose` (which regions exist).
- Produces:
  - `global_geography.match_points(points: DataFrame[geo_id, iso3, latitude, longitude], polygons: GeoDataFrame[region_id, region_name, iso3, geometry]) -> DataFrame[geo_id, region_id, region_name, method, distance_km, border_km]`;
  - `rw_polygons(codes: pd.DataFrame[code, name], nuts: GeoDataFrame) -> GeoDataFrame`;
  - `load_wup_to_region() -> DataFrame` with columns `geo_id, geo_name, iso3, region_id, region_name, method, distance_km, border_km, note`;
  - the CLI command `city-regions`.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_global_geography.py`:

```python
import geopandas as gpd
from shapely.geometry import box


def polygons() -> gpd.GeoDataFrame:
    # two countries side by side; country A has two regions split at x = 1
    return gpd.GeoDataFrame({
        "region_id": ["gadm1:A.1_1", "gadm1:A.2_1", "gadm1:B.1_1"], "region_name": ["West", "East", "Bland"],
        "iso3": ["AAA", "AAA", "BBB"],
        "geometry": [box(0, 0, 1, 1), box(1, 0, 2, 1), box(2, 0, 3, 1)]}, crs="EPSG:4326")


def test_points_inside_get_their_region_and_border_distance():
    pts = pd.DataFrame({"geo_id": ["wup:1", "wup:2"], "iso3": ["AAA", "AAA"],
                        "latitude": [0.5, 0.5], "longitude": [0.5, 1.95]})
    m = gg.match_points(pts, polygons()).set_index("geo_id")
    assert m.at["wup:1", "region_id"] == "gadm1:A.1_1" and m.at["wup:1", "method"] == "within"
    assert m.at["wup:2", "region_id"] == "gadm1:A.2_1"
    assert m.at["wup:2", "border_km"] < 10 < m.at["wup:1", "border_km"]  # 0.05 deg ~ 5.6 km from B


def test_offshore_point_gets_nearest_region_in_its_own_country():
    # just east of the A/B border, but the city belongs to country A: never assign B's region
    pts = pd.DataFrame({"geo_id": ["wup:3"], "iso3": ["AAA"], "latitude": [1.02], "longitude": [1.99]})
    m = gg.match_points(pts, polygons()).set_index("geo_id")
    assert m.at["wup:3", "region_id"] == "gadm1:A.2_1" and m.at["wup:3", "method"] == "nearest"
    assert 0 < m.at["wup:3", "distance_km"] < 5


def test_merged_roses_wolf_codes_are_dissolved():
    nuts = gpd.GeoDataFrame({"NUTS_ID": ["AT12", "AT13", "AT21"], "CNTR_CODE": ["AT"] * 3,
                             "geometry": [box(0, 0, 1, 1), box(1, 0, 2, 1), box(2, 0, 3, 1)]}, crs="EPSG:4326")
    codes = pd.DataFrame({"code": ["AT12+AT13", "AT21"], "name": ["Lower Austria", "Carinthia"]})
    p = gg.rw_polygons(codes, nuts).set_index("region_id")
    assert list(p.index) == ["nuts2:AT12+AT13", "nuts2:AT21"]
    assert p.at["nuts2:AT12+AT13", "geometry"].area == pytest.approx(2.0)
    assert p.at["nuts2:AT21", "iso3"] == "AUT"
```

- [ ] **Step 2: Run the tests and see them fail.**

Run: `"$PY" -m pytest tests/test_global_geography.py -q`
Expected: FAIL with AttributeError (`match_points`).

- [ ] **Step 3: Implement.** Add to `global_geography.py`: new imports at the top, and the functions before the `if __name__` block.

```python
from us_housing_crisis_analysis.config import RAW_DATA_DIR
from us_housing_crisis_analysis.sources._http import download_file

BOUNDARY_DIR = RAW_DATA_DIR / "boundaries"
NUTS_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2010_4326.geojson"
NUTS_PATH = BOUNDARY_DIR / "NUTS_RG_20M_2010_4326.geojson"
GADM_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_{iso3}_1.json.zip"
WUP_TO_REGION_PATH = CROSSWALKS_DIR / "wup_to_region.csv"
BORDER_KM = 10  # cities this close to a regional border are listed for a hand check


def download_boundaries(gadm_iso3: list[str], force: bool = False) -> list[str]:
    """NUTS 2010 plus one GADM level-1 file per country. Returns the ISO3 codes GADM has; a country
    GADM lacks (HTTP 404) is skipped with a warning, and its cities stay unmatched."""
    import requests
    from loguru import logger
    download_file(NUTS_URL, NUTS_PATH, force=force)
    found = []
    for iso3 in gadm_iso3:
        try:
            download_file(GADM_URL.format(iso3=iso3), BOUNDARY_DIR / f"gadm41_{iso3}_1.json.zip", force=force)
            found.append(iso3)
        except requests.HTTPError as e:
            logger.warning(f"no GADM 4.1 level-1 file for {iso3}: {e}")
    return found


def rw_polygons(codes: pd.DataFrame, nuts):
    """One polygon per Rosés-Wolf unit: NUTS 2010 parts ('AT12+AT13') dissolved together."""
    import geopandas as gpd
    from us_housing_crisis_analysis.sources.roses_wolf import RW_COUNTRIES
    parts = codes.assign(part=codes.code.str.split("+")).explode("part")
    shapes = nuts.set_index("NUTS_ID")[["geometry"]]
    missing = sorted(set(parts.part) - set(shapes.index))
    if missing:
        raise ValueError(f"Rosés-Wolf codes not in NUTS 2010: {missing}")
    g = gpd.GeoDataFrame(parts.merge(shapes, left_on="part", right_index=True), crs=nuts.crs)
    g = g.dissolve("code", aggfunc={"name": "first"}).reset_index()
    return g.assign(region_id="nuts2:" + g.code, region_name=g.name,
                    iso3=g.code.str[:2].map(RW_COUNTRIES))[["region_id", "region_name", "iso3", "geometry"]]


def gadm_polygons(iso3s: list[str]):
    import geopandas as gpd
    frames = [gpd.read_file(f"zip://{BOUNDARY_DIR / f'gadm41_{c}_1.json.zip'}") for c in iso3s]
    g = pd.concat(frames, ignore_index=True)
    return gpd.GeoDataFrame({"region_id": "gadm1:" + g.GID_1, "region_name": g.NAME_1, "iso3": g.GID_0},
                            geometry=g.geometry, crs=frames[0].crs)


def match_points(points: pd.DataFrame, polygons) -> pd.DataFrame:
    """Each city to the region of its own country that contains it. Off the (generalized) coastline:
    the nearest region of the same country, flagged 'nearest'. Distances in km, measured in a UTM
    zone per country."""
    import geopandas as gpd
    out = []
    for iso3, pts in points.groupby("iso3"):
        poly = polygons[polygons.iso3 == iso3]
        if poly.empty:
            continue
        p = gpd.GeoDataFrame(pts, geometry=gpd.points_from_xy(pts.longitude, pts.latitude), crs="EPSG:4326")
        utm = p.estimate_utm_crs()
        p, poly = p.to_crs(utm), poly.to_crs(utm)
        within = gpd.sjoin(p, poly[["region_id", "region_name", "geometry"]], how="left", predicate="within")
        within = within[~within.index.duplicated()]
        hit = within.region_id.notna()
        near = gpd.sjoin_nearest(p[~hit.to_numpy()], poly[["region_id", "region_name", "geometry"]],
                                 how="left", distance_col="distance_m")
        near = near[~near.index.duplicated()]
        matched = pd.concat([within[hit].assign(method="within", distance_m=0.0), near.assign(method="nearest")])
        borders = poly.set_index("region_id").boundary
        matched["border_km"] = [geom.distance(borders[r]) / 1000 for geom, r in zip(matched.geometry, matched.region_id)]
        out.append(pd.DataFrame({"geo_id": matched.geo_id, "region_id": matched.region_id,
                                 "region_name": matched.region_name, "method": matched.method,
                                 "distance_km": matched.distance_m / 1000, "border_km": matched.border_km}))
    return pd.concat(out, ignore_index=True)


def load_wup_to_region() -> pd.DataFrame:
    return pd.read_csv(WUP_TO_REGION_PATH)


@app.command("city-regions")
def write_city_regions():
    """Match every WUP agglomeration in a country with regional data (Rosés-Wolf or DOSE) to a region.
    Keeps the 'note' column of an existing file, so hand-check notes survive a rebuild."""
    import geopandas as gpd
    from us_housing_crisis_analysis.config import INTERIM_DATA_DIR
    from us_housing_crisis_analysis.sources import un_wup
    rw = pd.read_parquet(INTERIM_DATA_DIR / "roses_wolf.parquet")
    dose = pd.read_parquet(INTERIM_DATA_DIR / "dose.parquet")
    rw_iso = set(rw.country_iso3)
    gadm_iso = download_boundaries(sorted(set(dose.country_iso3) - rw_iso))
    codes = rw.drop_duplicates("geo_id").assign(code=lambda d: d.geo_id.str.removeprefix("nuts2:"))
    polys = pd.concat([rw_polygons(codes[["code", "geo_name"]].rename(columns={"geo_name": "name"}),
                                   gpd.read_file(NUTS_PATH)),
                       gadm_polygons(gadm_iso)], ignore_index=True)
    attrs = un_wup.agglomeration_attributes()
    pts = attrs[attrs.iso3.isin(rw_iso | set(gadm_iso))]
    m = attrs[["geo_id", "geo_name", "iso3"]].merge(match_points(pts, polys), on="geo_id")
    old = load_wup_to_region()[["geo_id", "note"]] if WUP_TO_REGION_PATH.exists() else pd.DataFrame(columns=["geo_id", "note"])
    m = m.merge(old, on="geo_id", how="left").sort_values("geo_id")
    m.to_csv(WUP_TO_REGION_PATH, index=False, float_format="%.2f")
    check = m[(m.method == "nearest") | (m.border_km < BORDER_KM)]
    print(f"{len(m)} cities matched; {len(check)} to check by hand:\n{check.to_string()}")
```

- [ ] **Step 4: Run the tests and see them pass.**

Run: `"$PY" -m pytest tests/test_global_geography.py -q`
Expected: 18 passed.

- [ ] **Step 5: Build and review the crosswalk.** Run `"$PY" -m us_housing_crisis_analysis.global_geography city-regions`. For every printed row (method `nearest`, or within 10 km of a regional border), check that the region is right: does the city's core lie in that region? Write `ok` or a short correction note in `note`.
  - If a match is wrong, correct `region_id`/`region_name` in the CSV by hand and say why in `note`.
  - Expected `nearest` rows include Venezia, Vigo and Bournemouth/Poole.
  - Report the counts (matched; checked; corrected) in the task report.

Then append to `tests/data/test_global.py`:

```python
def test_city_region_crosswalk():
    from us_housing_crisis_analysis import global_geography as gg
    m = gg.load_wup_to_region().set_index("geo_id")
    assert m.index.is_unique
    assert m.at["wup:22860", "region_id"] == "nuts2:UKI"       # London
    assert m.at["wup:20985", "region_id"] == "nuts2:FR10"      # Paris
    assert m.at["wup:21671", "region_id"] == "gadm1:JPN.41_1"  # Tokyo
    flagged = m[(m.method == "nearest") | (m.border_km < gg.BORDER_KM)]
    assert flagged.note.notna().all()  # every flagged match was checked by hand
    attrs = un_wup.agglomeration_attributes().set_index("geo_id")
    assert (attrs.loc[m.index, "iso3"] == m.iso3).all()  # never a region across a border
```

Run: `"$PY" -m pytest tests/data/test_global.py -q`. Expected: all pass.

- [ ] **Step 6: Docs.** In `sources.md`, add rows for GISCO NUTS 2010 (`NUTS_RG_20M_2010_4326.geojson`, © EuroGeographics, reuse with attribution) and GADM 4.1 level 1 (`gadm41_{ISO3}_1.json.zip`, free for academic use, no redistribution, so the raw files stay in gitignored `data/raw/boundaries/`). In `geography.md`, describe:
- the matching rule (within, otherwise nearest in the same country, UTM distances);
- the 10 km hand check;
- the fact that metro-wide agglomerations take the region of their point (WUP's coordinates);
- the counts.

- [ ] **Step 7: Commit.**

```bash
git add us_housing_crisis_analysis/global_geography.py references/crosswalks/wup_to_region.csv tests Claude
git commit -m "City-to-region crosswalk: WUP agglomerations to Rosés-Wolf and GADM regions, hand-checked (Plan 3)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Panels `global_regions` and `global_agglomerations`

**Files:**
- Modify: `us_housing_crisis_analysis/features.py`, `tests/test_features.py`, `tests/data/test_global.py`, `references/crosswalks/growth_allowlist.csv`, `references/known_values.csv`, `Claude/methods/pipeline.md`, master spec §4 (processed panels table)

**Interfaces:**
- Consumes: interim `roses_wolf`, `dose`, `estat_japan`, `un_wup`, `maddison`, `bea`; `global_geography.load_peer_groups()`, `load_wup_to_region()`; `un_wup.agglomeration_attributes()`.
- Produces:
  - `build_global_regions(roses_wolf, dose, estat_japan, peer_groups) -> DataFrame` with columns `REGION_COLUMNS = ["geo_id", "geo_name", "country_iso3", "country_unit", "year", "population", "income_pc", "income_source", "income_pc_1990ppp", "peer_group"]`, at decade years 1950–2020.
  - `build_global_agglomerations(un_wup, maddison, attributes, peer_groups, wup_to_region, regions, bea) -> DataFrame` with columns `AGGLOMERATION_COLUMNS = ["geo_id", "geo_name", "country_iso3", "country_unit", "year", "population", "gdppc", "urban_share", "peer_group", "concept", "capital", "census_years", "region_id", "region_income_pc"]`, every 5 years 1950–2015.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_features.py`:

```python
def glong(rows, source, level="region"):
    df = pd.DataFrame(rows, columns=["geo_id", "country_iso3", "year", "variable", "value"])
    return df.assign(geo_name=df.geo_id, geo_level=level, unit="x", source=source,
                     year=df.year.astype("int64"), value=df.value.astype("float64"))


PEERS = pd.DataFrame({"iso3": ["DEU", "JPN", "MEX", "AUT"], "name": ["D", "J", "M", "A"],
                      "peer_group": [1, 1, 5, 1], "reason": ["r"] * 4})


def test_global_regions_one_source_per_country_and_japan_census():
    rw = glong([("nuts2:DE60", "DEU", 1980, "population", 1.6e6), ("nuts2:DE60", "DEU", 1980, "gdp_pc", 40000),
                ("nuts2:DE60", "DEU", 1980, "gdp_pc_1990ppp", 30000)], "roses_wolf")
    dose = glong([("gadm1:DEU.6_1", "DEU", 1980, "population", 1.6e6), ("gadm1:DEU.6_1", "DEU", 1980, "grp_pc", 1),
                  ("gadm1:JPN.41_1", "JPN", 1960, "grp_pc", 12000), ("gadm1:JPN.41_1", "JPN", 1975, "population", 1),
                  ("gadm1:MEX.9_1", "MEX", 1970, "population", 7e6), ("gadm1:MEX.9_1", "MEX", 1970, "grp_pc", 9000),
                  ("gadm1:MEX.9_1", "MEX", 1971, "grp_pc", 9100)], "dose")
    jp = glong([("gadm1:JPN.41_1", "JPN", y, "population_census", 9e6) for y in (1950, 1955, 1960)], "estat_japan")
    p = features.build_global_regions(rw, dose, jp, PEERS).set_index(["geo_id", "year"])
    assert "gadm1:DEU.6_1" not in p.index.get_level_values(0)  # Germany comes from Rosés-Wolf only
    assert p.loc[("nuts2:DE60", 1980), "income_pc_1990ppp"] == 30000
    assert p.loc[("gadm1:JPN.41_1", 1960), "population"] == 9e6  # census, not DOSE
    assert p.loc[("gadm1:JPN.41_1", 1960), "income_pc"] == 12000
    assert np.isnan(p.loc[("gadm1:JPN.41_1", 1950), "income_pc"])  # no income yet: NaN, not 0
    assert 1955 not in p.index.get_level_values("year") and 1971 not in p.index.get_level_values("year")
    assert p.loc[("gadm1:MEX.9_1", 1970), "peer_group"] == 5


def test_global_regions_east_germany_is_its_own_unit_before_1990():
    rows = []
    for code in ("DE60", "DED2", "DE30"):
        for y in (1980, 1990):
            rows += [(f"nuts2:{code}", "DEU", y, "population", 1e6), (f"nuts2:{code}", "DEU", y, "gdp_pc", 1e4)]
    p = features.build_global_regions(glong(rows, "roses_wolf"), glong([], "dose"), glong([], "estat_japan"), PEERS)
    unit = p.set_index(["geo_id", "year"]).country_unit
    assert unit[("nuts2:DED2", 1980)] == "DEU_EAST" and unit[("nuts2:DED2", 1990)] == "DEU"
    assert unit[("nuts2:DE60", 1980)] == "DEU"
    assert ("nuts2:DE30", 1980) not in unit.index and unit[("nuts2:DE30", 1990)] == "DEU"


def test_global_agglomerations_join_national_and_regional_values():
    wup = pd.concat([
        glong([("wup:1", "MEX", y, "population", 1e6 + y) for y in (1950, 1955, 2015, 2020)], "un_wup", "agglomeration"),
        glong([("iso3:MEX", "MEX", 1950, "urban_share", 42.6)], "un_wup", "country")])
    mad = glong([("iso3:MEX", "MEX", 1950, "gdppc", 3000), ("iso3:MEX", "MEX", 1955, "gdppc", 3500)], "maddison", "country")
    attrs = pd.DataFrame({"geo_id": ["wup:1"], "geo_name": ["Ciudad"], "iso3": ["MEX"], "latitude": [19.4],
                          "longitude": [-99.1], "concept": ["Urban Agglomeration"], "capital": [True],
                          "census_years": ["1950 1960"]})
    xw = pd.DataFrame({"geo_id": ["wup:1"], "region_id": ["gadm1:MEX.9_1"]})
    regions = pd.DataFrame({"geo_id": ["gadm1:MEX.9_1"], "year": [1950], "income_pc": [9000.0]})
    p = features.build_global_agglomerations(wup, mad, attrs, PEERS, xw, regions, glong([], "bea", "state"))
    p = p.set_index("year")
    assert list(p.index) == [1950, 1955, 2015]  # projections dropped
    assert p.at[1950, "gdppc"] == 3000 and p.at[1950, "urban_share"] == 42.6
    assert p.at[1950, "region_income_pc"] == 9000 and np.isnan(p.at[1955, "region_income_pc"])
    assert np.isnan(p.at[2015, "gdppc"]) and p.at[1950, "peer_group"] == 5


def test_global_agglomerations_us_take_bea_state_income():
    wup = glong([("wup:23083", "USA", 1950, "population", 1.2e7)], "un_wup", "agglomeration")
    attrs = pd.DataFrame({"geo_id": ["wup:23083"], "geo_name": ["New York-Newark"], "iso3": ["USA"], "latitude": [40.7],
                          "longitude": [-74.0], "concept": ["Urban Agglomeration"], "capital": [False],
                          "census_years": ["1950"]})
    xw = pd.DataFrame({"geo_id": ["wup:23083"], "region_id": ["gadm1:USA.33_1"], "region_name": ["New York"]})
    bea = glong([("state:36", "USA", 1950, "income_pc", 1900)], "bea", "state").assign(geo_name="New York")
    peers = pd.DataFrame({"iso3": ["USA"], "name": ["U"], "peer_group": [1], "reason": ["r"]})
    p = features.build_global_agglomerations(wup, glong([], "maddison", "country"), attrs, peers, xw,
                                             pd.DataFrame(columns=["geo_id", "year", "income_pc"]), bea)
    assert p.region_income_pc.iloc[0] == 1900
```

- [ ] **Step 2: Run the tests and see them fail.**

Run: `"$PY" -m pytest tests/test_features.py -q -k global`
Expected: FAIL with AttributeError.

- [ ] **Step 3: Implement.** In `features.py`:
1. Extend the config import with `GDR_BERLIN, GDR_REGIONS, GDR_UNTIL, RQ0C_CITY_END, RQ0C_END, RQ0C_START`.
2. Add the code below before `@app.command()`.
3. Extend `main()`.

```python
REGION_COLUMNS = ["geo_id", "geo_name", "country_iso3", "country_unit", "year", "population", "income_pc",
                  "income_source", "income_pc_1990ppp", "peer_group"]


def _wide(df: pd.DataFrame, variable: str, name: str, years) -> pd.DataFrame:
    p = _pick(df, variable, years)
    return p[["geo_id", "year", "value"]].rename(columns={"value": name})


def build_global_regions(roses_wolf: pd.DataFrame, dose: pd.DataFrame, estat_japan: pd.DataFrame,
                         peer_groups: pd.DataFrame) -> pd.DataFrame:
    """Region x decade (RQ0c spec §4.1): Rosés-Wolf for its 16 countries, DOSE for the rest; Japan's
    population from its census (DOSE has none before 1975). GDR regions are their own country unit
    before 1990 and Berlin is dropped then (D-29). Missing income stays NaN."""
    years = list(range(RQ0C_START, RQ0C_END + 1, 10))
    names = pd.concat([roses_wolf, dose, estat_japan]).drop_duplicates("geo_id").set_index("geo_id")
    rw_iso = set(roses_wolf.country_iso3)
    dose = dose[~dose.country_iso3.isin(rw_iso)]
    rw_pop = _wide(roses_wolf, "population", "population", years)
    rw_inc = _wide(roses_wolf, "gdp_pc", "income_pc", years).merge(
        _wide(roses_wolf, "gdp_pc_1990ppp", "income_pc_1990ppp", years), on=["geo_id", "year"], how="outer")
    jp = dose.geo_id.str.startswith("gadm1:JPN.")
    pop = pd.concat([rw_pop, _wide(dose[~jp], "population", "population", years),
                     _wide(estat_japan, "population_census", "population", years)], ignore_index=True)
    inc = pd.concat([rw_inc.assign(income_source="roses_wolf"),
                     _wide(dose, "grp_pc", "income_pc", years).assign(income_source="dose")], ignore_index=True)
    out = pop.merge(inc, on=["geo_id", "year"], how="left")
    out["geo_name"] = out.geo_id.map(names.geo_name)
    out["country_iso3"] = out.geo_id.map(names.country_iso3)
    code = out.geo_id.str.removeprefix("nuts2:")
    before = out.year < GDR_UNTIL
    out = out[~(code.eq(GDR_BERLIN) & before)]
    east = code.reindex(out.index).isin(GDR_REGIONS) & before.reindex(out.index)
    out["country_unit"] = out.country_iso3.where(~east, "DEU_EAST")
    out["peer_group"] = out.country_iso3.map(peer_groups.set_index("iso3").peer_group)
    out["income_source"] = out.income_source.fillna(out.geo_id.str.startswith("nuts2:").map({True: "roses_wolf", False: "dose"}))
    return out[REGION_COLUMNS].sort_values(["geo_id", "year"]).reset_index(drop=True)


AGGLOMERATION_COLUMNS = ["geo_id", "geo_name", "country_iso3", "country_unit", "year", "population", "gdppc",
                         "urban_share", "peer_group", "concept", "capital", "census_years", "region_id",
                         "region_income_pc"]


def build_global_agglomerations(un_wup: pd.DataFrame, maddison: pd.DataFrame, attributes: pd.DataFrame,
                                peer_groups: pd.DataFrame, wup_to_region: pd.DataFrame,
                                regions: pd.DataFrame, bea: pd.DataFrame) -> pd.DataFrame:
    """Agglomeration x 5 years, 1950-2015 (master spec §4 panel; RQ0c spec §4.3, §4.5). National GDP
    and % urban by country-year; the region's income where the city is matched to a region (US: BEA
    state income, spec §4.4). Gaps stay NaN: a missing national GDP is never filled (D-27)."""
    years = list(range(RQ0C_START, RQ0C_CITY_END + 1, 5))
    a = _pick(un_wup, "population", years, "agglomeration")[["geo_id", "year", "value"]].rename(columns={"value": "population"})
    a = a.merge(attributes.drop(columns=["latitude", "longitude"]).rename(columns={"iso3": "country_iso3"}), on="geo_id")
    gdp = _pick(maddison, "gdppc", years)[["country_iso3", "year", "value"]].rename(columns={"value": "gdppc"})
    urb = _pick(un_wup, "urban_share", years, "country")[["country_iso3", "year", "value"]].rename(columns={"value": "urban_share"})
    a = a.merge(gdp, on=["country_iso3", "year"], how="left").merge(urb, on=["country_iso3", "year"], how="left")
    a["peer_group"] = a.country_iso3.map(peer_groups.set_index("iso3").peer_group)
    xw = wup_to_region.set_index("geo_id")
    a["region_id"] = a.geo_id.map(xw.region_id)
    reg_inc = regions.set_index(["geo_id", "year"]).income_pc
    a["region_income_pc"] = [reg_inc.get((r, y), float("nan")) for r, y in zip(a.region_id, a.year)]
    us = a.country_iso3.eq("USA")
    if us.any():
        state_inc = _pick(bea, "income_pc", years, "state").set_index(["geo_name", "year"]).value
        names = a.geo_id.map(xw.region_name) if "region_name" in xw else pd.Series(index=a.index, dtype=object)
        a.loc[us, "region_income_pc"] = [state_inc.get((n, y), float("nan")) for n, y in zip(names[us], a.year[us])]
    code = a.region_id.fillna("").str.removeprefix("nuts2:")
    a["country_unit"] = a.country_iso3.where(~(code.isin(GDR_REGIONS) & (a.year < GDR_UNTIL)), "DEU_EAST")
    return a[AGGLOMERATION_COLUMNS].sort_values(["geo_id", "year"]).reset_index(drop=True)
```

Extend `main()`:

```python
    from us_housing_crisis_analysis import global_geography
    from us_housing_crisis_analysis.sources import un_wup
    rw, dose, jp, wup, mad = (read(s) for s in ("roses_wolf", "dose", "estat_japan", "un_wup", "maddison"))
    peers = global_geography.load_peer_groups()
    regions = build_global_regions(rw, dose, jp, peers)
    panels["global_regions"] = regions
    panels["global_agglomerations"] = build_global_agglomerations(
        wup, mad, un_wup.agglomeration_attributes(), peers, global_geography.load_wup_to_region(), regions, bea)
```

These lines go after the existing `panels = {...}` dict and before the loop that writes the panels.

- [ ] **Step 4: Run the tests and see them pass.**

Run: `"$PY" -m pytest tests/test_features.py -q`
Expected: all pass.

- [ ] **Step 5: Allowlist and known values.** Append these rows to `references/crosswalks/growth_allowlist.csv`. The year is the start of the 5-year step. Before committing, verify the two rows marked "cause not checked" against a source, or leave the text as is:

```csv
wup:20357,1970,Phnom Penh: Khmer Rouge emptied the city in April 1975
wup:20667,1980,Shenzhen: Special Economic Zone founded 1980
wup:20667,1985,Shenzhen: Special Economic Zone growth
wup:23914,1990,Xinmi (China): UN series triples from a small base; cause not checked
wup:23914,1995,Xinmi (China): UN series triples from a small base; cause not checked
wup:23792,1990,Xinzheng (China): UN series triples from a small base; cause not checked
wup:23792,1995,Xinzheng (China): UN series triples from a small base; cause not checked
wup:204553,1980,Ruiru (Kenya): Nairobi satellite town growth from a small base; cause not checked
wup:204553,1985,Ruiru (Kenya): Nairobi satellite town growth from a small base; cause not checked
wup:21779,1990,Monrovia: first Liberian civil war (1989-1997)
wup:21826,1970,Cancún: planned resort city founded 1970
wup:21826,1975,Cancún: planned resort city
wup:21923,1985,Salalah (Oman): UN series triples; cause not checked
wup:22066,1965,Ciudad del Este: Friendship Bridge to Brazil opened 1965
wup:205913,2005,Doha Industrial Area: construction-worker housing during the Gulf building boom
wup:22303,1970,Naberezhnye Chelny: KamAZ truck plant built from 1969
wup:22608,2010,Aleppo: Syrian civil war
wup:23075,1980,Bonita Springs-Naples FL: growth from a small base
wup:23075,1985,Bonita Springs-Naples FL: growth from a small base
wup:23465,1970,Port St. Lucie FL: planned community developed from the 1960s
wup:23465,1975,Port St. Lucie FL: planned community
```

Append to `references/known_values.csv`:

```csv
global_agglomerations,wup:21671,1950,population,11274641,0.000001,"WUP 2018 File 12, Tokyo 1950 = 11,274.641 thousand; checked 2026-10-14"
global_agglomerations,wup:23083,1950,population,12338471,0.000001,"WUP 2018 File 12, New York-Newark 1950 = 12,338.471 thousand; checked 2026-10-14"
global_regions,gadm1:JPN.41_1,1980,population,11618281,0.000001,"Japan census 1980, Tokyo; equals DOSE V2.11; checked 2026-10-14"
```

- [ ] **Step 6: Build and add data tests.** Run `make features PYTHON_INTERPRETER="$PY"`. Append to `tests/data/test_global.py`:

```python
from us_housing_crisis_analysis.config import CROSSWALKS_DIR

# Rosés-Wolf population vs Maddison: tolerances where the two cover different territory
RW_TOLERANCE = {"PRT": 0.07,  # Azores and Madeira not in Rosés-Wolf
                "FRA": 0.045,  # overseas regions not in Rosés-Wolf
                ("NLD", 1950): 0.03,  # Flevoland (NL23) did not exist yet
                ("DNK", 1980): 0.06}


@pytest.mark.parametrize("year", [1950, 1980, 2010])
def test_roses_wolf_population_adds_up_to_maddison(processed, interim, year):
    r = processed("global_regions")
    r = r[(r.year == year) & r.geo_id.str.startswith("nuts2:")].groupby("country_iso3").population.sum()
    m = interim("maddison")
    m = m[(m.variable == "population_maddison") & (m.year == year)].set_index("country_iso3").value
    rel = (r / m[r.index] - 1).abs()
    for iso3, gap in rel.items():
        tol = RW_TOLERANCE.get((iso3, year), RW_TOLERANCE.get(iso3, 0.02))
        assert gap <= tol, (iso3, year, gap)


def test_regions_panel_rules(processed):
    r = processed("global_regions")
    assert not r.duplicated(["geo_id", "year"]).any()
    assert set(r.year) == set(range(1950, 2021, 10))
    assert r[r.geo_id == "nuts2:DE30"].year.min() == 1990
    assert (r[r.country_unit == "DEU_EAST"].year < 1990).all()
    assert r.peer_group.notna().all() and (r.income_pc.dropna() > 0).all()
    assert r[r.country_iso3 == "JPN"].query("year == 1960").income_pc.notna().sum() >= 46


def test_agglomeration_growth_is_plausible(processed):
    p = processed("global_agglomerations").sort_values(["geo_id", "year"])
    nxt = p.groupby("geo_id")[["year", "population"]].shift(-1)
    ratio = (nxt.population / p.population).where(nxt.year == p.year + 5)
    flagged = p.assign(ratio=ratio)[(ratio < 0.5) | (ratio > 3.0)]
    allow = pd.read_csv(CROSSWALKS_DIR / "growth_allowlist.csv", dtype={"year": "int64"})
    flagged = flagged.merge(allow, on=["geo_id", "year"], how="left", indicator=True)
    assert (flagged._merge == "both").all(), flagged[flagged._merge != "both"][["geo_id", "geo_name", "year", "ratio"]]


def test_missing_national_gdp_is_exactly_the_documented_set(processed):
    p = processed("global_agglomerations")
    missing = p[p.gdppc.isna()].groupby("country_iso3").year.max()
    assert {"ERI", "MAC", "PNG", "SOM", "SSD"} <= set(missing.index)
    assert missing.get("UKR") == 1970 and missing.get("CZE") == 1965 and missing.get("SVK") == 1980
```

Run: `"$PY" -m pytest tests/data -q`. Expected: all pass, including the known-values test, which now covers three more rows. If a missing-GDP country shows up that isn't in the documented set, report it rather than editing the test.

- [ ] **Step 7: Docs.** In `pipeline.md`, describe the two panels and their columns. In the master spec §4 processed-panels table:
- `global_agglomerations` → "agglomeration × 5-year step, 1950–2015, with peer group, national GDP, % urban and region income";
- add a row `global_regions | region × decade, 1950–2020 (Rosés-Wolf, DOSE, Japan census) | RQ0c`.

- [ ] **Step 8: Commit.**

```bash
git add us_housing_crisis_analysis/features.py tests references Claude docs/superpowers/specs/2026-10-08-housing-growth-mismatch-design.md
git commit -m "Build global_regions and global_agglomerations panels (Plan 3)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: `modeling/global_timing.py`, within-country β and break tests

**Files:**
- Create: `us_housing_crisis_analysis/modeling/global_timing.py`, `tests/test_global_timing.py`

**Interfaces:**
- Consumes: `breaks.prepare_decade_panel`, `breaks.chow_test`, `breaks.break_search`, `breaks.TestResult`, `breaks.BreakSearch` (read-only).
- Produces:
  - `region_decades(panel, start=1950, end=2020) -> DataFrame[geo_id, decade, growth, log_income, income_source, country_unit, peer_group]`;
  - `demean_within(dp, by=("country_unit", "decade")) -> DataFrame`, which drops cells with fewer than 2 units;
  - `chow_within(dp, break_decade, cluster="geo_id") -> breaks.TestResult`, where `cluster="country_unit"` is the country-cluster check;
  - `break_search_within(dp, max_breaks=3, min_segment=2) -> breaks.BreakSearch`;
  - `decade_betas_within(dp) -> DataFrame[decade, beta, se, n, n_countries]`;
  - `group_break_tests(dp, years=(1970, 1980, 1990), cluster="geo_id") -> dict` with keys `chow_<y>_p`, `chow_<y>_stat`, `bic_breaks`, `n_units`, `n_countries`, `decades`.

- [ ] **Step 1: Write the failing tests.** Create `tests/test_global_timing.py`:

```python
import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from us_housing_crisis_analysis.modeling import breaks, global_timing as gt

DECADES = list(range(1950, 2020, 10))


def simulate(beta_for, n_countries=5, n_regions=12, seed=0, noise=0.03, country_shock=0.2):
    """Regions in countries; each country-decade gets its own growth shock and income level, so a
    model without country x decade constants would mistake them for the income slope."""
    rng = np.random.default_rng(seed)
    rows = []
    for c in range(n_countries):
        for d in DECADES:
            shock, level = rng.normal(0, country_shock), rng.normal(0, 1)
            for r in range(n_regions):
                x = rng.normal(0, 0.3)
                rows.append({"geo_id": f"c{c}r{r}", "country_unit": f"C{c}", "decade": d,
                             "log_income": level + x, "growth": shock + 0.5 * level + beta_for(d) * x + rng.normal(0, noise),
                             "income_source": "s", "peer_group": 1})
    return pd.DataFrame(rows)


def explicit_chow(dp, T):
    d = dp.groupby(["country_unit", "decade"]).filter(lambda g: len(g) >= 2)
    fe = pd.get_dummies(d.country_unit + "_" + d.decade.astype(str), dtype=float)
    post = (d.decade >= T).to_numpy()
    X = fe.assign(s0=d.log_income.to_numpy() * ~post, s1=d.log_income.to_numpy() * post)
    fit = sm.OLS(d.growth, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.geo_id)[0]})
    return float(fit.wald_test("s0 = s1", scalar=True).statistic)


def test_planted_1980_drop_is_found_and_country_shocks_do_not_leak():
    dp = simulate(lambda d: 0.3 if d < 1980 else 0.05)
    b = gt.decade_betas_within(dp).set_index("decade").beta
    assert np.allclose(b[b.index < 1980], 0.3, atol=0.03) and np.allclose(b[b.index >= 1980], 0.05, atol=0.03)
    assert gt.chow_within(dp, 1980).p_value < 0.001
    assert gt.break_search_within(dp).breaks == (1980,)


@pytest.mark.parametrize("T", [1970, 1980, 1990])
def test_demeaned_chow_equals_explicit_dummies(T):
    dp = simulate(lambda d: 0.3 if d < 1980 else 0.1, n_countries=4, n_regions=8, seed=3)
    assert gt.chow_within(dp, T).statistic == pytest.approx(explicit_chow(dp, T), rel=1e-8)


def test_bic_differences_equal_explicit_dummies():
    dp = simulate(lambda d: 0.3 if d < 1980 else 0.1, n_countries=3, n_regions=6, seed=4)
    ours = gt.break_search_within(dp, max_breaks=1).bic
    d = dp.copy()
    fe = pd.get_dummies(d.country_unit + "_" + d.decade.astype(str), dtype=float)
    n = len(d)
    theirs = {}
    for combo in ours:
        seg = np.searchsorted(sorted(combo), d.decade.to_numpy(), side="right")
        X = fe.assign(**{f"s{k}": d.log_income.to_numpy() * (seg == k) for k in range(len(combo) + 1)})
        ssr = sm.OLS(d.growth, X).fit().ssr
        theirs[combo] = n * np.log(ssr / n) + (X.shape[1] + len(combo)) * np.log(n)
    base = ()
    for combo in ours:
        assert ours[combo] - ours[base] == pytest.approx(theirs[combo] - theirs[base], abs=1e-8)


@pytest.mark.slow
def test_no_planted_drop_rejects_about_5_percent():
    rejections = sum(gt.chow_within(simulate(lambda d: 0.2, seed=s), 1980).p_value < 0.05 for s in range(200))
    assert rejections <= 20  # about 5% of 200, with room for simulation noise


def test_single_region_cells_are_dropped_not_zeroed():
    dp = simulate(lambda d: 0.2, n_countries=2, n_regions=5)
    lone = dp.iloc[[0]].assign(geo_id="lone", country_unit="IRL")
    dm = gt.demean_within(pd.concat([dp, lone], ignore_index=True))
    assert "lone" not in set(dm.geo_id) and len(dm) == len(dp)
    assert gt.decade_betas_within(pd.concat([dp, lone])).n.sum() == len(dp)


def test_region_decades_keep_country_unit_of_the_start_year_and_skip_gaps():
    panel = pd.DataFrame({
        "geo_id": ["a"] * 4 + ["b"] * 4, "year": [1980, 1990, 2000, 2010] * 2,
        "population": [100.0, 110.0, 121.0, 133.0, 50.0, 55.0, np.nan, 60.0],
        "income_pc": [10.0, 11.0, np.nan, 12.0, 5.0, 6.0, 7.0, 8.0], "income_source": "s",
        "country_unit": ["DEU_EAST", "DEU", "DEU", "DEU", "DEU", "DEU", "DEU", "DEU"], "peer_group": 1})
    dp = gt.region_decades(panel, start=1980, end=2010).set_index(["geo_id", "decade"])
    assert dp.loc[("a", 1980), "country_unit"] == "DEU_EAST"
    assert ("a", 2000) not in dp.index  # no income at the start: dropped, not filled
    assert ("b", 1990) not in dp.index and ("b", 2000) not in dp.index  # population gap
    assert dp.loc[("a", 1980), "growth"] == pytest.approx(np.log(1.1))


def test_decade_betas_match_explicit_dummies():
    dp = simulate(lambda d: 0.2, n_countries=3, n_regions=6, seed=5)
    ours = gt.decade_betas_within(dp).set_index("decade")
    for d, g in dp.groupby("decade"):
        X = pd.get_dummies(g.country_unit, dtype=float).assign(x=g.log_income.to_numpy())
        fit = sm.OLS(g.growth.to_numpy(), X.to_numpy()).fit(cov_type="HC1")
        assert ours.at[d, "beta"] == pytest.approx(fit.params[-1], rel=1e-8)
        assert ours.at[d, "se"] == pytest.approx(fit.bse[-1], rel=1e-8)


def test_country_clustering_changes_the_test():
    dp = simulate(lambda d: 0.3 if d < 1980 else 0.1, seed=6)
    by_region, by_country = gt.chow_within(dp, 1980), gt.chow_within(dp, 1980, cluster="country_unit")
    assert np.isfinite(by_country.statistic) and by_country.statistic != pytest.approx(by_region.statistic)


def test_group_break_tests_row():
    row = gt.group_break_tests(simulate(lambda d: 0.3 if d < 1980 else 0.05))
    assert row["chow_1980_p"] < 0.001 and row["bic_breaks"] == "1980"
    assert row["n_countries"] == 5 and row["n_units"] == 60 and row["decades"] == "1950-2010"
```

- [ ] **Step 2: Run the tests and see them fail.**

Run: `"$PY" -m pytest tests/test_global_timing.py -q -m "not slow"`
Expected: FAIL with ImportError.

- [ ] **Step 3: Implement.** Create `us_housing_crisis_analysis/modeling/global_timing.py`:

```python
"""RQ0c: RQ0b's test inside other countries (spec §4.1-4.5).

For region r in country c and decade d:
    growth(r,d) = alpha(c,d) + beta_g(d) * ln income(r,d) + e(r,d)
alpha(c,d) is removed by demeaning growth and log income within country x decade, then breaks.py
runs unchanged (as Plan 1b removes year effects). Demeaning is exact for the slopes
(Frisch-Waugh-Lovell); the cluster-robust variance is rescaled so its small-sample factor counts
the absorbed constants, which reproduces the explicit-dummy regression (tests/test_global_timing)."""

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

from us_housing_crisis_analysis.config import RQ0C_COMPARE_YEARS, RQ0C_END, RQ0C_START
from us_housing_crisis_analysis.modeling import breaks

GROUP = ("country_unit", "decade")


def region_decades(panel: pd.DataFrame, start: int = RQ0C_START, end: int = RQ0C_END) -> pd.DataFrame:
    """breaks.prepare_decade_panel, plus each unit's country unit and peer group at the decade start."""
    dp = breaks.prepare_decade_panel(panel, start=start, end=end)
    keys = panel[["geo_id", "year", "country_unit", "peer_group"]].rename(columns={"year": "decade"})
    return dp.merge(keys, on=["geo_id", "decade"], how="left")


def demean_within(dp: pd.DataFrame, by=GROUP) -> pd.DataFrame:
    """Subtract country x decade means of growth and log income. Cells with one unit carry no
    within-country information and are dropped (they would demean to zero but still count in N)."""
    by = list(by)
    d = dp[dp.groupby(by).growth.transform("size") >= 2]
    g = d.groupby(by)
    return d.assign(growth=d.growth - g.growth.transform("mean"),
                    log_income=d.log_income - g.log_income.transform("mean"))


def _dof_scale(dm: pd.DataFrame, k_fitted: int, n_slopes: int, by=GROUP) -> float:
    """(N - K_true) / (N - K_fitted): statsmodels' cluster factor saw K_fitted regressors, the model
    has one constant per country x decade cell plus the slopes."""
    n, k_true = len(dm), dm.groupby(list(by)).ngroups + n_slopes
    return (n - k_true) / (n - k_fitted)


def chow_within(dp: pd.DataFrame, break_decade: int, by=GROUP, cluster: str = "geo_id") -> breaks.TestResult:
    """Chow test at break_decade with country x decade constants. cluster="country_unit" clusters
    by country instead of region (regions in one country share shocks; spec §4.6)."""
    dm = demean_within(dp, by)
    r = breaks.chow_test(dm.assign(geo_id=dm[cluster]), break_decade)  # chow_test clusters on geo_id
    stat = r.statistic * _dof_scale(dm, dm.decade.nunique() + 2, 2, by)
    return breaks.TestResult(float(stat), float(stats.chi2.sf(stat, 1)))


def break_search_within(dp: pd.DataFrame, max_breaks: int = 3, min_segment: int = 2, by=GROUP) -> breaks.BreakSearch:
    """breaks.break_search on demeaned data. The absorbed constants add the same penalty to every
    candidate set, so the chosen breaks and BIC differences equal the explicit-dummy search."""
    return breaks.break_search(demean_within(dp, by), max_breaks=max_breaks, min_segment=min_segment)


def decade_betas_within(dp: pd.DataFrame) -> pd.DataFrame:
    """beta per decade with country constants, standard errors clustered by region (HC1 within a
    decade, since each region appears once), corrected for the absorbed constants."""
    rows = []
    dm = demean_within(dp)
    for d, g in dm.groupby("decade"):
        fit = sm.OLS(g.growth, g[["log_income"]]).fit(cov_type="HC1")
        scale = _dof_scale(g, 1, 1, by=("country_unit",))
        rows.append({"decade": int(d), "beta": float(fit.params.iloc[0]),
                     "se": float(fit.bse.iloc[0] / np.sqrt(scale)), "n": len(g),
                     "n_countries": g.country_unit.nunique()})
    return pd.DataFrame(rows)


def group_break_tests(dp: pd.DataFrame, years=RQ0C_COMPARE_YEARS, cluster: str = "geo_id") -> dict:
    dm = demean_within(dp)
    row = {}
    for y in years:
        r = chow_within(dp, y, cluster=cluster)
        row[f"chow_{y}_stat"], row[f"chow_{y}_p"] = r.statistic, r.p_value
    found = break_search_within(dp).breaks
    row.update({"bic_breaks": " ".join(map(str, found)) or "none", "n_units": dm.geo_id.nunique(),
                "n_countries": dm.country_unit.nunique(),
                "decades": f"{dm.decade.min()}-{dm.decade.max()}"})
    return row
```

- [ ] **Step 4: Run the tests and see them pass.**

Run: `"$PY" -m pytest tests/test_global_timing.py -q`
Expected: all pass, including the slow test (about 30 s). `test_decade_betas_match_explicit_dummies` pins the HC1 rescale to the explicit-dummy fit (checked to 1e-15 in the prototype).

- [ ] **Step 5: Commit.**

```bash
git add us_housing_crisis_analysis/modeling/global_timing.py tests/test_global_timing.py
git commit -m "Within-country decade betas, Chow and BIC break search for peer regions (Plan 3)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: US vs peers, and the city panel

**Files:**
- Modify: `us_housing_crisis_analysis/modeling/global_timing.py`, `tests/test_global_timing.py`

**Interfaces:**
- Consumes: Task 9 functions; `breaks.prepare_decade_panel`.
- Produces:
  - `us_decades(us_state_longrun, start=1950, end=2020) -> DataFrame` in the `region_decades` format, with `country_unit == "USA"` and `peer_group == 1`;
  - `us_vs_peers(us: DataFrame, peers: DataFrame, T: int) -> dict` with keys `delta, delta_se, delta_p, delta_us, delta_us_se, delta_us_p, beta, beta_us, n_us, n_peer`;
  - `city_decades(aggl: DataFrame, start=1950, end=2015) -> DataFrame`, the `region_decades` format plus `half_decade: bool`, using `region_income_pc` as income.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_global_timing.py`:

```python
def us_and_peers(us_beta_for, peer_beta_for, seed=0):
    peers = simulate(peer_beta_for, seed=seed)
    us = simulate(us_beta_for, n_countries=1, n_regions=50, seed=seed + 100).assign(country_unit="USA")
    us["geo_id"] = "us_" + us.geo_id
    return us, peers


def test_us_only_drop_shows_in_delta_us():
    us, peers = us_and_peers(lambda d: 0.3 if d < 1980 else 0.0, lambda d: 0.3)
    r = gt.us_vs_peers(us, peers, 1980)
    assert r["delta_us"] == pytest.approx(-0.3, abs=0.05) and r["delta_us_p"] < 0.001
    assert abs(r["delta"]) < 0.05 and r["delta_p"] > 0.01


def test_shared_drop_shows_in_delta():
    us, peers = us_and_peers(lambda d: 0.3 if d < 1980 else 0.0, lambda d: 0.3 if d < 1980 else 0.0)
    r = gt.us_vs_peers(us, peers, 1980)
    assert r["delta"] == pytest.approx(-0.3, abs=0.05) and r["delta_p"] < 0.001
    assert abs(r["delta_us"]) < 0.05 and r["n_us"] == 50 * len(DECADES)


def test_us_decades_from_state_panel():
    panel = pd.DataFrame({"geo_id": ["state:24"] * 3, "geo_name": "Maryland", "year": [1950, 1960, 1970],
                          "population": [2.3e6, 3.1e6, 3.9e6], "income_pc": [1600.0, 2300.0, 4300.0],
                          "income_source": "bea"})
    dp = gt.us_decades(panel, start=1950, end=1970)
    assert list(dp.decade) == [1950, 1960] and set(dp.country_unit) == {"USA"}


def test_city_decades_use_region_income_and_flag_the_half_decade():
    rows = []
    for y, pop in zip(range(1950, 2016, 5), np.linspace(1e6, 3e6, 14)):
        rows.append({"geo_id": "wup:1", "year": y, "population": pop, "region_income_pc": 1000.0 if y % 10 == 0 else np.nan,
                     "country_unit": "MEX", "peer_group": 5})
    dp = gt.city_decades(pd.DataFrame(rows), start=1950, end=2015).set_index("decade")
    assert list(dp.index) == [1950, 1960, 1970, 1980, 1990, 2000, 2010]
    assert dp.at[2010, "half_decade"] and not dp.at[2000, "half_decade"]
    pop = dict(zip(range(1950, 2016, 5), np.linspace(1e6, 3e6, 14)))
    assert dp.at[2010, "growth"] == pytest.approx(2 * np.log(pop[2015] / pop[2010]))
    assert dp.at[1950, "growth"] == pytest.approx(np.log(pop[1960] / pop[1950]))
```

- [ ] **Step 2: Run the tests and see them fail.**

Run: `"$PY" -m pytest tests/test_global_timing.py -q -m "not slow"`
Expected: FAIL with AttributeError.

- [ ] **Step 3: Implement.** Append to `global_timing.py`:

```python
def us_decades(us_state_longrun: pd.DataFrame, start: int = RQ0C_START, end: int = RQ0C_END) -> pd.DataFrame:
    """US states in the region_decades format (one country unit, peer group 1)."""
    dp = breaks.prepare_decade_panel(us_state_longrun, start=start, end=end)
    return dp.assign(country_unit="USA", peer_group=1)


def us_vs_peers(us: pd.DataFrame, peers: pd.DataFrame, T: int) -> dict:
    """Spec §4.2: growth = alpha(c,d) + beta*y + delta*y*post + beta_US*y*US + delta_US*y*post*US.
    delta = the peers' change at T; delta_US = how much more the US changed. Clustered by unit."""
    dm = demean_within(pd.concat([us, peers], ignore_index=True))
    y = dm.log_income.to_numpy()
    post = (dm.decade >= T).to_numpy(float)
    is_us = (dm.country_unit == "USA").to_numpy(float)
    X = pd.DataFrame({"beta": y, "delta": y * post, "beta_us": y * is_us, "delta_us": y * post * is_us}, index=dm.index)
    fit = sm.OLS(dm.growth, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(dm.geo_id)[0]})
    se = fit.bse / np.sqrt(_dof_scale(dm, X.shape[1], X.shape[1]))
    p = 2 * stats.norm.sf(np.abs(fit.params / se))
    return {"beta": fit.params["beta"], "delta": fit.params["delta"], "delta_se": se["delta"], "delta_p": p[1],
            "beta_us": fit.params["beta_us"], "delta_us": fit.params["delta_us"], "delta_us_se": se["delta_us"],
            "delta_us_p": p[3], "n_us": int(is_us.sum()), "n_peer": int(len(dm) - is_us.sum())}


def city_decades(aggl: pd.DataFrame, start: int = RQ0C_START, end: int = 2015) -> pd.DataFrame:
    """Spec §4.3: city growth over ten years from each decade start, with the city's region income at
    the start. The last step (2010-2015) is five years, doubled and flagged half_decade."""
    p = aggl[["geo_id", "year", "population", "region_income_pc", "country_unit", "peer_group"]]
    frames = []
    for d in range(start, end, 10):
        horizon = min(10, end - d)
        a = p[p.year == d].merge(p[p.year == d + horizon][["geo_id", "population"]], on="geo_id", suffixes=("", "_end"))
        a = a[(a.population > 0) & (a.population_end > 0) & (a.region_income_pc > 0)]
        frames.append(pd.DataFrame({
            "geo_id": a.geo_id, "decade": d, "growth": np.log(a.population_end / a.population) * 10 / horizon,
            "log_income": np.log(a.region_income_pc), "income_source": "region", "country_unit": a.country_unit,
            "peer_group": a.peer_group, "half_decade": horizon < 10}))
    return pd.concat(frames, ignore_index=True).sort_values(["decade", "geo_id"]).reset_index(drop=True)
```

- [ ] **Step 4: Run the tests and see them pass.**

Run: `"$PY" -m pytest tests/test_global_timing.py -q -m "not slow"`
Expected: all pass.

- [ ] **Step 5: Commit.**

```bash
git add us_housing_crisis_analysis/modeling/global_timing.py tests/test_global_timing.py
git commit -m "US-vs-peers comparison at a decade boundary; city decade panel (Plan 3)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Context model, city growth and national GDP growth

**Files:**
- Modify: `us_housing_crisis_analysis/modeling/global_timing.py`, `tests/test_global_timing.py`

**Interfaces:**
- Produces:
  - `five_year_panel(aggl, end=2015) -> DataFrame[geo_id, country_iso3, peer_group, period, decade, growth5, gdp_growth5, urban_share]`. Rows lacking national GDP at either end are dropped.
  - `national_link(fp) -> DataFrame[peer_group, decade, beta, se, gamma, gamma_se, n, n_countries]`.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_global_timing.py`:

```python
def five_year_sim(beta=0.5, gamma=0.02, seed=0, n_countries=30, n_cities=8):
    rng = np.random.default_rng(seed)
    rows = []
    for c in range(n_countries):
        gdp = np.cumsum(rng.normal(0.1, 0.05, 14)) + 8
        urban = rng.uniform(20, 80)
        for k in range(n_cities):
            pop = 13.0
            for t, year in enumerate(range(1950, 2016, 5)):
                rows.append({"geo_id": f"c{c}k{k}", "country_iso3": f"C{c:02d}", "peer_group": 1 + c % 2,
                             "year": year, "population": np.exp(pop), "gdppc": np.exp(gdp[t]), "urban_share": urban})
                if t < 13:
                    pop += 0.05 + beta * (gdp[t + 1] - gdp[t]) + gamma * urban + rng.normal(0, 0.02)
    return pd.DataFrame(rows)


def test_national_link_recovers_planted_slopes():
    out = gt.national_link(gt.five_year_panel(five_year_sim()))
    assert set(out.peer_group) == {1, 2}
    assert np.allclose(out.beta, 0.5, atol=0.1)
    assert np.allclose(out.gamma.unique(), 0.02, atol=0.005)
    assert np.isfinite(out.se).all() and (out.se > 0).all()


def test_five_year_panel_drops_missing_national_gdp_without_filling():
    a = five_year_sim(n_countries=2, n_cities=1)
    a.loc[(a.country_iso3 == "C00") & (a.year < 1975), "gdppc"] = np.nan  # e.g. a former Soviet republic
    fp = gt.five_year_panel(a)
    c0 = fp[fp.country_iso3 == "C00"]
    assert c0.period.min() == 1975 and fp[fp.country_iso3 == "C01"].period.min() == 1950
    assert fp.gdp_growth5.notna().all() and fp.period.max() == 2010
```

- [ ] **Step 2: Run the tests and see them fail.**

Run: `"$PY" -m pytest tests/test_global_timing.py -q -m "not slow" -k "national or five_year"`
Expected: FAIL with AttributeError.

- [ ] **Step 3: Implement.** Append to `global_timing.py`:

```python
def five_year_panel(aggl: pd.DataFrame, end: int = 2015) -> pd.DataFrame:
    """Spec §4.5: 5-year city growth and national GDP growth from period t to t+5, % urban at t.
    A period without national GDP at either end is dropped (D-27: never filled from elsewhere)."""
    p = aggl[["geo_id", "country_iso3", "peer_group", "year", "population", "gdppc", "urban_share"]]
    nxt = p[["geo_id", "year", "population", "gdppc"]].assign(year=lambda d: d.year - 5)
    m = p.merge(nxt, on=["geo_id", "year"], suffixes=("", "_next"))
    m = m[(m.year + 5 <= end) & (m.population > 0) & (m.population_next > 0) & (m.gdppc > 0) & (m.gdppc_next > 0)]
    m = m.dropna(subset=["urban_share"])
    return pd.DataFrame({
        "geo_id": m.geo_id, "country_iso3": m.country_iso3, "peer_group": m.peer_group, "period": m.year,
        "decade": m.year // 10 * 10, "growth5": np.log(m.population_next / m.population),
        "gdp_growth5": np.log(m.gdppc_next / m.gdppc), "urban_share": m.urban_share,
    }).reset_index(drop=True)


def national_link(fp: pd.DataFrame) -> pd.DataFrame:
    """By peer group: growth5 = alpha(t) + beta(d) * gdp_growth5 + gamma * urban_share, clustered by
    country. Context only: it asks whether city growth follows *national* growth (spec §4.5)."""
    rows = []
    for g, d in fp.groupby("peer_group"):
        X = pd.get_dummies(d.period, prefix="t", dtype=float)
        for dec in sorted(d.decade.unique()):
            X[f"b_{dec}"] = d.gdp_growth5.to_numpy() * (d.decade == dec).to_numpy()
        X["gamma"] = d.urban_share.to_numpy()
        fit = sm.OLS(d.growth5, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.country_iso3)[0]})
        for dec in sorted(d.decade.unique()):
            sub = d[d.decade == dec]
            rows.append({"peer_group": int(g), "decade": int(dec), "beta": fit.params[f"b_{dec}"],
                         "se": fit.bse[f"b_{dec}"], "gamma": fit.params["gamma"], "gamma_se": fit.bse["gamma"],
                         "n": len(sub), "n_countries": sub.country_iso3.nunique()})
    return pd.DataFrame(rows)
```

In the simulation, `urban` is constant per country on the 20–80 scale, so γ is identified from cross-country differences in `urban_share`, with period effects absorbing the constant.

- [ ] **Step 4: Run the tests and see them pass.**

Run: `"$PY" -m pytest tests/test_global_timing.py -q -m "not slow"`
Expected: all pass.

- [ ] **Step 5: Commit.**

```bash
git add us_housing_crisis_analysis/modeling/global_timing.py tests/test_global_timing.py
git commit -m "Context model: city growth on national GDP growth by peer group (Plan 3)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: Notebook, outputs, finding and docs

**Files:**
- Create: `notebooks/1.2-lr-global-timing.ipynb` (written as a percent script, converted, then the script removed), `reports/figures/rq0c_regional_betas.png`, `reports/figures/rq0c_country_betas.png`, `reports/figures/rq0c_national_link.png`, `reports/tables/rq0c_tests.csv`, `reports/tables/rq0c_us_comparison.csv`
- Modify: `Claude/methods/analysis-methods.md` (RQ0c section and results log), `Claude/methods/decisions.md` (D-29), master spec (per RQ0c spec §10), `Claude/methods/geography.md`

**Interfaces:**
- Consumes: everything above; `plots.apply_style`, `plots.save_figure`, `plots.SERIES_COLORS`, `plots.SERIES_MARKERS`; `config.TABLES_DIR`, `US_BREAK_DECADES`, `RQ0C_COMPARE_YEARS`.

- [ ] **Step 1: Write the notebook as a percent script** at `notebooks/1.2-lr-global-timing.py`:

```python
# %% [markdown]
# # RQ0c: did other countries see the same change at the same time?
#
# RQ0b found that Americans used to move toward the richer parts of the country and largely
# stopped. Here the same test runs inside other countries: within each country and decade, did
# richer regions grow faster? Spec: `docs/superpowers/specs/2026-10-14-rq0c-global-timing-design.md`.

# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from us_housing_crisis_analysis.config import (
    INTERIM_DATA_DIR, PROCESSED_DATA_DIR, RQ0C_COMPARE_YEARS, TABLES_DIR, US_BREAK_DECADES,
)
from us_housing_crisis_analysis.global_geography import PEER_GROUP_NAMES, load_peer_groups
from us_housing_crisis_analysis.modeling import breaks, global_timing as gt
from us_housing_crisis_analysis.plots import MUTED, SERIES_COLORS, SERIES_MARKERS, apply_style, save_figure

apply_style()
TABLES_DIR.mkdir(parents=True, exist_ok=True)
read = lambda name: pd.read_parquet(PROCESSED_DATA_DIR / f"{name}.parquet")  # noqa: E731
interim = lambda name: pd.read_parquet(INTERIM_DATA_DIR / f"{name}.parquet")  # noqa: E731
regions, aggl, us_states = read("global_regions"), read("global_agglomerations"), read("us_state_longrun")

# %% [markdown]
# ## Coverage
# Regions per peer group and decade with income at the start (rows used in the main test).
# Peers outside the US only: the US enters through BEA state data, as in RQ0b.

# %%
dp_all = gt.region_decades(regions)
peers = dp_all[dp_all.country_unit != "USA"]
us = gt.us_decades(us_states)
coverage = gt.demean_within(peers).groupby(["peer_group", "decade"]).agg(
    regions=("geo_id", "nunique"), countries=("country_unit", "nunique")).unstack("decade")
coverage

# %% [markdown]
# ## Main test: β by decade, peers and the US on one scale

# %%
def comparable(dp):
    """Peer groups with at least two country units holding 2+ regions (else nothing within-country)."""
    return {g: d for g, d in dp.groupby("peer_group") if gt.demean_within(d).country_unit.nunique() >= 2}

group_betas = pd.concat([gt.decade_betas_within(d).assign(peer_group=g) for g, d in comparable(peers).items()],
                        ignore_index=True)
us_betas = breaks.decade_betas(us)
fig, ax = plt.subplots()
for i, (g, b) in enumerate(group_betas.groupby("peer_group")):
    ax.errorbar(b.decade + 1.5 * i - 3, b.beta, yerr=1.96 * b.se, label=PEER_GROUP_NAMES[g],
                color=SERIES_COLORS[i + 1], marker=SERIES_MARKERS[i + 1], capsize=2)
ax.errorbar(us_betas.decade, us_betas.beta, yerr=1.96 * us_betas.se, label="United States (states, BEA)",
            color=SERIES_COLORS[0], marker=SERIES_MARKERS[0], capsize=2)
for y in RQ0C_COMPARE_YEARS:
    ax.axvline(y, color=MUTED, lw=0.8, ls="--")
ax.axhline(0, color=MUTED, lw=0.8)
ax.set(xlabel="Decade start", ylabel="β: extra 10-year growth per log point of income",
       title="Did richer regions grow faster? Within-country β by decade")
ax.legend(fontsize=8)
save_figure(fig, "rq0c_regional_betas")

# %% [markdown]
# ## Break tests by peer group (regions and cities) and checks

# %%
def tests_row(dp, group, version, spec):
    return {"group": group, "version": version, "spec": spec, **gt.group_break_tests(dp)}

rows = []
for g, d in comparable(peers).items():
    rows.append(tests_row(d, g, "regions", "main"))
    std = d.assign(log_income=d.groupby(["country_unit", "decade"]).log_income.transform(lambda s: (s - s.mean()) / s.std()))
    rows.append(tests_row(std.dropna(subset=["log_income"]), g, "regions", "income standardized within country x decade"))
g1 = peers[peers.peer_group == 1]
rows.append(tests_row(g1[~g1.country_unit.eq("GBR")], 1, "regions", "without the UK"))
rows.append(tests_row(g1[~g1.country_unit.eq("JPN")], 1, "regions", "without Japan"))
rows.append({"group": 1, "version": "regions", "spec": "clustered by country",
             **gt.group_break_tests(g1, cluster="country_unit")})
# 1990-PPP income exists for Rosés-Wolf only, to 2015: DOSE regions and the 2010 decade drop out
rw90 = regions.assign(income_pc=regions.income_pc_1990ppp)
rows.append(tests_row(gt.region_decades(rw90).query("peer_group == 1"), 1, "regions", "Rosés-Wolf 1990 PPP"))
rows.append(tests_row(us, "US", "states", "BEA (RQ0b, for reference)"))

cities = gt.city_decades(aggl[aggl.country_iso3 != "USA"])
for g, d in comparable(cities).items():
    rows.append(tests_row(d, g, "cities", "main"))
# city-proper countries: most of the country's WUP agglomerations are city proper (Germany, Spain, ...)
concept = aggl.drop_duplicates("geo_id").groupby("country_iso3").concept
proper = set(concept.agg(lambda s: (s == "City Proper").mean() > 0.5).loc[lambda s: s].index)
c1 = cities[cities.peer_group == 1]
rows.append(tests_row(c1[~c1.country_unit.isin(proper)], 1, "cities", "without city-proper countries"))
big1950 = set(aggl.loc[(aggl.year == 1950) & (aggl.population >= 300_000), "geo_id"])
rows.append(tests_row(c1[c1.geo_id.isin(big1950)], 1, "cities", "300k+ in 1950 only"))
rows.append(tests_row(c1[~c1.half_decade], 1, "cities", "without the 2010-2015 x2 step"))
tests = pd.DataFrame(rows)
tests.to_csv(TABLES_DIR / "rq0c_tests.csv", index=False)
tests

# %% [markdown]
# ## Same timing as the US? (δ = peers' change at T, δ_US = how much more the US changed)
# Plan 1b dates the US break at about 1970 or about 1990 (D-28), so both rows are headlined;
# 1980 is shown for completeness.

# %%
comp = []
for g, d in comparable(peers).items():
    for T in RQ0C_COMPARE_YEARS:
        comp.append({"group": g, "version": "regions", "T": T, "headline": T in US_BREAK_DECADES,
                     **gt.us_vs_peers(us, d, T)})
us_comparison = pd.DataFrame(comp)
us_comparison.to_csv(TABLES_DIR / "rq0c_us_comparison.csv", index=False)
us_comparison[["group", "T", "headline", "delta", "delta_se", "delta_us", "delta_us_se", "delta_us_p", "n_us", "n_peer"]]

# %% [markdown]
# ## Group 2 with time-varying World Bank groups (spec §3.5 check)
# World Bank groups start with 1987 data, so this covers the decades from 1990: a country counts as
# group 2 in a decade if the World Bank classed it high income in the decade's start year (data
# years 1990, 2000, 2010) and it is not in group 1 or 3.

# %%
wb = interim("worldbank").query("variable == 'wb_income_group'")
high = set(zip(wb.loc[wb.value == 4, "country_iso3"], wb.loc[wb.value == 4, "year"]))
p = peers[(peers.decade >= 1990) & ~peers.peer_group.isin([1, 3])]
iso = p.country_unit.str[:3]
tv = p[[(c, d) in high for c, d in zip(iso, p.decade)]]
fixed = peers[(peers.peer_group == 2) & (peers.decade >= 1990)]
display(gt.decade_betas_within(tv).merge(gt.decade_betas_within(fixed), on="decade", suffixes=("_time_varying", "_fixed")))

# %% [markdown]
# ## Per-country lines (larger countries)

# %%
big = ["FRA", "DEU", "ITA", "ESP", "GBR", "JPN"]
fig, axes = plt.subplots(2, 3, figsize=(10, 5.5), sharey=True)
for ax, c in zip(axes.flat, big):
    b = gt.decade_betas_within(peers[peers.country_unit == c])
    ax.fill_between(b.decade, b.beta - 1.96 * b.se, b.beta + 1.96 * b.se, color=SERIES_COLORS[1], alpha=0.2)
    ax.plot(b.decade, b.beta, color=SERIES_COLORS[1], marker="o")
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_title(f"{c} ({b.n.max()} regions)", fontsize=10)
fig.suptitle("β by decade within each large peer country (95% bands)")
save_figure(fig, "rq0c_country_betas")

# %% [markdown]
# ## Calibration: the US through the global lens (spec §4.4)
# 1. DOSE US states (regional GDP per head) vs the RQ0b state β (BEA personal income).
# 2. WUP US agglomerations with their state's BEA income vs the RQ0b metro β.

# %%
dose_us = dp_all[dp_all.country_unit == "USA"]
cal = gt.decade_betas_within(dose_us).merge(us_betas, on="decade", suffixes=("_dose", "_bea"))
cal["inside_bea_95"] = (cal.beta_dose - cal.beta_bea).abs() <= 1.96 * cal.se_bea
us_cities = gt.city_decades(aggl[aggl.country_iso3 == "USA"])
metro_betas = breaks.decade_betas(breaks.prepare_decade_panel(read("us_metro_longrun"), start=1950))
cal_cities = gt.decade_betas_within(us_cities).merge(metro_betas, on="decade", suffixes=("_wup", "_rq0b_metro"))
display(cal)
cal_cities

# %% [markdown]
# ## WUP 2025 check (one city definition everywhere, 1975-2015)
# The Degree-of-Urbanisation cities are not matched to regions in this plan, so the check runs the
# context model (§4.5), which needs only national values: same model and peer groups as below.

# %%
w, mad = interim("un_wup"), interim("maddison")
dou = w[w.variable == "population_degurba"][["geo_id", "country_iso3", "year", "value"]].rename(columns={"value": "population"})
gdp = mad[mad.variable == "gdppc"][["country_iso3", "year", "value"]].rename(columns={"value": "gdppc"})
urb = w[w.variable == "urban_share"][["country_iso3", "year", "value"]].rename(columns={"value": "urban_share"})
dou = dou.merge(gdp, on=["country_iso3", "year"], how="left").merge(urb, on=["country_iso3", "year"], how="left")
dou["peer_group"] = dou.country_iso3.map(load_peer_groups().set_index("iso3").peer_group)
link_2025 = gt.national_link(gt.five_year_panel(dou.dropna(subset=["peer_group"])))
link_2025

# %% [markdown]
# ## Context: city growth and national GDP growth (spec §4.5; not compared with the US break)

# %%
fp = gt.five_year_panel(aggl)
dropped = aggl[aggl.gdppc.isna()].groupby("country_iso3").year.agg(["min", "max", "count"])
print("Agglomeration-periods without national GDP (dropped):")
display(dropped)
link = gt.national_link(fp)
fig, ax = plt.subplots()
for i, (g, b) in enumerate(link.groupby("peer_group")):
    ax.errorbar(b.decade + i - 2, b.beta, yerr=1.96 * b.se, label=PEER_GROUP_NAMES[g],
                color=SERIES_COLORS[i + 1], marker=SERIES_MARKERS[i + 1], capsize=2)
ax.axhline(0, color=MUTED, lw=0.8)
ax.set(xlabel="Decade", ylabel="β: city growth per unit of national GDP growth (5 years)",
       title="Context: did city growth follow national growth?")
ax.legend(fontsize=8)
save_figure(fig, "rq0c_national_link")
link

# %% [markdown]
# ## Finding
# (fill in after running)
#
# Write it in plain language, in the form of spec §1: "In Western Europe and Japan, the pull of
# richer regions also weakened, but around 19XX (or: did not weaken); the US drop after 19XX was
# larger by Z (p = …)". Use the headline rows T = 1970 and T = 1990. Say what the calibration
# shows (regional GDP vs personal income) and name it as a limitation if the DOSE US β falls
# outside the RQ0b intervals. Keep it descriptive (no causal claims).
```

`display` is Jupyter's built-in; the notebook only runs under nbconvert or Jupyter.

- [ ] **Step 2: Convert, run and look.**

```bash
"$PY" -m jupytext --to notebook notebooks/1.2-lr-global-timing.py -o notebooks/1.2-lr-global-timing.ipynb
rm notebooks/1.2-lr-global-timing.py
make notebooks PYTHON_INTERPRETER="$PY"
```

Expected: both notebooks run without errors, and all five output files exist. Open the three figures and both tables. Check the following, and report anything odd instead of adjusting it:
- every peer-group line has a point for each decade where the coverage table shows at least 2 countries;
- `rq0c_us_comparison.csv` has rows for T = 1970, 1980 and 1990, with `headline` true for 1970 and 1990;
- the calibration table says whether DOSE US β is inside the BEA intervals;
- the dropped-GDP table lists the former Soviet republics before 1973, CZE before 1970, SVK before 1985, and ERI/MAC/PNG/SOM/SSD.

- [ ] **Step 3: Write the finding.** Replace "(fill in after running)" with the actual finding, following the cell's own instructions, and re-run with `make notebooks`. A notebook that still contains "(fill in after running)" isn't finished.

- [ ] **Step 4: Docs.**
- **`analysis-methods.md`:** add an "RQ0c — global timing" section covering:
  - the model;
  - demeaning with the degrees-of-freedom correction;
  - the data per country (Rosés-Wolf, DOSE, Japan census);
  - GDR handling;
  - US break decades 1970 and 1990;
  - the city panel's half-decade step;
  - calibration;
  - the context model and its caveat.

  Add a dated entry to the results log with the headline numbers from the tables.
- **`decisions.md`:** add **D-29 · RQ0c design and build choices**, covering:
  - the spec's eight decisions (user, 2026-10-14);
  - Japan census population (user, 2026-10-14);
  - US break decades (1970, 1990) from D-28, per spec §5.1;
  - GDR as its own country unit before 1990, with Berlin dropped (Claude; **flag for owner review**);
  - per-country Maddison tolerances;
  - DOSE US 1.5% tolerance;
  - GISCO NUTS 2010 at 1:20M with a nearest-region fallback;
  - the 2010–2015 ×2 city step (flagged);
  - growth allowlist rows;
  - `global_geography.py` as a new module rather than an extension of `geography.py` (spec §5 said extend; geopandas stays out of the US geography module).

  Update "Open items" to say Plan 3 is done.
- **Master spec**, per RQ0c spec §10:
  - §2 RQ0c row (question and years);
  - §3 data tiers (Rosés-Wolf, DOSE, e-Stat Japan; WUP 2018 named) and peer groups (the fixed rule and five groups);
  - §4 package layout (`sources/roses_wolf.py`, `dose.py`, `estat_japan.py`, `modeling/global_timing.py`, `global_geography.py`; RQ0c removed from `elasticity.py`; `region` geo level);
  - §5 RQ0c (replace with a short summary pointing to the RQ0c spec §4);
  - §7 testing;
  - §8 risks (city concepts, income concept, decadal vs. annual timing);
  - §10 build step 3 (add Rosés-Wolf, DOSE, e-Stat).

  Set the RQ0c spec's status line to "Approved; implemented in Plan 3 (2026-MM-DD)".

- [ ] **Step 5: Final checks.**

Run: `make test PYTHON_INTERPRETER="$PY" && "$PY" -m ruff check`
Expected: everything passes, data tests included.

- [ ] **Step 6: Commit.**

```bash
git add notebooks reports/figures/rq0c_*.png reports/tables/rq0c_*.csv Claude docs/superpowers/specs
git commit -m "RQ0c notebook: within-country betas, break tests, US vs peers, finding (Plan 3)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Spec coverage

| RQ0c spec section | Where |
|---|---|
| §3.1 sources (WUP 2018/2025, Maddison, World Bank, Rosés-Wolf, DOSE) | Tasks 2–5 |
| §3.3 regional income; Japan and Australia coverage | Tasks 4, 5, Execution notes |
| §3.4 matching (ISO3, point-in-polygon, hand check, no parent fill) | Tasks 2, 7, 8, 11 |
| §3.5 peer groups, fixed, five groups; time-varying check | Task 6 (rule), Task 3 (`wb_income_group`), Task 12 (time-varying group-2 cell, decades 1990+) |
| §4.1 main test, demeaning, Chow at 1970/1980/1990, BIC, per-country lines | Tasks 9, 12 |
| §4.2 US vs peers | Tasks 10, 12 |
| §4.3 cities and three checks | Tasks 10, 12 |
| §4.4 calibration | Task 12 |
| §4.5 context model | Tasks 11, 12 |
| §4.6 robustness table | Task 9 (`cluster="country_unit"`), Task 12 (`rq0c_tests.csv` spec rows: standardized income, without UK/Japan, 1990 PPP, country clustering, city checks, without the ×2 step; time-varying group 2 cell) |
| §5 components and outputs | File structure, Task 12 |
| §5.1 comparison contract | Global Constraints (`US_BREAK_DECADES`), Task 12 |
| §6 tests | Tasks 2–11 |
| §10 spec changes on approval | Task 12 Step 4 |
