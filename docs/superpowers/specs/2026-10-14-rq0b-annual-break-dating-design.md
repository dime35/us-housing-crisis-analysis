# Design: Dating the RQ0b break with annual data (Plan 1b)

- **Date:** 2026-10-14
- **Status:** Approved by the owner, 2026-10-14
- **Extends:** `2026-10-08-housing-growth-mismatch-design.md` (§2 RQ0b, §4 panels, §5 methods, §10 build order)
- **Builds on:** Plan 1 (branch `plan-1-rq0b`), decisions D-20 to D-25

## 1. Summary in plain terms

Plan 1 showed that **people used to move toward richer places and largely stopped doing so**. State β (how much faster richer states grew) was positive in every decade from 1880 to 1960 and has been about zero or slightly negative since 1990. It could not say **when** the change happened. With one data point per decade, the 1970s and 1980s are one noisy dot each, and the break tests pointed to 1970, 1980 or 1990 depending on the version.

This plan uses **year-by-year data** to narrow that down. BEA publishes income and population every year: since 1929 for states and since 1969 for counties (which add up to metros). Most of it is already downloaded. The plan produces three things:

1. **A sliding ten-year picture.** The same β as now, but for windows starting every year (1969–79, 1970–80, …). The curve moves one year at a time, so a drop shows up where it happens.
2. **A best-guess break year with a range,** e.g. "most likely 1978, almost certainly between 1974 and 1983". The range is the honest answer to "when".
3. **An oil-cycle check.** The 1970s oil boom and 1980s bust made energy states rich and fast-growing, then poor and shrinking, inside the same window we care about. That could look like a break even if migration behavior didn't change. Every result is rerun without the energy states.

**What success looks like:** one or two sentences for the paper, of the form *"The break most likely happened around year X (range Y–Z); it holds up without the energy states"*, or a plain statement that annual data can't pin it down, with the reason.

## 2. Goals and non-goals

**Goals**
- Annual state panel, 1929–2024, and annual metro panel, 1969–2024, from one source (BEA) throughout.
- Rolling-window β by start year for both, comparable to the decade β.
- A single break year for each version, with a significance test that accounts for searching over years, and a range for the year.
- Robustness: without energy states; five-year windows; a cross-check against the decade results.
- An updated RQ0b finding, figure and table.

**Non-goals**
- No new causal claims. RQ0b stays descriptive (spec §1).
- No new income concepts or sources beyond BEA (and one BEA industry table to classify energy states).
- No annual data before 1929 (states) or 1969 (metros). It doesn't exist at that frequency.
- The decade analysis is kept as is. This adds to it and doesn't replace it.

## 3. Data

| Panel | Grain | Population | Income | Status |
|---|---|---|---|---|
| `us_state_annual` (new) | state × year, 1929–2024 | BEA SAINC1 line 2 (Census mid-year estimates) | BEA SAINC1 line 3 (per capita personal income) | Income downloaded; population is one more request to the same table |
| `us_metro_annual` (started early, spec §4) | metro (2023 CBSA) × year, 1969–2024 | BEA CAINC1 line 2, counties summed to CBSAs | BEA CAINC1 line 1 ÷ line 2, counties summed (D-23) | Already in `data/interim/bea.parquet` |
| Energy classification | state | — | BEA SAINC5S: mining earnings ÷ total earnings, 1980 | One new request |

- **One source throughout.** Population and income both come from BEA in every year, so there is no income-source switch inside the annual series. That removes the confound behind the 1970 metro break in Plan 1.
- **Population is partly estimated between censuses.** Census mid-year estimates are revised to meet the next census, which spreads any surprise smoothly across the decade. That can blur a break's timing by a few years. The break-year range will be correspondingly wider; it isn't hidden.
- **`us_metro_annual` is started early.** The spec plans it for RQ2/RQ4 (2000+, adding permits, prices and the Wharton index in build step 5). This plan creates it with population and income from 1969. Step 5 adds columns; it doesn't create a second panel.
- **Same geography rules as Plan 1:** 2023 CBSAs from counties, Connecticut's 8 old counties, BEA combo areas and zero placeholders as in D-23 and D-24.
- **County splits across metro lines (D-27).** A metro-year whose one-year growth crosses a county split is dropped, as in the decade panel: Broomfield 2001, La Paz 1983, Cibola 1981. (Los Alamos 1949 and Menominee 1961 fall before 1969.)

## 4. Methods

### 4.1 Rolling-window β (the picture)

For each start year t and each unit i: growth over the next ten years, `ln pop(t+10) − ln pop(t)`, regressed on `ln income(t)`, one cross-section per t (same as the decade model). Windows start every year: states 1929–2014, metros 1969–2014. HC1 standard errors per window, as in Plan 1.

Neighboring windows share nine of their ten years, so the curve is smooth by construction. It is for reading, not for testing; the tests are in 4.2.

### 4.2 Break year, significance and range (the test)

Pooled model on **annual** growth, so the observations don't overlap:

`growth(i,t) = ln pop(i,t+1) − ln pop(i,t) = α_t + β_before · ln income(i,t) · [t < T] + β_after · ln income(i,t) · [t ≥ T] + e(i,t)`

- α_t are year fixed effects. They absorb anything that hits every place the same year (recessions, national migration trends, how the Census estimates were revised).
- **Break year T:** try every candidate year, leaving out the first and last 15% of years so each side has enough data. The estimate is the year with the best fit (lowest sum of squared residuals, the standard Bai-Perron choice).
- **Candidate years in practice:** states 1929–2024 → about 1943–2009; states 1969–2024 and metros 1969–2024 → about 1977–2015. So **only the long state series can date a break in the early or mid-1970s.** The metro and short-state versions test whether there was a break from the late 1970s on, and are read that way.
- **5% trimming as a check (metros and the 1969+ states).** Earliest candidate about 1972. Estimates near the edge rest on only 3–5 "before" years and the critical value is higher (Andrews, one restriction, 5% level: about 8.85 at 15% trimming vs. about 9.8 at 5%), so the 15% result stays the main one.
- **Edge estimates.** When the estimated year is the first candidate year, it is reported as "at or before" that year: the test can detect an earlier break but can only place it at the edge.
- **Is there a break at all?** For each candidate T, the Wald statistic for β_before = β_after uses standard errors clustered by unit (robust to a place's own year-to-year correlation). The largest of these (sup-Wald) is compared with Andrews' (1993) critical values for one restriction at the trimming actually used, computed by simulating the statistic's limiting distribution in the code rather than copied from a table. Ordinary p-values would overstate significance, because we picked the year that fits best.
- **Range for the year:** resample units (states or metros) with replacement, re-estimate T each time (999 draws), and report the middle 90% of the estimates. Resampling whole units keeps each unit's years together, so it respects the year-to-year correlation that the estimates-revision smoothing creates. This kind of resampling isn't guaranteed to give a correct range for a break year, so it is checked by simulation (§6), and Bai's (1997) standard interval for the break date is reported next to it.
- **More than one break:** as a cross-check, the Plan 1 BIC search (`breaks.break_search`) is run on the annual panel with up to 3 breaks and segments of at least 5 years. A brute-force search would be about 100,000 fits for states (about 14,000 for metros), each with about 100 year dummies. So growth and income are demeaned within year once, up front, which removes the year effects exactly (the same fit, without the dummies); the BIC still counts the year effects as parameters. A test on small panels checks that this gives the same breaks and BIC as the existing search.

**Plain reading of the outputs:** sup-Wald says whether a change happened; T says when it most likely happened; the range says how sure we are about the year; β_before and β_after say how strong the pull toward income was on each side.

**Two scales for β.** β_before and β_after measure one year of growth, so they are about 1/10 the size of the ten-year β in 4.1 and in Plan 1. They are stored under names that say so (`beta_before_annual`, `beta_after_annual`) and are also shown ×10 (`beta_before_10y`, `beta_after_10y`) wherever they sit next to decade results.

### 4.3 Robustness

| Check | Why |
|---|---|
| **Without energy states** (states whose 1980 mining share of earnings is at least 3× the national share; metros whose first-listed state in the CBSA title is one of those states) | The oil boom and bust could create a spurious break |
| **Five-year windows** in 4.1 | Shows the picture doesn't depend on the ten-year horizon |
| **Income standardized within year** | Same as Plan 1; guards against changes in the spread of incomes |
| **States 1969–2024 only** | Puts the state and metro results on the same years |
| **Without WWII years** (state series: growth years 1940–1946 dropped) | Annual state population in those years swings with troop moves and war industry |
| **5% trimming** (metros and 1969+ states) | Lets the test name break years back to about 1972 |
| **Cross-check with the decade panel** | The rolling β for windows starting in 1970, 1980, … should be close to the decade β for those decades. A big gap means a data problem, not a finding |

The energy-state rule and the resulting list are recorded in `analysis-methods.md`, and the list is printed in the notebook so a reader can see which states it removes.

## 5. Components

| Unit | What it does | Depends on |
|---|---|---|
| `sources/bea.py` (extend) | Two new requests: SAINC1 line 2 (state population) and SAINC5S mining and total earnings (states, 1980). Same parser, same zero-placeholder and suppression rules | BEA API key |
| `features.py` (extend) | `build_us_state_annual`, `build_us_metro_annual` (counties → 2023 CBSAs, as in D-23), `energy_states` | interim `bea`, `geography` |
| `modeling/annual_breaks.py` (new) | `rolling_betas`, `annual_growth_panel`, `sup_wald_break`, `bootstrap_break_year`; reuses Plan 1's design-matrix logic, generalized from decades to any period column | `breaks.py`, statsmodels |
| Notebook `1.1-lr-us-structural-break` (extend) | New section "Annual data: when did the break happen?" with figure, table and updated finding | the above |

Outputs: `reports/figures/rq0b_annual_betas.png` (rolling β for states and metros, with the estimated break year and its range shaded) and `reports/tables/rq0b_annual_tests.csv` (columns `version, spec, trim, break_year, range_low, range_high, bai_low, bai_high, sup_wald, beta_before_annual, beta_after_annual, beta_before_10y, beta_after_10y, n_units, years`).

## 6. Testing

- **Synthetic recovery (fast tests):** an annual panel with a planted break in 1978 → estimated T within ±2 years, and the range covers 1978. No planted break → sup-Wald below the 5% critical value. A planted temporary boom-bust in a subset of "energy" units → the without-energy specification shows no break.
- **Range coverage (slow test):** across at least 200 synthetic panels with a planted break year, the bootstrap 90% range contains the planted year 80–97% of the time. Outside that band the range is not used, and Bai's interval becomes the reported range.
- **Rolling β:** a planted constant slope is recovered in every window.
- **Demeaned break search:** on small synthetic panels, the demeaned multi-break search returns the same breaks and BIC values as `breaks.break_search` with year dummies.
- **Data tests:** the metro-years dropped for county splits (Broomfield 2001, La Paz 1983, Cibola 1981; D-27) are absent from `us_metro_annual`; annual state population sums within 1% of the census count for 1930, 1940, …, 2020 (Alaska and Hawaii excluded from both sides before 1950, since BEA reports zeros for them; D-24); annual metro population for 2020 within 1% of the Census estimates base (as in Plan 1); no zero or negative income; the panels are unique by (unit, year); the decade cross-check above holds: each rolling β for a window starting in 1970, 1980, …, 2010 lies inside the 95% interval of the decade β for that decade (metros: the BEA decades 1970+; states: 1930+).

## 7. Risks

| Risk | Mitigation |
|---|---|
| Oil cycle mistaken for a break | Without-energy specification; reported next to the main result |
| Smoothing in intercensal population estimates blurs timing | Year fixed effects; the bootstrap range widens rather than hides it; stated as a limitation |
| Annual growth is noisy | The test uses the pooled panel (thousands of unit-years); the picture uses ten-year windows |
| Searching over years overstates significance | Andrews critical values for sup-Wald; never an ordinary p-value for the chosen year |
| 1929–1945 (Depression, war) dominates the state series | The 1969–2024 state specification; candidate years trimmed at both ends |
| WWII troop and war-industry moves distort 1940–1946 state population | Without-WWII-years check (§4.3) |
| A break before about 1977 can't be dated with metros or the 1969+ state series (15% trimming) | 5% trimming check (earliest about 1972); edge estimates written "at or before"; the 1929–2024 state version is the instrument for earlier dates |

## 8. Decisions for the user

All decided by the owner on 2026-10-14:

1. **Order of work.** Plan 1b runs on a new branch off `plan-1-rq0b`, before Plan 2 (RQ0a). (The Plan 1 review fixes are in: D-26, D-27.)
2. **Energy-state rule.** 1980 mining share of earnings at least 3× the national share. The resulting list is shown to the owner before results are run; if it misses an obvious oil state, the hand-picked list (TX, OK, LA, WY, AK, NM, WV, ND) is run as a robustness check.
3. **Where results go.** A new section in the existing RQ0b notebook and one paragraph in the RQ0b results, so RQ0b stays one story.
4. **Metro trimming.** 15% for the main result, 5% as a check; edge estimates written "at or before"; the 1929–2024 state series dates early-1970s breaks (§4.2).

## 9. Where this sits in the master plan

The spec's build order (§10) has 8 steps. Status and where Plan 1b fits:

| Step | Content | Research questions | Status |
|---|---|---|---|
| 1 | Scaffolding: dependencies, config, long format, test harness | — | **Done** (Plan 1) |
| 2a | Tier 0 US data → `us_state_longrun`, `us_metro_longrun` → RQ0b decade analysis | RQ0b | **Done** (Plan 1); review fixes committed (D-26, D-27) |
| **2b** | **Annual data → `us_state_annual`, `us_metro_annual` (1969+) → RQ0b break dating** | **RQ0b** | **This design (Plan 1b)** |
| 2c | City-proper population (Census decennial) → RQ0a city vs. metro | RQ0a | Next (Plan 2) |
| 3 | Tier 0 global: UN WUP, World Bank, Maddison → `global_agglomerations` | RQ0c | Planned |
| 4 | Tier 1: OECD and Eurostat metros → `oecd_metro_panel` | RQ1 | Planned |
| 5 | Tier 2: permits (BPS), prices (FHFA), Wharton index, OECD housing → adds columns to `us_metro_annual`; `national_housing` | RQ2, RQ3, RQ4 | Planned; starts from the panel Plan 1b creates |
| 6 | Stats NZ → Auckland event study | RQ5 | Planned |
| 7 | Featured cities, including hand-collected data | profiles | Planned |
| 8 | Paper, dashboard, `make all` end-to-end check | all | Planned |

How Plan 1b connects to later work:
- **RQ0c (step 3)** asks whether other countries show the same timing. A sharper US break year makes that comparison more precise. The global data is five-yearly, so a US year range of a few years is about the precision it can use.
- **RQ2–RQ4 (step 5)** use `us_metro_annual`. Plan 1b builds its population and income columns from 1969, so step 5 adds housing columns to an existing, tested panel.
- **The paper (step 8):** RQ0b becomes "whether and when", with the decade figure for the long view (1880+) and the annual figure for the timing (1969+).

## 10. Spec changes on approval

- §2 RQ0b: years become "states 1880–2020 decennial and 1929–2024 annual; metros 1940–2020 decennial and 1969–2024 annual".
- §4 panels: add `us_state_annual`; `us_metro_annual` starts in 1969 (population and income) and gains housing columns in step 5.
- §5 RQ0b: add the annual break-dating method (4.1–4.3 above).
- §8 risks: add the oil cycle and intercensal smoothing.
- §10 build order: add step 2b.
