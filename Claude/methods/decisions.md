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

### D-29 · Wording of the RQ0b finding, and standards for future designs
- **Decision:**
  - **Wording:** RQ0b findings say "population growth stopped following income" (richer places no longer grow faster), not "people stopped moving toward richer places". Total growth includes births and deaths; the moving claim waits for Plan 1c's net-migration split.
  - **Standards for every new design spec:**
    - (a) a decision rule fixed before anything is run, including a "can't tell" outcome;
    - (b) for each confound, which way it could push the result, without assuming a direction;
    - (c) whether the change could be gradual rather than a single break;
    - (d) no fit-score (BIC/AIC) comparison as a headline test on panel data whose observations are correlated within units. Use inference that allows for that correlation (clustered tests, unit resampling).
- **Why:** a design review of Plan 1c (2026-10-15) found these gaps in Plans 1 and 1b. They change no reported numbers, but the earlier write-ups overstated the moving interpretation, and the multi-break BIC searches deserve less weight than they got.
- **Decided by:** user, 2026-10-15 (proposed by Claude).

### D-30 · Plan 1c judgment calls (1970 or 1990?)
- **Decision:**
  - **Scope (option A):** the three-period test on annual state growth with oil-year effects, plus net migration by decade with an exact split of growth. No hand entry of the 1939–1967 birth and death tables (option B), no yearly net migration, no 1940s, no metro version. *Decided by: user, 2026-10-15.*
  - **Decision rule, fixed before running (spec §4.1):** the 90% unit-bootstrap range of share = (β_pre − β_mid) / (β_pre − β_post) decides between "1970", "1990", "gradual" and "can't tell". If β_pre = β_post isn't rejected at 5%, the answer is "can't tell". The main version sets the answer, and any annual check that disagrees makes it "fragile". The rule was not changed after the results came in. *Decided by: user, 2026-10-15.*
  - **Oil window:** 1973–1990 in the main version, with 1973–1986 as a check. The energy states are the `features.energy_states` rule list, with the hand list as a check (D-28). *Decided by: user, 2026-10-15.*
  - **Where the results go:** a new section in notebook 1.1, plus a paragraph in the RQ0b results. *Decided by: user, 2026-10-15.*
  - **Branch:** `plan-1c-break-year` off `plan-1-rq0b`, in the main project folder. *Decided by: user, 2026-10-15.*
  - **The share range is not coverage-checked.** It uses the same unit bootstrap as Plan 1b's break-year range (999 draws, seed 0). That range's 80–97% acceptance band and its fallback to Bai's interval (D-28, *decided by: user, 2026-10-14*) were set for a break year. Plan 1c runs no coverage simulation for the share. Like the Plan 1b range, it treats states as independent of one another. *Decided by: Claude.*
  - **Immigration data test replaced.** The spec (§6) wanted state net migration summed to the US to land within 25% of published net international migration. The test is now "the national sum is positive in every decade". Published net-immigration figures differ from residual-method net migration by up to 2× (undocumented migration, census coverage changes), so a 25% band would test the published figure, not this data. *Decided by: Claude (plan, 2026-10-15).*
  - **Coverage and base-population tests changed form (spec §6).** The spec wanted (a) counties matched to states covering at least 99.5% of US population in each decade, and (b) the APL's own base populations matching `us_state_longrun` within 0.5%. The plan shipped "at least 49 states" and a 2020-only population check without recording it; the whole-branch review caught this. The tests in `tests/data/test_us_net_migration.py` now sum each file's base populations over the counties the parser kept and check:
    - **All 51 states in every decade.**
    - **Unadjusted census bases, within 0.5% for every state:** 1950s–60s `V19`/`V199`, the 1970s file's enumerated `PTOT70`/`PTOT80`, and 2020 `f1tttt`. This is test (b), and it gives (a) state by state. One exception: Alaska in 1970 is held to 1%. The 1960s and 1970s files take their 1970 counts from Bowles, Beale and Lee (1975). These are 89,330 (0.04%) above the NHGIS count nationally, and Alaska is 302,419 against 300,382 (+0.68%).
    - **Undercount-adjusted bases, checked against the documented adjustment.** These are the bases each file computes net migration on: 1970s `AWTOT70`+`ANWTOT70` and `ATOT80`, the 1980s age cells, and the 1990s `P90`/`P00`. Test (b) fails here by design: DC is 3.5% above the census in the 1980s file's 1980 base and 5.8% above in the 1990s file's 1990 base. So the test checks that the national base minus the census count lands within 15% of the DA net undercount:
      - 1970: +6.20M (DA 5.5M);
      - 1980: +3.17M (1970s file) and +2.85M (1980s file), against DA 2.8M;
      - 1990: +4.38M (1980s file) and +4.17M (1990s file), against DA 4.7M;
      - 2000: +338,030 (1990s file), against DA 338,000.

      The 1970s file used the Census Bureau's 1985 rates (3.0% in 1970, 1.5% in 1980; codebook §1.1), which is why it sits about 13% above the DA figures. The 2000s file adjusts the estimates base with ACE Revision II and DA, and there is no published national total to compare it with. So it is held to the sign and under 0.5%: +518k in 2000 and +974k in 2010.
    - **County sums equal the file's own state rows**, for net migration and every base, wherever the file has state rows (1950s, 1960s, 1970s, 2000s, 2010s). The match is within 10 persons, except in the 2000s, where 0.1% is allowed: that file's state rows were estimated separately (net migration up to 470 apart).
    - **Where 99.5% can't be computed directly:** the 1980s and 1990s files have no state or US rows and carry only adjusted bases. There the DA band bounds coverage instead. Losing more than about 0.39M people (1980s) or 51k (1990s, from `P00`) fails the test, which means coverage of at least 99.8%.
    - Evidence that the parser keeps every county row, from the review: no county-like row is dropped for a missing value or a bad code; there are no duplicate codes; and the 1990s merged units (xx9xx) replace their components.
    - *Decided by: Claude (final-review fix, 2026-10-15).*
  - **Two growth scales.** The annual test uses one-year log growth (Plan 1b's panel), shown ×10 next to decade results. The decade test uses ten-year simple percent changes, so that total = net migration + residual holds exactly (spec §3). The share has no units, so both read the same way. *Decided by: Claude (plan, 2026-10-15).*
  - **The residual is "natural increase + census coverage change" (spec deviation, Task 4).** N = G − M includes any change in census coverage between the two counts, not just births minus deaths.
    - **What the national check shows:** compared with NCHS births − deaths (`references/manual_data/us_natural_increase.csv`), it is within 5% in the 1950s, 1960s, 2000s and 2010s (ratios 1.011, 1.002, 0.969, 0.979). It is off in the 1970s (1.230), 1980s (0.914) and 1990s (1.204).
    - **Why those three decades:** the demographic-analysis net undercount was 2.7% in 1970, 1.2% in 1980, 1.8% in 1990 and 0.12% in 2000 (NRC 1995; Census Bureau DA 2000; `sources.md`). Sign and size fit.
    - **What the test checks:** the spec wanted 5% in every decade. The data test (`tests/data/test_us_net_migration.py`) keeps 5% for 1950/1960/2000/2010. For 1970/1980/1990 it checks only the documented direction (above 1, below 1, above 1) with |ratio − 1| < 0.25.
    - **How it is labelled:** "natural increase + census coverage change" in the table, the figure legend, the finding and the paper sentence.
    - **What it affects:** the residual's β for the 1970s–90s carries coverage noise. Net migration is kept clear of it only from the 1970s on, because the coverage basis of M switches at the 1970 cut (final review):
      - **1970s–2000s:** the APL files compute net migration on undercount-adjusted bases. Examples: 1980 +2.85M and 1990 +4.38M above the census in the 1980s file; `P00` = 281.76M in the 1990s file. So coverage change stays out of M and sits in the residual.
      - **1950s–60s:** the file (ICPSR 8493) uses unadjusted census counts (`V19` = 151,325,798, the 1950 count). There the coverage change sits in M, and the residual is close to births minus deaths (ratios 1.011 and 1.002).
      - **The 1950s–60s part is small.** The national net undercount fell about 0.7M in the 1950s (6.3M to 5.6M) and 0.1M in the 1960s (5.6M to 5.5M; NRC 1995). That is about 0.4% and 0.05% of the population, and the differences between states are smaller still. The undercount was highest in groups concentrated in lower-income states. So, if anything, this lowers β_M before 1970, which works against the "1970" answer.
    - **Alternative, not built: a coverage-free natural increase from the files already on disk.**
      - The 1980s file (ICPSR 26761) carries undercount-adjusted populations for 1980 and 1990.
      - The 1990s file (ICPSR 4171) carries county births and deaths (`BTH`, `DTH`) and adjusted 1990 and 2000 populations.
      - So natural increase can be rebuilt for the 1980s–90s without coverage change. State-level NCHS births and deaths for 1950–2019 would cover every decade, but that is a larger sourcing job.
      - **The 1980s check (final review, recomputed):**
        - The file's adjusted 1990 minus adjusted 1980 minus net migration gives a national natural increase of 16.96M, against NCHS 16.87M: a ratio of 1.005. A data test holds this within 1%.
        - The coverage part of our residual is N minus that in-file natural increase, per starting population. Its 1980s income slope is −0.0003 (HC1 se 0.005), against β_N = 0.067.
        - So the 1980s rise in β_N is not coverage.
      - The owner can ask for either version.
    - *Decided by: Claude (controller ruling, 2026-10-15), flagged to the owner.*
  - **No natural-increase decade is left unsourced.** NCHS births and deaths cover all seven decades (1950–2019). The 1950s figures exclude Alaska and Hawaii (roughly 0.2M of 25M). *Decided by: Claude.*
  - **ICPSR column choices per decade:** in `config.NETMIG_FILES` (study, file member, column), and listed in the net-migration row of `Claude/research/sources.md`:
    - 1950s and 1960s: `V532` (ICPSR 8493);
    - 1970s: `NMETOTAL` (ICPSR 8697, undercount-adjusted);
    - 1980s: the sum of 36 age cells (ICPSR 26761);
    - 1990s: `NMG_TT_T` (ICPSR 4171);
    - 2000s: the sum of 18 age groups (ICPSR 34638);
    - 2010s: APL `m1tttt`.

    All totals include the cohorts born during the decade. *Decided by: Claude, checked against each codebook.*
  - **1980s net migration is the sum of the 36 male/female age cells.** The file's all-ages total loses two digits in its largest counties, so it is corrupted exactly where the weight is. The age-cell sum gives a US total of 6,737,671. *Decided by: Claude.*
  - **1990s fixed-width positions were inferred from the data.** The ICPSR 4171 codebook lists variable names but no column positions. The positions were inferred from the file and confirmed by four accounting identities that hold across the columns. `NMG_TT_T` is columns 7726–7732. *Decided by: Claude.*
  - **Pre-1980 county codes are kept as they are.** In the 1950s–60s, and for some units in the 1970s (and 12 merged units in the 1990s), the county part of the code is not FIPS. Only the state part, which is FIPS in every decade, is used, since Plan 1c only sums to states. A future county-level join on those decades would need a crosswalk. *Decided by: Claude.*
  - **The ICPSR zips keep ICPSR's standard names** (e.g. `ICPSR_08493-V2.zip`) in `data/raw/netmig/`, so the config names what a fresh download produces. *Decided by: Claude.*
  - **Context printed beyond the brief's table:** the notebook prints the main versions' β's per decade and the Wald tests of β_mid = β_pre and β_mid = β_post, as spec §4.1 asks. The table keeps the planned columns, with `p_pre_post` (the guard) added to the spec's list. *Decided by: Claude.*
  - **Task order:** the code-only tasks (cells, three-period test, rule) came first, so work could start before the owner's ICPSR download. The spec's component order put the data first. *Decided by: Claude (plan, 2026-10-15).*
- **Why:** each call either keeps the approved Plan 1c spec or records where the data forced a departure. The methods are in `analysis-methods.md` (RQ0b — 1970 or 1990?), the data in `pipeline.md` and `sources.md`.
- **Alternatives:**
  - a coverage simulation for the share range (not in the spec);
  - state vital statistics instead of the residual;
  - the files' all-ages total for the 1980s (corrupted);
  - a county code crosswalk for the 1950s–70s (no current use).

### D-31 · Plan 2 judgment calls (RQ0a, city vs. metro)
- **Decision:**
  - **Owner's choices (spec §9):** the main city is each metro's first-named city, and the headline is the metros holding a 1950 top-100 city (A; the spec corrects this to the largest 1950 city, which changes only Norfolk); annexation is measured with land area and a fixed vs. annexing split (A), with tract-based same-boundary cities (B) only if needed later; the yardstick is half the US growth rate, with 5% per decade as a check (C); periods 1950–70, 1970–90, 1990–2020 (A). The three rules were fixed in the spec before any class was computed and were not changed after the results came in. *Decided by: user, 2026-10-18.*
  - **Implementation calls** (plan `2026-10-19-plan-2-rq0a-city-vs-metro.md`, Execution notes): *Decided by: Claude (plan and build, 2026-10-19).*
    1. No schema change: the existing geo level `city` (prefix `place:`) is used.
    2. The 1990 Census Gazetteer is added as the 1990 land-area source (WP27 1950–1980, Gazetteers 1990–2020). Without it 7 headline cities stayed "unknown" for annexing in two periods, over the spec's limit of 5; with it 5, 5 and 0, so ICPSR 7735 was not needed. Disclosed: while planning, annexing flags were computed for the headline cities (unconditioned; at 20%: 39 annexing / 37 fixed in 1950–70, 20 / 56 in 1970–90, 14 / 67 in 1990–2020); no class, share or rule result was computed.
    3. Place-code changes in a committed table (Louisville 2020 = balance + old city; 1990 "remainder" codes; Macon 2014).
    4. A city's 2020 count is used only where CESTA and NHGIS agree in 2010 within 0.5% (drops Honolulu and Crystal City TX; neither is a headline city).
    5. CESTA vs. WP27: 8 headline city-years differ by more than 0.5% (listed in `geography.md` and pinned by a test), not the 2 the spec named.
    6. Austin is in the 1950 top 100 (rank 73), so all nine featured US metros are headline metros.
    7. Puerto Rico's 6 metros are left out (387 metros); 7 main-city overrides, 3 of them metros with no city series.
    8. Connecticut's legacy counties count as central; Waterbury and Macon can't be placed by the 2020 place-to-county file (listed in the test).
    9. Which checks apply to which rule (the spec didn't say): the core check applies to rule 1 only and the annexing thresholds to rule 2 only; rule 3 is about metros only.
    10. Rule 3 is two rows in `rq0a_answers.csv`; context rows sit in the same table with an empty answer.
    11. NHGIS places with 4-digit, non-FIPS codes are dropped (they collided with real codes after padding).
- **Result (2026-10-19):** all three answers robust: mostly suburbanization (S = 0.88, range 0.79–0.96); plateau concentrated in fixed-boundary cities (D = 0.69, 0.54–0.82); metros fell behind later, by 1970–90 (F 0.09 → 0.43 → 0.36), almost only in the Northeast and Midwest.

### D-32 · Fixes from the outside review of the notebooks and class report
- **Context:** three independent reviewers checked notebooks 1.0 and 1.1 and the class report, then cross-examined each other's findings (2026-10-19). Every reported number reproduced. The problems were in interpretation: data-chosen cut years with a nominal p-value, a "1970" timing answer that depends on DC, "slower after 1990" for a slope not different from zero, behavioural wording against D-29, mixed growth scales, and untraceable numbers.
- **Decision:** fix the write-ups and make every number traceable; leave the preset rules and their answers unchanged. *Decided by: user, 2026-10-19.*
- **Implementation calls:** *Decided by: Claude, 2026-10-19.*
  1. RQ0b: per-slope clustered SEs and an Andrews p-value for the single-break search (`annual_breaks.andrews_p_value`); a leave-one-state-out run of the rule (not a preset check, so it can't make an answer "fragile"); the test statistics and decade β's saved to tables. Results in `analysis-methods.md` (Plan 1c, "After the outside review").
  2. RQ0a: stricter keep-up bars (¾ and the full US rate) and a headline vs. other-metros comparison, as exploratory rows in their own table (`rq0a_exploratory.csv`), so the preset answers and their robust/fragile labels stay as registered. The "Limits" note on the headline set is corrected (selection makes rule 3's rise larger). US growth and the city-share summary are saved to tables.

## Open items
- Plan 1 (scaffolding and RQ0b) is complete on branch `plan-1-rq0b`, with the whole-branch review fixes in (D-26, D-27).
- Plan 1b (annual break dating) is complete on branch `plan-1b-annual-breaks` (D-28). Finding: annual data confirm the state break but can't pin down the year (about 1990 with all states, about 1970 without the energy states). Next is Plan 2 (RQ0a, city-proper), which includes the 1900–1930 county splits. RQ0c (global timing) is in design.
- Plan 1c (1970 or 1990?) is implemented on branch `plan-1c-break-year`, with the whole-branch review fixes in (D-30). Finding: by the preset rule, annual total growth can't tell (share 0.40, range −0.18 to 1.26), and the answer is fragile (standardized income gives 1970). Decade net migration gives 1970 (share 0.65, range 0.38–1.08), robust to its three checks, and accounts for about 95% of the decline. RQ0c's US comparison (Plan 1c spec §9) therefore has no single answer to follow: the owner decides whether it uses the decade net-migration answer (1970) or treats the timing as open.
- Open for the owner: (a) the natural-increase residual includes census coverage change, so a coverage-free version could replace it if the births part matters: from the APL files' own adjusted populations and births and deaths for the 1980s–90s, or from state vital statistics for every decade (D-30); (b) the share range has no coverage simulation (D-30); (c) the annual and decade tests define "before" differently (1929–69 vs. 1950s–60s), which is why their answers differ; any follow-up comparing them on the same window would be a new, post-hoc analysis.
- Plan 2 (RQ0a, city vs. metro) is implemented on branch `plan-2-rq0a` (D-31). Finding: the 1950–70 plateau of old big cities was mostly a city-proper pattern (88% of those that fell behind sat in metros that kept up), concentrated in fixed-boundary cities, and whole metros fell behind only from 1970–90, almost only in the Northeast and Midwest. Still open: same-boundary city populations (option B, tract-based, 1970+) if the boundary result needs a counterfactual; the 1900–1930 county splits (not needed while metro figures start in 1940).
- Confirm the Rosés-Wolf database URL; verify citations when building `references/references.bib`.
- Decide what to do with the empty root-level `sources.md`.
- No deadline or target paper length set yet.
