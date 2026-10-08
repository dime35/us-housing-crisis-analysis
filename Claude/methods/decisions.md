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

## Open items
- Spec review and approval → then write the implementation plan (writing-plans).
- Confirm the Rosés-Wolf database URL; verify citations when building `references/references.bib`.
- Decide what to do with the empty root-level `sources.md`.
- No deadline or target paper length set yet.
