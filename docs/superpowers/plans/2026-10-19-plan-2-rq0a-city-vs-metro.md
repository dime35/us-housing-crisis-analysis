# Plan 2: RQ0a, did US cities stall, or did their metros? Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a metro × decade panel of main-city, metro and suburb population plus city land area, classify the 81 headline metros in 1950–70, 1970–90 and 1990–2020, and give the spec's three preset answers with ranges, checks and a robust/fragile verdict.

**Architecture:**
- Three new source modules feed `data/interim/`:
  - `sources/cesta.py`: city population 1790–2010, keyed by 2010 place code;
  - `sources/wp27.py`: 1950–1990 top-100 population and land area;
  - `sources/gazetteer.py`: land area of every place in 1990, 2000, 2010 and 2020.
- `sources/nhgis.py` adds table AV0 (place population 1970–2020).
- `geography.py` builds and loads committed crosswalks: the 1950 top-100 cities, each metro's main city, place-code changes and city–county consolidations.
- `features.build_us_city_metro` writes `us_city_metro.parquet`.
- `modeling/city_metro.py` holds growth, classes, annexing flags, the unit-resampling ranges and the three decision rules.
- Notebook `1.0-lr-city-vs-metro` runs everything and writes two figures and two tables.

**Tech Stack:** Python 3.12, pandas, numpy, matplotlib, ipumspy (NHGIS API), pytest, jupytext and nbconvert.

**Spec:** `docs/superpowers/specs/2026-10-18-rq0a-city-vs-metro-design.md` (approved 2026-10-19). It builds on Plan 1 (`us_metro_longrun`, `geography.py`, D-27) and on Plan 1c's conventions (periods, preset rules, unit resampling with 999 draws and seed 0).

## Global Constraints

- **Branch and folder:**
  - Work on branch `plan-2-rq0a` (already created off `plan-1-rq0b`), in the main project folder, since `data/` lives only there.
  - Never run `pip install -e .` anywhere else.
  - Run tools as `venv/bin/python -m ...`. `make test-fast` runs the tests that need no data; `make test` runs everything.
- **The decision rules are fixed (spec §4.3). Never tune them to results.** "At the bar" counts as reaching it.
  - **Keeps up** if growth ≥ bar.
    - Main bar: ½ × US growth over the same period (US = 50 states + DC).
    - Absolute check: 5% per decade, compounded.
  - **Rule 1:** S = share of plateau cities (headline cities that fell behind in 1950–70) whose metro kept up.
    - low ≥ ⅔ → "mostly suburbanization";
    - high ≤ ⅓ → "mostly metro stagnation";
    - low > ⅓ and high < ⅔ → "mixed";
    - otherwise → "can't tell".
  - **Rule 2:** among headline metros that kept up in 1950–70, D = fall-behind share of fixed-boundary cities − fall-behind share of annexing cities.
    - fewer than 15 cities in either group (actual data) → "not testable";
    - low > 0 → "plateau concentrated in fixed-boundary cities";
    - high ≤ 0 → "not a boundary effect";
    - otherwise → "can't tell".
  - **Rule 3:** F₁, F₂, F₃ = share of headline metros falling behind in each period. Differences use metros classed in both periods.
    - low(F₂ − F₁) > 0 → "later, by 1970–90";
    - else low(F₃ − F₁) > 0 → "later, only after 1990";
    - high of both ≤ 0 → "not later";
    - otherwise → "can't tell".
  - **Ranges:** 90%, from 999 draws resampling headline metros with replacement, seed 0. Draws where the statistic is undefined are skipped and counted.
  - **Fragile:** the main version sets each answer. If any check that applies to that rule gives a different answer, the answer is "fragile", with the disagreeing checks named.
- **Periods:** 1950–70, 1970–90, 1990–2020. City background 1900–1950; metro figures from 1940.
- **Annexing:** land area at the end of the period more than 20% above the start (checks at 10% and 40%), or a consolidation with the county inside the period. Area is taken never to shrink materially (bracket rule, spec §3.4).
- **Wording (D-29):** findings describe population ("the city fell behind while its metro kept up"), never moves or causes.
- **Docs:** every task that adds a source, method or decision updates `Claude/research/sources.md`, `Claude/methods/*.md` or `Claude/methods/decisions.md` in the same commit. The new decision entry takes the next free number (D-31 now).
- **Commits:** commit after every task. Messages end with:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  ```

## Execution notes (found while writing this plan, 2026-10-19)

All checks below were run on the real files in the session scratchpad.

**Sources:**
- **CESTA:**
  - The pinned file is `https://raw.githubusercontent.com/cestastanford/historical-us-city-populations/9b267baf1a7a662ca2076cc966166662346f80bc/data/1790-2010_MASTER.csv`: 8,915 rows, old-Mac CR line ends (pandas reads them).
  - `STPLFIPS_2010` read as text is a zero-padded 7-digit code; "0" or blank means no code (1,389 blank, 726 "0"). No 7-digit code appears twice.
  - Missing counts are 0 or blank.
  - The repository has no license file. The data are Census counts.
- **NHGIS AV0:** a test extract (place level) has columns `NHGISCODE, GISJOIN, YEAR, STATE, STATEFP, STATENH, PLACE, PLACEA, NAME, AV0AA, AV0AAM`.
  - `YEAR` also holds ACS ranges such as "2016-2020". Only 4-digit census years are kept.
  - The place code is `STATEFP + PLACEA`. AV0 2010 equals CESTA 2010 for 6,797 of 6,799 shared codes; the two others are Honolulu CDP and Crystal City TX.
  - **Louisville 2020 is split in two:** 2148006 "metro government (balance)" has 386,884 and 2148000 "Louisville city" (an inactive place) has 246,161. Their sum, 633,045, is the continuation of the 2010 balance (597,337), and their 2020 land areas (263.5 + 61.5 sq mi) add up to the 2010 balance's 325.2.
  - Macon's code changed in 2014 (1349000 → 1349008, Macon-Bibb County).
- **WP27 tables 18–22** parse to exactly 100 places a year once traps are handled:
  - the 1950 table prints Memphis twice;
  - tied ranks print as "97-T";
  - some rows have "*" with no leader dots;
  - one land area has a thousands comma (Anchorage 1,697.6);
  - two names have no comma before the state ("Spokane city WA", "Tacoma city WA").
  - Matched to CESTA by name (minus " city", " CDP", …) and state, every row matches except five, which are hand-coded:

    | WP27 name | Place code |
    |---|---|
    | New York city, NY | 3651000 |
    | Nashville-Davidson, TN | 4752006 |
    | Lexington-Fayette, KY | 2146027 |
    | Arlington CDP, VA | 5103000 |
    | Metairie CDP, LA | 2250115 |
- **Gazetteers:**
  - 2000 (`places2k.zip`) is fixed width. Land area in sq mi is at characters 120–131, and latitude and longitude can touch.
  - 2010 is tab-separated with CRLF line ends and padded values.
  - 2020 is tab-separated.
- **Place-to-county:** `https://www2.census.gov/geo/docs/reference/codes2020/national_place_by_county2020.txt` (pipe-separated) maps places to counties. In Connecticut it uses the old counties, so it must go through `county_to_cbsa()` (legacy counties included).

**Counts the spec predicted, now confirmed:**
- **81 headline metros**, and the 19 other 1950 top-100 cities exactly as spec §3.2 lists them.
- Hartford, New Haven and Bridgeport only resolve through the Connecticut legacy-county mapping.
- Norfolk is the one headline metro whose largest 1950 city is not first-named.
- No headline city is missing a CESTA count in 1900–2010. City ≤ metro holds in every decade 1940–2010 for every metro.

**Departures from the spec, recorded here and in D-31 (Task 7):**
1. **No schema change.** `schema.GEO_PREFIXES` already has level `"city"` with prefix `place:`. The spec's new level `"place"` would duplicate it.
2. **The 1990 Census Gazetteer is added as the 1990 land-area source.** (`https://www2.census.gov/geo/docs/maps-data/data/gazetteer/places.zip`, land area in thousands of m².) Area then comes from WP27 for 1950–1980 and from Gazetteers for 1990–2020, one source per year.
   - WP27's 1990 table becomes a check. On the 94 shared places, population is identical and area within 0.22%.
   - **Why:** without it, 7 headline cities stay "unknown" in 1970–90 and in 1990–2020, which is over the spec's limit of 5. With it, the counts at the 20% threshold are 5 (1950–70), 5 (1970–90) and 0 (1990–2020): Savannah, Peoria, South Bend, Canton and Chattanooga. So **ICPSR 7735 is not needed** (the spec's trigger is more than 5).
   - **Disclosed (spec §4.5):** writing this plan computed annexing flags for the headline cities, unconditioned. At 20% they were 39 annexing and 37 fixed in 1950–70, 20 and 56 in 1970–90, and 14 and 67 in 1990–2020. No growth class, share or rule result was computed.
3. **Place-code changes** go in a committed table (`references/crosswalks/place_code_changes.csv`) that both the 2020 population join and the Gazetteer area join use:
   - Louisville 2020 = 2148006 + 2148000;
   - Louisville 1990 and 2000 = 2148000;
   - Jacksonville 1990 = 1235160 ("remainder");
   - Indianapolis 1990 = 1836010 ("remainder");
   - Macon 2020 = 1349008.
4. **A city's 2020 count is used only if its CESTA and NHGIS 2010 counts agree within 0.5%.** This drops 2020 for Honolulu (CESTA keeps the pre-2010 CDP; NHGIS has "Urban Honolulu", 13% smaller) and Crystal City TX. Neither is a headline city.
5. **CESTA vs. WP27: 8 known exceptions over 0.5% among headline cities, not 2:**

   | City | Year | CESTA vs. WP27 |
   |---|---|---|
   | Mobile | 1960 | −3.9% |
   | Jacksonville | 1970 | −4.7% (WP27 = Duval County) |
   | Portland | 1970 | −0.7% |
   | Sacramento | 1970 | +1.1% |
   | Austin | 1970 | +0.7% |
   | Youngstown | 1970 | +0.8% |
   | Shreveport | 1980 | +0.6% |
   | Dayton | 1980 | −4.8% |

   CESTA stays the single population source. Of these, only 1970 is a period endpoint, and only Jacksonville's gap is large (its WP27 figure is the whole consolidated city, as the spec says).
6. **Austin is in the 1950 top 100** (rank 73), so all nine featured US metros are headline metros, and `rq0a_city_share.png` labels them without drawing Austin separately. The spec said otherwise.
7. **Metro coverage:**
   - The 6 Puerto Rico metros are left out, which gives 387 metros.
   - The first-named city is matched to CESTA by the longest name that starts the title, ignoring case, in the title's first state.
   - A committed overrides table covers 7 metros. Four are names CESTA spells differently: New York, Boise City, Urban Honolulu and Barnstable Town. Three have a main city that isn't in CESTA and get no city series: Amherst Town, Homosassa Springs and Lexington Park.
8. **Connecticut legacy counties count as central** in the central-counties check, since every 2023 Connecticut planning region in a metro is central. Two main cities aren't found in their own metro by the 2020 place-to-county file; the test lists them:
   - Waterbury, whose old county maps to the New Haven metro;
   - Macon, whose 2010 code no longer exists in 2020.
9. **Which checks apply to which rule** (the spec didn't say):
   - Rule 1: absolute yardstick, bar at ⅓ and ⅔, core = all old cities, central counties.
   - Rule 2: absolute yardstick, bar at ⅓ and ⅔, annexing threshold 10% and 40%, central counties. The core check doesn't apply, because annexing flags belong to the main city.
   - Rule 3: absolute yardstick, bar at ⅓ and ⅔, central counties. Rule 3 is about metros only.
10. **Minor fixes:**
    - Rule 3 is shown as two rows in `rq0a_answers.csv` ("3 (F2−F1)" and "3 (F3−F1)", same answer).
    - Context rows (weighted S, S in later periods, unconditioned D, F by region) are in the same file with an empty `answer`.
    - The central/outlying counts in spec §3.1 (1,325/590) are for all CBSAs. Among metro counties they are 769/483.

## Review Focus

1. **A CESTA 0 or blank** must become missing, never a city of 0 people. Otherwise growth is −100% or infinite. Tested in Task 1.
2. **Louisville 2020** must be the sum of the two NHGIS places. Taking the "balance" alone would show a 35% loss. Tested in Task 3 (logic) and Task 4 (data, known value).
3. **A metro with a county split inside a period (Denver 1990–2020)** must lose its metro and suburb growth for that period only, keep its city growth, and drop out of rule 3's 1990–2020 pair. Tested in Tasks 5 and 6.
4. **A resampled draw with an empty group** (no plateau cities, or no annexing cities) must be skipped and counted, never crash or count as 0. Tested in Task 6.
5. **The bracket rule** must not call a city "fixed" when the only known span shows a big gain, and must not call it "annexing" when the gain could fall outside the period. Tested in Task 5.

---

## File structure

| File | Responsibility | Task |
|---|---|---|
| `us_housing_crisis_analysis/config.py` | `RQ0A_*` constants | 1 |
| `us_housing_crisis_analysis/sources/cesta.py`, `sources/__init__.py` | CESTA city population | 1 |
| `us_housing_crisis_analysis/sources/nhgis.py` | + AV0 place extract and parser | 1 |
| `us_housing_crisis_analysis/sources/wp27.py`, `references/crosswalks/wp27_place_fips.csv` | WP27 tables 18–22 | 2 |
| `us_housing_crisis_analysis/sources/gazetteer.py` | Gazetteer land area 1990–2020 | 2 |
| `us_housing_crisis_analysis/geography.py` | central flag; place-to-county; old cities; metro main city; loaders | 3 |
| `references/crosswalks/{old_cities_1950,metro_main_city,metro_main_city_overrides,place_code_changes,city_county_consolidations}.csv` | Committed crosswalks | 3 |
| `us_housing_crisis_analysis/features.py` | `apply_place_code_changes`, `city_population`, `city_land_area`, `build_us_city_metro`; `main()` | 4 |
| `references/known_values.csv` | Detroit, Houston, Louisville values | 4 |
| `us_housing_crisis_analysis/modeling/city_metro.py` | growth, classes, annexing, units, ranges, rules | 5, 6 |
| `tests/test_cesta.py`, `tests/test_wp27.py`, `tests/test_gazetteer.py`, `tests/test_nhgis.py`, `tests/test_geography.py`, `tests/test_features.py`, `tests/test_city_metro.py`, `tests/data/test_us_city_metro.py` | Tests | 1–6 |
| `tests/fixtures/{cesta,wp27,gazetteer}/…`, `tests/fixtures/nhgis/av0_place.csv` | Excerpts of the real files | 1, 2 |
| `notebooks/1.0-lr-city-vs-metro.ipynb` | Analysis, figures, tables, finding | 7 |
| `reports/figures/rq0a_city_share.png`, `reports/figures/rq0a_classes.png`, `reports/tables/rq0a_classes.csv`, `reports/tables/rq0a_answers.csv` | Outputs | 7 |
| `Claude/…`, master spec, RQ0a spec | Docs | 1–7 |

---

### Task 1: City population sources (CESTA, NHGIS AV0)

**Files:**
- Create: `us_housing_crisis_analysis/sources/cesta.py`, `tests/test_cesta.py`, `tests/fixtures/cesta/master_sample.csv`, `tests/fixtures/nhgis/av0_place.csv`
- Modify: `us_housing_crisis_analysis/config.py`, `us_housing_crisis_analysis/sources/__init__.py`, `us_housing_crisis_analysis/sources/nhgis.py`, `tests/test_nhgis.py`, `Claude/research/sources.md`

**Interfaces:**
- Produces:
  - `cesta.parse(path) -> DataFrame` and `cesta.load() -> DataFrame` (long format: `geo_level="city"`, `geo_id="place:SSPPPPP"` with the 2010 code, `variable="population"`, years 1790–2010, `source="cesta"`).
  - `nhgis.parse_places(path) -> DataFrame` (long: `geo_level="city"`, years 1970–2020, `source="nhgis"`). `nhgis.load()` now returns states, counties and places.
  - `config.RQ0A_*` constants (below).

- [ ] **Step 1: Add the constants** to `us_housing_crisis_analysis/config.py`, after the `ICPSR_INCOME_FILES` block:

```python
# RQ0a (Plan 2): city vs. metro. City populations from 1900, metro populations from 1940, classes in
# three periods (Plan 1c's cuts). Keep-up bars: relative = RQ0A_BAR_FRACTION x US growth over the
# same period (50 states + DC); absolute = RQ0A_ABSOLUTE_RATE per decade, compounded. Annexing: land
# area up more than RQ0A_ANNEX_THRESHOLD over the period (checks 0.10 and 0.40).
RQ0A_CITY_START = 1900
RQ0A_METRO_START = 1940
RQ0A_PERIODS = ((1950, 1970), (1970, 1990), (1990, 2020))
RQ0A_BAR_FRACTION = 0.5
RQ0A_ABSOLUTE_RATE = 0.05
RQ0A_ANNEX_THRESHOLD = 0.20
RQ0A_MIN_GROUP = 15  # rule 2: fewer cities than this in either group -> "not testable"
# Two city sources must agree this closely where they overlap (CESTA vs. NHGIS in 2010)
RQ0A_OVERLAP_TOLERANCE = 0.005
```

- [ ] **Step 2: Download CESTA and make the fixture.** Write `us_housing_crisis_analysis/sources/cesta.py`:

```python
"""Stanford CESTA, Historical U.S. City Populations (US Census Bureau and Erik Steiner): decennial
city populations 1790-2010, keyed by each place's 2010 state+place FIPS code."""

from pathlib import Path

import pandas as pd

from us_housing_crisis_analysis.config import RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file

# Pinned to the repository's last commit (2018-03-22), so the file can't change under us
COMMIT = "9b267baf1a7a662ca2076cc966166662346f80bc"
URL = (f"https://raw.githubusercontent.com/cestastanford/historical-us-city-populations/{COMMIT}/"
       "data/1790-2010_MASTER.csv")
RAW_DIR = RAW_DATA_DIR / "cesta"
PATH = RAW_DIR / "1790-2010_MASTER.csv"
YEARS = range(1790, 2011, 10)


def download(force: bool = False) -> list[Path]:
    return [download_file(URL, PATH, force=force)]


def parse(path: Path) -> pd.DataFrame:
    """The file has old-Mac (CR) line ends, which pandas reads. Missing counts are stored as 0 or
    left blank and are dropped here, never read as zero people. Places without a 2010 code ("0" or
    blank: places that no longer exist, or Arlington CDP, VA) are dropped."""
    raw = pd.read_csv(path, dtype=str)
    fips = raw["STPLFIPS_2010"].fillna("").str.strip()
    raw = raw.assign(STPLFIPS_2010=fips)[fips.str.fullmatch(r"\d{7}")]
    raw = raw.assign(name=raw["CityST"].fillna(raw["City"] + ", " + raw["ST"]))
    long = raw.melt(id_vars=["STPLFIPS_2010", "name"], value_vars=[str(y) for y in YEARS],
                    var_name="year", value_name="value")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long[long["value"] > 0]
    df = pd.DataFrame(
        {
            "geo_id": "place:" + long["STPLFIPS_2010"], "geo_name": long["name"], "geo_level": "city",
            "country_iso3": "USA", "year": long["year"].astype("int64"), "variable": "population",
            "value": long["value"].astype("float64"), "unit": "persons", "source": "cesta",
        }
    )
    return validate_long(df.reset_index(drop=True))


def load() -> pd.DataFrame:
    return parse(PATH)
```

Then download and cut the fixture (header plus five places, keeping the CR line ends):

```bash
venv/bin/python -c "from us_housing_crisis_analysis.sources import cesta; cesta.download()"
venv/bin/python - <<'EOF'
from pathlib import Path
rows = [r for r in Path("data/raw/cesta/1790-2010_MASTER.csv").read_bytes().split(b"\r") if r]
keys = (b',Detroit,"Detroit, MI",', b',Gary,"Gary, IN",', b',Brooklyn,"Brooklyn, NY",',
        b',Arlington,"Arlington, VA",', b',Louisville,"Louisville, KY",')
keep = [rows[0]] + [r for r in rows[1:] if any(k in r for k in keys)]
assert len(keep) == 6, len(keep)
out = Path("tests/fixtures/cesta"); out.mkdir(parents=True, exist_ok=True)
(out / "master_sample.csv").write_bytes(b"\r".join(keep) + b"\r")
EOF
```

- [ ] **Step 3: Write the failing tests.** Create `tests/test_cesta.py`:

```python
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import cesta


def parsed(fixtures_dir):
    return cesta.parse(fixtures_dir / "cesta" / "master_sample.csv")


def test_output_is_valid_long_format(fixtures_dir):
    validate_long(parsed(fixtures_dir))


def test_ids_are_2010_place_codes(fixtures_dir):
    v = parsed(fixtures_dir).set_index(["geo_id", "year"]).value
    assert v[("place:2622000", 1950)] == 1_849_568  # Detroit
    assert v[("place:2148006", 2010)] == 597_337  # Louisville/Jefferson County (balance)


def test_zero_counts_are_missing_not_zero(fixtures_dir):
    df = parsed(fixtures_dir)
    assert (df.value > 0).all()
    gary = set(df.loc[df.geo_id == "place:1827000", "year"])  # Gary, IN, founded 1906
    assert 1900 not in gary and 1910 in gary


def test_places_without_a_2010_code_are_dropped(fixtures_dir):
    names = set(parsed(fixtures_dir).geo_name)
    assert "Brooklyn, NY" not in names and "Arlington, VA" not in names
    assert "Detroit, MI" in names


def test_download_skips_when_file_exists(tmp_path, monkeypatch):
    path = tmp_path / "master.csv"
    path.write_text("x")
    monkeypatch.setattr(cesta, "PATH", path)
    assert cesta.download() == [path]
```

- [ ] **Step 4: Run them.** `venv/bin/python -m pytest tests/test_cesta.py -v`. Expected: all pass, since Step 2 wrote the module. If one fails, fix the module, not the test.

- [ ] **Step 5: Extend NHGIS with AV0.** In `us_housing_crisis_analysis/sources/nhgis.py`:
  - Change the module docstring to `"""NHGIS (IPUMS): state and county population from time series table A00 (1790-2020), and place population from table AV0 (1970-2020, nominal: each place within its boundary at each census)."""`.
  - Below `A00_FILES`, add:

```python
AV0_DIR = RAW_DIR / "av0"
AV0_FILES = {"*_ts_nominal_place.csv": "av0_place.csv"}
AV0_YEARS = ["1970", "1980", "1990", "2000", "2010", "2020"]
```

  - Replace `download` with:

```python
def download(force: bool = False) -> list[Path]:
    return _download_a00(force) + _download_av0(force)


def _download_a00(force: bool) -> list[Path]:
    paths = [A00_DIR / name for name in A00_FILES.values()]
    if all(p.exists() for p in paths) and not force:
        return paths
    from ipumspy import AggregateDataExtract, TimeSeriesTable

    extract = AggregateDataExtract(
        collection="nhgis",
        description="Total population, states and counties, 1790-2020",
        time_series_tables=[TimeSeriesTable("A00", geog_levels=["state", "county"])],
        tst_layout="time_by_row_layout",
    )
    run_extract(extract, A00_DIR)
    return unpack_csvs(A00_DIR, A00_FILES)


def _download_av0(force: bool) -> list[Path]:
    paths = [AV0_DIR / name for name in AV0_FILES.values()]
    if all(p.exists() for p in paths) and not force:
        return paths
    from ipumspy import AggregateDataExtract, TimeSeriesTable

    extract = AggregateDataExtract(
        collection="nhgis",
        description="Total population, places, 1970-2020 (nominal)",
        time_series_tables=[TimeSeriesTable("AV0", geog_levels=["place"], years=AV0_YEARS)],
        tst_layout="time_by_row_layout",
    )
    run_extract(extract, AV0_DIR)
    return unpack_csvs(AV0_DIR, AV0_FILES)
```

  - Add the parser and extend `load`:

```python
def parse_places(path: Path) -> pd.DataFrame:
    """AV0 places: one row per place and census year. YEAR also holds ACS ranges ("2016-2020"),
    which are dropped. The ID is the place's code in that year (codes change, for example
    Louisville after its 2003 merger; features.apply_place_code_changes handles it)."""
    raw = _read(path)
    raw = raw[raw["YEAR"].str.fullmatch(r"\d{4}")]
    value = pd.to_numeric(raw["AV0AA"], errors="coerce")
    df = pd.DataFrame(
        {
            "geo_id": "place:" + raw["STATEFP"].str.zfill(2) + raw["PLACEA"].str.zfill(5),
            "geo_name": raw["PLACE"] + ", " + raw["STATE"], "geo_level": "city", "country_iso3": "USA",
            "year": raw["YEAR"].astype("int64"), "variable": "population",
            "value": value.astype("float64"), "unit": "persons", "source": "nhgis",
        }
    )
    return validate_long(df[value.notna()].reset_index(drop=True))


def load() -> pd.DataFrame:
    counties = parse_population(A00_DIR / "a00_state.csv", A00_DIR / "a00_county.csv")
    return validate_long(pd.concat([counties, parse_places(AV0_DIR / "av0_place.csv")], ignore_index=True))
```

- [ ] **Step 6: Download AV0 and make its fixture.** Run `venv/bin/python -m us_housing_crisis_analysis.dataset download --source nhgis`; it submits only the AV0 extract (minutes to hours). Then:

```bash
venv/bin/python - <<'EOF'
import pandas as pd
d = pd.read_csv("data/raw/nhgis/av0/av0_place.csv", dtype=str, encoding="latin-1")
code = d.STATEFP.str.zfill(2) + d.PLACEA.str.zfill(5)
d[code.isin(["2622000", "2148006", "2148000", "0100124"])].to_csv("tests/fixtures/nhgis/av0_place.csv", index=False)
EOF
```

- [ ] **Step 7: Update the NHGIS tests.** In `tests/test_nhgis.py`, replace `test_download_skips_when_files_exist` and add the place test:

```python
def test_download_skips_when_files_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(nhgis, "A00_DIR", tmp_path)
    monkeypatch.setattr(nhgis, "AV0_DIR", tmp_path)
    for name in ("a00_state.csv", "a00_county.csv", "av0_place.csv"):
        (tmp_path / name).write_text("x")

    def fail(*args, **kwargs):
        raise AssertionError("extract submitted although files exist")

    monkeypatch.setattr(nhgis, "run_extract", fail)
    assert len(nhgis.download()) == 3


def test_av0_places_keep_census_years_only(fixtures_dir):
    df = nhgis.parse_places(fixtures_dir / "nhgis" / "av0_place.csv")
    validate_long(df)
    assert set(df.geo_level) == {"city"}
    assert set(df.year) <= {1970, 1980, 1990, 2000, 2010, 2020}
    v = df.set_index(["geo_id", "year"]).value
    assert v[("place:2622000", 2020)] == 639_111  # Detroit
    assert v[("place:2148006", 2020)] == 386_884  # Louisville balance, without the old city
    assert v[("place:2148000", 2020)] == 246_161  # Louisville's old city, a separate place in 2020
```

- [ ] **Step 8: Register the source and run.** In `sources/__init__.py`, append `"cesta"` to `SOURCE_NAMES`. Then:

```bash
venv/bin/python -m pytest tests/test_cesta.py tests/test_nhgis.py -v
venv/bin/python -m us_housing_crisis_analysis.dataset load --source cesta
venv/bin/python -m us_housing_crisis_analysis.dataset load --source nhgis
```

Expected: tests pass; `cesta` about 100,000 rows; `nhgis` gains about 140,000 place rows.

- [ ] **Step 9: Docs.** In `Claude/research/sources.md`:
  - Replace the planned "Population of the 100 Largest Cities" and "Decennial census city populations 2000–2020" rows with this row:

    | Field | Value |
    |---|---|
    | Source | Historical U.S. City Populations, 1790–2010 |
    | Provider | Stanford CESTA (US Census Bureau and Erik Steiner) |
    | URL | https://github.com/cestastanford/historical-us-city-populations, file `data/1790-2010_MASTER.csv` pinned to commit 9b267ba |
    | Coverage | 8,915 US places, decennial 1790–2010, with each place's 2010 FIPS code |
    | Access / license | Public download; no license file; Census counts; cite CESTA |
    | Module | `sources/cesta.py` |
    | Status | active (0 or blank = missing; places without a 2010 code dropped) |
    | Accessed | 2026-10-19 |

  - Extend the NHGIS row: "time series AV0 (place population 1970–2020, nominal) for 2020 city counts and the 2010 overlap check".

- [ ] **Step 10: Commit.**

```bash
git add us_housing_crisis_analysis/config.py us_housing_crisis_analysis/sources tests/test_cesta.py tests/test_nhgis.py tests/fixtures/cesta tests/fixtures/nhgis/av0_place.csv Claude/research/sources.md
git commit -m "Add city population sources: CESTA 1790-2010 and NHGIS AV0 places (Plan 2 Task 1)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Land area sources (Working Paper 27, Gazetteers)

**Files:**
- Create: `us_housing_crisis_analysis/sources/wp27.py`, `us_housing_crisis_analysis/sources/gazetteer.py`, `references/crosswalks/wp27_place_fips.csv`, `tests/test_wp27.py`, `tests/test_gazetteer.py`, `tests/fixtures/wp27/tab{18,19,22}.txt`, `tests/fixtures/gazetteer/gaz_{1990,2000,2010,2020}.txt`
- Modify: `us_housing_crisis_analysis/sources/__init__.py`, `Claude/research/sources.md`

**Interfaces:**
- Consumes: `cesta.parse`, `cesta.PATH` (to build the WP27 name crosswalk once).
- Produces:
  - `wp27.parse_table(path, year) -> DataFrame[year, rank, wp27_name, state, population, land_sqmi, note]`;
  - `wp27.to_long(rows, place_fips) -> DataFrame`;
  - `wp27.load()`: long, `geo_level="city"`, variables `population` (persons) and `land_area` (sq_mi), years 1950–1990;
  - `gazetteer.decode(bytes) -> str`;
  - `gazetteer.parse(year, text) -> DataFrame[geoid, name, land_sqmi]`;
  - `gazetteer.load()`: long, `variable="land_area"`, `unit="sq_mi"`, years 1990, 2000, 2010 and 2020, keyed by that year's place code.

- [ ] **Step 1: Write `us_housing_crisis_analysis/sources/wp27.py`.**

```python
"""Census Working Paper 27 (Gibson 1998), "Population of the 100 Largest Cities and Other Urban
Places in the United States: 1790 to 1990", tables 18-22 (1950-1990): population and land area of
each year's 100 largest urban places."""

from pathlib import Path
import re

import pandas as pd

from us_housing_crisis_analysis.config import CROSSWALKS_DIR, RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file

URL = "https://www2.census.gov/library/working-papers/1998/demographics/pop-twps0027/tab{n}.txt"
TABLES = {1950: 18, 1960: 19, 1970: 20, 1980: 21, 1990: 22}
RAW_DIR = RAW_DATA_DIR / "wp27"
PLACE_FIPS_PATH = CROSSWALKS_DIR / "wp27_place_fips.csv"

# A data row: rank (ties print as "97-T"), place and state, an optional " *" (see the paper's notes
# for individual places) and leader dots, then population, land area in sq mi (can carry a
# thousands comma: Anchorage 1,697.6) and density
ROW = re.compile(r"^\s*(\d+)(?:-T)?\s+(.+?)(\s\*)?\.*\s+([\d,]+)\s+([\d,.]+)\s+([\d,]+)\s*$")
# "Detroit city, MI", and in two rows "Spokane city WA" (no comma)
PLACE = re.compile(r"^(.*?),?\s([A-Z]{2})$")
# Place-type words dropped before matching names to CESTA
SUFFIX = r" (city|town|village|borough|CDP|municipality)$"


def download(force: bool = False) -> list[Path]:
    return [download_file(URL.format(n=n), RAW_DIR / f"tab{n}.txt", force=force) for n in TABLES.values()]


def parse_table(path: Path, year: int) -> pd.DataFrame:
    """One row per place. Exact duplicate rows are dropped (the 1950 table prints Memphis twice)."""
    rows = []
    for line in Path(path).read_text(encoding="latin-1").splitlines():
        m = ROW.match(line)
        if not m:
            continue
        rank, place, star, pop, area, _ = m.groups()
        p = PLACE.match(place.strip())
        if p is None:
            raise ValueError(f"{Path(path).name}: no state in {place!r}")
        rows.append({"year": year, "rank": int(rank), "wp27_name": p.group(1), "state": p.group(2),
                     "population": float(pop.replace(",", "")),
                     "land_sqmi": float(area.replace(",", "")), "note": star is not None})
    return pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)


def parse_all(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    parts = [parse_table(Path(raw_dir) / f"tab{n}.txt", year) for year, n in TABLES.items()]
    for part in parts:
        if len(part) != 100:
            raise ValueError(f"WP27 {part.year.iloc[0]}: {len(part)} places, expected 100")
    return pd.concat(parts, ignore_index=True)


def load_place_fips() -> pd.DataFrame:
    return pd.read_csv(PLACE_FIPS_PATH, dtype=str)


def to_long(rows: pd.DataFrame, place_fips: pd.DataFrame) -> pd.DataFrame:
    m = rows.merge(place_fips, on=["wp27_name", "state"], how="left")
    missing = m[m.place_fips.isna()]
    if len(missing):
        raise ValueError(f"no place code for {sorted(set(missing.wp27_name + ', ' + missing.state))}")
    base = pd.DataFrame({"geo_id": "place:" + m.place_fips, "geo_name": m.wp27_name + ", " + m.state,
                         "geo_level": "city", "country_iso3": "USA", "year": m.year.astype("int64"),
                         "source": "wp27"})
    out = pd.concat([
        base.assign(variable="population", value=m.population.astype("float64"), unit="persons"),
        base.assign(variable="land_area", value=m.land_sqmi.astype("float64"), unit="sq_mi"),
    ], ignore_index=True)
    return validate_long(out)


def load() -> pd.DataFrame:
    return to_long(parse_all(RAW_DIR), load_place_fips())
```

- [ ] **Step 2: Download, cut the fixtures, build the name crosswalk.**

```bash
venv/bin/python -c "from us_housing_crisis_analysis.sources import wp27; wp27.download()"
venv/bin/python - <<'EOF'
from pathlib import Path
keep = ("Memphis city", "Spokane city WA", "Arlington CDP", "Detroit city", "Madison city",
        "Anchorage city", "Houston city")
out = Path("tests/fixtures/wp27"); out.mkdir(parents=True, exist_ok=True)
for n in (18, 19, 22):
    lines = Path(f"data/raw/wp27/tab{n}.txt").read_text(encoding="latin-1").splitlines(keepends=True)
    (out / f"tab{n}.txt").write_text("".join(lines[:12] + [l for l in lines[12:] if any(k in l for k in keep)]))
EOF
venv/bin/python - <<'EOF'
import pandas as pd
from us_housing_crisis_analysis.sources import cesta, wp27
rows = wp27.parse_all()
c = cesta.parse(cesta.PATH).drop_duplicates("geo_id")
split = c.geo_name.str.rsplit(", ", n=1)
names = pd.DataFrame({"place_fips": c.geo_id.str.removeprefix("place:"), "city": split.str[0], "state": split.str[1]})
names = names[~names.duplicated(["city", "state"], keep=False)]
places = rows.drop_duplicates(["wp27_name", "state"])[["wp27_name", "state"]]
places = places.assign(city=places.wp27_name.str.replace(wp27.SUFFIX, "", regex=True))
out = places.merge(names, on=["city", "state"], how="left")
# Names CESTA spells differently, checked by hand (population agrees with CESTA in every year)
hand = {("New York city", "NY"): "3651000", ("Nashville-Davidson", "TN"): "4752006",
        ("Lexington-Fayette", "KY"): "2146027", ("Arlington CDP", "VA"): "5103000",
        ("Metairie CDP", "LA"): "2250115"}
out["place_fips"] = [hand.get((n, s), f) for n, s, f in zip(out.wp27_name, out.state, out.place_fips)]
assert out.place_fips.notna().all(), out[out.place_fips.isna()]
assert not out.place_fips.duplicated().any()
out.sort_values(["state", "wp27_name"])[["wp27_name", "state", "place_fips"]].to_csv(wp27.PLACE_FIPS_PATH, index=False)
print(len(out), "places")
EOF
```

Expected: about 150 places, with none unmatched and no code used twice.

- [ ] **Step 3: Write the WP27 tests.** Create `tests/test_wp27.py`:

```python
import pandas as pd
import pytest

from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import wp27


def table(fixtures_dir, n, year):
    return wp27.parse_table(fixtures_dir / "wp27" / f"tab{n}.txt", year)


def test_duplicate_rows_notes_and_missing_commas(fixtures_dir):
    t = table(fixtures_dir, 18, 1950).set_index("wp27_name")
    assert (t.index == "Memphis city").sum() == 1  # printed twice in the 1950 table
    assert t.loc["Spokane city", "state"] == "WA" and t.loc["Spokane city", "land_sqmi"] == 41.5
    assert t.loc["Arlington CDP", "note"] and t.loc["Arlington CDP", "population"] == 135_449
    assert t.loc["Detroit city", "population"] == 1_849_568 and t.loc["Detroit city", "land_sqmi"] == 139.6
    assert t.loc["Houston city", "land_sqmi"] == 160.0


def test_tied_ranks_and_area_with_a_thousands_comma(fixtures_dir):
    assert "Madison city" in set(table(fixtures_dir, 19, 1960).wp27_name)  # rank "97-T"
    t = table(fixtures_dir, 22, 1990).set_index("wp27_name")
    assert t.loc["Anchorage city", "land_sqmi"] == 1697.6
    assert t.loc["Houston city", "land_sqmi"] == 539.9


def test_to_long_needs_a_code_for_every_place(fixtures_dir):
    t = table(fixtures_dir, 18, 1950)
    codes = pd.DataFrame({"wp27_name": ["Detroit city"], "state": ["MI"], "place_fips": ["2622000"]})
    with pytest.raises(ValueError, match="no place code"):
        wp27.to_long(t, codes)
    out = validate_long(wp27.to_long(t[t.wp27_name == "Detroit city"], codes))
    assert set(out.variable) == {"population", "land_area"}
    assert set(out.geo_id) == {"place:2622000"}


def test_crosswalk_codes_are_unique():
    c = wp27.load_place_fips()
    assert not c.duplicated(["wp27_name", "state"]).any() and not c.place_fips.duplicated().any()
    assert c.place_fips.str.fullmatch(r"\d{7}").all()
```

Run: `venv/bin/python -m pytest tests/test_wp27.py -v`. Expected: PASS.

- [ ] **Step 4: Write `us_housing_crisis_analysis/sources/gazetteer.py`.**

```python
"""Census Gazetteer place files: land area of every place in 1990, 2000, 2010 and 2020, keyed by
that year's state+place FIPS code (codes can change between years; see
features.apply_place_code_changes)."""

import io
from pathlib import Path
import re
import zipfile

from loguru import logger
import pandas as pd

from us_housing_crisis_analysis.config import RAW_DATA_DIR
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources._http import download_file

BASE = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
# year -> (path under BASE, member inside the zip)
FILES = {
    1990: ("places.zip", "places.txt"),
    2000: ("places2k.zip", "places2k.txt"),
    2010: ("Gaz_places_national.zip", "Gaz_places_national.txt"),
    2020: ("2020_Gazetteer/2020_Gaz_place_national.zip", "2020_Gaz_place_national.txt"),
}
RAW_DIR = RAW_DATA_DIR / "gazetteer"
SQ_M_PER_SQ_MI = 2_589_988.110336
# 1990: "SS PPPPP Name...   ST  pop  housing  land  water  lat  lon"; land and water areas are in
# thousands of square meters (Detroit 0000359284 -> 138.7 sq mi, as in Working Paper 27)
ROW_1990 = re.compile(r"^(\d{2}) (\d{5}) (.+?)\s+[A-Z]{2}\s+\d+\s+\d+\s+(\d{10})\s+\d{10}\s+[+-]\d+\s+[+-]\d+\s*$")
# 2000: fixed width (Census record layout); latitude and longitude can touch, so no splitting
COLSPECS_2000 = {"geoid": (2, 9), "name": (9, 73), "land_sqmi": (119, 131)}


def download(force: bool = False) -> list[Path]:
    return [download_file(BASE + path, RAW_DIR / f"gaz_{year}.zip", force=force)
            for year, (path, _) in FILES.items()]


def decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def read_text(year: int) -> str:
    with zipfile.ZipFile(RAW_DIR / f"gaz_{year}.zip") as z:
        return decode(z.read(FILES[year][1]))


def parse(year: int, text: str) -> pd.DataFrame:
    """geoid (that year's 7-digit place code), name, land_sqmi. Codes that appear twice in a file
    (two tiny places in 1990) are dropped."""
    if year == 1990:
        rows = [(m[1] + m[2], m[3], int(m[4]) * 1000 / SQ_M_PER_SQ_MI)
                for line in text.splitlines() if (m := ROW_1990.match(line))]
        df = pd.DataFrame(rows, columns=["geoid", "name", "land_sqmi"])
    elif year == 2000:
        df = pd.read_fwf(io.StringIO(text), colspecs=list(COLSPECS_2000.values()),
                         names=list(COLSPECS_2000), dtype={"geoid": str}, header=None)
    else:
        raw = pd.read_csv(io.StringIO(text), sep="\t", dtype=str)
        raw.columns = raw.columns.str.strip()
        df = pd.DataFrame({"geoid": raw.GEOID.str.strip(), "name": raw.NAME.str.strip(),
                           "land_sqmi": pd.to_numeric(raw.ALAND_SQMI.str.strip())})
    dupes = df.geoid.duplicated(keep=False)
    if dupes.any():
        logger.info(f"gazetteer {year}: dropped codes listed twice: {sorted(set(df.geoid[dupes]))}")
    return df[~dupes].astype({"land_sqmi": "float64"}).reset_index(drop=True)


def load() -> pd.DataFrame:
    parts = []
    for year in FILES:
        g = parse(year, read_text(year))
        parts.append(pd.DataFrame({
            "geo_id": "place:" + g.geoid, "geo_name": g.name, "geo_level": "city", "country_iso3": "USA",
            "year": year, "variable": "land_area", "value": g.land_sqmi, "unit": "sq_mi",
            "source": "gazetteer"}))
    out = pd.concat(parts, ignore_index=True)
    return validate_long(out.astype({"year": "int64"}))
```

- [ ] **Step 5: Download and cut the Gazetteer fixtures** (real lines, original line ends):

```bash
venv/bin/python -c "from us_housing_crisis_analysis.sources import gazetteer; gazetteer.download()"
venv/bin/python - <<'EOF'
from pathlib import Path
from us_housing_crisis_analysis.sources import gazetteer as gz
keep = ("2622000", "4835000", "2148000", "2148006", "1235160", "1836003")

def hit(year, line, g):
    if year == 1990:
        return line.startswith(f"{g[:2]} {g[2:]} ")
    if year == 2000:
        return line[2:9] == g
    return f"\t{g}\t" in line

out = Path("tests/fixtures/gazetteer"); out.mkdir(parents=True, exist_ok=True)
for year in gz.FILES:
    lines = gz.read_text(year).splitlines(keepends=True)
    head = [] if year in (1990, 2000) else lines[:1]
    body = [l for l in lines if any(hit(year, l, g) for g in keep)]
    (out / f"gaz_{year}.txt").write_text("".join(head + body), newline="")
    print(year, len(body))
EOF
```

- [ ] **Step 6: Write the Gazetteer tests.** Create `tests/test_gazetteer.py`:

```python
import pytest

from us_housing_crisis_analysis.sources import gazetteer


def parsed(fixtures_dir, year):
    text = gazetteer.decode((fixtures_dir / "gazetteer" / f"gaz_{year}.txt").read_bytes())
    return gazetteer.parse(year, text).set_index("geoid")


@pytest.mark.parametrize("year", [1990, 2000, 2010, 2020])
def test_detroit_land_area_in_square_miles(fixtures_dir, year):
    assert parsed(fixtures_dir, year).loc["2622000", "land_sqmi"] == pytest.approx(138.7, abs=0.1)


def test_1990_area_matches_working_paper_27(fixtures_dir):
    # WP27 table 22: Houston 539.9 sq mi; the 1990 file stores thousands of square meters
    assert parsed(fixtures_dir, 1990).loc["4835000", "land_sqmi"] == pytest.approx(539.9, rel=0.005)


def test_codes_are_that_years_codes(fixtures_dir):
    g1990, g2020 = parsed(fixtures_dir, 1990), parsed(fixtures_dir, 2020)
    assert "1235160" in g1990.index  # Jacksonville city (remainder)
    assert {"2148000", "2148006"} <= set(g2020.index)  # Louisville: old city and balance
    assert g2020.loc[["2148000", "2148006"], "land_sqmi"].sum() == pytest.approx(325.2, abs=0.2)
```

Run: `venv/bin/python -m pytest tests/test_wp27.py tests/test_gazetteer.py -v`. Expected: PASS.

- [ ] **Step 7: Register, load, check.** Append `"wp27"` and `"gazetteer"` to `SOURCE_NAMES`. Then:

```bash
venv/bin/python -m us_housing_crisis_analysis.dataset load --source wp27
venv/bin/python -m us_housing_crisis_analysis.dataset load --source gazetteer
```

Expected:
- `wp27`: 1,000 rows (500 places × 2 variables).
- `gazetteer`: about 100,000 rows. Two duplicate 1990 codes are logged (one in PA, one in VI).

- [ ] **Step 8: Docs.** Add two rows to `Claude/research/sources.md`, accessed 2026-10-19.
  - **Working Paper 27** (Gibson 1998):
    - URL: https://www2.census.gov/library/working-papers/1998/demographics/pop-twps0027/tab18.txt to tab22.txt.
    - Coverage: top-100 urban places, population and land area, 1950–1990. Public domain.
    - Module: `sources/wp27.py`.
    - Status: active. Land area 1950–1980; population and 1990 area are checks. Names are matched to CESTA codes in `references/crosswalks/wp27_place_fips.csv` (5 hand-coded).
  - **Census Gazetteer place files:**
    - URLs: the four `FILES` paths under https://www2.census.gov/geo/docs/maps-data/data/gazetteer/.
    - Coverage: every place's land area, 1990, 2000, 2010 and 2020. Public domain.
    - Module: `sources/gazetteer.py`.
    - Status: active. The 1990 area is in thousands of m², and the 1990 file is added beyond the spec (D-31).

- [ ] **Step 9: Commit.**

```bash
git add us_housing_crisis_analysis/sources references/crosswalks/wp27_place_fips.csv tests/test_wp27.py tests/test_gazetteer.py tests/fixtures/wp27 tests/fixtures/gazetteer Claude/research/sources.md
git commit -m "Add city land area sources: Working Paper 27 and Census Gazetteers (Plan 2 Task 2)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Crosswalks (old cities, each metro's main city, code changes, consolidations)

**Files:**
- Modify: `us_housing_crisis_analysis/geography.py`, `tests/test_geography.py`, `Claude/methods/geography.md`
- Create: `references/crosswalks/old_cities_1950.csv`, `references/crosswalks/metro_main_city.csv`, `references/crosswalks/metro_main_city_overrides.csv`, `references/crosswalks/place_code_changes.csv`, `references/crosswalks/city_county_consolidations.csv`

**Interfaces:**
- Consumes: `parse_delineation`, `county_to_cbsa`, the interim `cesta` and `wp27` frames.
- Produces:
  - `parse_delineation(path)` adds a bool `central` column. `county_to_cbsa()` carries `central` too (Connecticut legacy counties: True).
  - `parse_place_counties(path=PLACE_COUNTY_PATH) -> DataFrame[place_fips, county_fips]`.
  - `place_cbsas(place_counties, crosswalk) -> DataFrame[place_fips, cbsa_code]`.
  - `cesta_names(cesta) -> DataFrame[place_fips, city, state, geo_name]`.
  - `build_old_cities(wp27, place_cbsa, cesta_ids) -> DataFrame[rank_1950, place_fips, city_name, population_1950, cbsa_code, main_city, in_cesta]`.
  - `build_metro_main_city(crosswalk, names, old_cities, overrides) -> DataFrame[cbsa_code, cbsa_title, city_name, place_fips, top100_1950_rank, headline, note]`.
  - Loaders: `load_old_cities()`, `load_metro_main_city()`, `load_main_city_overrides()`, `load_place_code_changes()`, `load_consolidations()`.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_geography.py`:

```python
import pytest


def test_central_flag(delineation_xlsx):
    d = geo.parse_delineation(delineation_xlsx).set_index("county_fips")
    assert d.loc["24510", "central"] and not d.loc["51019", "central"]
    cw = geo.county_to_cbsa(geo.parse_delineation(delineation_xlsx)).set_index("county_fips")
    assert cw.loc["09003", "central"]  # Connecticut legacy county: every CT planning region in a metro is central


def test_parse_place_counties(tmp_path):
    p = tmp_path / "pbc.txt"
    p.write_text("STATE|STATEFP|COUNTYFP|COUNTYNAME|PLACEFP|PLACENS|PLACENAME|TYPE|CLASSFP|FUNCSTAT\n"
                 "MI|26|163|Wayne County|22000|01626181|Detroit city|INCORPORATED PLACE|C1|A\n")
    out = geo.parse_place_counties(p)
    assert out.to_dict("records") == [{"place_fips": "2622000", "county_fips": "26163"}]


def cesta_long(rows):
    """rows: (place_fips, 'City, ST', year, population)"""
    return pd.DataFrame({"geo_id": ["place:" + r[0] for r in rows], "geo_name": [r[1] for r in rows],
                         "geo_level": "city", "year": [r[2] for r in rows], "variable": "population",
                         "value": [float(r[3]) for r in rows]})


def test_old_cities_mark_each_metros_largest_1950_city():
    wp27 = cesta_long([("5157000", "Norfolk city, VA", 1950, 213_513), ("5182000", "Virginia Beach city, VA", 1950, 5_390),
                       ("3651000", "New York city, NY", 1950, 7_891_957), ("3451000", "Newark city, NJ", 1950, 438_776)])
    pc = pd.DataFrame({"place_fips": ["5157000", "5182000", "3651000", "3451000"],
                       "cbsa_code": ["47260", "47260", "35620", "35620"]})
    old = geo.build_old_cities(wp27, pc, cesta_ids={"5157000", "3651000", "3451000"}).set_index("place_fips")
    assert old.loc["3651000", "rank_1950"] == 1 and old.loc["3651000", "main_city"]
    assert not old.loc["3451000", "main_city"] and old.loc["5157000", "main_city"]
    assert not old.loc["5182000", "in_cesta"]
    with pytest.raises(ValueError, match="more than one metro"):
        geo.build_old_cities(wp27, pd.concat([pc, pd.DataFrame({"place_fips": ["5157000"], "cbsa_code": ["99999"]})]), set())


def main_city_inputs():
    cw = pd.DataFrame({
        "county_fips": ["37067", "16055", "47037", "36061", "51810", "72127", "25001"],
        "cbsa_code": ["49180", "17660", "34980", "35620", "47260", "41980", "12700"],
        "cbsa_title": ["Winston-Salem, NC", "Coeur d'Alene, ID", "Nashville-Davidson--Murfreesboro--Franklin, TN",
                       "New York-Newark-Jersey City, NY-NJ", "Virginia Beach-Chesapeake-Norfolk, VA-NC",
                       "San Juan-Bayamón-Caguas, PR", "Barnstable Town, MA"]})
    names = pd.DataFrame({"place_fips": ["3774440", "3775000", "1616750", "4752006", "3651000", "5182000", "5157000"],
                          "city": ["Winston", "Winston-Salem", "Coeur D'Alene", "Nashville", "New York City",
                                   "Virginia Beach", "Norfolk"],
                          "state": ["NC", "NC", "ID", "TN", "NY", "VA", "VA"]})
    names["geo_name"] = names.city + ", " + names.state
    old = pd.DataFrame({"rank_1950": [1, 48], "place_fips": ["3651000", "5157000"], "city_name": ["x", "y"],
                        "population_1950": [7.9e6, 213_513.0], "cbsa_code": ["35620", "47260"],
                        "main_city": [True, True], "in_cesta": [True, True]})
    overrides = pd.DataFrame({"cbsa_code": ["35620", "12700"], "place_fips": ["3651000", None],
                              "note": ["CESTA: New York City", "not in CESTA"]})
    return cw, names, old, overrides


def test_main_city_matching_rules():
    m = geo.build_metro_main_city(*main_city_inputs()).set_index("cbsa_code")
    assert m.loc["49180", "place_fips"] == "3775000"  # longest name that starts the title
    assert m.loc["17660", "place_fips"] == "1616750"  # case ignored
    assert m.loc["34980", "place_fips"] == "4752006"
    assert "41980" not in m.index  # Puerto Rico left out
    assert pd.isna(m.loc["12700", "place_fips"]) and m.loc["12700", "city_name"] == "Barnstable Town"
    assert m.loc["35620", "headline"] and m.loc["35620", "top100_1950_rank"] == 1
    assert m.loc["47260", "place_fips"] == "5157000"  # headline: largest 1950 city, not first-named
    assert "first-named" in m.loc["47260", "note"]
    assert not m.loc["49180", "headline"]


def test_main_city_unmatched_title_raises():
    cw, names, old, overrides = main_city_inputs()
    with pytest.raises(ValueError, match="no CESTA city"):
        geo.build_metro_main_city(cw, names[names.city != "Winston-Salem"].iloc[1:], old, overrides)


def test_committed_tables_load():
    changes = geo.load_place_code_changes()
    assert set(changes.columns) >= {"place_fips", "year", "source_fips"}
    lou = changes[(changes.place_fips == "2148006") & (changes.year == 2020)]
    assert set(lou.source_fips) == {"2148006", "2148000"}
    cons = geo.load_consolidations().set_index("place_fips").year
    assert cons["4752006"] == 1963 and cons["2148006"] == 2003
```

Run: `venv/bin/python -m pytest tests/test_geography.py -v`. Expected: FAIL (missing functions).

- [ ] **Step 2: Implement in `us_housing_crisis_analysis/geography.py`.**
  - In `parse_delineation`, add to the frame: `"central": raw["Central/Outlying County"].eq("Central"),`.
  - In `county_to_cbsa`, replace `ct = ct[ct.cbsa_code.isin(cbsas.index)].join(cbsas, on="cbsa_code")` with:

```python
    # Every 2023 Connecticut planning region in a metro is a central county, so the legacy
    # counties are central too (used by the RQ0a central-counties check)
    ct = ct[ct.cbsa_code.isin(cbsas.index)].join(cbsas, on="cbsa_code").assign(central=True)
```

  - Add near the top, after `DELINEATION_PATH`:

```python
PLACE_COUNTY_URL = "https://www2.census.gov/geo/docs/reference/codes2020/national_place_by_county2020.txt"
PLACE_COUNTY_PATH = RAW_DIR / "national_place_by_county2020.txt"
```

  - Make `download` return `[download_file(DELINEATION_URL, DELINEATION_PATH, force=force), download_file(PLACE_COUNTY_URL, PLACE_COUNTY_PATH, force=force)]`.
  - Append:

```python
# --- RQ0a (Plan 2): cities and their metros. See geography.md "Secondary unit: city proper". ---
OLD_CITIES_PATH = CROSSWALKS_DIR / "old_cities_1950.csv"
MAIN_CITY_PATH = CROSSWALKS_DIR / "metro_main_city.csv"
MAIN_CITY_OVERRIDES_PATH = CROSSWALKS_DIR / "metro_main_city_overrides.csv"
PLACE_CODE_CHANGES_PATH = CROSSWALKS_DIR / "place_code_changes.csv"
CONSOLIDATIONS_PATH = CROSSWALKS_DIR / "city_county_consolidations.csv"


def parse_place_counties(path: Path = PLACE_COUNTY_PATH) -> pd.DataFrame:
    """2020 place -> county pairs (a place in several counties has several rows). Connecticut is on
    its old counties, which county_to_cbsa maps to metros."""
    d = pd.read_csv(path, sep="|", dtype=str)
    return pd.DataFrame({"place_fips": d.STATEFP + d.PLACEFP, "county_fips": d.STATEFP + d.COUNTYFP})


def place_cbsas(place_counties: pd.DataFrame, crosswalk: pd.DataFrame) -> pd.DataFrame:
    """Unique (place, metro) pairs, through the place's counties."""
    m = place_counties.merge(crosswalk[["county_fips", "cbsa_code"]], on="county_fips")
    return m[["place_fips", "cbsa_code"]].drop_duplicates().reset_index(drop=True)


def cesta_names(cesta: pd.DataFrame) -> pd.DataFrame:
    """place_fips, city, state and geo_name of every CESTA place."""
    c = cesta.drop_duplicates("geo_id")
    split = c.geo_name.str.rsplit(", ", n=1)
    return pd.DataFrame({"place_fips": c.geo_id.str.removeprefix("place:").to_numpy(),
                         "city": split.str[0].to_numpy(), "state": split.str[1].to_numpy(),
                         "geo_name": c.geo_name.to_numpy()})


def build_old_cities(wp27: pd.DataFrame, place_cbsa: pd.DataFrame, cesta_ids: set[str]) -> pd.DataFrame:
    """The 1950 top 100 (Working Paper 27, table 18), ranked by 1950 population, each with its 2023
    metro. main_city marks the metro's largest 1950 city: "the city" of a headline metro (spec §3.2).
    in_cesta is False for a city with no CESTA series (Arlington CDP, VA), which the
    all-old-cities-as-core check leaves out."""
    p = wp27[(wp27.year == 1950) & (wp27.variable == "population")]
    old = pd.DataFrame({"place_fips": p.geo_id.str.removeprefix("place:").to_numpy(),
                        "city_name": p.geo_name.to_numpy(), "population_1950": p.value.to_numpy()})
    old = old.sort_values("population_1950", ascending=False, kind="stable").reset_index(drop=True)
    old.insert(0, "rank_1950", old.index + 1)
    metros = place_cbsa[place_cbsa.place_fips.isin(old.place_fips)].groupby("place_fips").cbsa_code.agg(list)
    multi = metros[metros.str.len() > 1]
    if len(multi):
        raise ValueError(f"old cities in more than one metro: {multi.to_dict()}")
    old["cbsa_code"] = old.place_fips.map(metros.str[0])
    old["main_city"] = old.cbsa_code.notna() & ~old.cbsa_code.duplicated()
    old["in_cesta"] = old.place_fips.isin(cesta_ids)
    return old


def build_metro_main_city(crosswalk: pd.DataFrame, names: pd.DataFrame, old_cities: pd.DataFrame,
                          overrides: pd.DataFrame) -> pd.DataFrame:
    """One row per metro outside Puerto Rico (owner's choice A, spec §3.2):
    - headline metros (holding a 1950 top-100 city) take their largest 1950 city;
    - other metros take the first-named city of the CBSA title: the CESTA place in the title's
      first state with the longest name that starts the title (followed by "-", "," or "/"),
      ignoring case;
    - overrides (cbsa_code, place_fips, note) settle titles that don't match; a blank place_fips
      means the city isn't in CESTA, so the metro has no city series."""
    metros = crosswalk[~crosswalk.county_fips.str.startswith("72")].drop_duplicates("cbsa_code")
    names = names[~names.duplicated(["city", "state"], keep=False)]
    by_state = dict(tuple(names.groupby("state")))
    label = names.set_index("place_fips").geo_name
    ov = overrides.set_index("cbsa_code")
    rows, unmatched = [], []
    for code, title in zip(metros.cbsa_code, metros.cbsa_title):
        if code in ov.index:
            fips, note = ov.at[code, "place_fips"], ov.at[code, "note"]
        else:
            g = by_state.get(first_listed_state(title), names.iloc[:0])
            t = title.lower()
            hits = g[[any(t.startswith(c.lower() + sep) for sep in "-,/") for c in g.city]]
            if hits.empty:
                unmatched.append(title)
                continue
            fips, note = hits.loc[hits.city.str.len().idxmax(), "place_fips"], ""
        fips = fips if isinstance(fips, str) and fips else pd.NA
        city = label.get(fips, pd.NA) if fips is not pd.NA else title.split(",")[0].split("-")[0]
        rows.append({"cbsa_code": code, "cbsa_title": title, "city_name": city, "place_fips": fips,
                     "top100_1950_rank": pd.NA, "headline": False, "note": note})
    if unmatched:
        raise ValueError(f"no CESTA city for {unmatched}; add them to {MAIN_CITY_OVERRIDES_PATH.name}")
    out = pd.DataFrame(rows).set_index("cbsa_code")
    for o in old_cities[old_cities.main_city].itertuples():
        if o.cbsa_code not in out.index:
            continue
        first = out.at[o.cbsa_code, "city_name"]
        if out.at[o.cbsa_code, "place_fips"] != o.place_fips:
            out.at[o.cbsa_code, "note"] = f"largest 1950 city; first-named is {first}"
        out.loc[o.cbsa_code, ["place_fips", "city_name", "top100_1950_rank", "headline"]] = [
            o.place_fips, label.get(o.place_fips, o.city_name), o.rank_1950, True]
    out["top100_1950_rank"] = out.top100_1950_rank.astype("Int64")
    out["headline"] = out.headline.astype(bool)
    return out.reset_index()


def first_listed_state(title: str) -> str | None:
    m = re.search(r", ([A-Z]{2})", title)
    return m.group(1) if m else None


def _read_crosswalk(path: Path, **kw) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"cbsa_code": str, "place_fips": str, "source_fips": str,
                                    "county_fips": str}, **kw)


def load_old_cities() -> pd.DataFrame:
    return _read_crosswalk(OLD_CITIES_PATH)


def load_metro_main_city() -> pd.DataFrame:
    d = _read_crosswalk(MAIN_CITY_PATH)
    return d.astype({"top100_1950_rank": "Int64", "headline": bool})


def load_main_city_overrides() -> pd.DataFrame:
    return _read_crosswalk(MAIN_CITY_OVERRIDES_PATH)


def load_place_code_changes() -> pd.DataFrame:
    return _read_crosswalk(PLACE_CODE_CHANGES_PATH)


def load_consolidations() -> pd.DataFrame:
    return _read_crosswalk(CONSOLIDATIONS_PATH)
```

  - Add `import re` to the imports.

- [ ] **Step 3: Write the committed hand tables.**

`references/crosswalks/metro_main_city_overrides.csv`:

```csv
cbsa_code,place_fips,note
11200,,"Amherst Town-Northampton, MA: Amherst has no CESTA series, so no city series"
12700,2503690,Barnstable Town: CESTA names it Barnstable
14260,1608830,Boise City: CESTA names it Boise
26140,,"Homosassa Springs, FL: a CDP not in CESTA, so no city series"
30500,,"Lexington Park, MD: a CDP not in CESTA, so no city series"
35620,3651000,New York: CESTA names it New York City
46520,1571550,"Urban Honolulu: CESTA names it Honolulu (the pre-2010 CDP, so its 2020 count is not used)"
```

`references/crosswalks/place_code_changes.csv` (each row: the value for `place_fips` in `year` sums the listed `source_fips`; checked 2026-10-19 on NHGIS AV0 and the Gazetteers):

```csv
place_fips,year,source_fips,note
1235000,1990,1235160,Jacksonville city (remainder) in the 1990 Gazetteer
1836003,1990,1836010,Indianapolis city (remainder) in the 1990 Gazetteer
2148006,1990,2148000,Louisville city before its 2003 merger with Jefferson County
2148006,2000,2148000,Louisville city before its 2003 merger with Jefferson County
2148006,2020,2148006,"Louisville 2020, part 1: the metro government (balance) without the old city"
2148006,2020,2148000,"Louisville 2020, part 2: the old city, a separate inactive place in 2020; with part 1 it equals the 2010 balance (land 263.5 + 61.5 = 325.2 sq mi)"
1349000,2020,1349008,Macon-Bibb County: Macon consolidated with Bibb County in 2014 (new code)
```

`references/crosswalks/city_county_consolidations.csv` (the headline cities; years are each consolidated government's first year):

```csv
place_fips,city,county_fips,year,source
4752006,"Nashville-Davidson, TN",47037,1963,"Metropolitan Government of Nashville and Davidson County, in effect April 1, 1963"
1235000,"Jacksonville, FL",12031,1968,"City of Jacksonville and Duval County consolidated October 1, 1968"
1836003,"Indianapolis, IN",18097,1970,"Unigov (Indianapolis and Marion County), in effect January 1, 1970"
2148006,"Louisville, KY",21111,2003,"Louisville/Jefferson County Metro Government, in effect January 6, 2003"
```

- [ ] **Step 4: Run the logic tests.** `venv/bin/python -m pytest tests/test_geography.py -v`. Expected: PASS.

- [ ] **Step 5: Build the two generated crosswalks** from the real data:

```bash
venv/bin/python -c "from us_housing_crisis_analysis import geography; geography.download()"
venv/bin/python - <<'EOF'
import pandas as pd
from us_housing_crisis_analysis import geography as geo
from us_housing_crisis_analysis.config import INTERIM_DATA_DIR
cesta = pd.read_parquet(INTERIM_DATA_DIR / "cesta.parquet")
wp27 = pd.read_parquet(INTERIM_DATA_DIR / "wp27.parquet")
cw = geo.county_to_cbsa()
pc = geo.place_cbsas(geo.parse_place_counties(), cw)
old = geo.build_old_cities(wp27, pc, set(cesta.geo_id.str.removeprefix("place:")))
old.to_csv(geo.OLD_CITIES_PATH, index=False)
main = geo.build_metro_main_city(cw, geo.cesta_names(cesta), old, geo.load_main_city_overrides())
main.to_csv(geo.MAIN_CITY_PATH, index=False)
print(len(old), old.main_city.sum(), len(main), main.headline.sum(), main.place_fips.isna().sum())
print(main[main.note.fillna("").str.contains("first-named")])
EOF
```

Expected: `100 81 387 81 3`, and one "first-named" row (Norfolk; first-named Virginia Beach). Read `old_cities_1950.csv` by eye:
- the 19 non-main cities are the spec §3.2 list;
- Arlington CDP has `in_cesta` False;
- Hartford, New Haven and Bridgeport have metros.

- [ ] **Step 6: Docs.** In `Claude/methods/geography.md`, rewrite "Secondary unit: city proper":
  - **Sources:** CESTA counts 1900–2010 (2010 place codes), NHGIS AV0 for 2020. A city's 2020 count is used only if the two sources agree in 2010 within 0.5%.
  - **Main city:** first-named city, except headline metros (1950 top 100), which take their largest 1950 city. There are 81 headline metros, and Norfolk is the exception. Puerto Rico is left out. Point to the overrides table.
  - **Place-code changes and consolidations:** the two tables.
  - **Annexing rule and bracket rule.** Land area comes from WP27 for 1950–1980 and from Gazetteers for 1990–2020.
  - **Source disagreements:** the 8 listed CESTA vs. WP27 exceptions.
  - **Central counties:** Connecticut legacy counties count as central.
  - **Open item:** the 1900–1930 county splits stay open (not needed while metro figures start in 1940).

- [ ] **Step 7: Commit.**

```bash
git add us_housing_crisis_analysis/geography.py tests/test_geography.py references/crosswalks Claude/methods/geography.md
git commit -m "Build RQ0a crosswalks: 1950 top-100 cities, each metro's main city, code changes (Plan 2 Task 3)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: The `us_city_metro` panel and its data checks

**Files:**
- Modify: `us_housing_crisis_analysis/features.py`, `tests/test_features.py`, `references/known_values.csv`, `Claude/methods/pipeline.md`
- Create: `tests/data/test_us_city_metro.py`

**Interfaces:**
- Consumes: the interim `cesta`, `nhgis`, `wp27` and `gazetteer` frames; the processed `us_metro_longrun`; `county_to_cbsa()` (with `central`); `split_decades`; the Task 3 loaders.
- Produces:
  - `features.apply_place_code_changes(places, changes) -> DataFrame[place_fips, year, value]`;
  - `features.city_population(cesta, nhgis, changes) -> DataFrame[place_fips, year, value]`;
  - `features.city_land_area(wp27, gazetteer, changes) -> DataFrame[place_fips, year, value]`;
  - `features.build_us_city_metro(cesta, nhgis, wp27, gazetteer, metro_longrun, crosswalk, main_city, old_cities, changes) -> DataFrame` with columns `CITY_METRO_COLUMNS`:
    - `geo_id`, `geo_name`, `year` (1900–2020);
    - `city_fips`, `city_name`, `headline`;
    - `city_population`, `metro_population` (1940 on), `suburb_population`, `core_population` (headline metros), `metro_central_population`;
    - `city_land_sqmi`;
    - `growth_comparable`, `central_growth_comparable` (False where a county split crosses the metro's, or the central counties', line in that decade; D-27).

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_features.py`:

```python
def places(rows, variable="population", source="x"):
    """rows: (place_fips, year, value)"""
    return long([("place:" + f, "city", y, variable, v) for f, y, v in rows], source)


CHANGES = pd.DataFrame({"place_fips": ["2148006", "2148006", "2148006"], "year": [2000, 2020, 2020],
                        "source_fips": ["2148000", "2148006", "2148000"]})


def test_place_code_changes_sum_and_relabel():
    p = pd.DataFrame({"place_fips": ["2148006", "2148000", "2148000", "2622000"],
                      "year": [2020, 2020, 2000, 2020], "value": [386_884.0, 246_161.0, 256_231.0, 639_111.0]})
    out = features.apply_place_code_changes(p, CHANGES).set_index(["place_fips", "year"]).value
    assert out[("2148006", 2020)] == 633_045  # balance + old city
    assert out[("2148006", 2000)] == 256_231  # the pre-merger city
    assert out[("2622000", 2020)] == 639_111
    assert ("2148000", 2020) not in out.index


def test_2020_count_used_only_where_2010_sources_agree():
    cesta = places([("2622000", 2010, 713_777), ("1571550", 2010, 387_170)])
    nhgis = places([("2622000", 2010, 713_777), ("2622000", 2020, 639_111),
                    ("1571550", 2010, 337_256), ("1571550", 2020, 350_964)])  # Honolulu CDP redefined
    out = features.city_population(cesta, nhgis, CHANGES.iloc[:0]).set_index(["place_fips", "year"]).value
    assert out[("2622000", 2020)] == 639_111
    assert ("1571550", 2020) not in out.index
    assert out[("1571550", 2010)] == 387_170


def test_land_area_one_source_per_year():
    wp27 = places([("2622000", 1950, 139.6), ("2622000", 1990, 138.7)], "land_area")
    gaz = places([("2622000", 1990, 138.72), ("2148000", 2000, 62.1)], "land_area")
    out = features.city_land_area(wp27, gaz, CHANGES).set_index(["place_fips", "year"]).value
    assert out[("2622000", 1950)] == 139.6 and out[("2622000", 1990)] == 138.72  # Gazetteer from 1990
    assert out[("2148006", 2000)] == 62.1


def test_city_metro_panel(tmp_path, monkeypatch):
    splits = tmp_path / "county_splits.csv"
    splits.write_text("new_fips,parent_fips,split_year,note\n08014,08013,2001,x\n")
    monkeypatch.setattr(features, "COUNTY_SPLITS_PATH", splits)
    cw = pd.DataFrame({"county_fips": ["08031", "08013", "08014"], "cbsa_code": ["19740"] * 3,
                       "cbsa_title": ["Denver, CO"] * 3, "area_type": ["metro"] * 3,
                       "central": [True, True, False]})
    main = pd.DataFrame({"cbsa_code": ["19740"], "cbsa_title": ["Denver, CO"], "city_name": ["Denver, CO"],
                         "place_fips": ["0820000"], "top100_1950_rank": [24], "headline": [True], "note": [""]})
    old = pd.DataFrame({"rank_1950": [24, 90], "place_fips": ["0820000", "0804000"], "city_name": ["a", "b"],
                        "population_1950": [1.0, 1.0], "cbsa_code": ["19740", "19740"],
                        "main_city": [True, False], "in_cesta": [True, True]})
    cesta = places([("0820000", 1950, 400), ("0820000", 1990, 450), ("0820000", 2010, 600),
                    ("0804000", 1950, 50)])  # the second old city has no 1990 count
    nhgis = places([("0820000", 2010, 600), ("0820000", 2020, 700)])
    nhgis = pd.concat([nhgis, long([("county:08031", "county", y, "population", 1000) for y in (1950, 1990, 2000)]
                                   + [("county:08013", "county", y, "population", 500) for y in (1950, 1990, 2000)], "nhgis")])
    metro = pd.DataFrame({"geo_id": "cbsa:19740", "geo_name": "Denver, CO", "year": [1930, 1950, 1990, 2000],
                          "population": [900.0, 1500.0, 1600.0, 1700.0]})
    area = places([("0820000", 1950, 66.8)], "land_area")
    gaz = places([("0820000", 1990, 153.3)], "land_area")
    p = features.build_us_city_metro(cesta, nhgis, area, gaz, metro, cw, main, old, CHANGES.iloc[:0])
    p = p.set_index("year")
    assert list(p.columns) == [c for c in features.CITY_METRO_COLUMNS if c != "year"]
    assert np.isnan(p.loc[1930, "metro_population"])  # metro figures start in 1940
    assert p.loc[1950, "suburb_population"] == 1100
    assert p.loc[1950, "core_population"] == 450
    assert np.isnan(p.loc[1990, "core_population"])  # an old city is missing that year
    assert p.loc[1990, "metro_central_population"] == 1500  # Denver + Boulder, not the outlying county
    assert p.loc[2020, "city_population"] == 700
    assert p.loc[1990, "city_land_sqmi"] == 153.3
    assert not p.loc[2000, "central_growth_comparable"] and p.loc[1990, "growth_comparable"]
    assert p.headline.all() and set(p.city_fips) == {"0820000"}
```

Run: `venv/bin/python -m pytest tests/test_features.py -v`. Expected: the four new tests FAIL.

- [ ] **Step 2: Implement in `features.py`.**
  - Extend the config import with `RQ0A_CITY_START, RQ0A_METRO_START, RQ0A_OVERLAP_TOLERANCE`.
  - Add to the geography import: `load_metro_main_city, load_old_cities, load_place_code_changes`.
  - Add before `@app.command()`:

```python
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
    m = m[~pd.Series(own, index=m.index)]
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
    dropped = sorted(set(a.loc[a.year == 2020, "place_fips"]) & set(c10.index) - agree)
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
    """Metro x decade (spec 2026-10-18 §2): the main city, the metro (from 1940), the suburbs
    (metro - city), the core (all the metro's 1950 top-100 cities with a CESTA series; missing if
    any of them is), the metro's central counties, and the city's land area."""
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
```

  - In `main()`:
    - Read the extra sources: `cesta, wp27, gaz = (read(s) for s in ("cesta", "wp27", "gazetteer"))`.
    - After the `panels` dict is built, add:

```python
    panels["us_city_metro"] = build_us_city_metro(
        cesta, nhgis, wp27, gaz, panels["us_metro_longrun"], county_to_cbsa(), load_metro_main_city(),
        load_old_cities(), load_place_code_changes())
```

- [ ] **Step 3: Run the logic tests.** `venv/bin/python -m pytest tests/test_features.py -v`. Expected: PASS. If the panel test's metro or county frames don't match the implementation's column names, fix the implementation.

- [ ] **Step 4: Build the panel.** `make features`. Expected: `us_city_metro: 5,031 rows, 387 units` (387 metros × 13 decades).

- [ ] **Step 5: Known values.** Append to `references/known_values.csv`:

```csv
us_city_metro,cbsa:19820,1950,city_population,1849568,0,"Detroit city 1950: CESTA and Working Paper 27 table 18 agree"
us_city_metro,cbsa:26420,1950,city_land_sqmi,160.0,0.001,"Houston land area 1950, Working Paper 27 table 18"
us_city_metro,cbsa:26420,1990,city_land_sqmi,539.9,0.005,"Houston land area 1990, WP27 table 22; the panel's 1990 area is the 1990 Gazetteer (within 0.22% of WP27 for every top-100 place)"
us_city_metro,cbsa:31140,2020,city_population,633045,0,"Louisville 2020 = NHGIS AV0 balance 386,884 + old-city place 246,161 (place_code_changes.csv)"
```

- [ ] **Step 6: Write the data tests.** Create `tests/data/test_us_city_metro.py`:

```python
import pandas as pd
import pytest

from us_housing_crisis_analysis import features, geography
from us_housing_crisis_analysis.config import RAW_DATA_DIR, RQ0A_OVERLAP_TOLERANCE

pytestmark = pytest.mark.data

# Headline cities where CESTA and Working Paper 27 differ by more than 0.5% (found 2026-10-19;
# CESTA stays the population source). Jacksonville 1970: WP27 has all of Duval County.
CESTA_WP27_EXCEPTIONS = {
    ("0150000", 1960), ("1235000", 1970), ("4159000", 1970), ("0664000", 1970), ("4805000", 1970),
    ("3988000", 1970), ("2270000", 1980), ("3921000", 1980),
}
# CBSA codes of the featured US metros (master spec §2)
FEATURED = {"35620", "31080", "14460", "41860", "47900", "12580", "40060", "26420", "12420"}
# Main cities the 2020 place-to-county file can't place in their own metro: Waterbury (old CT county
# maps to New Haven), Macon (its 2010 code was replaced in 2014)
NOT_PLACED = {"0980000", "1349000"}


def headline(processed):
    p = processed("us_city_metro")
    return p[p.headline]


def headline_fips(processed):
    return set(headline(processed).city_fips)


def test_headline_metros(processed):
    h = headline(processed)
    assert h.geo_id.nunique() == 81
    assert h.groupby("geo_id").city_fips.nunique().eq(1).all() and h.city_fips.notna().all()
    assert FEATURED <= set(h.geo_id.str.removeprefix("cbsa:"))


def test_headline_cities_have_every_count_and_area(processed):
    h = headline(processed)
    assert h.city_population.notna().all(), h[h.city_population.isna()][["geo_name", "year"]]
    for y in (1950, 1990, 2000, 2010, 2020):
        assert h[h.year == y].city_land_sqmi.notna().all(), (y, h[(h.year == y) & h.city_land_sqmi.isna()].geo_name)


def test_city_never_exceeds_metro(processed):
    p = processed("us_city_metro").dropna(subset=["city_population", "metro_population"])
    bad = p[p.city_population > p.metro_population]
    assert bad.empty, bad[["geo_name", "year", "city_population", "metro_population"]]
    c = p.dropna(subset=["core_population"])
    assert (c.core_population <= c.metro_population).all() and (c.core_population >= c.city_population).all()


def test_cesta_matches_nhgis_2010_for_headline_cities(interim, processed):
    fips = headline_fips(processed)
    c = interim("cesta").query("year == 2010").set_index("geo_id").value
    n = interim("nhgis").query("geo_level == 'city' and year == 2010").set_index("geo_id").value
    ids = ["place:" + f for f in fips]
    rel = (n.reindex(ids) / c.reindex(ids) - 1).abs()
    assert (rel <= RQ0A_OVERLAP_TOLERANCE).all(), rel[~(rel <= RQ0A_OVERLAP_TOLERANCE)]


def test_cesta_vs_wp27_only_known_exceptions(interim, processed):
    fips = headline_fips(processed)
    c = interim("cesta").set_index(["geo_id", "year"]).value
    w = interim("wp27").query("variable == 'population'")
    w = w[w.geo_id.str.removeprefix("place:").isin(fips)]
    rel = (c.reindex(list(zip(w.geo_id, w.year))).to_numpy() / w.value.to_numpy()) - 1
    off = {(g.removeprefix("place:"), y) for g, y, r in zip(w.geo_id, w.year, rel) if abs(r) > 0.005}
    assert off == CESTA_WP27_EXCEPTIONS


def test_wp27_1990_area_matches_gazetteer_1990(interim):
    w = interim("wp27").query("variable == 'land_area' and year == 1990")
    g = interim("gazetteer").query("year == 1990")
    pw = features._places(w, "land_area", [1990])
    pg = features.apply_place_code_changes(features._places(g, "land_area", [1990]), geography.load_place_code_changes())
    m = pw.merge(pg, on=["place_fips", "year"], suffixes=("_wp27", "_gaz"))
    assert len(m) >= 95
    assert ((m.value_gaz / m.value_wp27 - 1).abs() < 0.005).all()


def test_us_totals_50_states_and_dc(processed):
    s = processed("us_state_longrun")
    s = s[s.geo_id.str.removeprefix("state:").isin(set(geography.state_divisions().index))]
    t = s.groupby("year").population.sum()
    for year, total in {1950: 151.326e6, 1970: 203.212e6, 1990: 248.710e6, 2020: 331.449e6}.items():
        assert t[year] == pytest.approx(total, rel=1e-4)


def test_crosswalks_rebuild_to_the_committed_files(interim):
    path = RAW_DATA_DIR / "geography" / "national_place_by_county2020.txt"
    if not path.exists():
        pytest.skip("place-to-county file not downloaded")
    cesta, wp27 = interim("cesta"), interim("wp27")
    cw = geography.county_to_cbsa()
    pc = geography.place_cbsas(geography.parse_place_counties(path), cw)
    old = geography.build_old_cities(wp27, pc, set(cesta.geo_id.str.removeprefix("place:")))
    pd.testing.assert_frame_equal(old, geography.load_old_cities(), check_dtype=False)
    main = geography.build_metro_main_city(cw, geography.cesta_names(cesta), old, geography.load_main_city_overrides())
    pd.testing.assert_frame_equal(main.fillna({"note": ""}), geography.load_metro_main_city().fillna({"note": ""}),
                                  check_dtype=False)
    # every main city lies in its metro, except the two the 2020 file can't place
    pairs = set(zip(pc.place_fips, pc.cbsa_code))
    misplaced = {f for f, c in zip(main.place_fips, main.cbsa_code) if pd.notna(f) and (f, c) not in pairs}
    assert misplaced == NOT_PLACED


def test_annexing_unknowns_stay_within_the_spec_limit(processed):
    # Spec §3.4: more than 5 unknown headline cities in a period would call for ICPSR 7735
    from us_housing_crisis_analysis.modeling import city_metro as cm
    from us_housing_crisis_analysis.config import RQ0A_PERIODS
    h = headline(processed)
    for start, end in RQ0A_PERIODS:
        flags = cm.annexing_by_metro(h, start, end, consolidations=geography.load_consolidations())
        assert (flags == "unknown").sum() <= 5, (start, flags[flags == "unknown"])
```

The last test needs `annexing_by_metro` from Task 5. Until then it fails, so run it at the end of Task 5.

- [ ] **Step 7: Run.** `venv/bin/python -m pytest tests/data/test_us_city_metro.py tests/data/test_us_longrun.py -v -k "not annexing"`. Expected: all pass. Report a failure instead of loosening a test; the counts above come from the real files.

- [ ] **Step 8: Docs.** In `Claude/methods/pipeline.md`:
  - Add a row to "Processed panels": `us_city_metro` | metro (2023 CBSA, Puerto Rico left out) × decade, 1900–2020 | RQ0a. Describe the columns as in this task's Interfaces.
  - Add the new sources to the data-flow text.

- [ ] **Step 9: Commit.**

```bash
git add us_housing_crisis_analysis/features.py tests/test_features.py tests/data/test_us_city_metro.py references/known_values.csv Claude/methods/pipeline.md
git commit -m "Build the us_city_metro panel with its data checks (Plan 2 Task 4)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Growth, classes and annexing flags (`modeling/city_metro.py`, part 1)

**Files:**
- Create: `us_housing_crisis_analysis/modeling/city_metro.py`, `tests/test_city_metro.py`

**Interfaces:**
- Consumes: the `us_city_metro` panel columns; `geography.first_listed_state_fips`, `geography.state_divisions`.
- Produces:
  - `us_growth(state_longrun, states, periods=RQ0A_PERIODS) -> dict[(start, end), float]`
  - `keep_up_bar(start, end, yardstick, us, fraction=RQ0A_BAR_FRACTION) -> float`
  - `keeps_up(growth, bar) -> Series` (1.0 / 0.0 / NaN)
  - `period_growth(panel, periods=RQ0A_PERIODS, central=False) -> DataFrame[geo_id, city, metro, suburb, core, start, end]`
  - `classify(growth, us, yardstick="relative", fraction=RQ0A_BAR_FRACTION, city_col="city") -> DataFrame` (+ `city_keeps`, `metro_keeps`, `class`)
  - `core_recovery(classes) -> Series[bool]`
  - `annexing(area, start, end, threshold=RQ0A_ANNEX_THRESHOLD, consolidations=None) -> Series` ("annexing" / "fixed" / "unknown", indexed by place code)
  - `annexing_by_metro(panel, start, end, threshold=..., consolidations=None) -> Series` (by `geo_id`)
  - `regions(panel) -> Series` (`geo_id` → "Northeast + Midwest" / "South + West")
  - `units(panel, us, *, yardstick="relative", fraction=..., threshold=..., core=False, central=False, consolidations=None, periods=RQ0A_PERIODS) -> DataFrame`, one row per headline metro: `geo_id`, `city_<start>`, `metro_<start>`, `annex_<start>` for each period, `city_pop_1950`, `region`.

- [ ] **Step 1: Write the failing tests.** Create `tests/test_city_metro.py`:

```python
import numpy as np
import pandas as pd
import pytest

from us_housing_crisis_analysis.modeling import city_metro as cm

US = {(1950, 1970): 0.343, (1970, 1990): 0.224, (1990, 2020): 0.333}


def test_us_growth_uses_listed_states_only():
    s = pd.DataFrame({"geo_id": ["state:01", "state:72", "state:01", "state:72"], "year": [1950, 1950, 1970, 1970],
                      "population": [100.0, 50.0, 150.0, 999.0]})
    assert cm.us_growth(s, ["01"], [(1950, 1970)]) == {(1950, 1970): pytest.approx(0.5)}


def test_bars():
    assert cm.keep_up_bar(1950, 1970, "relative", US) == pytest.approx(0.1715)
    assert cm.keep_up_bar(1990, 2020, "absolute", US) == pytest.approx(0.157625)
    assert cm.keep_up_bar(1950, 1970, "relative", US, fraction=1 / 3) == pytest.approx(0.343 / 3)
    with pytest.raises(ValueError):
        cm.keep_up_bar(1950, 1970, "other", US)


def test_keeps_up_at_the_bar_and_missing():
    g = pd.Series([1.1 / 1.0 - 1, 0.0999, np.nan])  # 0.10000000000000009, just below, missing
    out = cm.keeps_up(g, 0.1)
    assert out.iloc[0] == 1.0 and out.iloc[1] == 0.0 and np.isnan(out.iloc[2])
    assert cm.keeps_up(pd.Series([0.30000000000000004 - 1e-12]), 0.3).iloc[0] == 1.0


def panel_rows(geo, city, metro, core=None, comparable=None, years=(1950, 1970, 1990, 2020), headline=True,
               fips="x", area=None):
    core = core or [np.nan] * len(years)
    comparable = comparable or [True] * len(years)
    area = area or [np.nan] * len(years)
    return pd.DataFrame({"geo_id": geo, "geo_name": f"{geo}, OH", "year": list(years), "city_fips": fips,
                         "headline": headline, "city_population": city, "metro_population": metro,
                         "core_population": core, "metro_central_population": [m / 2 for m in metro],
                         "city_land_sqmi": area, "growth_comparable": comparable,
                         "central_growth_comparable": [True] * len(years)})


def test_period_growth_and_the_d27_flag():
    p = panel_rows("cbsa:1", [100, 90, 90, 120], [200, 300, 300, 450], comparable=[True, True, False, True])
    g = cm.period_growth(p).set_index("start")
    assert g.loc[1950, "city"] == pytest.approx(-0.1) and g.loc[1950, "metro"] == pytest.approx(0.5)
    assert g.loc[1950, "suburb"] == pytest.approx(210 / 100 - 1)
    assert np.isnan(g.loc[1990, "metro"]) and np.isnan(g.loc[1990, "suburb"])  # split in the 1990s
    assert g.loc[1990, "city"] == pytest.approx(120 / 90 - 1)  # city growth kept
    c = cm.period_growth(p, central=True).set_index("start")
    assert c.loc[1950, "metro"] == pytest.approx(0.5)  # central counties: half the metro here


def test_four_classes_and_core_recovery():
    g = pd.DataFrame({"geo_id": ["a", "b", "c", "d", "a", "b"], "start": [1950] * 4 + [1970] * 2,
                      "end": [1970] * 4 + [1990] * 2, "city": [0.3, -0.1, -0.1, 0.3, 0.2, np.nan],
                      "metro": [0.3, 0.3, 0.0, 0.0, 0.2, 0.2]})
    c = cm.classify(g, US)
    assert c["class"].iloc[:4].tolist() == ["growing", "suburbanizing", "stagnant", "city-led"]
    assert pd.isna(c["class"].iloc[5])  # city missing -> no class
    g2 = pd.DataFrame({"geo_id": ["b", "b", "b"], "start": [1950, 1970, 1990], "end": [1970, 1990, 2020],
                       "city": [-0.1, 0.3, 0.3], "metro": [0.3, 0.3, 0.3]})
    rec = cm.core_recovery(cm.classify(g2, US))
    assert rec.tolist() == [False, True, True]


def area(rows):
    """rows: {place: {year: sq mi}}"""
    return pd.DataFrame(rows).T


def test_annexing_exact_threshold_and_consolidation():
    a = area({"up": {1950: 100, 1970: 125}, "flat": {1950: 100, 1970: 120}, "cons": {1950: 22, 1970: 22}})
    cons = pd.DataFrame({"place_fips": ["cons"], "year": [1963]})
    f = cm.annexing(a, 1950, 1970, consolidations=cons)
    assert f.to_dict() == {"up": "annexing", "flat": "fixed", "cons": "annexing"}
    assert cm.annexing(a, 1950, 1970, threshold=0.1)["flat"] == "annexing"


def test_annexing_bracket_rule():
    a = area({"small": {1950: 100, 2000: 105}, "big": {1950: 100, 2000: 300}, "none": {1950: 100}})
    f = cm.annexing(a, 1950, 1970)
    assert f["small"] == "fixed"  # at most +5% over 1950-2000, so not more than 20% in 1950-70
    assert f["big"] == "unknown"  # the gain could fall outside 1950-70
    assert f["none"] == "unknown"


def test_units_frame():
    p = pd.concat([
        panel_rows("cbsa:1", [100, 90, 90, 120], [200, 300, 300, 450], core=[150, 140, 140, 160], fips="p1",
                   area=[50, 50, 50, 50]),
        panel_rows("cbsa:2", [100, 200, 220, 300], [150, 250, 260, 400], fips="p2", area=[30, 90, np.nan, 200]),
        panel_rows("cbsa:3", [1, 1, 1, 1], [9, 9, 9, 9], headline=False),
    ])
    u = cm.units(p, US).set_index("geo_id")
    assert list(u.index) == ["cbsa:1", "cbsa:2"]
    assert u.loc["cbsa:1", "city_1950"] == 0 and u.loc["cbsa:1", "metro_1950"] == 1
    assert u.loc["cbsa:1", "annex_1950"] == "fixed" and u.loc["cbsa:2", "annex_1950"] == "annexing"
    assert u.loc["cbsa:2", "annex_1970"] == "unknown"  # 1990 area missing, 1970-2020 gain over 20%
    assert u.loc["cbsa:1", "city_pop_1950"] == 100 and u.loc["cbsa:1", "region"] == "Northeast + Midwest"
    assert cm.units(p, US, core=True).set_index("geo_id").loc["cbsa:1", "city_1950"] == 0  # 150 -> 140


def test_regions():
    p = pd.DataFrame({"geo_id": ["cbsa:1", "cbsa:2"], "geo_name": ["Detroit, MI", "Houston, TX"]})
    assert cm.regions(p).to_dict() == {"cbsa:1": "Northeast + Midwest", "cbsa:2": "South + West"}
```

Run: `venv/bin/python -m pytest tests/test_city_metro.py -v`. Expected: FAIL (no module).

- [ ] **Step 2: Implement `us_housing_crisis_analysis/modeling/city_metro.py` (part 1).**

```python
"""RQ0a (Plan 2): did US cities stall, or did their metros? Growth by period, keep-up classes,
annexing flags, and the three preset answers with unit-resampling ranges (spec 2026-10-18 §4).
Class names describe growth patterns, not moves (D-29)."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from us_housing_crisis_analysis.config import (
    RQ0A_ABSOLUTE_RATE, RQ0A_ANNEX_THRESHOLD, RQ0A_BAR_FRACTION, RQ0A_MIN_GROUP, RQ0A_PERIODS,
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
```

`RQ0A_MIN_GROUP` and `dataclass` are used in Task 6. If ruff flags them as unused before then, leave them; Task 6 uses them.

- [ ] **Step 3: Run.**

```bash
venv/bin/python -m pytest tests/test_city_metro.py -v
venv/bin/python -m pytest tests/data/test_us_city_metro.py -v -k annexing
```

Expected: PASS. The data test shows at most 5 unknowns per period.

- [ ] **Step 4: Commit.**

```bash
git add us_housing_crisis_analysis/modeling/city_metro.py tests/test_city_metro.py
git commit -m "RQ0a growth, keep-up classes and annexing flags (Plan 2 Task 5)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Ranges and the three preset rules (`modeling/city_metro.py`, part 2)

**Files:**
- Modify: `us_housing_crisis_analysis/modeling/city_metro.py`, `tests/test_city_metro.py`

**Interfaces:**
- Consumes: the `units()` frame from Task 5.
- Produces:
  - `Range(estimate, low, high, skipped)` (frozen dataclass)
  - `paired_draws(u, stat, draws=999, level=0.90, seed=0) -> Range`
  - `share_metro_kept_up(u, start=1950, weight=None) -> float` (rule 1's S)
  - `rule2_groups(u, start=1950, conditioned=True) -> tuple[int, int]` (fixed, annexing)
  - `fall_behind_gap(u, start=1950, conditioned=True) -> float` (rule 2's D)
  - `fall_behind_share(u, start) -> float` (F)
  - `fall_behind_rise(u, later, first=1950) -> float` (F_later − F_first on metros classed in both)
  - `decide_rule1(low, high) -> str`
  - `decide_rule2(low, high, n_fixed, n_annexing, min_group=RQ0A_MIN_GROUP) -> str`
  - `decide_rule3(rise2: Range, rise3: Range) -> str`
  - `robustness(main: str, checks: dict[str, str]) -> str`

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_city_metro.py`:

```python
def u_frame(city50, metro50, annex50=None, metro70=None, metro90=None, pop=None):
    n = len(city50)
    return pd.DataFrame({"geo_id": [f"m{i}" for i in range(n)], "city_1950": city50, "metro_1950": metro50,
                         "annex_1950": annex50 or ["fixed"] * n, "metro_1970": metro70 or metro50,
                         "metro_1990": metro90 or metro50, "city_pop_1950": pop or [1.0] * n})


def test_share_metro_kept_up_plain_and_weighted():
    u = u_frame([0, 0, 0, 1], [1, 1, 0, 1], pop=[1, 1, 2, 9])
    assert cm.share_metro_kept_up(u) == pytest.approx(2 / 3)
    assert cm.share_metro_kept_up(u, weight="city_pop_1950") == pytest.approx(0.5)
    assert np.isnan(cm.share_metro_kept_up(u_frame([1, 1], [1, 1])))  # no plateau city


def test_fall_behind_gap_conditions_on_metros_that_kept_up():
    u = u_frame([0, 0, 1, 1, 0], [1, 1, 1, 1, 0], annex50=["fixed", "annexing", "annexing", "fixed", "annexing"])
    # kept-up metros: fixed {0, 1} -> 1/2 fell behind; annexing {0, 1} -> 1/2 -> D = 0
    assert cm.fall_behind_gap(u) == pytest.approx(0.0)
    assert cm.rule2_groups(u) == (2, 2)
    # unconditioned adds the stagnant-metro annexing city that fell behind
    assert cm.fall_behind_gap(u, conditioned=False) == pytest.approx(0.5 - 2 / 3)
    assert np.isnan(cm.fall_behind_gap(u_frame([0, 1], [1, 1])))  # no annexing city


def test_fall_behind_rise_pairs_metros_classed_in_both_periods():
    u = u_frame([0] * 4, [1, 1, 1, 0], metro90=[0, 0, np.nan, np.nan])
    # pairs for 1990: m0, m1 (kept up, then fell behind) -> 1.0 - 0.0
    assert cm.fall_behind_rise(u, 1990) == pytest.approx(1.0)
    assert cm.fall_behind_share(u, 1950) == pytest.approx(0.25)


def test_paired_draws_keep_metros_together_and_count_skips():
    u = u_frame([0] * 30, [1, 0] * 15, metro70=[1, 0] * 15)
    r = cm.paired_draws(u, lambda d: cm.fall_behind_rise(d, 1970))
    assert r.low == 0 and r.high == 0 and r.skipped == 0  # same metros in both periods
    rare = u_frame([0] + [1] * 39, [1] * 40)  # one plateau city: many draws have none
    r = cm.paired_draws(rare, cm.share_metro_kept_up)
    assert r.skipped > 0 and r.low == r.high == 1.0
    assert cm.paired_draws(rare, cm.share_metro_kept_up) == r  # seeded


def test_rule1_outcomes_and_boundaries():
    assert cm.decide_rule1(2 / 3, 0.9) == "mostly suburbanization"
    assert cm.decide_rule1(0.1, 1 / 3) == "mostly metro stagnation"
    assert cm.decide_rule1(0.4, 0.6) == "mixed"
    assert cm.decide_rule1(1 / 3, 0.6) == "can't tell"  # mixed needs low above 1/3
    assert cm.decide_rule1(0.5, 0.8) == "can't tell"
    assert cm.decide_rule1(np.nan, np.nan) == "can't tell"


def test_rule2_outcomes():
    assert cm.decide_rule2(0.1, 0.5, 14, 30) == "not testable"
    assert cm.decide_rule2(0.1, 0.5, 15, 15) == "plateau concentrated in fixed-boundary cities"
    assert cm.decide_rule2(-0.4, 0.0, 20, 20) == "not a boundary effect"
    assert cm.decide_rule2(0.0, 0.3, 20, 20) == "can't tell"


def test_rule3_outcomes():
    R = cm.Range
    assert cm.decide_rule3(R(0.2, 0.05, 0.3, 0), R(0.3, 0.1, 0.5, 0)) == "later, by 1970–90"
    assert cm.decide_rule3(R(0.1, -0.05, 0.3, 0), R(0.3, 0.1, 0.5, 0)) == "later, only after 1990"
    assert cm.decide_rule3(R(-0.1, -0.3, 0.0, 0), R(-0.1, -0.2, -0.01, 0)) == "not later"
    assert cm.decide_rule3(R(0.0, -0.1, 0.1, 0), R(-0.1, -0.2, -0.01, 0)) == "can't tell"


def test_robustness_names_disagreeing_checks():
    assert cm.robustness("mixed", {"a": "mixed", "b": "mixed"}) == "robust"
    assert cm.robustness("mixed", {"a": "can't tell", "b": "mixed", "c": "x"}) == "fragile: a; c"
```

Run: `venv/bin/python -m pytest tests/test_city_metro.py -v`. Expected: the new tests FAIL.

- [ ] **Step 2: Implement.** Append to `modeling/city_metro.py`:

```python
@dataclass(frozen=True)
class Range:
    estimate: float
    low: float
    high: float
    skipped: int  # draws where the statistic was undefined (an empty group)


def paired_draws(u: pd.DataFrame, stat, draws: int = 999, level: float = 0.90, seed: int = 0) -> Range:
    """The middle `level` of `stat` over draws that resample headline metros (rows of `u`) with
    replacement. A row carries every period, so a draw keeps the same metros in all periods, and
    two statistics computed with the same seed use the same draws. Draws where `stat` is NaN are
    skipped and counted."""
    rng = np.random.default_rng(seed)
    n = len(u)
    vals = np.array([stat(u.iloc[rng.integers(0, n, n)]) for _ in range(draws)], dtype=float)
    ok = vals[~np.isnan(vals)]
    a = (1 - level) / 2
    low, high = (np.quantile(ok, a), np.quantile(ok, 1 - a)) if len(ok) else (np.nan, np.nan)
    return Range(float(stat(u)), float(low), float(high), int(np.isnan(vals).sum()))


def share_metro_kept_up(u: pd.DataFrame, start: int = 1950, weight: str | None = None) -> float:
    """Rule 1's S: among cities that fell behind in the period ("plateau cities") with a metro
    class, the share whose metro kept up (optionally weighted, e.g. by 1950 city population)."""
    m = (u[f"city_{start}"] == 0) & u[f"metro_{start}"].notna()
    if not m.any():
        return np.nan
    k = u.loc[m, f"metro_{start}"]
    if weight is None:
        return float(k.mean())
    w = u.loc[m, weight]
    return float((k * w).sum() / w.sum())


def _rule2_rows(u: pd.DataFrame, start: int, conditioned: bool) -> pd.DataFrame:
    m = u[f"city_{start}"].notna() & u[f"annex_{start}"].isin(["fixed", "annexing"])
    if conditioned:
        m &= u[f"metro_{start}"] == 1
    return u[m]


def rule2_groups(u: pd.DataFrame, start: int = 1950, conditioned: bool = True) -> tuple[int, int]:
    """(fixed-boundary, annexing) city counts in rule 2's comparison."""
    v = _rule2_rows(u, start, conditioned)[f"annex_{start}"]
    return int((v == "fixed").sum()), int((v == "annexing").sum())


def fall_behind_gap(u: pd.DataFrame, start: int = 1950, conditioned: bool = True) -> float:
    """Rule 2's D: fall-behind share of fixed-boundary cities minus that of annexing cities, among
    metros that kept up (conditioned) or all metros. NaN if either group is empty."""
    v = _rule2_rows(u, start, conditioned)
    behind = 1 - v[f"city_{start}"]
    fixed, annexing_ = behind[v[f"annex_{start}"] == "fixed"], behind[v[f"annex_{start}"] == "annexing"]
    if fixed.empty or annexing_.empty:
        return np.nan
    return float(fixed.mean() - annexing_.mean())


def fall_behind_share(u: pd.DataFrame, start: int) -> float:
    """F: the share of metros with a class in the period that fell behind."""
    k = u[f"metro_{start}"].dropna()
    return float(1 - k.mean()) if len(k) else np.nan


def fall_behind_rise(u: pd.DataFrame, later: int, first: int = 1950) -> float:
    """Rule 3: F(later) - F(first) over metros classed in both periods."""
    v = u[u[f"metro_{first}"].notna() & u[f"metro_{later}"].notna()]
    if v.empty:
        return np.nan
    return float(v[f"metro_{first}"].mean() - v[f"metro_{later}"].mean())


def decide_rule1(low: float, high: float) -> str:
    """Spec §4.3, rule 1, fixed before any class was computed."""
    if low >= 2 / 3 - EPS:
        return "mostly suburbanization"
    if high <= 1 / 3 + EPS:
        return "mostly metro stagnation"
    if low > 1 / 3 + EPS and high < 2 / 3 - EPS:
        return "mixed"
    return "can't tell"


def decide_rule2(low: float, high: float, n_fixed: int, n_annexing: int,
                 min_group: int = RQ0A_MIN_GROUP) -> str:
    """Spec §4.3, rule 2. The group-size floor is checked on the actual data first."""
    if min(n_fixed, n_annexing) < min_group:
        return "not testable"
    if low > 0:
        return "plateau concentrated in fixed-boundary cities"
    if high <= 0:
        return "not a boundary effect"
    return "can't tell"


def decide_rule3(rise2: Range, rise3: Range) -> str:
    """Spec §4.3, rule 3: the first period clearly above 1950-70 (F1, F2, F3 are always printed, so
    a steady rise reads as gradual)."""
    if rise2.low > 0:
        return "later, by 1970–90"
    if rise3.low > 0:
        return "later, only after 1990"
    if rise2.high <= 0 and rise3.high <= 0:
        return "not later"
    return "can't tell"


def robustness(main: str, checks: dict[str, str]) -> str:
    """'robust', or 'fragile: ' and the checks whose answer differs from the main one (spec §4.4)."""
    differ = [name for name, answer in checks.items() if answer != main]
    return "fragile: " + "; ".join(differ) if differ else "robust"
```

  - `fall_behind_rise` computes (1 − later) − (1 − first) = first − later on the keep-up means.
  - The `decide_*` functions compare NaN as False, so an all-skipped range gives "can't tell". (Rule 2 checks "not testable" first.)

- [ ] **Step 3: Run.**

```bash
venv/bin/python -m pytest tests/test_city_metro.py -v
make test-fast
venv/bin/python -m ruff check us_housing_crisis_analysis
```

Expected: all pass; ruff clean.

- [ ] **Step 4: Commit.**

```bash
git add us_housing_crisis_analysis/modeling/city_metro.py tests/test_city_metro.py
git commit -m "RQ0a resampling ranges and the three preset decision rules (Plan 2 Task 6)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Notebook 1.0, outputs, finding and docs

**Files:**
- Create: `notebooks/1.0-lr-city-vs-metro.ipynb` (via a percent script), `reports/figures/rq0a_city_share.png`, `reports/figures/rq0a_classes.png`, `reports/tables/rq0a_classes.csv`, `reports/tables/rq0a_answers.csv`
- Modify: `Claude/methods/analysis-methods.md`, `Claude/methods/decisions.md`, `docs/superpowers/specs/2026-10-08-housing-growth-mismatch-design.md`, `docs/superpowers/specs/2026-10-18-rq0a-city-vs-metro-design.md`

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `rq0a_answers.csv`: `rule, version, estimate, low, high, n, answer, detail`;
  - `rq0a_classes.csv`: `cbsa_code, city, headline, period, city_growth, metro_growth, suburb_growth, yardstick, class, annexing, core_recovery`.

- [ ] **Step 1: Write the notebook as a percent script** at `notebooks/1.0-lr-city-vs-metro.py`:

```python
# %% [markdown]
# # RQ0a: did US cities stall, or did their metros? (Plan 2)
#
# Spec: `docs/superpowers/specs/2026-10-18-rq0a-city-vs-metro-design.md`. Each headline metro (one
# holding a 1950 top-100 city; "the city" is its largest 1950 city) is classed in 1950–70, 1970–90
# and 1990–2020 by whether its city and its metro kept up with US population growth (main bar:
# half the US rate). Three questions get answers from rules fixed before anything was computed
# (spec §4.3); every answer has a 90% range from resampling headline metros (999 draws, seed 0)
# and is "fragile" if a check that applies to it disagrees. Findings describe population, not
# moves (D-29).

# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from us_housing_crisis_analysis import geography
from us_housing_crisis_analysis.config import PROCESSED_DATA_DIR, RQ0A_PERIODS, TABLES_DIR
from us_housing_crisis_analysis.modeling import city_metro as cm
from us_housing_crisis_analysis.plots import MUTED, SERIES_COLORS, apply_style, save_figure

apply_style()
panel = pd.read_parquet(PROCESSED_DATA_DIR / "us_city_metro.parquet")
states = pd.read_parquet(PROCESSED_DATA_DIR / "us_state_longrun.parquet")
consolidations = geography.load_consolidations()
US = cm.us_growth(states, geography.state_divisions().index)
label = {s: f"{s}–{e}" for s, e in RQ0A_PERIODS}
head = panel[panel.headline]
print(f"{head.geo_id.nunique()} headline metros; US growth by period:",
      {label[s]: f"{g:+.1%}" for (s, e), g in US.items()})

# %% [markdown]
# ## Background: cities 1900–1950, metros in the 1940s (described, not classed)

# %%
bg = head[head.year <= 1950].pivot(index="geo_id", columns="year", values="city_population")
city_decades = (bg.shift(-1, axis=1) / bg - 1).iloc[:, :-1].median().rename("median city growth")
metro40 = head.pivot(index="geo_id", columns="year", values="metro_population")
print("Median headline-city growth by decade:", city_decades.map("{:+.1%}".format).to_dict())
print(f"Median headline-metro growth 1940–50: {(metro40[1950] / metro40[1940] - 1).median():+.1%}")

# %% [markdown]
# ## Classes by period, both yardsticks

# %%
growth = cm.period_growth(panel)
annex = pd.concat([cm.annexing_by_metro(panel, s, e, consolidations=consolidations).rename(s)
                   for s, e in RQ0A_PERIODS], axis=1)
rows = []
for yardstick in ("relative", "absolute"):
    c = cm.classify(growth, US, yardstick)
    c["core_recovery"] = cm.core_recovery(c)
    rows.append(c.assign(yardstick=yardstick))
classes = pd.concat(rows, ignore_index=True)
classes["annexing"] = [annex.at[g, s] for g, s in zip(classes.geo_id, classes.start)]
meta = panel.drop_duplicates("geo_id").set_index("geo_id")
out = pd.DataFrame({
    "cbsa_code": classes.geo_id.str.removeprefix("cbsa:"), "city": classes.geo_id.map(meta.city_name),
    "headline": classes.geo_id.map(meta.headline), "period": classes.start.map(label),
    "city_growth": classes.city, "metro_growth": classes.metro, "suburb_growth": classes.suburb,
    "yardstick": classes.yardstick, "class": classes["class"], "annexing": classes.annexing,
    "core_recovery": classes.core_recovery})
out.to_csv(TABLES_DIR / "rq0a_classes.csv", index=False)
hc = out[out.headline]
shares = hc.groupby(["yardstick", "period"])["class"].value_counts(normalize=True).unstack().fillna(0)
shares.round(2)

# %%
order = ["growing", "suburbanizing", "stagnant", "city-led"]
fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
for ax, yardstick in zip(axes, ("relative", "absolute")):
    s = shares.loc[yardstick].reindex(columns=order, fill_value=0).loc[list(label.values())]
    bottom = np.zeros(len(s))
    for i, cls in enumerate(order):
        ax.bar(s.index, s[cls], bottom=bottom, color=SERIES_COLORS[i], label=cls)
        bottom += s[cls].to_numpy()
    ax.set_title("Half the US rate" if yardstick == "relative" else "5% per decade", loc="left", fontsize=11)
axes[0].set_ylabel("Share of headline metros")
axes[1].legend(loc="upper left", bbox_to_anchor=(1, 1))
save_figure(fig, "rq0a_classes")

# %% [markdown]
# ## City share of its metro, 1940–2020

# %%
FEATURED = {"35620": "New York", "31080": "Los Angeles", "14460": "Boston", "41860": "San Francisco",
            "47900": "Washington", "12580": "Baltimore", "40060": "Richmond", "26420": "Houston",
            "12420": "Austin"}
share = head[head.year >= 1940].assign(share=lambda d: d.city_population / d.metro_population)
wide = share.pivot(index="year", columns="geo_id", values="share")
fig, ax = plt.subplots(figsize=(9, 5))
ax.fill_between(wide.index, wide.quantile(0.25, axis=1), wide.quantile(0.75, axis=1), color=MUTED, alpha=0.2,
                lw=0, label="middle half of headline metros")
ax.plot(wide.index, wide.median(axis=1), color="black", lw=2.5, label="median")
for code, name in FEATURED.items():
    s = wide[f"cbsa:{code}"]
    ax.plot(s.index, s, color=MUTED, lw=1)
    ax.annotate(name, (s.index[-1], s.iloc[-1]), xytext=(4, 0), textcoords="offset points", fontsize=8, va="center")
ax.set(xlabel="Census year", ylabel="City population ÷ metro population")
ax.set_title("Main city's share of its metro (2023 metro boundaries)", loc="left", fontsize=11)
ax.legend(loc="upper right")
save_figure(fig, "rq0a_city_share")

# %% [markdown]
# ## The three preset answers
#
# Checks that apply: rule 1 — absolute yardstick, bar at ⅓ and ⅔, core = all old cities, central
# counties; rule 2 — absolute yardstick, bar at ⅓ and ⅔, annexing threshold 10% and 40%, central
# counties; rule 3 — absolute yardstick, bar at ⅓ and ⅔, central counties (plan, Execution notes 9).

# %%
VERSIONS = {
    "main": {}, "absolute yardstick": {"yardstick": "absolute"},
    "bar at 1/3 of US growth": {"fraction": 1 / 3}, "bar at 2/3 of US growth": {"fraction": 2 / 3},
    "annexing threshold 10%": {"threshold": 0.10}, "annexing threshold 40%": {"threshold": 0.40},
    "core = all old cities": {"core": True}, "central counties only": {"central": True},
}
APPLIES = {
    "1": ["main", "absolute yardstick", "bar at 1/3 of US growth", "bar at 2/3 of US growth",
          "core = all old cities", "central counties only"],
    "2": ["main", "absolute yardstick", "bar at 1/3 of US growth", "bar at 2/3 of US growth",
          "annexing threshold 10%", "annexing threshold 40%", "central counties only"],
    "3": ["main", "absolute yardstick", "bar at 1/3 of US growth", "bar at 2/3 of US growth",
          "central counties only"],
}
U = {name: cm.units(panel, US, consolidations=consolidations, **kw) for name, kw in VERSIONS.items()}


def row(rule, version, r, n, answer, detail=""):
    return {"rule": rule, "version": version, "estimate": r.estimate, "low": r.low, "high": r.high, "n": n,
            "answer": answer, "detail": detail}


def rule1(u, version):
    r = cm.paired_draws(u, cm.share_metro_kept_up)
    n = int(((u.city_1950 == 0) & u.metro_1950.notna()).sum())
    return [row("1", version, r, n, cm.decide_rule1(r.low, r.high), f"skipped draws: {r.skipped}")]


def rule2(u, version):
    r = cm.paired_draws(u, cm.fall_behind_gap)
    nf, na = cm.rule2_groups(u)
    return [row("2", version, r, nf + na, cm.decide_rule2(r.low, r.high, nf, na),
                f"fixed {nf}, annexing {na}; skipped draws: {r.skipped}")]


def rule3(u, version):
    r2 = cm.paired_draws(u, lambda d: cm.fall_behind_rise(d, 1970))
    r3 = cm.paired_draws(u, lambda d: cm.fall_behind_rise(d, 1990))
    answer = cm.decide_rule3(r2, r3)
    f = ", ".join(f"F({label[s]}) = {cm.fall_behind_share(u, s):.2f}" for s, _ in RQ0A_PERIODS)
    n2 = int((u.metro_1950.notna() & u.metro_1970.notna()).sum())
    n3 = int((u.metro_1950.notna() & u.metro_1990.notna()).sum())
    return [row("3 (F2−F1)", version, r2, n2, answer, f), row("3 (F3−F1)", version, r3, n3, answer, f)]


RULES = {"1": rule1, "2": rule2, "3": rule3}
answers = []
for rule, fn in RULES.items():
    rows_ = [x for v in APPLIES[rule] for x in fn(U[v], v)]
    main = rows_[0]["answer"]
    checks = {x["version"]: x["answer"] for x in rows_ if x["version"] != "main"}
    verdict = cm.robustness(main, checks)
    for x in rows_:
        if x["version"] == "main":
            x["detail"] = f"{verdict}; {x['detail']}"
    answers += rows_

# Context, no rule (spec §4.3)
u = U["main"]
ctx = [row("1", "context: weighted by 1950 city population",
           cm.paired_draws(u, lambda d: cm.share_metro_kept_up(d, weight="city_pop_1950")), "", "")]
for s in (1970, 1990):
    n = int(((u[f"city_{s}"] == 0) & u[f"metro_{s}"].notna()).sum())
    ctx.append(row("1", f"context: S in {label[s]}", cm.paired_draws(u, lambda d, s=s: cm.share_metro_kept_up(d, s)), n, ""))
nf, na = cm.rule2_groups(u, conditioned=False)
ctx.append(row("2", "context: all headline metros (not conditioned)",
               cm.paired_draws(u, lambda d: cm.fall_behind_gap(d, conditioned=False)), nf + na, "",
               f"fixed {nf}, annexing {na}"))
for region, g in u.groupby("region"):
    for s, _ in RQ0A_PERIODS:
        ctx.append(row("3", f"context: F in {label[s]}, {region}",
                       cm.paired_draws(g, lambda d, s=s: cm.fall_behind_share(d, s)), int(g[f"metro_{s}"].notna().sum()), ""))
table = pd.DataFrame(answers + ctx)
table.to_csv(TABLES_DIR / "rq0a_answers.csv", index=False)
table.round(3)

# %% [markdown]
# **Answer (fill in after running):** for each rule, lead with the rule's answer for the main
# version, with the estimate and its 90% range, and say whether it is robust or fragile (name the
# disagreeing checks). Rule 1: "Of the N old big cities that fell behind the US in 1950–70, X% sat
# in metros that kept up (90% range a–b): <answer>". Rule 2: the two group sizes, D and its range,
# and the reminder that D > 0 is partly mechanical. Rule 3: F₁, F₂, F₃, the answer, and whether
# the rise looks gradual; then the regional context. Use "fell behind" / "kept up" (D-29). End
# with one sentence for the paper.
```

- [ ] **Step 2: Convert, execute, look.**

```bash
venv/bin/python -m jupytext --to notebook notebooks/1.0-lr-city-vs-metro.py -o notebooks/1.0-lr-city-vs-metro.ipynb
rm notebooks/1.0-lr-city-vs-metro.py
venv/bin/python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=python3 notebooks/1.0-lr-city-vs-metro.ipynb
ls reports/tables/rq0a_answers.csv reports/tables/rq0a_classes.csv reports/figures/rq0a_city_share.png reports/figures/rq0a_classes.png
```

Expected: the notebook runs and the four outputs exist. Before writing anything, read the tables and look at both figures:
- Are the classes plausible for well-known cases (Detroit, Houston)?
- Are the skipped-draw counts small?

Report anything odd instead of adjusting it. **Do not change a rule, bar or threshold after seeing results.**

- [ ] **Step 3: Write the finding.** Replace the "(fill in after running)" cell, following its own instructions and the rules' output **as it is**, then re-execute. A notebook that still contains "(fill in after running)" isn't finished.

- [ ] **Step 4: Run everything.** `make test`. Expected: all pass, no data tests skipped.

- [ ] **Step 5: Docs.**
  - **`analysis-methods.md`:** rewrite the RQ0a section (yardsticks, classes, rules, checks, which check applies to which rule). Add a Results log entry with the three answers, ranges and verdicts.
  - **`decisions.md`:** add **D-31 · Plan 2 judgment calls (RQ0a)**:
    - The owner's four choices (spec §9: main city A, annexing by land area A, yardstick C, periods A), and the rules fixed before running. *Decided by: user, 2026-10-18.*
    - Departures 1–10 from this plan's Execution notes, including the disclosed annexing counts. *Decided by: Claude (plan, 2026-10-19).*
    - Update "Open items": Plan 2 is done and gives the finding; option B (same-boundary cities) stays open; the 1900–1930 county splits stay open.
  - **Master spec** (`2026-10-08-…-design.md`):
    - §2 RQ0a row, years: "classes 1950–2020; background 1900–1950";
    - §3 Tier 0: name CESTA, NHGIS AV0, WP27 and the Gazetteers;
    - §4 processed panels: add `us_city_metro`;
    - §5 RQ0a: a short paragraph pointing to the Plan 2 spec and stating the answers.
  - **RQ0a spec:**
    - set Status to "Approved 2026-10-19; implemented (Plan 2)";
    - add §11 "Changes made while planning", listing departures 1–10 (and the §4.5 addition: the annexing counts seen while planning).

- [ ] **Step 6: Commit.**

```bash
git add notebooks/1.0-lr-city-vs-metro.ipynb reports/tables/rq0a_*.csv reports/figures/rq0a_*.png Claude docs/superpowers/specs
git commit -m "RQ0a city vs. metro: classes, three preset answers, figures and finding (Plan 2 Task 7)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Spec coverage (Plan 2)

| Spec item | Task |
|---|---|
| §3.1 sources: CESTA, NHGIS AV0, WP27, Gazetteers, `us_metro_longrun`, central flag, US total | 1, 2, 3, 4 |
| §3.1 ICPSR 7735 only if needed | not needed (Execution notes 2); guarded by a data test (Task 4) |
| §3.2 main city, headline metros, crosswalk, old-cities list | 3 |
| §3.3 one source per year, 0 = missing, city-counties, disagreements listed, suburbs, D-27 | 1, 3, 4, 5 |
| §3.4 land area, annexing flag, consolidations, bracket rule, unknowns printed | 2, 3, 5, 7 |
| §4.1 growth and the two yardsticks | 5 |
| §4.2 classes and core recovery | 5 |
| §4.3 rules 1–3 with ranges, skipped draws, context | 6, 7 |
| §4.4 checks and "fragile" | 6, 7 |
| §5 confounds (central-counties and core checks; stated items in the finding) | 4, 7 |
| §6 components and outputs | 1–7 |
| §7 logic and data tests | 1–6 |
| §10.1 doc changes | 1–4, 7 |
