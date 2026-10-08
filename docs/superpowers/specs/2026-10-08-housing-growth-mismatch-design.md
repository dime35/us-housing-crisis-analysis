# Design: US Housing Constraints and the Growth Mismatch of American Cities

- **Date:** 2026-10-08
- **Status:** Draft — awaiting user review
- **Purpose:** Portfolio project and academic research. Deliverables are a reproducible repo, analysis notebooks, a Markdown paper, and a static interactive dashboard.

## 1. Intent

Many US cities grew rapidly before 1950 and have plateaued since. This project asks whether that plateau is a long-standing structural pattern or a more recent break tied to constrained housing supply, and how US metros compare with peers worldwide in converting economic growth into population growth, housing supply, and affordable housing.

**Success criteria**

1. `make all` rebuilds every dataset, notebook, figure, the paper, and the dashboard from raw downloads (plus documented hand-collected files).
2. Each research question (RQ0a–RQ5) has a notebook, at least one paper figure or table, and a stated finding with its limitations.
3. Claims are labeled honestly: RQ0–RQ4 are descriptive and associational; RQ5 is the single causal case study.
4. Every source is documented in `Claude/research/sources.md`; every method in `Claude/methods/`.

## 2. Research questions

| ID | Question | Hypothesis | Tier / years |
|---|---|---|---|
| RQ0a | How much of the post-1950 plateau in US cities is suburbanization (city vs. metro) versus real metro stagnation? | City-proper plateaus are largely boundary artifacts; metro slowdown is later and uneven | Tier 0, 1900–2020 |
| RQ0b | Is there a structural break in how US population growth responds to income, and when? | The relationship holds through 1950 and weakens after ~1980 (cf. Ganong & Shoag 2017) | Tier 0: states 1880–2020; metros 1940–2020 |
| RQ0c | Do non-US agglomerations show the same timing? | Peer cities show no comparable break, or a different one | Tier 0 global, 1950–2020 |
| RQ1 | For the same GDP growth, do US metros add fewer people than OECD peers? | The population-to-GDP growth elasticity is lower in the US | Tier 1, ~2000–2022 |
| RQ2 | Within the US, are the metros with the largest mismatch the ones that build least? | High-GDP-growth, low-permit metros show the largest gap | Tier 2, US metros |
| RQ3 | Has US housing stock growth lagged peers? | US is in the bottom half of the OECD since 2000; long-run US unit growth (1940+) slows with the population break | Tiers 0 and 2 |
| RQ4 | Have housing costs outpaced incomes more in the US, and most in the most-regulated metros? | Yes; within the US, price-to-income growth rises with the Wharton index | Tier 2 |
| RQ5 | Did Auckland's 2016 upzoning raise construction? | Yes | Featured case |

**Primary population definition:** metropolitan areas with constant, modern boundaries. City-proper population is a secondary contrast (RQ0a).

## 3. Scope

### Data tiers

| Tier | Coverage | Geography | Key variables |
|---|---|---|---|
| 0 — Long-run US | 1880–2020, decennial | States (1880+); all US metros (constant 2023 CBSA boundaries, built from counties, 1900+); city-proper for major cities | Population, housing units (1940+). Income per capita, every decade with no gaps: **states** from Klein (1880–1910), Easterlin (1920), BEA (1929+); **metros** from 1940 full-count census wage income (IPUMS), median family income (1950–60), BEA personal income (1969+) |
| 0 — Long-run global | 1950–2020, 5-year | ~1,900 UN WUP agglomerations (300k+) | Population, national GDP per capita, national urbanization rate |
| 1 — OECD metro panel | ~2000–2022, annual | ~600 OECD metros plus Eurostat metro regions for non-OECD EU members | Population, GDP |
| 2 — Housing | US: all metros, 2000+. International: national-level | US metros; OECD countries | Housing stock, permits/completions, house prices, price-to-income, Wharton index (US) |

### Peer groups (for every international comparison)

1. High-income mature (e.g., Western Europe, Japan, Canada, Australia, NZ)
2. High-income newly developed (e.g., Korea, Israel, Singapore, Gulf states)
3. Transition economies (Central and Eastern Europe)
4. Developing Asia and Middle East (e.g., China, Vietnam, India, Egypt, Iran, Turkey)

Assignment rules (World Bank income group plus historical classification) are defined in `config.py` and documented in `Claude/methods/`.

### Featured cities (~25)

| Theme | Cities |
|---|---|
| US constrained | SF Bay Area, Boston, Los Angeles, New York, Washington DC |
| US mid-size or shrinking core | Baltimore, Richmond |
| US high-building | Houston, Austin |
| Peers that build a lot | Tokyo, Seoul, Toronto |
| Constrained peers | London, Paris, Sydney |
| Eastern Europe | Warsaw, Prague, Bucharest |
| Middle East | Tel Aviv, Istanbul, Dubai |
| Developing / fast-growing Asia | Shanghai, Singapore, Ho Chi Minh City |

Each featured city gets a 1950+ profile. Housing metrics not available from standard sources are hand-collected from national statistics offices where feasible.

### Out of scope (Phase 2)

- Approval and rejection rates of housing projects (England planning statistics, US city permit records, Canadian and Australian portals)
- Growth of zoning and building codes over time (code length, National Zoning Atlas)

The Wharton index stays in Phase 1, but only as a regression variable.

## 4. Architecture

Package-first layout following Cookiecutter Data Science. Reusable code lives in the package; notebooks import it for analysis.

```
us_housing_crisis_analysis/
├── config.py          # paths, year ranges, featured cities, peer-group rules
├── sources/           # one module per source; each exposes download() and load()
│   ├── census_decennial.py   # city-proper population 1790–2020
│   ├── nhgis.py              # state population (1880+), county population (1900+), housing units (1940+), median family income (1950+)
│   ├── ipums.py              # 1940 full-count census wage income, aggregated to counties
│   ├── census_pep.py         # annual metro/county population estimates
│   ├── bea.py                # metro GDP 2001+, county personal income 1969+, state income 1929+
│   ├── census_bps.py         # building permits by metro
│   ├── fhfa.py               # metro house price index
│   ├── wharton.py            # WRLURI 2006 and 2018
│   ├── oecd.py               # metro DB, house prices, price-to-income, housing stock
│   ├── eurostat.py           # metro regions for EU members outside the OECD
│   ├── un_wup.py             # agglomerations 1950+, urbanization rates
│   ├── worldbank.py          # national GDP per capita, income groups
│   ├── maddison.py           # long-run national GDP
│   ├── statsnz.py            # building consents by region (RQ5)
│   └── manual.py             # loads hand-collected files, incl. Klein and Easterlin state income tables
├── geography.py       # crosswalks: county→CBSA, CBSA↔OECD metro, UN WUP↔OECD metro, featured-city IDs
├── dataset.py         # Typer CLI: download / load all sources → data/interim
├── features.py        # builds the analysis panels → data/processed
├── modeling/
│   ├── elasticity.py   # panel regressions (RQ1, RQ2, RQ0c)
│   ├── breaks.py       # decade-by-decade coefficients and break tests (RQ0b)
│   └── event_study.py  # Auckland difference-in-differences and synthetic control (RQ5)
├── plots.py           # shared matplotlib style for paper figures
└── dashboard.py       # builds the static Plotly dashboard
```

`modeling/train.py` and `modeling/predict.py` from the template are removed; this project estimates models rather than training predictors.

### Source module contract

- `download(force: bool = False) -> list[Path]` writes the original files to `data/raw/<source>/`. If the files already exist it skips them unless `force=True`.
- `load() -> pd.DataFrame` returns the **shared long format**:

| Column | Type | Meaning |
|---|---|---|
| `geo_id` | str | Stable ID (e.g., `cbsa:12580`, `county:24510`, `oecd:US019`, `wup:21853`, `iso3:USA`) |
| `geo_name` | str | Human-readable name |
| `geo_level` | str | `city`, `county`, `metro`, `agglomeration`, `state`, `country` |
| `country_iso3` | str | ISO 3166-1 alpha-3 code |
| `year` | int | Reference year |
| `variable` | str | Standard variable name (e.g., `population`, `gdp_real_ppp`, `housing_units`, `permits_units`) |
| `value` | float | Value |
| `unit` | str | Unit (e.g., `persons`, `usd_2015_ppp`, `index_2015=100`) |
| `source` | str | Source module name |

`dataset.py load` writes each source's output to `data/interim/<source>.parquet`.

### Processed panels (`data/processed/`, wide Parquet)

| Panel | Grain | Feeds |
|---|---|---|
| `us_state_longrun` | state × decade, 1880–2020 | RQ0b (state version) |
| `us_metro_longrun` | metro × decade, 1900–2020, plus city-proper for major cities | RQ0a, RQ0b (metro version), RQ3 (long run) |
| `us_metro_annual` | metro × year, 2000+ | RQ2, RQ4 |
| `oecd_metro_panel` | metro × year, ~2000–2022 | RQ1, RQ2 |
| `global_agglomerations` | agglomeration × 5-year step, 1950–2020, with peer group | RQ0c |
| `national_housing` | country × year | RQ3, RQ4 |

### Storage and version control

- `/data/` is gitignored. Raw files are reproducible from `download()`.
- Hand-collected inputs (China yearbook extracts, featured-city housing statistics) and reviewed crosswalk tables are small and not downloadable, so they live in **`references/manual_data/`** and **`references/crosswalks/`**, which are committed.
- API keys (IPUMS/NHGIS, BEA) are read from `.env`, which is gitignored.

### Build targets

| Target | Does |
|---|---|
| `make data` | download and load all sources → `data/interim/` |
| `make features` | build panels → `data/processed/` |
| `make notebooks` | execute all notebooks in order with nbconvert |
| `make paper` | render `reports/paper.md` to HTML/PDF with Quarto |
| `make dashboard` | build `reports/dashboard/index.html` |
| `make test` | run pytest |
| `make all` | all of the above in order |

### Dependencies

pandas, pyarrow, requests, python-dotenv, typer, loguru, tqdm, statsmodels, linearmodels, ruptures, matplotlib, plotly, jupyter, nbconvert, pytest. External tool: Quarto, for rendering the paper. `pyproject.toml` `requires-python` changes to `>=3.12` to match the venv.

## 5. Methods

Full write-ups are kept in `Claude/methods/analysis-methods.md`.

- **RQ0a — city vs. metro decomposition.** Track the central city's share of metro population by decade and split metro growth into core and suburban parts. Classify each metro as: suburbanizing (core declined, metro grew), stagnant (both stagnated), growing (both grew), or core-recovery.
- **RQ0b — US structural break.** For each decade d: Δln(pop)_i,d = α_d + β_d · ln(income per capita)_i,d−1 + ε, where i is a state or a metro. Each version starts at the first decade from which income exists for every decade onward, with no interpolated gaps: **states 1880–2020**, **metros 1940–2020**. Plot β_d for both versions. The break tests run on the pooled unit × decade panel, with income interacted with period indicators, because a series of 7–14 β_d values is too short for them: Chow tests at 1950 and 1980, and a Bai-Perron multiple-break search. Each change of income source (e.g., Klein → Easterlin → BEA) gets an indicator, and results are reported with and without the decades where the source changes.
- **RQ0c — global timing.** Five-year agglomeration population growth regressed on national GDP per capita growth and urbanization rate, estimated by peer group with decade interactions.
- **RQ1 — OECD elasticity.** Δ5 ln(pop)_it = β Δ5 ln(GDP)_it + γ (Δ5 ln(GDP)_it × US_i) + metro FE + year FE, with standard errors clustered by country. A robustness check replaces GDP with GDP per worker. Reported as an association because of reverse causality.
- **RQ2 — US mismatch.** Metro residuals from an RQ1-style model regressed on permits per capita and the Wharton index.
- **RQ3/RQ4 — supply and affordability.** National rankings and trends by peer group. US metros: Δ(price-to-income) regressed on the Wharton index and permit intensity. Long-run US housing unit growth since 1940 compared against population growth.
- **RQ5 — Auckland.** Monthly building consents per capita in Auckland compared with the rest of New Zealand. Difference-in-differences with an event-study plot around the 2016 Unitary Plan; synthetic control as a robustness check.
- **Robustness (all RQs).** Alternative metro definitions, dropping featured cities, alternative time windows, and dropping the developing peer group.

## 6. Outputs

**Notebooks** (`notebooks/`):

| Notebook | Covers |
|---|---|
| `0.1-lr-data-audit` | coverage and missingness |
| `1.0-lr-city-vs-metro` | RQ0a |
| `1.1-lr-us-structural-break` | RQ0b |
| `1.2-lr-global-timing` | RQ0c |
| `2.0-lr-oecd-elasticity` | RQ1 |
| `2.1-lr-us-mismatch` | RQ2 |
| `3.0-lr-housing-supply-affordability` | RQ3, RQ4 |
| `4.0-lr-auckland-event-study` | RQ5 |
| `5.0-lr-featured-cities` | featured-city profiles |

Notebooks save figures to `reports/figures/` and tables to `reports/tables/`.

**Paper:** `reports/paper.md`, with sections Introduction, Literature, Data, Methods, Results (by RQ), Discussion, Limitations, Future Work (Phase 2), and References. Citations live in `references/references.bib`. Figures are embedded by path.

**Dashboard:** `reports/dashboard/index.html`, a static self-contained Plotly page containing:
- a world map of the population-to-GDP mismatch;
- a featured-city explorer covering 1950 onward;
- the US break-coefficient chart;
- US metro scatter plots (mismatch vs. Wharton index and permits).

## 7. Testing and validation

Tests focus on data correctness and estimator correctness, not code coverage. Each test is written in the build step that introduces the code it covers (§10).

**Two tiers:**
- **Fast tests** run on small raw-file samples committed in `tests/fixtures/`. They need no network or API keys and run on every commit.
- **Data tests** (`@pytest.mark.data`) run on cached data in `data/` and are skipped when it is absent.

**Schema and panels (fast):**
- every source's `load()` output conforms to the long-format schema: column types, no nulls in key columns, `geo_id` prefix consistent with `geo_level`, unique (`geo_id`, `year`, `variable`), one `unit` per `variable`;
- panels have unique (`geo_id`, `year`) pairs and years within the expected range.

**Crosswalks and geography:**
- each county maps to at most one CBSA;
- CBSA 2020 populations built from the crosswalk match official Census 2020 CBSA totals within 0.1% (data);
- explicit cases for known boundary changes: Connecticut's 2022 shift from 8 counties to 9 planning regions, Virginia independent city mergers (e.g., Bedford, Clifton Forge), Broomfield CO (2001), Alaska boroughs, Miami-Dade FIPS change;
- featured cities resolve to the IDs in the committed crosswalk; no OECD metro matches more than one UN WUP agglomeration.

**Units and classifications (fast):**
- deflation, PPP conversion, and index rebasing (2015 = 100) match hand-checked values;
- every country in a panel gets exactly one peer group, with spot checks (Korea → high-income newly developed, Poland → transition, Vietnam → developing).

**Estimator recovery on synthetic data (fast):**
- `elasticity.py`: on a simulated panel with β = 0.5 and US interaction −0.3, the estimates fall within tolerance and the clustered standard errors are finite;
- `breaks.py`: on a simulated pooled panel, the Chow test and Bai-Perron detect breaks planted at 1950 or 1980 and detect none in a panel without one; a level jump planted at an income-source change is absorbed by the source indicator rather than reported as a break;
- `event_study.py`: the DiD recovers a simulated +20% post-2016 effect, the pre-period coefficients are about 0, and a 2012 placebo shows no effect.

**Plausibility bounds (data):** no negative populations; no metro whose population changes by more than ±80% in one decade unless it is on a committed allowlist; permits per capita within a sane range.

**Known-value checks (data)**, so a broken download fails loudly, with values recorded in `references/known_values.csv`:
- Detroit city 1950 population = 1,849,568;
- US 2020 census resident population = 331,449,281;
- US 1880 census population = 50,189,209;
- one state value each from the Klein and Easterlin tables, and one 1940 IPUMS county wage income value;
- two or three CBSA 2020 Census counts (e.g., San Francisco–Oakland), one year of BEA personal income, one OECD metro, and one UN WUP agglomeration.

**Not tested:** live network calls (one mocked test checks that `download()` skips existing files unless `force=True`); plotting internals. The dashboard gets a smoke test: the HTML is built, is self-contained, and contains the four expected charts.

**Notebook execution:** `make notebooks` must complete without errors. Logic worth testing moves from notebooks into the package.

**Sanity check (notebook, not pytest):** the RQ0b notebook roughly reproduces Ganong & Shoag's (2017) decline in income convergence before the project's own findings are trusted.

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Metro boundaries change over time | Constant 2023 CBSA boundaries built from counties for all years; county boundary changes handled via NHGIS standardized or time-consistent tables where available, and documented |
| Historical income data is coarse | Each RQ0b version starts at the first decade with income for every decade onward (states 1880, metros 1940); no interpolation |
| Changes of income source can look like structural breaks | Source indicators; results with and without the decades where the source changes |
| 1940 census wage income is top-coded at $5,000 and excludes business and farm income | Documented as a limitation; metro results checked against the state version, which uses full personal income |
| UN WUP ↔ OECD metro matching | Automatic match by name and coordinate distance; manual review for featured cities; committed table in `references/crosswalks/` |
| Source APIs change or disappear | Raw files cached; provenance in `Claude/research/sources.md` |
| Comparing fast-urbanizing countries with mature ones | Peer groups plus urbanization control; never pool without them |
| Limited international housing data | Two-tier design; featured-city housing data collected by hand, with sources noted |

## 9. Documentation and workflow conventions

- `Claude/research/sources.md`: every source and reference, with URL, coverage, access date, license, and the module that uses it.
- `Claude/methods/`: `pipeline.md` (data flow and architecture), `analysis-methods.md` (models per RQ), and `geography.md` (crosswalks and boundary decisions).
- Commit after every completed step.

## 10. Build order

1. Scaffolding: dependencies, config, long-format schema, test harness
2. Tier 0 US: NHGIS, Census decennial, IPUMS 1940 full count, BEA income, Klein and Easterlin state income (hand-collected), crosswalks → `us_state_longrun` and `us_metro_longrun` → RQ0a and RQ0b notebooks
3. Tier 0 global: UN WUP, World Bank, Maddison → `global_agglomerations` → RQ0c
4. Tier 1: OECD and Eurostat metros → `oecd_metro_panel` → RQ1
5. Tier 2: BPS, FHFA, Wharton, Census population estimates, OECD housing → `us_metro_annual` and `national_housing` → RQ2 to RQ4
6. RQ5: Stats NZ → Auckland event study
7. Featured cities, including hand-collected data
8. Paper, dashboard, and the `make all` end-to-end check

Each step ends with tests passing, docs updated, and a commit.
