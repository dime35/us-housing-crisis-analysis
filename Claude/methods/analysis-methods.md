# Analysis Methods

Model specifications for each research question. Update this file whenever a specification, variable definition, or robustness check changes.

## Evidence standard

RQ0–RQ4 are descriptive and associational. RQ5 is the one causal design. The paper labels findings accordingly.

## RQ0a — City vs. metro decomposition (US; classes 1950–2020, background 1900–1950)

Plan 2; spec `docs/superpowers/specs/2026-10-18-rq0a-city-vs-metro-design.md`; panel `us_city_metro` (sources and city rules in `geography.md`, "Secondary unit: city proper"); code `modeling/city_metro.py`; notebook `1.0-lr-city-vs-metro`.

- **Units:** every 2023 metro outside Puerto Rico has a main city. The **81 headline metros** hold a 1950 top-100 city, and their main city is their largest 1950 city. All rules use the headline metros.
- **Growth** over a period = end ÷ start − 1, for the city, the metro, the suburbs (metro − city) and the core (all the metro's 1950 top-100 cities). Periods 1950–70, 1970–90, 1990–2020. Metro and suburb growth are dropped for a period containing a county split across the metro line (D-27; Denver 1990–2020).
- **Keeps up** if growth ≥ the bar (a value at the bar keeps up). Main bar: half of US growth over the same period (50 states + DC: +34.3%, +22.4%, +33.3%, so bars +17.1%, +11.2%, +16.6%). Check: 5% per decade compounded (+10.25% over 20 years, +15.76% over 30). Constants in `config.RQ0A_*`.
- **Classes:** growing (both keep up), suburbanizing (city behind, metro keeps up), stagnant (both behind), city-led (city keeps up, metro behind); **core recovery** = the city keeps up after falling behind in an earlier period. Labels describe growth patterns, not moves (D-29).
- **Annexing:** land area up more than 20% over the period, or a city–county consolidation inside it; bracket rule where an end is missing (`geography.md`).
- **Rules, fixed before any class was computed** (90% ranges from 999 draws resampling headline metros, seed 0; draws with an empty group skipped and counted):
  1. S = share of plateau cities (fell behind in 1950–70) whose metro kept up. low ≥ ⅔ → mostly suburbanization; high ≤ ⅓ → mostly metro stagnation; low > ⅓ and high < ⅔ → mixed; else can't tell.
  2. Among metros that kept up in 1950–70: D = fall-behind share of fixed-boundary cities − that of annexing cities. Fewer than 15 in either group → not testable; low > 0 → plateau concentrated in fixed-boundary cities; high ≤ 0 → not a boundary effect; else can't tell.
  3. F₁, F₂, F₃ = share of metros falling behind per period; differences on metros classed in both periods. low(F₂ − F₁) > 0 → later, by 1970–90; else low(F₃ − F₁) > 0 → later, only after 1990; both highs ≤ 0 → not later; else can't tell.
- **Checks and "fragile":** an answer is fragile if any check that applies to its rule disagrees. Rule 1: absolute yardstick, bar at ⅓ and ⅔ of US growth, core = all old cities, central counties only. Rule 2: absolute yardstick, bars at ⅓ and ⅔, annexing threshold 10% and 40%, central counties. Rule 3: absolute yardstick, bars at ⅓ and ⅔, central counties.
- **Context, no rule:** S weighted by 1950 city population and S in the later periods; D over all headline metros; F by region (Northeast + Midwest vs. South + West, by the metro's first-listed state).

## RQ0b — US structural break (decennial; states 1880–2020, metros 1940–2020)

For each decade d, with i a state or a metro:

Δln(pop)_{i,d} = α_d + β_d · ln(income per capita)_{i,d} + ε_{i,d}

Growth runs from the start of decade d to the start of the next; income is measured at the start of decade d, so it precedes the growth it explains.

- β_d > 0 means richer places grow faster. A falling β_d means that link is weakening. Growth counts births and deaths as well as moves, so β_d alone doesn't show people *moving* toward richer places; Plan 1c (`docs/superpowers/specs/2026-10-15-rq0b-1970-vs-1990-design.md`) splits growth into net migration and natural increase.
- **Start-year rule:** each version starts at the first decade from which income exists for every decade onward. No decade is interpolated.
- **Income, state version (1880–2020):** Klein (1880, 1890, 1900, 1910); Easterlin (1920); BEA state personal income per capita (annual from 1929; decade years 1930+ are used). Territories take their later state's ID where boundaries already matched (`territory_to_state.csv`, see `geography.md`), so Arizona, Idaho, Montana, New Mexico, Utah, Washington and Wyoming are in the 1880 panel (and Alaska and Hawaii from 1950, when BEA data begins). States with income: 45 (1880), 47 (1890), 48 (1900–1920), 49 (1930–1940), 51 (1950+).
- **Income, metro version (1940–2020):** 1940 full-count census wage and salary income (IPUMS), aggregated county → CBSA; Census county median family income for 1950 and 1960 (1949 and 1959 income), from the County Data Books in ICPSR 2896 (Haines), with NHGIS table NT39 as a cross-check for 1950; BEA personal income per capita (1969, used for 1970, onward).
  - **BEA metro income definition:** BEA county personal income summed over the metro's 2023 counties ÷ BEA county population summed the same way (D-23). Connecticut uses the 8 old counties via `ct_legacy_counties.csv`, like every other year.
  - **1950/1960 income definition:** median income of families (not families and unrelated individuals), current dollars: 1949 income from the 1952 County Data Book (ICPSR 2896 Part 72, `var20`) and 1959 income from the 1962 County Data Book (Part 74, `var22`). US rows match the published census medians ($3,073 and $5,660). County IDs come from the `fips` column; in the 1952 file `statefip`/`counfip` aren't FIPS codes. Only county rows (`level` = 1) are kept, plus these rules: DC's 1952 code 11010 is set to 11001; Alaska's judicial districts (codes 2900.1 etc.) and xx000 duplicate rows are dropped; blank or zero income means suppressed and is dropped (1950: 70 counties, all small; 1960: 16). That leaves 3,041 counties for 1950 and 3,117 for 1960. Elizabeth City and Warwick VA (merged into Hampton and Newport News in 1952 and 1958) appear only in 1950.
  - **1950/1960 metro aggregation (approximation):** county medians can't be summed, so a metro's 1950 or 1960 income is the population-weighted mean of its counties' median family incomes (weights: NHGIS county population for the same year). Weighting happens at the original county code, before historical codes are merged, so merged counties (e.g., Elizabeth City into Hampton) average rather than add. The result isn't the metro's true median; it is a consistent index across metros for a given year.
  - **1950 cross-check (NHGIS NT39, done once 2026-10-14):** NT39 reports median family income (1949, universe: families) only as $500 brackets, so the check is bracket agreement rather than a value match. All 2,986 counties with a bracket in both sources have the ICPSR value inside the NHGIS bracket (100%). The correlation of log ICPSR income with the log bracket midpoint is 0.98, and the median gap to the midpoint is $124 (as expected for $500 brackets). The two sources measure the same concept.
  - **1940 income definition:** wage and salary income (INCWAGE) summed over everyone in the county ÷ all persons in the county. Top-coded values stay at $5,000. Missing wages (999998) count as 0 (robustness: `income_pc_wages_reported` leaves them out of the denominator instead; it raises metro log income by about 0.09 on average), and the missing share is kept per county as `wage_missing_share` (8.6% of persons nationally; county median 6.1%, max 62%). County codes come from COUNTYICP (D-22), with 24 codes overridden in `countyicp_fixes.csv` where ICPSR's numbering differs from FIPS (D-26). 0.1% of counties (0.02% of persons) are dissolved counties with no FIPS code and stay as `county:nhgis-*`.
- **Main figure:** β_d by decade for both versions.
- **Estimation (`modeling/breaks.py`):** β_d is a separate OLS per decade with HC1 standard errors. A unit drops out of a decade if it lacks population at either end or income at the start; nothing is filled (`prepare_decade_panel`).
- **Tests:** run on the pooled unit × decade panel, because 7–14 β_d values are too few for break tests on their own. The pooled design has decade fixed effects (α_d) plus one income slope per segment, where a segment is the run of decades between breaks.
  - **Chow tests at 1950 and 1980:** a Wald test that the slopes before and after the break are equal, with standard errors clustered by unit (robust to heteroskedasticity and serial correlation within a unit).
  - **Bai-Perron-style global search:** every set of 0–3 breaks at decade boundaries, with at least 2 decades per segment, is fitted, and the set with the lowest BIC is chosen. "No break" is a candidate, so the search can return none.
  - Synthetic tests check that the code recovers a known slope, finds a planted 1980 break, finds no break when none is planted, and doesn't read an income-source level shift as a break.
- **Source changes:** no source indicators (D-20). A source changes only between decades, so a source indicator is collinear with the decade fixed effects, which already absorb any level shift in measured income. Source changes fall in 1920 and 1930 (states) and 1950 and 1970 (metros).
- **Robustness:**
  - log income standardized within each decade (`standardize_within_decade`), so sources with different spreads (1940 wages vs. later total income) are comparable;
  - results with the source-change decades dropped (`source_change_decades`);
  - the metro version compared with the state version, which uses full personal income rather than 1940 wages.

## RQ0b — annual break dating (states 1929–2024, metros 1969–2024)

Plan 1b (spec `docs/superpowers/specs/2026-10-14-rq0b-annual-break-dating-design.md`; code `modeling/annual_breaks.py`). The question: *when* did the decade β change? BEA is the only source, for both population and income, in every year (`us_state_annual`, `us_metro_annual`; see `pipeline.md`). A unit missing a value drops out of that year only, and nothing is interpolated. A metro-year whose one-year growth crosses a county split is left out of every growth calculation (D-27, D-28).

- **Rolling β (the picture, `rolling_betas`):** the decade model on overlapping windows: ln pop(t+h) − ln pop(t) on ln income(t), one cross-section per start year t, HC1 errors. h = 10 (main) and 5 (check). Starts: states 1929–2014, metros 1969–2014. A window is dropped for a metro if any step inside it is flagged. Neighboring windows share most of their years, so the curve is for reading, not testing.
- **Single-break model (the test, `sup_wald_break`):** pooled one-year growth,
  growth(i,t) = ln pop(i,t+1) − ln pop(i,t) = α_t + β_before · ln income(i,t) · [t < T] + β_after · ln income(i,t) · [t ≥ T] + e(i,t).
  - **Demeaning:** growth and log income are demeaned within year once (weighted when bootstrapping). Every year lies wholly in one segment, so this removes the year effects exactly (Frisch-Waugh-Lovell), and each candidate T is a closed-form fit from cumulative sums.
  - **Break year:** the candidate with the lowest sum of squared residuals (Bai-Perron choice). T is the first year of the "after" segment, i.e. the growth from T to T+1.
  - **Trimming and candidate years:** with n growth years, the first candidate is position k = floor(trim · n) and the last is n − k, so each side has at least k years (D-28). The main trim is 15%. States 1929–2023 growth years (n = 95): candidates 1943–2010. States and metros 1969–2023 (n = 55): 1977–2016. A 5% trim is run as a check for metros and the 1969+ states (candidates 1971–2022). An estimate on the first candidate is flagged `at_edge` and written "at or before".
  - **Significance:** for each candidate, a Wald test of β_before = β_after with standard errors clustered by unit (statsmodels' small-sample factor). The largest of these (sup-Wald) is compared with the Andrews (1993) 5% critical value for one restriction at the trim used. That value is simulated in code (Brownian bridge, 10,000-step grid, 20,000 draws, fixed seed), not copied from a table: 8.81 at 15% and 9.84 at 5% (table 9.84). At 15% the simulated 8.81 sits between Andrews' 1993 table (8.85) and the Andrews (2003) corrigendum, which revises it to 8.68. The null distribution can also shift when the spread of incomes changes over time (Hansen 2000), and income dispersion fell sharply from 1929 to 1980. The margins here are wide (17.8 vs. 8.81, or 2.2–5.9 against it), so neither point changes a conclusion. An ordinary p-value is never reported for the chosen year.
  - **Caveats on the test:**
    - Andrews' values are asymptotic and only approximate here. T is fixed at 95 or 55 years, the candidates are whole years, the effective "time" the statistic moves along is weighted by how spread out incomes are in each year (not uniform), and floor trimming makes the candidate range slightly wider than π0 (k/n = 14/95 = 0.147 and 8/55 = 0.145 at 15%; 2/55 = 0.036 at 5%).
    - The break year is the lowest-SSR year, while significance is the largest clustered Wald statistic over all candidates. The two can sit in different years. Without the energy states, for example, the best fit is 1970 but the largest Wald statistic is at 1989 (20.4 with the rule, 22.1 with the hand list). The Wald statistic at 1970 is still above 8.81: 16.5 and 17.5 (printed in the notebook).
- **Range for the break year:**
  - **Bootstrap (`bootstrap_break_year`):** resample whole units with replacement (999 draws, seed 0), re-estimate T, and take the middle 90%. Whole units keep each unit's years together, so it respects serial correlation within a unit, including the smoothing from intercensal estimates. It treats units as independent of one another, so shocks that hit a region's states or metros together (correlation across units in the same year) aren't reflected, and the range may be too narrow under such shocks.
  - **Bai (1997) interval (`bai_interval`):** T ± ceil(7.7 / L) at 90%, with L = (Δβ)² Q² / Ω, Q the mean per-year sum of demeaned x², and Ω the mean per-year sum of (x e)². It allows for heteroskedasticity across units but ignores serial correlation within a unit and correlation across units in the same year (spatial correlation), so it is expected to be too narrow on this data.
  - **Coverage check and rule (`range_coverage`, owner's rule, D-28):** 200 synthetic panels keep the real units, years and incomes, plant the estimated break and slopes, and reuse the fitted residuals with a random sign per unit (199 bootstrap draws each). One sign per unit keeps each unit's serial correlation and heteroskedasticity, but it breaks any correlation across units within a year. So the check, like the bootstrap itself, assumes units are independent, and it can't show whether the range is too narrow under regional shocks. It also plants a single sharp break, so it validates the range only for a single-break process. The state data look more like a U-shape (β falls, rebounds around 1980, then falls again). Target: the bootstrap 90% range contains the planted year in 80–97% of panels. Below 80%, Bai's interval is reported instead. Above 97%, the bootstrap range is still used and noted as conservative. That is legitimate with sharp breaks: the estimate often lands exactly on the true year, and percentile ranges taken from a discrete set of years are conservative. Results (main specifications, `rq0b_annual_range_coverage.csv`):
    - states: bootstrap 96%, Bai 55.5%;
    - metros: bootstrap 98% (above the band, so conservative), Bai 78%. This is computed for the best-fitting metro split even though no metro break is detected (sup-Wald 5.5 < 8.81), so it doesn't make the metro range a range for a break year. The figure shows the metro split as a dotted line with no shading.
    - The bootstrap range is reported for both versions (`reported_range`). The figure draws the dashed break line and the shaded range only where sup-Wald exceeds its critical value. The simulated panels have no correlation across units, so Bai's low coverage there comes from the serial correlation (and heteroskedasticity over time) it ignores, not from spatial correlation.
- **More than one break (`demeaned_break_search`):** the Plan 1 BIC search (0–3 breaks, segments of at least 5 years, break dates counted as parameters) on the demeaned data. The year effects still count as parameters. On small panels it returns the same breaks and BIC as `breaks.break_search` with year dummies (test).
- **Energy states (`features.energy_states`):** a state whose 1980 mining share of earnings (BEA SAINC5S line 200 ÷ line 35) is at least 3× the national share (2.03%). The rule gives WY, WV, OK, NM, LA, KY, TX and AK. The hand list TX, OK, LA, WY, AK, NM, WV, ND is run too, because the rule includes Kentucky (coal) and leaves out North Dakota (2.7×) (D-28). Metros are dropped when the first state listed in the CBSA title is an energy state.
- **Robustness rows (`rq0b_annual_tests.csv`):**
  - states: without energy states (rule; hand list); income standardized within year; without WWII growth years (1940–1946); 1969–2024 only (15% and 5% trimming);
  - metros: 5% trimming; without energy states (both lists); standardized income;
  - five-year rolling windows (figure);
  - decade cross-check (data test): each rolling β for a window starting in 1970, 1980, … lies inside the 95% interval of the decade β.
- **Fixed-effect cells (Plan 1c):** year, year × energy group in 1973–1990 (`oil_cells`), or year × census division (`division_cells`); removed exactly by demeaning within cells, since each cell lies in one year.
- **Two scales for β:** β_before and β_after measure one-year growth, so they are about a tenth of the ten-year β. They are stored as `beta_before_annual`/`beta_after_annual` and shown ×10 as `beta_before_10y`/`beta_after_10y` next to decade results. In the standardized-income rows, log income is z-scored within year, so the `beta_*` columns there are per standard deviation of log income and are not on the decade scale.
- **Outputs:** figure `reports/figures/rq0b_annual_betas.png`; tables `reports/tables/rq0b_annual_tests.csv` (columns as in the spec plus `at_edge`, `reported_range`, `sup_wald_cv5` and `multi_breaks`; D-28) and `reports/tables/rq0b_annual_range_coverage.csv`.

## RQ0b — 1970 or 1990? (Plan 1c)

Plan 1c (spec `docs/superpowers/specs/2026-10-15-rq0b-1970-vs-1990-design.md`, §4; code `three_period`, `share_range`, `decide` in `modeling/annual_breaks.py`). Plan 1b dated one break; the question here is which of two candidate dates the change belongs to, or whether it was gradual. Notebook `1.1-lr-us-structural-break`, section "1970 or 1990? (Plan 1c)"; results in the Results log below.

- **Model (`three_period`):** growth on log income (one-year log growth for the annual panel; the decade rates below for the decade panel) with a separate slope for each of three periods, cuts at 1970 and 1990 (`config.RQ0B_CUTS`): β_pre (growth years to 1969), β_mid (1970–1989), β_post (1990 on). Decade data use the same cuts (1950s–60s, 1970s–80s, 1990s on). Fixed effects for each cell (the year by default) are removed by demeaning within cells, which is exact because each cell lies inside one period. Standard errors are clustered by unit, with statsmodels' small-sample factor G/(G−1)·(N−1)/(N−K), K = cells + 3 slopes; p-values are chi-square(1), as `wald_test(..., use_f=False)` (test against statsmodels with cell dummies).
- **Share:** share = (β_pre − β_mid) / (β_pre − β_post). 0 means 1970–89 looks like the period before, 1 means it looks like the period after. The 90% range comes from resampling whole units (`share_range`, 999 draws, seed 0), keeping each unit's years together. Draws where a period has no variation in income give an undefined share and are skipped. That includes a period whose only unit is drawn several times: its demeaned income is then rounding residue, not exact zeros, so a period counts as having no variation when its demeaned sum of squares is at most 1e-12 of its sum of squares before demeaning. The real data have no such draws.
- **Decision rule (`decide`, fixed before running, never tuned to results):**

  | range (low, high) | answer |
  |---|---|
  | low > 0 and high ≥ 1 | 1970 |
  | low ≤ 0 and high < 1 | 1990 |
  | low > 0 and high < 1 | gradual |
  | low ≤ 0 and high ≥ 1 | can't tell |

  Guard: if β_pre = β_post is not rejected at 5% (clustered Wald), the answer is "can't tell", whatever the range says.
- **Fragile:** the main version sets the answer. If any robustness version gives a different answer, the finding is reported as "fragile".
- **Cells:** the main annual version uses year cells plus year × energy group in 1973–1990 (`oil_cells`, the `features.energy_states` rule list), so the energy states get their own year effects during the oil boom and bust. Checks: year cells only (no oil effects, as in Plan 1b); the hand list; a 1973–1986 window; year × census division throughout (`division_cells`, crosswalk `references/crosswalks/state_divisions.csv`, the within-region check). Every cell lies inside one year, so the slopes stay exact. The decade versions use decade cells.
- **Annual versions (states 1929–2024, `us_state_annual`):** main (oil-year effects); no oil effects; hand list; 1973–1986 window; within census division; income standardized within year (with oil-year effects); without the WWII growth years 1940–1946 (with oil-year effects). Only these annual checks count toward "fragile".
- **Decade versions (`us_state_net_migration`, 50 states and DC, 1950s–2010s):** the same test, rule and range (decade cells; before = 1950s–60s, middle = 1970s–80s, after = 1990s–2010s) on three outcomes, all divided by the starting population: total growth G = (P(d+10) − P(d)) / P(d), net migration M = NM(d) / P(d), and the residual G − M. The residual is natural increase **plus any change in census coverage between the two counts**, so it is labelled "natural increase + census coverage change" (D-30). Net-migration checks: without the six gateway states for immigrants (CA, NY, NJ, IL, FL, TX; `config.GATEWAY_STATES`); without the energy states (rule list); log income standardized within decade.
- **Split:** per decade (cross-section OLS, HC1) and per period (the three-period β's), β_G = β_M + β_N exactly; the notebook asserts it. Table `reports/tables/rq0b_growth_split.csv` (`level, label, beta_total, beta_migration, beta_natural`), figure `reports/figures/rq0b_growth_split.png`.
- **Context, printed in the notebook (descriptive, not part of the rule):** the main versions' β's per decade (annual ×10) and the Wald tests of β_mid = β_pre and β_mid = β_post; Plan 1b's single-break search (`sup_wald_break`) and its resampling votes (`bootstrap_break_year`), re-run with oil-year effects.
- **Two growth scales:** annual β's are one-year log growth (×10 ≈ ten-year scale); decade β's are ten-year simple percent changes, not log changes, so that G = M + N holds exactly. Decade log-growth β's on the same sample were close to Plan 1's (1950s 0.28, 1990s −0.08); this was checked once, not reproduced in a table. The share has no units, so both read the same way (D-30). The percent-change β's run larger than log β's on the same states: 1950s 0.351 (`rq0b_growth_split.csv`) vs 0.276 (`rq0b_decade_betas.csv`), so slopes from the two scales (e.g. the 0.37 decade drop and the 0.20 annual drop) are not comparable in size.
- **Added after the outside review (2026-10-19; descriptive, not part of the preset rule, D-32):**
  - `three_period` also returns clustered standard errors per slope (`se_pre`, `se_mid`, `se_post`).
  - **Search-adjusted p-value:** the 1970 and 1990 cuts came from break searches on the same data, so the fixed-cut Wald p is nominal. `andrews_p_value(stat, trim)` gives the share of the simulated Andrews null at or above a sup-Wald statistic; it is applied to the single-break search on annual states with year effects only.
  - **Leave one state out:** the rule is re-run without each state in turn for the main annual version, the annual version without oil effects, and the two main decade versions (999 draws each). Table `reports/tables/rq0b_leave_one_out.csv` (`analysis, outcome, spec, beta_pre, beta_mid, beta_post, share, share_low, share_high, p_pre_post, answer, left_out, share_full, answer_full`).
  - **Saved statistics:** `reports/tables/rq0b_test.csv` (`statistic, value`: the class report's test, slopes and SEs on the ten-year scale, the mid-period Wald p's, the sup-Wald, its critical values and search-adjusted p); `reports/tables/rq0b_decade_betas.csv` (`version, decade, beta, se, n`: the decade β's behind `rq0b_betas.png` and `rq0b_test.png`).
- **Output table:** `reports/tables/rq0b_1970_vs_1990.csv`, one row per version: `analysis, outcome, spec, beta_pre, beta_mid, beta_post, share, share_low, share_high, p_pre_post, answer, detail` (the spec's columns plus `p_pre_post`, the guard). The main row's `detail` says "robust" or lists the annual checks that disagree.
- **Additivity:** OLS is linear in the outcome, so β for total growth equals β for net migration plus β for the residual (natural increase + census coverage change), decade by decade and period by period (test, and asserted in the notebook).

## RQ0c — Global timing (5-year, 1950–2020)

Agglomeration population growth regressed on national GDP per capita growth and the national urbanization rate. Estimated separately by peer group, with decade interactions.

## RQ1 — OECD elasticity (~2000–2022)

Δ5 ln(pop)_{it} = β · Δ5 ln(GDP)_{it} + γ · (Δ5 ln(GDP)_{it} × US_i) + μ_i + τ_t + ε_{it}

- μ_i = metro fixed effects; τ_t = year fixed effects. Standard errors clustered by country.
- γ < 0 means US metros add fewer people for the same GDP growth.
- **Robustness:** GDP per worker in place of GDP. Population mechanically raises GDP, so this is reported as an association.

## RQ2 — US mismatch

Take each metro's residual from an RQ1-style model and regress it on permits per capita and the Wharton index.

## RQ3 / RQ4 — Housing supply and affordability

- **National:** housing stock growth and price-to-income trends, ranked within peer groups.
- **US metros:** Δ(price-to-income) regressed on the Wharton index and permit intensity.
- **Long-run US:** housing unit growth since 1940 compared with population growth.

## RQ5 — Auckland upzoning (2016 Unitary Plan)

- Monthly building consents per capita: Auckland compared with the rest of New Zealand.
- Difference-in-differences with an event-study plot.
- Synthetic control as a robustness check.

## Peer groups

1. High-income mature
2. High-income newly developed
3. Transition economies
4. Developing Asia and Middle East

Assignment rules are defined in `config.py` and recorded here once implemented. International results are never pooled across peer groups without group controls.

## Robustness applied throughout

- alternative metro definitions;
- dropping featured cities;
- alternative time windows;
- dropping the developing peer group.

## Results log

- **RQ0b, 2026-10-14 (Plan 1; notebook `1.1-lr-us-structural-break`, table `reports/tables/rq0b_tests.csv`, figure `reports/figures/rq0b_betas.png`):**
  - State β_d is positive 1880–1960 (0.03–0.28) and zero or negative from 1990 (−0.08 to −0.01), matching the direction in Ganong & Shoag (2017).
  - States: Chow 1950 p = 0.97, 1980 p = 0.09; BIC search: no break. Standardized income: Chow 1980 p < 0.001, break at 1970. Source-change decades dropped: Chow 1980 p = 0.06, no break.
  - Metros (re-run after the review fixes: 1940 county codes, BIC break-date penalty, county-split decades dropped): Chow 1950 p = 0.011, 1980 p = 0.07; BIC search: 1970 (also the switch to BEA income). Standardized income: 1950 p = 0.004, break at 1970. Source-change decades (1950, 1970) dropped: 1950 p = 0.025, 1980 p = 0.015, break at 1990. 1940 missing wages excluded: 1950 p = 0.014, 1980 p = 0.08, break at 1970.
  - Caveat: in the metro 1950 Chow test the pre-break period is the 1940 decade alone, the only wage-only decade, so it can't separate a behavioral change from the change of income concept.
  - Reading: the decline in income-directed growth is clear, but its timing (1970, 1980 or 1990) is not sharply identified with decadal data.
- **RQ0b annual, 2026-10-14 (Plan 1b; same notebook, table `reports/tables/rq0b_annual_tests.csv`, coverage `reports/tables/rq0b_annual_range_coverage.csv`, figure `reports/figures/rq0b_annual_betas.png`):**
  - States 1929–2023 growth years, main: sup-Wald 17.8 (5% critical value 8.81), so there is a clear break. Best fit 1990, bootstrap range 1943 or earlier (the first candidate) to 1990, Bai 1986–1994. Ten-year-scale β goes from 0.165 to −0.028. The bootstrap estimates split between 1990 (37%) and 1970 (30%), as printed in the notebook. Multi-break search: 1940, 1955, 1990.
  - States without energy states: 1970 for both the rule (range 1946–1990, sup-Wald 20.4) and the hand list (range 1957–1990, sup-Wald 22.1). β goes from 0.16 to −0.05. About half the bootstrap draws pick 1970 (53% with the rule, 52% with the hand list). Largest Wald at 1989; Wald at 1970 is 16.5 and 17.5. Multi-break search: 1940, 1945, 1970.
  - States, standardized income: 1970 (range 1955–1990, sup-Wald 41.5). Without WWII years: 1990 (range 1950–1990, sup-Wald 12.2).
  - States 1969–2023: no clear single break (sup-Wald 2.2 at 15%, critical value 8.81; 4.2 at 5%, critical value 9.84). Best fit 1990. Candidates start in 1977 (1971 at 5%), so this sample can't test a break around 1970.
  - Metros 1969–2023: no clear single break (sup-Wald 5.5, below 8.81 at 15% and 9.84 at 5%). Best fit 1980 (range 1978–2010; 1975–2010 at 5%), with β going from −0.060 to +0.035, the opposite direction. Without energy states: best fit 2009, sup-Wald 3.0 (rule) and 2.5 (hand list). Standardized: 1980, sup-Wald 5.9. Multi-break search: 1981, 1990, 2007.
  - Coverage: bootstrap 96% (states) and 98% (metros, above the band, so conservative); Bai 55.5% and 78%. Bootstrap ranges are reported. The metro coverage is for the best-fitting split, not a detected break, so the metro range isn't a range for a break year. No estimate is at the edge.
  - Reading: annual data confirm the break for states but can't pin down the year. It is about 1990 with all states and raw income. It is about 1970 without the energy states, and also with income standardized within year even with the energy states included (sup-Wald 41.5, the strongest). From the early 1970s on, neither states nor metros show a single clear break. The 1969–2024 samples are tested from 1977, and from 1971 with 5% trimming (states 4.2 and metros 5.5, both below 9.84): state β rebounds for windows starting around 1980 before falling. The 1940s breaks in the multi-break search fall in the war and early postwar years, and 1955 is a further 1950s shift. The later break in every 1929–2024 state version is about 1970 or about 1990.
- **RQ0b 1970 or 1990, 2026-10-15 (Plan 1c; same notebook, table `reports/tables/rq0b_1970_vs_1990.csv`, split `reports/tables/rq0b_growth_split.csv`, figure `reports/figures/rq0b_growth_split.png`):**
  - **Answer (main version, annual total growth with oil-year effects): can't tell, fragile.** Share 0.40, 90% range −0.18 to 1.26. The guard passes: β_pre = β_post is rejected, p < 0.001. On the ten-year scale, β is 0.174 before 1970, 0.093 in 1970–89 and −0.028 from 1990. 1970–89 differs significantly from neither side (Wald p = 0.32 against before, 0.16 against after).
  - **Robustness (annual):**
    - **Fragile** because income standardized within year gives "1970": share 0.67 (0.43–1.14).
    - **Can't tell** in the other five checks:
      - no oil effects: 0.35 (−0.31 to 1.17);
      - hand list: 0.46 (−0.14 to 1.30);
      - 1973–1986 window: 0.35 (−0.33 to 1.15);
      - within census division: 0.79 (−1.13 to 2.44), with β_post +0.057 on the ten-year scale;
      - without the WWII years: 0.27 (−0.56 to 1.32).
    - In the no-oil row, β_post equals Plan 1b's −0.028 exactly. β_pre (1929–69) is 0.174, against Plan 1b's 0.165 over 1929–89.
  - **Decade answers (1950s–2010s): "1970" for total growth and for net migration.**
    - **Total growth:** β 0.320 / 0.096 / −0.047; share 0.61 (0.34–1.23).
    - **Net migration:** β 0.291 / 0.065 / −0.058; share 0.65 (0.38–1.08). Mid vs. before: p < 0.001; mid vs. after: p = 0.14.
    - **Net-migration checks, all "1970":**
      - without the gateway states: 0.64 (0.36–1.15);
      - without the energy states: 0.64 (0.32–1.16);
      - standardized income: 0.73 (0.55–1.05).
    - **Natural increase + census coverage change:** β 0.029 / 0.031 / 0.012. The guard fails (p = 0.65), so "can't tell".
  - **Split:**
    - Total β falls 0.367 from before to after. Net migration accounts for 0.349 (95%); natural increase + census coverage change accounts for 0.018 (5%).
    - From before to the middle, total β falls 0.225, of which net migration accounts for 0.226.
    - Decade β's for total / net migration:

      | Decade | Total | Net migration |
      |---|---|---|
      | 1950s | 0.351 | 0.322 |
      | 1960s | 0.274 | 0.244 |
      | 1970s | −0.031 | −0.032 |
      | 1980s | 0.252 | 0.185 |
      | 1990s | −0.082 | −0.093 |
      | 2000s | −0.048 | −0.050 |
      | 2010s | −0.012 | −0.034 |

    - The residual's β for the 1970s–90s carries census coverage noise (national ratios to NCHS births − deaths: 1.23, 0.91 and 1.20).
      - From the 1970s on, net migration is computed on the APL files' undercount-adjusted bases, so coverage change stays out of it and sits in the residual.
      - The 1950s–60s file uses unadjusted census counts, so there the coverage change sits in net migration. It is small: the national undercount fell about 0.7M in the 1950s and 0.1M in the 1960s. If anything it lowers β_M before 1970, which works against "1970" (D-30).
      - In the 1980s, a coverage-free natural increase rebuilt from the file's adjusted populations matches NCHS (ratio 1.005). The coverage part of the residual has an income slope of −0.0003, so the 1980s β_N of 0.067 is not coverage (D-30).
  - **Single-break search with oil-year effects:** best year 1989, sup-Wald 18.5 (critical value 8.81). Votes: 1970 37%, 1990 26%, 1989 15%, 1943 7%; Plan 1b without oil effects had 1990 37% and 1970 30%.
  - **Reading:**
    - Annual total growth can't place the change. Decade net migration places it at 1970.
    - The two define "before" differently: 1929–69 annually, including the lower-β Depression and war years, against the 1950s–60s by decade.
    - The middle period isn't one regime. The 1970s look like "after", and in the 1980s net migration followed income again.
    - Moving accounts for nearly all of the decline in how growth followed income.
  - **After the outside review (2026-10-19, D-32):**
    - Annual states, year effects only: β per decade 0.174 (SE 0.038), 0.103 (0.112), −0.028 (0.047). The post-1990 slope is not different from zero.
    - Single-break search, year effects only: sup-Wald 17.8 at 1990; search-adjusted p = 0.0008 (5% critical value 8.81, 1% 12.50).
    - Leaving out DC changes every answer: both decade versions become "gradual" (shares 0.52, 0.56) and both annual versions "1990" (shares 0.07, 0.01). No other single state changes any answer. β_pre = β_post is rejected in every leave-one-out run (largest p 0.0005).
    - Reading: the change itself is robust; its timing is not. The decade "1970" depends on DC.
- **RQ0a city vs. metro, 2026-10-19 (Plan 2; notebook `1.0-lr-city-vs-metro`, tables `reports/tables/rq0a_answers.csv` and `rq0a_classes.csv`, figures `reports/figures/rq0a_city_share.png` and `rq0a_classes.png`):**
  - **Rule 1: mostly suburbanization, robust.** Of the 49 headline cities that fell behind the US in 1950–70, 88% sat in metros that kept up (90% range 79–96%). Checks: absolute 93%, bar at ⅓ 91%, at ⅔ 78%, core = all old cities 88%, central counties 86%. Weighted by 1950 population 95%. In later periods the share falls: 44% (34–55%) in 1970–90, 36% (25–49%) in 1990–2020.
  - **Rule 2: plateau concentrated in fixed-boundary cities, robust.** Among the 69 metros that kept up in 1950–70 with a known flag (33 fixed, 36 annexing; 5 unknown), 91% of fixed-boundary cities fell behind against 22% of annexing cities: D = 0.69 (0.54–0.82). Checks give 0.63–0.71; not conditioned, 0.66. Partly mechanical (annexed residents count as city growth).
  - **Rule 3: later, by 1970–90, robust.** F = 9% → 43% → 36%; F₂ − F₁ = 0.35 (0.25–0.44), F₃ − F₁ = 0.28 (0.17–0.37). A jump in 1970–90 that partly eased, not a steady climb. Northeast + Midwest 12% → 77% → 61%; South + West 5% → 5% → 8%.
  - No draws were skipped in any rule. The city's share of its metro fell from a median of about 0.50 (1940) to 0.24 (2020).
- **Class progress report, 2026-10-19 (`reports/class_report/report.tex` → `report.pdf`, build with `latexmk -pdf` in that folder):**
  - The report's statistical test is β_pre = β_post in the annual three-period model with year effects only (the "no oil effects" row of `rq0b_1970_vs_1990.csv`): ten-year-scale β 0.174 vs −0.028, difference 0.203 (SE 0.046, 95% CI 0.112–0.294), Wald χ²(1) = 19.0, p = 1.3e-5, 51 states, 4,803 state-years. It is a simpler version of the Plan 1c guard; the other annual rows' p-values are its robustness table.
  - New figure `reports/figures/rq0b_test.png` (notebook `1.1`, Plan 1c section): state decade β's (plotted at mid-decade) with the three period slopes of that test overlaid.
  - Figure fixes: `rq0b_betas.png` labels the dashed lines as the Chow break dates and moves the legend off the data; `rq0a_city_share.png` spreads end labels apart (`plots.spread_labels`); `rq0a_classes.png` spells out the class definitions and both "kept up" bars. All result tables are unchanged by the re-run.
