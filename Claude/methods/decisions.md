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

### D-22 · Execution corrections to Plan 1 (Tasks 1–9)
- Windham County CT maps to Putnam (micropolitan), not Worcester. The 2023 file puts its successor region there.
- Easterlin's state figures are in Easterlin (1957), Table Y-1, p. 753; the 1960 NBER chapter has regions only. 1919–21 values were transcribed from page photos the user supplied and verified three ways (see `references/manual_data/README.md`).
- IPUMS 1940 county codes come from `COUNTYICP` (`COUNTYNHG` isn't offered for the full count). The NHGIS code = state FIPS × 100000 + COUNTYICP, as IPUMS documents. **Partly superseded by D-26:** the rule fails for 24 codes (all of Maryland after Baltimore County, and five others), which are now overridden.
- API keys are kept out of error output: HTTP errors are re-raised with the bare URL, and CLI tracebacks don't print local variables.
- ICPSR 2896 (Task 9): `ICPSR_INCOME_FILES` takes `member` (the Stata file inside the downloaded zip) and `fips_col` instead of the plan's `state_col`/`county_col`, because the 1952 `statefip`/`counfip` columns aren't FIPS codes; both years carry a correct 5-digit `fips` column (1952 matches 1962 by name for all 3,102 shared counties).
- **Decided by:** Claude (execution rulings, recorded in the plan ledger).

### D-23 · BEA metro income built from counties
- **Decision:** metro income for 1970+ is BEA county personal income (CAINC1 line 1) summed over each 2023 CBSA's counties, ÷ BEA county population (line 2) summed the same way. BEA's MSA-level table isn't used. Combo areas are mapped with `bea_county_combos.csv`, zeros are dropped as placeholders, and Connecticut uses the old counties.
- **Why:** the API returns error 101 ("Unknown error") for CAINC1 at the MSA level (checked 2026-10-14, after BEA's outage ended). Building from counties also puts 1970+ on the same county sets as 1940–1960. Check: county populations add up to 203.8M (1970) and 331.6M (2020), so nothing is counted twice; 386 of 393 metros have data (missing: 6 in Puerto Rico, which BEA doesn't cover, and Waterbury-Shelton, which has no historical series).
- **Alternatives:** BEA's MSA table through its interactive download (current delineation, but no API access and Connecticut on planning regions).
- **Decided by:** user (2026-10-14); proposed by Claude.

### D-24 · Territories, territory counties and Indian Territory in the RQ0b panels (Plan 1 Task 10)
- **Decision:**
  - State panel: territory rows take their later state's ID where the boundary already matched (9 territories); Oklahoma 1900 = Oklahoma + Indian Territory; Oklahoma 1890 and Dakota 1880 stay unmapped.
  - Metro panel: territory counties are matched by name to the later state's counties (150 rows in `county_fixes.csv`, 6 by hand), plus 10 renames and mergers.
  - Metro-years in Oklahoma 1900 are dropped where a metro county has no count (Indian Territory had no counties), and the unmatched-population test excludes Indian Territory. All other unmatched shares are ≤ 0.14% per decade.
  - BEA zeros are dropped at the state level too (Alaska and Hawaii report 0 for 1929–1949).
- **Why:** without the territory mapping, Klein's 1880–1910 income for 7–8 western states had no population to attach to, and the metro build lost 1.9% of 1900 population. Territory county numbers aren't FIPS, so a code rule only works for Arizona and Hawaii; name matching follows NHGIS's own nominal linking. The Indian Territory nations can't be assigned to counties without area weighting, and the 1900 metro rows aren't used by RQ0b (which starts in 1940).
- **Alternatives:** area-weighting Indian Territory nations onto 1907 counties; leaving territories out of the 1880–1900 state panel; a `nhgis` state-only start year of 1910.
- **Decided by:** user (approved 2026-10-14); proposed by Claude.

### D-25 · Notebook execution and figure style (Plan 1 Task 12)
- **Decision:** `make notebooks` runs `python -m nbconvert` with the `python3` kernel as seen from the venv, not `python -m jupyter nbconvert`. Figures use a fixed categorical color order (validated for colorblind separation and contrast) with a marker shape per series and direct labels at line ends; `plots.SERIES_COLORS` is the order.
- **Why:** `python -m jupyter nbconvert` resolves the `jupyter-nbconvert` subcommand on the shell PATH, which on this machine is a separate installation (`~/ENTER`) whose kernel lacks the project's packages. Calling the module directly keeps execution inside the venv.
- **Alternatives:** registering a project kernel (unnecessary: the venv's own `python3` kernel is found once nbconvert runs from the venv).
- **Decided by:** Claude (execution ruling).
- Judgment calls from Tasks 3–11 are recorded in D-21 to D-24 and the plan ledger.

### D-26 · Fixes from the Plan 1 whole-branch review
- **Decision:**
  - **1940 county codes:** `references/crosswalks/countyicp_fixes.csv` overrides 24 COUNTYICP codes where ICPSR's numbering differs from FIPS × 10: 19 Maryland counties (Calvert on), Ste. Genevieve MO and Warwick VA (both from the ICPSR 2896 files, which list ICPSR and FIPS codes side by side), and Pershing NV, Ormsby NV and Union OR (matched on 1940 population against NHGIS). A data test now compares every county's 1940 IPUMS persons with its NHGIS population (gap ≤ max(7%, 100 people)).
  - **1940 missing wages:** a robustness variant, `income_pc_wages_reported`, leaves people with a missing wage out of the denominator; it is reported next to the main specification.
  - **BIC break search:** the penalty counts break dates as parameters (Yao 1988 convention).
  - **BEA raw files:** the echoed request, which contains the API key, is removed before saving.
  - **Smaller items:** 1900 "Persons in the Military" dropped from the state panel; the unmatched-population test tightened to 0.2%; the growth plausibility test no longer compares across missing decades; spec corrected (risk table; income is measured at the start of decade d); `geography.md` no longer claims boundary-standardized counts.
- **Why:** the review found Maryland's 1940 counties shifted by one slot (Kent got Montgomery's people), which put wrong 1940 income on about six metros; state-level checks couldn't see it. Results barely moved after the fix (metro Chow 1950 p from 0.009 to 0.011; same break years).
- **Open:** counties split across a 2023 CBSA line; resolved for 1940+ in D-27.
- **Decided by:** user (missing-wage variant, 2026-10-14); Claude (the other fixes, from the review).

### D-27 · County splits across metro lines: drop the decade, don't reallocate
- **Decision:** for each county split where the new county and its parent end up in different metros (or one in none), the growth of every metro holding either piece is dropped for the decade containing the split (`county_splits.csv`, `growth_comparable`). Done now for 1940 onward (5 splits, 8 metro-decades); the 1900–1930 splits are done in Plan 2 from the Newberry Library atlas, since RQ0a uses those decades.
- **Why:** the parent's earlier count includes area that later left, so that decade's growth compares different areas (Boulder 2000–2010 shows +1% instead of about +9%). Dropping uses no invented numbers; reallocating would need the pre-split population of the split-off area, which no census reports. Results barely moved (metro Chow 1950 p = 0.011; same break years).
- **Alternatives:** reallocating pre-split population by the new county's share at its first census; documenting only.
- **Decided by:** user (approach, 2026-10-14); proposed by Claude.

### D-28 · Plan 1b judgment calls (annual break dating)
- **Decision:**
  - **Order of work:** Plan 1b runs on its own branch (`plan-1b-annual-breaks`, off `plan-1-rq0b`), before Plan 2 (RQ0a). *Decided by: user, 2026-10-14.*
  - **Energy-state rule and list:** a state counts as an energy state if its 1980 mining share of earnings is at least 3× the national share (2.03%). The rule gives WY 11.9×, WV 7.8×, OK 4.9×, NM 4.7×, LA 4.0×, KY 3.8×, TX 3.1× and AK 3.02×. It picks Kentucky (coal) and leaves out North Dakota (2.7×), so the hand list (TX, OK, LA, WY, AK, NM, WV, ND) is also run as a robustness check, as the spec provides. A data test pins the eight states, so a BEA revision that moves Alaska across the line is caught. *Decided by: user (rule and fallback to the hand list), 2026-10-14; Claude (applying the fallback).*
  - **Where the results go:** a new section in notebook 1.1, so RQ0b stays one story. *Decided by: user, 2026-10-14.*
  - **Trimming:** 15% for the main result and 5% as a check for metros and the 1969+ states. Edge estimates are written "at or before". The 1929–2024 state series is what dates early-1970s breaks. *Decided by: user, 2026-10-14.*
  - **Coverage rule for the bootstrap range:** the target band is 80–97%. Below 80%, Bai's interval is reported instead. Above 97%, the bootstrap range is still used and noted as conservative. That happens legitimately with sharp breaks: the estimate often lands exactly on the true year, and percentile ranges from a discrete set of years are conservative. Results: states 96%, metros 98% (conservative). *Decided by: user, 2026-10-14.*
  - **Split growth years come from the data:** BEA first shows the new counties in Broomfield 2002, La Paz 1983 and Cibola 1982, so the flagged growth steps are 2001 (Denver, Boulder, Greeley), 1982 (Yuma) and 1981 (Albuquerque). The spec's "La Paz 1983" was the legal split year. *Decided by: Claude.*
  - **Candidate positions:** the first candidate break is at position floor(trim · n) of n growth years, and the last at n − floor(trim · n). This makes the candidate range slightly wider than the nominal trim (14/95 = 0.147 at 15%). *Decided by: Claude.*
  - **Extra table columns:** `rq0b_annual_tests.csv` adds `at_edge`, `reported_range`, `sup_wald_cv5` and `multi_breaks` to the spec's list, so the table can be read on its own. *Decided by: Claude.*
- **Why:** each call keeps the method as the approved Plan 1b spec describes it and records where the data forced a choice. The methods are in `analysis-methods.md` (RQ0b — annual break dating).
- **Alternatives:** the hand list only (the rule is reproducible and was approved first); the legal split years (they don't match what the BEA data shows); Bai's interval as the main range (its simulated coverage is 55–78%).

## Open items
- Plan 1 (scaffolding and RQ0b) is complete on branch `plan-1-rq0b`, with the whole-branch review fixes in (D-26, D-27).
- Plan 1b (annual break dating) is complete on branch `plan-1b-annual-breaks` (D-28). Finding: annual data confirm the state break but can't pin down the year (about 1990 with all states, about 1970 without the energy states). Next is Plan 2 (RQ0a, city-proper), which includes the 1900–1930 county splits. RQ0c (global timing) is in design.
- Confirm the Rosés-Wolf database URL; verify citations when building `references/references.bib`.
- Decide what to do with the empty root-level `sources.md`.
- No deadline or target paper length set yet.
