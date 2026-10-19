# US Housing Crisis Analysis

Do Americans still move toward the places where incomes are highest, and if not, when did that
stop? This project builds long-run US population and income panels (states 1880–2020, metros
1940–2020, cities 1900–2020) to establish those facts. A later stage will test whether housing
supply and land-use rules explain them.

**Status (October 2026):** two questions are answered. The housing questions are planned and not
yet built.

| Question | Status | Answer so far |
|---|---|---|
| **RQ0b**: does population growth still follow income, and when did that change? | done (Plans 1, 1b, 1c) | Richer states grew faster before 1970; from 1990 they did not (Wald χ²(1) = 19.0, p = 1.3×10⁻⁵). About 95% of the change is migration. Whether the date is 1970 or 1990 is not settled. |
| **RQ0a**: when big cities stalled after 1950, was it the city or the whole metro? | done (Plan 2) | In 1950–70 it was mostly suburbanization (88% of stalled cities were in metros that kept growing). Whole metros fell behind from 1970–90, almost all in the Northeast and Midwest. |
| RQ0c, RQ1–RQ5: global timing, OECD comparison, housing supply, prices, Auckland upzoning | planned | — |

The short write-up is [`reports/class_report/report.pdf`](reports/class_report/report.pdf).

---

## Where things are

```
├── Makefile                      make data / features / notebooks / test (run `make` for the list)
├── pyproject.toml                package metadata and dependencies (Python ≥ 3.12)
├── us_housing_crisis_analysis/   the Python package
│   ├── config.py                 paths, year ranges and every analysis constant (cut years, thresholds)
│   ├── sources/                  one module per data source: download() and load()
│   ├── schema.py                 the shared long format every source returns, and its validator
│   ├── dataset.py                CLI: download and load every source into data/interim/
│   ├── geography.py              county → metro, place → county → metro, the 1950 top-100 cities
│   ├── features.py               builds the analysis panels into data/processed/
│   ├── modeling/
│   │   ├── breaks.py             RQ0b: decade slopes, Chow tests, break search
│   │   ├── annual_breaks.py      RQ0b: annual break dating, the three-period test, bootstrap ranges
│   │   └── city_metro.py         RQ0a: growth, keep-up classes, annexing, bootstrap, decision rules
│   └── plots.py                  shared figure style
├── notebooks/
│   ├── 1.0-lr-city-vs-metro.ipynb        RQ0a
│   └── 1.1-lr-us-structural-break.ipynb  RQ0b
├── references/
│   ├── crosswalks/               reviewed lookup tables (county fixes, city codes, metro main cities)
│   ├── manual_data/              hand-transcribed inputs (historical state income, US births − deaths), with a README
│   └── known_values.csv          published figures the data tests check against
├── reports/
│   ├── figures/                  every figure, written by the notebooks
│   ├── tables/                   every result table (CSV), written by the notebooks
│   └── class_report/             LaTeX report (report.tex → report.pdf)
├── tests/                        unit tests; tests/data/ checks the built data
├── docs/superpowers/
│   ├── specs/                    design specs: what each analysis does and its decision rules
│   └── plans/                    implementation plans, task by task
├── Claude/
│   ├── research/sources.md       every data source: URL, coverage, license, access date
│   └── methods/                  pipeline.md, geography.md, analysis-methods.md (with a results log), decisions.md
└── data/                         not in git; rebuilt by the pipeline (raw → interim → processed)
```

**How data flows**

```
sources/<name>.download()  →  data/raw/<name>/              original files, never edited
sources/<name>.load()      →  data/interim/<name>.parquet   one long format for every source
features.py                →  data/processed/<panel>.parquet
notebooks/*.ipynb          →  reports/figures/*.png, reports/tables/*.csv
```

Every source returns the same columns (`geo_id, geo_name, geo_level, country_iso3, year,
variable, value, unit, source`). IDs carry a prefix so they never collide: `state:06`,
`county:24510`, `cbsa:12580`, `place:2622000`.

---

## Reproducing the results

### 1. Set up the environment

Python 3.12 or later.

```bash
python3.12 -m venv venv
make requirements          # installs the package and its dependencies into venv/
```

The Makefile calls `venv/bin/python`, so the environment must be in `venv/`.

### 2. Get API keys (free)

Create a file `.env` in the project root (it is gitignored):

```
IPUMS_API_KEY=...   # one key covers IPUMS NHGIS and IPUMS USA: https://account.ipums.org/api_keys
BEA_API_KEY=...     # https://apps.bea.gov/API/signup/
```

### 3. Download the files that need a login

ICPSR has no API. Create a free account at https://www.icpsr.umich.edu, download these files,
and save the zips **unopened, under exactly these names**:

| Save in | File | What it is |
|---|---|---|
| `data/raw/icpsr/` | `ICPSR_02896-V3 1952.zip` | ICPSR 2896, Part 72 (1952 County Data Book), Stata |
| `data/raw/icpsr/` | `ICPSR_02896-V3 1962.zip` | ICPSR 2896, Part 74 (1962 County Data Book), Stata |
| `data/raw/netmig/` | `ICPSR_08493-V2.zip` | county net migration 1950s and 1960s |
| `data/raw/netmig/` | `ICPSR_08697-V1.zip` | county net migration 1970s |
| `data/raw/netmig/` | `ICPSR_26761-V1.zip` | county net migration 1980s |
| `data/raw/netmig/` | `ICPSR_04171-V1.zip` | county net migration 1990s |
| `data/raw/netmig/` | `ICPSR_34638-V1.zip` | county net migration 2000s |

The net migration studies belong to ICPSR collection 2760
(https://www.icpsr.umich.edu/sites/icpsr/view/collections/2760). The 2010s file downloads by
itself. If a file is missing, `make data` stops and prints these instructions. The exact
members and columns read from each file are documented in `config.py` (`NETMIG_FILES`,
`ICPSR_INCOME_FILES`).

### 4. Build the data

```bash
make data        # downloads every other source, then loads all of them into data/interim/
make features    # builds the analysis panels into data/processed/
```

`make data` skips any file already on disk; `venv/bin/python -m us_housing_crisis_analysis.dataset
download --source bea --force` downloads one source again. The IPUMS 1940 census extract is
submitted through the API and can take hours to be ready; the command waits for it.

Panels built by `make features`:

| Panel | Grain | Used by |
|---|---|---|
| `us_state_longrun` | state × decade, 1880–2020 | RQ0b |
| `us_metro_longrun` | 2023 metro × decade, 1900–2020 (income from 1940) | RQ0a, RQ0b |
| `us_state_annual` | state × year, 1929–2024 | RQ0b |
| `us_metro_annual` | 2023 metro × year, 1969–2024 | RQ0b |
| `us_state_net_migration` | state × decade, 1950s–2010s | RQ0b |
| `us_city_metro` | metro × decade, 1900–2020 (main city, metro, suburbs, city land area) | RQ0a |

Column definitions and data rules are in `Claude/methods/pipeline.md`; the city rules are in
`Claude/methods/geography.md`.

### 5. Run the analysis

```bash
make notebooks   # runs every notebook in place and rewrites reports/figures and reports/tables
```

| Result | Notebook | Tables | Figures | Spec |
|---|---|---|---|---|
| RQ0b by decade (Chow tests, break search) | `1.1-lr-us-structural-break` | `rq0b_tests.csv` | `rq0b_betas.png` | `2026-10-08-housing-growth-mismatch-design.md` |
| RQ0b annual break dating | `1.1-…` | `rq0b_annual_tests.csv`, `rq0b_annual_range_coverage.csv` | `rq0b_annual_betas.png` | `2026-10-14-rq0b-annual-break-dating-design.md` |
| RQ0b 1970 or 1990, and the before-vs-after test | `1.1-…` | `rq0b_1970_vs_1990.csv`, `rq0b_growth_split.csv` | `rq0b_test.png`, `rq0b_growth_split.png` | `2026-10-15-rq0b-1970-vs-1990-design.md` |
| RQ0a city vs. metro | `1.0-lr-city-vs-metro` | `rq0a_answers.csv`, `rq0a_classes.csv` | `rq0a_city_share.png`, `rq0a_classes.png` | `2026-10-18-rq0a-city-vs-metro-design.md` |

Each notebook ends with a written finding. Bootstrap ranges use a fixed seed (0), so a re-run
gives the same numbers.

### 6. Check it

```bash
make test        # all tests (about 250, under a minute); data tests skip if data/ isn't built
make test-fast   # only tests that need no downloaded data
```

The tests in `tests/data/` check the built panels against published figures in
`references/known_values.csv` (for example Detroit's 1950 population), and check that the city
crosswalks can be rebuilt from their sources.

### 7. Build the report

```bash
cd reports/class_report && latexmk -pdf report.tex
```

Needs a LaTeX distribution (TeX Live or MacTeX). The report reads its figures from
`reports/figures/`.

`make all` runs steps 4–6 in order.

---

## How decisions were made

- Every analysis has a **design spec** (`docs/superpowers/specs/`) written before any result was
  computed. Each spec fixes the decision rule ("1970" vs. "1990" vs. "can't tell", and so on) and
  the robustness checks in advance. A result is reported as "fragile" if any check disagrees.
- Each spec has an **implementation plan** (`docs/superpowers/plans/`), which records any changes
  made while building it.
- `Claude/methods/decisions.md` logs every project decision (D-1, D-2, …) with alternatives and
  reasons. `Claude/methods/analysis-methods.md` describes each model and keeps a dated results
  log.

## Data terms

All sources are public, but some have conditions:
- **ICPSR** files may not be redistributed, which is why they must be downloaded by hand.
- **IPUMS** (NHGIS and USA) requires citation.

`Claude/research/sources.md` lists the terms and citation for every source.

## Use of AI tools

This project's code, tests, documentation and report were written with the help of Claude Code,
an AI coding assistant made by Anthropic.
