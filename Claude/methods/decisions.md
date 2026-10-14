# Decision Record

Log of project decisions: what was decided, the alternatives considered, and why. Add new entries at the bottom; when a decision is reversed, mark the old entry **Superseded by D-xx** instead of deleting it.

**Decided by:** `user` = chosen by the project owner · `default` = proposed by Claude and not yet explicitly confirmed

---

## Session 2026-10-08 — Initial brainstorming

### D-01 · Project purpose
- **Decision:** Portfolio project **and** academic research. The deliverable is a final presentable report backed by a reproducible repo.
- **Alternatives:** portfolio only; persuasive essay or blog post; academic only.
- **Implication:** Methods must be statistically defensible and cited; everything must rebuild from the pipeline.
- **Decided by:** user

### D-02 · Comparison set
- **Decision:** A full OECD metro panel for the statistics, **plus** a set of featured cities for storytelling.
- **Alternatives:** OECD only; OECD plus global fast-growing cities; hand-picked pairs only.
- **Rationale:** The panel makes the core claim credible; featured cities make the report readable and avoid accusations of cherry-picking.
- **Decided by:** user. Coverage later expanded by D-09.

### D-03 · Analytical depth
- **Decision:** Descriptive analysis plus panel regression (population-to-GDP elasticity, with a US interaction and fixed effects), plus **one** causal case study: the Auckland 2016 upzoning event study.
- **Alternatives:** descriptive only; full causal identification (Saiz-style instruments, multiple difference-in-differences studies).
- **Decided by:** user (b); the single event study was Claude's suggestion, included in the approved spec.

### D-04 · Housing metrics added
- **Decision:** Beyond population and GDP, analyze housing stock growth, new construction (permits and completions), and house prices relative to incomes.
- **Rationale:** Completes the causal chain: economic growth → housing supply response → prices → population.
- **Decided by:** user

### D-05 · Handling uneven housing data coverage (two-tier design)
- **Decision:**
  - Tier 1: OECD metros with population and GDP only.
  - Tier 2: housing metrics, compared at national level internationally and at metro level across the US.
  - Featured cities: housing data collected by hand from national statistics offices.
- **Alternatives:** hand-build a full international metro housing panel; housing metrics for the US only.
- **Decided by:** user

### D-06 · Approvals and building-code threads deferred
- **Decision:** Housing project approval and rejection rates, and the growth of zoning and building codes, are deferred to **Phase 2**.
- **Alternatives:** keep them as supporting evidence; make them full co-equal threads.
- **Note:** The Wharton regulation index stays in Phase 1, but only as a regression variable.
- **Decided by:** user (deferral); keeping the Wharton index was Claude's proposal, not objected to.

### D-07 · Long-run historical scope (back to 1900/1950)
- **Decision:** Extend the data back to at least 1950, and 1900 for US population, to test whether the post-1950 plateau of US cities is a long-standing structural pattern or a later break. This adds a **Tier 0** long-run layer, which uses income as a stand-in for GDP before 2001.
- **Decided by:** user

### D-08 · Primary population definition
- **Decision:** Metro areas with constant, modern boundaries are primary. City-proper population is a secondary contrast that measures how much of the "plateau" is suburbanization.
- **Alternatives:** city-proper primary; both equal.
- **Rationale:** City-proper plateaus are partly an artifact of fixed boundaries and suburbanization, and reviewers would challenge them.
- **Decided by:** user

### D-09 · Expanded city coverage and peer groups
- **Decision:**
  - Add Baltimore, Richmond and Washington DC, plus cities in the Middle East, Asia and Eastern Europe.
  - Add a global tier: about 1,900 UN WUP agglomerations (1950+) paired with national GDP.
  - International comparisons are made **within peer groups** (high-income mature, high-income newly developed, transition economies, developing Asia and Middle East), with an urbanization-rate control.
  - About 25 featured cities, grouped by theme rather than in pairs (list in the spec, §3).
- **Rationale:** Fast-urbanizing cities grow for different reasons (rural-to-urban migration); peer groups keep the comparison honest.
- **Decided by:** user (coverage); peer-group method proposed by Claude and accepted.

### D-10 · Output formats
- **Decision:** Three outputs:
  - analysis in numbered Jupyter notebooks;
  - a Markdown paper (`reports/paper.md`, rendered with Quarto);
  - a static interactive dashboard.
- **Decided by:** user

### D-11 · Pipeline architecture
- **Decision:**
  - Package-first layout following Cookiecutter Data Science: one module per data source, a shared long format, processed Parquet panels, and notebooks that import the package.
  - Builds run through `make`.
  - The dashboard is static Plotly HTML rather than Streamlit.
- **Alternatives:** notebook-first with papermill; a workflow engine (Snakemake or DVC).
- **Decided by:** user

### D-12 · Data sources and pipeline structure (spec Section 2)
- **Decision:** The source list, package layout, five processed panels, API keys stored in `.env`, and the make targets, as written in the spec.
- **Decided by:** user

### D-13 · Analysis methods (spec Section 3)
- **Decision:**
  - RQ0a: city-vs-metro decomposition.
  - RQ0b: decade-by-decade convergence coefficients, Ganong & Shoag style, with Bai-Perron and Chow break tests.
  - RQ0c: global timing by peer group.
  - RQ1: OECD elasticity with fixed effects.
  - RQ2: residual mismatch vs. permits and Wharton.
  - RQ3/RQ4: supply and affordability.
  - RQ5: Auckland difference-in-differences and synthetic control.
  - RQ0–RQ4 are labeled associational; RQ5 is causal.
- **Decided by:** user

### D-14 · Outputs, testing, risks (spec Section 4)
- **Decision:**
  - Notebook list.
  - Paper structure with a BibTeX bibliography.
  - Dashboard contents.
  - pytest schema, crosswalk and panel tests, plus checks against known values.
  - Cached raw downloads.
- **Decided by:** user (approved by moving to the spec)

### D-15 · Documentation conventions
- **Decision:**
  - Maintain `Claude/research/sources.md` (every source and reference).
  - Maintain `Claude/methods/` (pipeline, methods, architecture, and this decision record).
  - Recorded in `Claude/CLAUDE.md`.
- **Decided by:** user

### D-16 · Git workflow
- **Decision:** Commit after every completed step. `Claude/CLAUDE.md` is now tracked; its `.gitignore` rule was removed.
- **Decided by:** user

### D-17 · Choices made while writing the spec — pending review
These were made by Claude while drafting the spec and haven't been explicitly confirmed:
- Hand-collected data and reviewed crosswalks are committed under `references/manual_data/` and `references/crosswalks/`, because `/data/` is gitignored.
- The template's `modeling/train.py` and `modeling/predict.py` are removed.
- Turkey is placed in the "developing Asia and Middle East" peer group despite OECD membership.
- `requires-python` changes to `>=3.12` to match the venv.
- US metros use the 2023 CBSA delineation as the constant boundary.
- **Decided by:** default

### D-18 · Testing plan (spec Section 7)
- **Decision:** Fast tests on committed fixtures plus `@pytest.mark.data` tests on cached data; estimator-recovery tests on synthetic data; CBSA totals checked against official Census totals; explicit tests for county boundary changes. No tests of live downloads or plotting internals.
- **Decided by:** user

### D-19 · RQ0b extended before 1950
- **Decision:**
  - Each RQ0b version starts at the first decade from which income exists for every decade onward, with no interpolation: states 1880–2020 (Klein 1880–1910, Easterlin 1920, BEA 1930+); metros 1940–2020 (1940 IPUMS full-count wage income, then Census and BEA).
  - The manufacturing-wage proxy for pre-1940 metros was considered and dropped.
  - Chow and Bai-Perron tests run on the pooled unit × decade panel, not on the β_d series; each income source gets an indicator.
- **Why:** The 1950 Chow test needs data before 1950. The user rejected dropping or interpolating gap decades in favor of starting where the series is complete. Klein (2013) fills Easterlin's 1890 and 1910 gaps, so the state version can start in 1880.
- **Decided by:** user (start-year rule); Claude (pooled testing, source indicators, Klein as the gap filler)

### D-20 · Spec approved; corrections made while planning
- **Decision:**
  - The user approved the spec, including the D-17 defaults.
  - Corrections made while writing the first plan:
    - RQ0b source indicators dropped. They are collinear with the decade fixed effects, which already absorb source-level shifts. Within-decade standardized income was added as a robustness check.
    - Bai-Perron is implemented as a global SSR search over decade boundaries with BIC selection. `ruptures` was dropped; `ipumspy`, `openpyxl` and `jupytext` were added.
    - The CBSA check uses a 1% tolerance against the Census Bureau's 2020 estimates base, excluding Connecticut.
    - The plausibility bound is "falls by half or triples", not ±80%, which would flag genuine Sun Belt growth.
    - Known-value checks on hand-collected and IPUMS data were replaced with independent cross-checks (Klein vs. Easterlin; IPUMS 1940 vs. BEA 1940).
  - Implementation is split into one plan per build stage. Plan 1 covers scaffolding and RQ0b; RQ0a (city-proper) is Plan 2.
- **Decided by:** user (approval); Claude (corrections, plan split)

### D-21 · 1950/1960 county income from ICPSR 2896, not NHGIS
- **Decision:** RQ0b metro income for 1950 and 1960 comes from ICPSR study 2896 (Haines), using the County Data Book parts for 1952 (1949 income) and 1962 (1959 income). The user downloads the files by hand, and `sources/icpsr.py` reads them. NHGIS table NT39 (1950) is used once as a cross-check. Plan 1 Task 9 was rewritten, and Task 10 reads income from `icpsr`.
- **Why:** The NHGIS metadata API (checked 2026-10-09) shows a 1950 county median family income table (`1950_cPHA`, NT39), but the 1960 county dataset (`1960_cPop`) has only 15 population tables and no income. Without 1960 income, the start-year rule would push the metro version's start from 1940 to 1970. ICPSR 2896 covers both years from one consistent Census series.
- **Alternatives:** the 1960 Census supplementary report ranking county incomes (a PDF to transcribe); starting the metro version in 1970.
- **Decided by:** user (2026-10-11); source proposed by Claude.

### D-22 · Execution corrections to Plan 1 (Tasks 1–8)
- Windham County CT maps to Putnam (micropolitan), not Worcester. The 2023 file puts its successor region there.
- Easterlin's state figures are in Easterlin (1957), Table Y-1, p. 753; the 1960 NBER chapter has regions only. 1919–21 values were transcribed from page photos the user supplied and verified three ways (see `references/manual_data/README.md`).
- IPUMS 1940 county codes come from `COUNTYICP` (`COUNTYNHG` isn't offered for the full count). The NHGIS code = state FIPS × 100000 + COUNTYICP, as IPUMS documents.
- API keys are kept out of error output: HTTP errors are re-raised with the bare URL, and CLI tracebacks don't print local variables.
- **Decided by:** Claude (execution rulings, recorded in the plan ledger).

### D-23 · BEA metro income built from counties
- **Decision:** metro income for 1970+ is BEA county personal income (CAINC1 line 1) summed over each 2023 CBSA's counties, ÷ BEA county population (line 2) summed the same way. BEA's MSA-level table isn't used. Combo areas are mapped with `bea_county_combos.csv`, zeros are dropped as placeholders, and Connecticut uses the old counties.
- **Why:** the API returns error 101 ("Unknown error") for CAINC1 at the MSA level (checked 2026-10-14, after BEA's outage ended). Building from counties also puts 1970+ on the same county sets as 1940–1960. Check: county populations add up to 203.8M (1970) and 331.6M (2020), so nothing is counted twice; 386 of 393 metros have data (missing: 6 in Puerto Rico, which BEA doesn't cover, and Waterbury-Shelton, which has no historical series).
- **Alternatives:** BEA's MSA table through its interactive download (current delineation, but no API access and Connecticut on planning regions).
- **Decided by:** user (2026-10-14); proposed by Claude.

## Open items
- Finish Plan 1 on branch `plan-1-rq0b`. Waiting on: the user's ICPSR download (Task 9). Tasks 1–8 are complete. Then write Plan 2 (RQ0a, city-proper).
- Confirm the Rosés-Wolf database URL; verify citations when building `references/references.bib`.
- Decide what to do with the empty root-level `sources.md`.
- No deadline or target paper length set yet.
