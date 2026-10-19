# Design: RQ0a, did US cities stall, or did their metros? (Plan 2)

- **Date:** 2026-10-18
- **Status:** Approved 2026-10-19; implemented (Plan 2, `docs/superpowers/plans/2026-10-19-plan-2-rq0a-city-vs-metro.md`). §10 lists corrections found while writing the spec, §11 changes made while planning and building
- **Extends:** `2026-10-08-housing-growth-mismatch-design.md` (§2 RQ0a, §3 Tier 0, §5 RQ0a method, §6 notebook `1.0-lr-city-vs-metro`, §10 build step 2)
- **Builds on:** Plan 1 (`us_metro_longrun`, `geography.py`, the NHGIS source, D-27 drop rather than invent), Plan 1c (three periods cut at 1970 and 1990, preset decision rules, unit resampling), D-29 (design standards)

## 1. Summary in plain terms

Many large US cities stopped growing after 1950. RQ0a asks how much of that is the city proper falling behind while its metro area kept growing, and how much is the whole metro falling behind. The master spec's hypothesis: city-proper plateaus are largely an artifact of fixed city boundaries, and metro slowdown came later and unevenly.

The answer frames the rest of the project. If the old cities' metros kept growing, the "plateau" is a feature of where city lines are drawn, which is why every other RQ uses metros (D-08). RQ0a is descriptive. It says nothing about why people lived where they did.

**What gets built.** For every US metro, the population of its main city and of the rest of the metro (the suburbs), by decade, plus the city's land area so that annexation can be seen. Each headline metro is classified in three periods (1950–70, 1970–90, 1990–2020) by whether its city and its metro kept up with US population growth. Three questions get a preset answer:

1. Of the old big cities that fell behind in 1950–70, did most of their metros keep up? (suburbanization, metro stagnation, mixed, or can't tell)
2. Among metros that kept up, did fixed-boundary cities fall behind more often than annexing ones? (boundary effect or not)
3. Did more of the old metros fall behind after 1970 than in 1950–70? (later, not later, or can't tell)

**What success looks like:** sentences of the form *"Of the N old big cities that fell behind the US in 1950–70, X% sat in metros that kept up (90% range a–b): mostly suburbanization"*, and *"the share of old metros falling behind rose from F₁ in 1950–70 to F₂ in 1970–90"*, each with its robustness status.

## 2. Goals and non-goals

**Goals**
- A metro × decade panel `us_city_metro`, 1900–2020: main-city population, metro population (1940 on), suburb population, city land area (1950 on), an annexing flag per period, and the headline flag.
- A class for every metro and period under two yardsticks, with the three preset answers and their checks.
- A figure of the city's share of its metro over time and a figure of class shares by period.

**Non-goals**
- No same-boundary city populations (tract-based, 1970+). That is option B from the design conversation, kept for later if annexation results are unclear.
- No split of growth into moving vs. births and deaths for cities. Findings describe population, not moves (D-29).
- No causal claims, and no link to income or housing yet (RQ0b and RQ2–RQ4 do that).
- No fix for the 1900–1930 county splits (`geography.md`). Metro figures start in 1940 in this plan, so they aren't needed. The item stays open for any later pre-1940 metro use.

## 3. Data

### 3.1 Sources

| Purpose | Source | What exactly | Years | Access |
|---|---|---|---|---|
| City population | **Stanford CESTA, *Historical U.S. City Populations*** (U.S. Census Bureau and Erik Steiner) | `data/1790-2010_MASTER.csv`: 8,915 places, decennial counts, with each place's 2010 state+place FIPS (`STPLFIPS_2010`) | 1790–2010 | GitHub raw file pinned to commit `9b267ba` (2018-03-22); public domain, MIT for code; scripted |
| City population, 2020 | **NHGIS time-series table AV0** ("Total Population", **nominally integrated**), place level | Each place's count within its boundary at that census | 1970–2020 (decennial; 2020 used, 1970–2010 as a check) | IPUMS API, existing key |
| City land area, 1950–1990 | **Census Working Paper 27** (Gibson 1998), tables 18–22 | Land area (sq mi) of the 100 largest urban places in each census | 1950, 1960, 1970, 1980, 1990 | Text files on www2.census.gov; public domain; scripted |
| City land area, 2000–2020 | **Census Gazetteer files**, places | Land area (sq mi) of every place | 2000, 2010, 2020 | census.gov; public domain; scripted |
| City land area, gaps (only if needed, §3.4) | ICPSR 7735, *County and City Data Book Consolidated File: City Data, 1944–1977* | Cities over 25,000; whether it has land area is not yet confirmed | 1944–1977 | Manual ICPSR download, like the net-migration files |
| Metro population | `us_metro_longrun` (Plan 1) | 2023 CBSA boundaries built from NHGIS county counts | 1900–2020 (used from 1940) | existing |
| Central vs. outlying counties | OMB 2023 delineation file (already downloaded by `geography.py`) | Column "Central/Outlying County" (1,325 central, 590 outlying) | 2023 | existing |
| US population | `us_state_longrun`, **50 states + DC only** (territories and the NHGIS pseudo-states excluded) | 151.33M (1950), 203.21M (1970), 248.71M (1990), 331.45M (2020) | — | existing |

**Not used:** NHGIS table CL8. It is standardized to 2010 geography, so its 2020 value is the 2020 population inside the 2010 city boundary, not the city proper.

### 3.2 Which city is "the city"

- **Every metro:** the first-named city in its 2023 CBSA title (owner's choice A, 2026-10-18), e.g. Detroit for Detroit–Warren–Dearborn.
- **Headline metros:** the metros that contain a city from the 1950 top 100 (Working Paper 27, table 18). For these, "the city" is the metro's **largest city in 1950**. That is the first-named city in every case but one: Virginia Beach–Chesapeake–Norfolk, where Norfolk (213,513 in 1950) is the old city and Virginia Beach (5,390) is not. A count made while writing this spec gives **81 headline metros**: 78 matched by name, plus Louisville (title "Louisville/Jefferson County"), Spokane, and Norfolk's metro. The other 19 cities of the 1950 top 100 sit in a metro whose largest 1950 city is another top-100 city: Oakland and Berkeley (San Francisco), St. Paul (Minneapolis), Fort Worth (Dallas), Long Beach (Los Angeles), Cambridge (Boston), Newark, Jersey City, Yonkers, Paterson and Elizabeth (New York), Camden and Wilmington (Philadelphia), Gary (Chicago), Kansas City KS (Kansas City MO), Tacoma (Seattle), Fall River and New Bedford (Providence), Arlington CDP (Washington). The count is pinned when the crosswalk is built.
- **Crosswalk:** `references/crosswalks/metro_main_city.csv` (`cbsa_code, city_name, place_fips, top100_1950_rank, headline, note`), built by script and checked by hand. A second file lists every 1950 top-100 city with its CBSA, for the "all old cities as core" check. An old city with no CESTA series after 1940 (likely Arlington CDP, which is not incorporated) is listed and left out of that check.

### 3.3 City population rules

- **One source per year:** CESTA for 1900–2010, NHGIS AV0 for 2020, joined on `STPLFIPS_2010`.
- **CESTA stores missing counts as 0.** A 0 is read as missing, never as zero people. A city with a missing count in a period's start or end year gets no class for that period.
- **City-counties.** CESTA follows the Census "balance" (the consolidated government minus separately incorporated places inside it): Indianapolis (1970 on), Nashville-Davidson (1970 on), Louisville/Jefferson County (2010 on). Jacksonville's series likewise leaves out the beach towns and Baldwin. The jump at consolidation is real territory gained, so the annexing flag catches it (§3.4). Consolidations are listed in a committed table `references/crosswalks/city_county_consolidations.csv` (city, county, year, source); the headline ones are Nashville 1963, Jacksonville 1968, Indianapolis 1970 and Louisville 2003, the first three inside 1950–70.
- **Source disagreements are expected and are listed, not fixed.** Detroit 1970 is 1,514,063 in CESTA and 1,511,482 in Working Paper 27 (−0.17%); Jacksonville 1970 is 504,265 and 528,865 (WP27's figure equals all of Duval County). CESTA stays the single population source. A data test compares CESTA with WP27 for every headline city and year, within 0.5%, with the known exceptions listed in the test and in `geography.md`.
- **Suburbs** = metro population − city population. A test checks that no city is larger than its metro in any decade.
- **County splits inside a period** (D-27, `growth_comparable`): if a metro has a flagged decade inside a period, its metro and suburb growth for that period is dropped. Among headline metros this affects only Denver in 1990–2020 (Broomfield, 2001).

### 3.4 Land area and the annexing flag

- Area by city and year comes from WP27 (1950–1990, while the city is in that year's top 100) and the Gazetteers (2000–2020).
- **Annexing in a period:** land area at the end of the period is more than 20% above the start. Checks use 10% and 40%. A consolidation with its county inside the period always counts as annexing.
- **Gaps.** WP27 lists only each year's top 100. Of the 1950 top 100, 16 are missing from the 1960 table and 37 from the 1990 table (some are name mismatches the parser must handle). The missing ones are mostly cities that shrank, so the gaps are not random (§5).
  - **Bracket rule.** Area is treated as never shrinking materially (de-annexation and remeasurement are small: Detroit 139.6 → 138.0 → 138.7 sq mi in 1950, 1970, 1990). So if a city's area grew less than the threshold over a longer span that contains the period, it is fixed-boundary in that period. Example: area known in 1950 and 2000, up 5% overall, so fixed-boundary in 1950–70 and 1970–90.
  - If a period's flag is still unknown after the bracket rule for more than 5 headline cities, the plan adds the ICPSR 7735 file (if it has land area). Otherwise it is not used.
  - A city whose flag stays unknown is left out of rule 2 for that period, and the count is printed.
- **Area concept changes.** WP27 may report a consolidated city's whole area where CESTA reports the balance's population, and WP27 (1950–80) and the Gazetteers (TIGER, 1990 on) measure area differently. Area changes at the 1990→2000 source switch are checked by hand for the city-counties. The 20% threshold sits well above remeasurement noise of about 1–2%.

## 4. Methods

### 4.1 Growth and the two yardsticks

For a city, metro or suburb, growth over a period = population at the end ÷ population at the start − 1. Periods: **1950–70, 1970–90, 1990–2020** (Plan 1c's cuts). Background: city growth by decade 1900–1950 and metro growth in the 1940s are shown, not classified.

| Yardstick | "Keeps up" in a period if growth is… | Bars |
|---|---|---|
| **Main: relative to the US** | at least half of US growth over the same period | US growth +34.3%, +22.4%, +33.3% → bars **+17.1%, +11.2%, +16.6%** (code uses the unrounded values) |
| **Check: absolute** | more than 5% per decade, compounded | **+10.25%** (20 years), **+15.76%** (30 years) |

Otherwise it "falls behind". A value exactly at the bar keeps up.

### 4.2 Classes

| City | Metro | Class |
|---|---|---|
| keeps up | keeps up | growing |
| falls behind | keeps up | suburbanizing |
| falls behind | falls behind | stagnant |
| keeps up | falls behind | city-led |

**Core recovery** is a separate label: the city fell behind in an earlier period and keeps up in a later one. Class names are labels for growth patterns (D-29): "suburbanizing" means the city fell behind while its metro kept up, not that anyone is shown to have moved.

### 4.3 The three preset answers

The rules below are fixed before any class is computed. The headline metros are the whole 1950 top-100 set, not a sample, so each 90% range (999 draws resampling headline metros with replacement, seed 0, as in Plan 1c) measures how much an answer depends on which metros happen to be in the set. Draws where a needed group is empty are skipped and counted.

**Rule 1: how much of the post-1950 plateau is suburbanization?** Plateau cities = headline cities that fell behind in 1950–70. S = share of them whose metro kept up in 1950–70.

| 90% range of S (low, high) | Answer |
|---|---|
| low ≥ ⅔ | mostly suburbanization |
| high ≤ ⅓ | mostly metro stagnation |
| low > ⅓ and high < ⅔ | mixed |
| anything else (the range reaches across ⅓ or ⅔) | can't tell |

Also reported, without a rule: S weighted by 1950 city population, and S for 1970–90 and 1990–2020.

**Rule 2: is the plateau a boundary effect?** Among headline metros that **kept up** in 1950–70, D = (share of fixed-boundary cities that fell behind) − (share of annexing cities that fell behind). Conditioning on metros that kept up keeps metro growth (and with it most of the Sun Belt vs. Rust Belt difference) out of the comparison.

| 90% range of D (low, high) | Answer |
|---|---|
| fewer than 15 cities in either group (actual data; checked first) | not testable |
| low > 0 | plateau concentrated in fixed-boundary cities |
| high ≤ 0 | not a boundary effect |
| low ≤ 0 < high | can't tell |

The same comparison over all headline metros (not conditioned) is printed as context.

D > 0 is partly mechanical: people in annexed land are counted as city growth. That is what "boundary artifact" means, so it is the claim being tested, but it does not show what a fixed-boundary city would have done with more land. That counterfactual needs same-boundary populations (option B).

**Rule 3: did metros fall behind later?** F₁, F₂, F₃ = share of headline metros falling behind in 1950–70, 1970–90, 1990–2020. Differences use metros classed in both periods (paired draws: each draw keeps the same metros in every period).

| 90% ranges | Answer |
|---|---|
| low(F₂ − F₁) > 0 | later, by 1970–90 |
| otherwise, low(F₃ − F₁) > 0 | later, only after 1990 |
| high(F₂ − F₁) ≤ 0 and high(F₃ − F₁) ≤ 0 | not later |
| anything else | can't tell |

A gradual change shows up as F₁ < F₂ < F₃. Rule 3 names the first period that is clearly higher than 1950–70, and the three shares are always printed, so a steady rise is described as gradual rather than squeezed into one date.

"Uneven" is description only: F by Census region, Northeast + Midwest vs. South + West (by the metro's first-listed state).

### 4.4 Robustness and "fragile"

The main version (relative yardstick, half the US rate, 20% annexing threshold, main city only, all metro counties) sets each answer. If any check below gives a different answer, that answer is reported as **fragile**, with the disagreeing checks named (as in Plan 1c):

| Check | Why |
|---|---|
| Absolute yardstick | the half-of-US bar is our choice |
| Bar at ⅓ and ⅔ of US growth | same |
| Annexing threshold 10% and 40% (rule 2) | same |
| Core = all 1950 top-100 cities in the metro (e.g. New York + Newark + Jersey City + Yonkers + Paterson + Elizabeth) | old second cities otherwise count as suburbs |
| Metro = central counties only (OMB flag) | 2023 metros include counties that were rural in 1950 |

### 4.5 What we've already seen

While checking sources (2026-10-18) these values were looked at: Detroit 1950 and 1970, Houston's 1950 and 1990 land area, the CESTA rows for Indianapolis, Nashville, Jacksonville, Louisville, Norfolk, Virginia Beach, Denver and Spokane, and US totals by period. No growth class, share or rule result was computed.

## 5. Confounds: which way each could push

| Confound | Which way it could push | Handling |
|---|---|---|
| 2023 metro boundaries include counties that were rural in 1950; rural counties lost people in 1950–70 and gained exurban growth later | Metros look weaker early and stronger later: more "stagnant" in 1950–70 (lower S), and F₁ up, against "later" | Central-counties check |
| Old second cities (Newark, Oakland, St. Paul…) counted as suburbs | Pulls suburb growth down; metro classes unchanged | All-old-cities-as-core check |
| Headline cities chosen by 1950 size; many were at their peak | More cities fall behind in 1950–70; could raise F₁ (against "later") | Stated: this is the group the question asks about |
| Land area missing mostly for cities that shrank (they left the top-100 tables) | Fewer fixed-boundary decliners in rule 2's fixed group, lowering D (against "boundary effect") | Bracket rule; ICPSR 7735 if gaps remain; unknown count printed |
| Annexing cities are mostly in the South and West, in fast-growing metros | Raises D through metro growth, not boundaries | Rule 2 conditions on metros that kept up; unconditioned version printed as context |
| Census coverage improved over time, and large cities were probably undercounted more in early censuses | City counts could look stronger in later periods (more core recovery); likely a few percent, small next to bars of 11–17% | Stated |
| Births, deaths and ageing differ between cities and suburbs | Either way | Wording rule: findings describe population, not moves |
| Source switches (CESTA → NHGIS at 2020; WP27 → Gazetteer at 2000) | Either way, at those dates | 2010 overlap test for population; hand check of area at the switch |

## 6. Components

| Unit | What it does | Depends on |
|---|---|---|
| `sources/cesta.py` (new) | Downloads the pinned MASTER CSV; `load()` returns `place:<SSPPPPP>` population by year (`STPLFIPS_2010` is stored as a float, e.g. 203000.0 → `0203000`), 0 → missing | `_http.download_file` |
| `sources/wp27.py` (new) | Downloads tables 18–22; parses rank, place name, population and land area from the fixed-width text, including names without a comma ("Spokane city WA") and "*" notes | — |
| `sources/gazetteer.py` (new) | Downloads the 2000, 2010 and 2020 place Gazetteer files → land area (sq mi) by place FIPS | — |
| `sources/nhgis.py` (extend) | Adds the AV0 place extract → `place:` population, 1970–2020 | existing IPUMS client |
| `schema.py` (extend) | New `geo_level` "place" with prefix `place:` | — |
| `geography.py` (extend) | Builds and checks `metro_main_city.csv` and the old-cities list; central-county flag from the delineation file | existing delineation parser |
| `features.py` (extend) | `build_us_city_metro` → `data/processed/us_city_metro.parquet`, one row per metro × decade: city, metro, suburb population, city area, `headline`, `growth_comparable` | the above |
| `modeling/city_metro.py` (new) | `period_growth`, `classify`, `annexing`, `rule_share` (rule 1), `rule_diff` (rules 2 and 3), `paired_draws` | numpy, pandas |
| Notebook `1.0-lr-city-vs-metro` (new) | Panel checks, classes, the three answers and checks, figures, tables, finding | the above |

**Outputs**
- `reports/figures/rq0a_city_share.png`: city share of metro population by decade, 1940–2020, headline metros (median and interquartile band), with the featured US cities in the headline set labelled (Austin, not in the 1950 top 100, is drawn separately).
- `reports/figures/rq0a_classes.png`: share of headline metros in each class by period, both yardsticks.
- `reports/tables/rq0a_classes.csv`: `cbsa_code, city, period, city_growth, metro_growth, suburb_growth, yardstick, class, annexing, core_recovery`.
- `reports/tables/rq0a_answers.csv`: `rule, version, estimate, low, high, n, answer, detail` (the main row's `detail` says "robust" or names the disagreeing checks).

## 7. Testing

**Logic (fast, made-up data)**
- Growth and class for each of the four classes; a value exactly at the bar keeps up; core recovery across periods.
- Annexing: above and below 20%, consolidation, the bracket rule, unknown.
- Each rule's outcomes, including "can't tell" and rule 2's "not testable"; skipped draws counted.
- Paired draws keep the same metros across periods.
- CESTA 0 read as missing; WP27 parser on a small fixture with a "*" note and a comma-less name.

**Data (on downloaded files)**
- Detroit 1950 = 1,849,568 in CESTA and WP27 (`references/known_values.csv`).
- Houston land area 160.0 sq mi (1950) and 539.9 (1990) from WP27.
- CESTA 2010 = NHGIS AV0 2010 for every headline city (exact, or listed).
- CESTA vs. WP27 within 0.5% for every headline city and WP27 year, known exceptions listed (Detroit 1970 inside; Jacksonville 1970 outside).
- City ≤ metro in every decade; every headline metro has exactly one city; 81 headline metros (pinned when built); US totals by period as in §3.1.

## 8. Risks

| Risk | Mitigation |
|---|---|
| CESTA's upstream file changes or disappears | Pinned commit; raw file cached in `data/raw/cesta/` |
| ICPSR 7735 has no land area | Bracket rule first; unknowns left out of rule 2 and counted; "not testable" floor |
| WP27 name formats vary by year | Parser fixture; join WP27 to CESTA by name + state with a hand-checked match table for the misses |
| Few annexing cities among metros that kept up | Rule 2's "not testable" floor; unconditioned version as context |
| A 30-year last period vs. 20-year earlier ones | The relative yardstick compares with US growth over the same years |

## 9. Decisions made with the owner (2026-10-18)

1. The city in each metro is its first-named city; the headline is metros whose old main city was in the 1950 top 100 (A). §3.2 corrects one case (Norfolk).
2. Annexation is handled with land area and a fixed-boundary vs. annexing split (A); tract-based same-boundary cities (B) only if needed later.
3. Yardstick: relative to US growth as the main version, absolute as a check (C).
4. Periods: 1950–70, 1970–90, 1990–2020 (A), with 1900–1950 as background.

## 10. Corrections found while writing the spec

These differ from what was said in the design conversation:
1. **2020 city counts come from NHGIS table AV0, not CL8.** CL8 is standardized to 2010 boundaries, which would hide 2010–2020 annexation.
2. **Norfolk's metro is in the headline.** Under "first-named city" it would have dropped out, because the 2023 title starts with Virginia Beach. Headline metros use their largest 1950 city (§3.2): 81 metros, not about 80.
3. **Rule 2 now compares only metros that kept up.** Comparing all metros would mostly measure Sun Belt vs. Rust Belt metro growth, because annexing cities sit in fast-growing metros.
4. **Missing land area is not random.** Added the bracket rule and stated its direction (§3.4, §5). ICPSR 7735 becomes conditional.
5. **The US total excludes territories.** The state panel includes Puerto Rico from 2010 and NHGIS pseudo-states, so 2020 would be 334.7M instead of 331.4M.
6. **Detroit 1970 and Jacksonville 1970 differ between sources.** CESTA stays the single population source, with listed exceptions instead of a single known value.
7. **Denver 1990–2020 loses its metro class** under D-27 (Broomfield). Rule 3 uses metros classed in both periods.
8. **The 1900–1930 county splits are not part of Plan 2.** Metro figures start in 1940, so they aren't needed.

### 10.1 Spec and doc changes on approval

- Master spec §2 RQ0a row: years "classes 1950–2020; background 1900–1950"; §3 Tier 0: city-proper sources named; §4: new sources and `us_city_metro` panel; §5 RQ0a: replaced by §4 here; §7: the tests in §7.
- `Claude/methods/analysis-methods.md` RQ0a section; `geography.md` (main-city crosswalk, annexing rule, source disagreements, the 1900–1930 item stays open); `pipeline.md` (new panel); `Claude/research/sources.md` rows for CESTA, NHGIS AV0, WP27, Gazetteers (and ICPSR 7735 if used).
- `Claude/methods/decisions.md`: one entry for this design, numbered with the next free number at build time.

## 11. Changes made while planning and building (2026-10-19)

Recorded in D-31; each was checked on the real files.
1. No schema change: the existing geo level `city` (prefix `place:`) is used, not a new `place` level (§6).
2. **The 1990 Census Gazetteer is the 1990 land-area source** (§3.1, §3.4): area comes from WP27 for 1950–1980 and Gazetteers for 1990–2020; WP27's 1990 table is a check (identical populations, area within 0.22%). Unknown annexing flags at 20%: 5, 5 and 0 by period, so ICPSR 7735 is not used. **Addition to §4.5:** while planning, annexing flags were computed for the headline cities (unconditioned; 39 annexing / 37 fixed in 1950–70, 20 / 56 in 1970–90, 14 / 67 in 1990–2020). No class, share or rule result was computed before the rules ran.
3. Place-code changes are applied from a committed table: Louisville 2020 = metro government balance + the old city (a separate inactive place in 2020; 633,045 together), Louisville 1990 and 2000 = the pre-merger city, the 1990 "remainder" codes for Jacksonville and Indianapolis, Macon 2020 = Macon-Bibb County.
4. A city's 2020 count is used only where CESTA and NHGIS agree in 2010 within 0.5% (drops Honolulu, whose CDP was redefined, and Crystal City TX).
5. CESTA vs. WP27 (§3.3, §7): 8 headline city-years exceed 0.5%: Mobile 1960, Jacksonville 1970, Portland 1970, Sacramento 1970, Austin 1970, Youngstown 1970, Shreveport 1980, Dayton 1980.
6. Austin was 73rd in 1950, so it is a headline metro; `rq0a_city_share.png` labels all nine featured US metros (§6 Outputs said otherwise).
7. Puerto Rico's metros are left out (387 metros). A committed overrides table settles 7 main-city names; 3 metros have no city series.
8. Connecticut's legacy counties count as central. Hartford, New Haven and Bridgeport resolve through the legacy-county mapping.
9. Checks per rule (§4.4): rule 1 — absolute yardstick, bars at ⅓ and ⅔, core = all old cities, central counties; rule 2 — absolute yardstick, bars at ⅓ and ⅔, annexing threshold 10% and 40%, central counties; rule 3 — absolute yardstick, bars at ⅓ and ⅔, central counties.
10. Rule 3 is reported as two rows (F₂ − F₁ and F₃ − F₁); context rows share `rq0a_answers.csv` with an empty answer.

