# Design: RQ0c, did other countries see the same change at the same time? (Plan 3)

- **Date:** 2026-10-14
- **Status:** Approved by the owner, 2026-10-14 (all eight decisions in §8 accepted as recommended)
- **Extends:** `2026-10-08-housing-growth-mismatch-design.md` (§2 RQ0c, §3 peer groups, §4 sources and panels, §5 RQ0c method, §10 build step 3)
- **Builds on:** Plan 1 (RQ0b decade results, `modeling/breaks.py`), D-20 (pooled tests, decade fixed effects), D-27 (drop rather than invent). Waits on Plan 1b (`2026-10-14-rq0b-annual-break-dating-design.md`) for one number only, the US break year.

## 1. Summary in plain terms

RQ0b found that **Americans used to move toward the richer parts of the country and largely stopped**, somewhere around the 1970s–80s. RQ0c asks whether that also happened elsewhere, and when. If rich countries in Europe, Japan or Australia saw the same fade at the same time, the US story is probably about something they all share (the end of farm-to-factory migration, ageing, two-earner households). If peers kept moving toward rich regions while Americans stopped, the US story is more likely about something American, such as housing limits in its richest places.

**The main design change from the master spec.** The master spec's RQ0c model regresses city growth on **national** GDP growth. That answers a different question: "do cities grow faster in countries whose economies grow faster?" It can't see whether people move toward the **richer places inside a country**, which is what RQ0b measures. So this design makes the headline test a copy of RQ0b run inside other countries:

1. **Main test, regions (like US states).** For about 16 Western European countries (Rosés-Wolf database, regions every ten years from 1950) and for Japan, Australia and others (DOSE database, 1960s+): did regions with higher income per head grow faster in population, decade by decade? Same formula as RQ0b, same ten-year steps, same break tests.
2. **Second test, cities (like US metros).** The UN's 1,860 large agglomerations, 1950–2015, each matched to its region, with the same question asked of cities.
3. **Context, the master spec's national model.** City growth vs. national GDP growth, by peer group, for the whole world. Kept because it covers every country, but labeled as a different question and not compared to the US break.

**How it connects to Plan 1b.** Plan 1b will give the US break year, e.g. "most likely 1978, range 1974–83". The regional data comes every ten years, so the comparison can only be made at a decade boundary. RQ0c therefore computes the US-vs-peers comparison **for 1970, 1980 and 1990 now**, and the final paragraph picks the row that matches Plan 1b's year once it's known. Nothing in RQ0c has to wait.

**What success looks like:** a sentence of the form *"In Western Europe and Japan, the pull of richer regions also weakened, but around 19XX (or: did not weaken); the US drop after 19XX was larger by Z (p = …)"*, plus a figure with the US β line on the same scale as the peers'.

## 2. Goals and non-goals

**Goals**
- A region × decade panel for peer countries, 1950–2020, with population and income per head from one source per country.
- An agglomeration × five-year panel for the world, 1950–2015, with national GDP per head, urbanization, peer group and (where possible) its region's income.
- Decade-by-decade β for each peer group, on the same scale as the US decade β, with the same break tests as RQ0b.
- A direct test of whether the US change was larger than its peers' at the US break date.
- A check that the method, run on US data from the global sources, reproduces the US result.

**Non-goals**
- No causal claims. RQ0c stays descriptive (spec §1).
- No annual break dating abroad. Regional data is mostly decadal; annual dating stays a US-only result (Plan 1b).
- No new housing variables. That's RQ1–RQ4.
- No hand-collected regional data in this plan. Countries without regional income in Rosés-Wolf or DOSE are covered only by the context model.

## 3. Data

### 3.1 What's used

| Purpose | Source | What exactly | Years | Access |
|---|---|---|---|---|
| Regional population and income, Europe | **Rosés-Wolf database, v7 (2025)** | NUTS-2 regions (2010 boundaries): population and GDP per head in 2011 PPP $ | Benchmarks 1950, 1960, 1970, 1980, 1990, 2000, 2010, (2015, and the v7 extension to 2022) | Free, **manual download** (site is bot-protected), like ICPSR |
| Regional population and income, rest of world | **DOSE V2.11** (Wenz et al. 2023) | First-level regions (GADM-1): population and GDP per head (2015 US$) | 1953–2020, annual where reported; countries start at different years (Japan 1960, Australia 1953 sparse, Canada 1981, Korea 1985) | Zenodo CSV, CC BY 4.0, scripted download |
| Agglomeration population | **UN World Urbanization Prospects, 2018 revision**, File 12 | 1,860 agglomerations with 300k+ people in 2018 (144 in the US), with coordinates and the UN's statistical concept for each | 1950–2015 every 5 years (later values are projections, not used) | Archive zip, CC BY 3.0 IGO, scripted download |
| National urbanization rate | WUP 2018, File 21 | % of population urban, national definitions | 1950–2015 | same zip |
| National GDP per head | **Maddison Project Database 2023** | `gdppc`, 2011 PPP $ | 1950–2022; 146 of 169 countries from 1950 | Dataverse file, CC BY 4.0 |
| Peer-group rule; GDP check | World Bank WDI and `OGHIST.xlsx` | Income groups by year (FY89+); GDP per head, constant 2015 US$ | 1960–2025 | API without key, CC BY 4.0 |
| Robustness only | WUP 2025, File 21 (Degree of Urbanisation cities) | 16,828 cities defined the same way in every country | 1975–2050 annual | CC BY 3.0 IGO |

Full URLs, licenses and coverage notes are in `Claude/research/sources.md` (updated 2026-10-14).

### 3.2 Why WUP 2018 and not the new 2025 revision

The master spec's "~1,900 agglomerations, 300k+, five-year steps from 1950" is the **2018** revision. The UN replaced it in November 2025 with a different product:

| | WUP 2018 | WUP 2025 |
|---|---|---|
| City definition | Each country's own: urban agglomeration (US, France, China), **city proper** (all of Germany, Spain), metropolitan area (Italy, Canada) | One rule everywhere: dense 1 km² cells (1,500+/km²) adding up to 50,000+ |
| Years | 1950–2015 estimates | **1975**–2025 estimates |
| US cities | 144 urban agglomerations (Detroit 1950: 2.77M) | Dense cores only (Detroit 2020: 0.83M; 63 US cities reach 300k) |

WUP 2025 starts in 1975, which leaves no "before" period for a 1970s–80s break, and its dense-core cities leave out the suburbs, where most US metro growth happened. WUP 2018 covers 1950 onward, but its city concepts differ between countries. The design handles that by **only ever comparing cities within the same country** (country × period fixed effects, §4.1), so a German city proper is compared with other German cities proper, never with a US urban agglomeration. WUP 2025 is used as a 1975+ check because its definition is the same everywhere.

The 2018 files are no longer on the main download page but are in the UN's archive zip (checked 2026-10-14). They are old-style `.xls`, so the package needs `xlrd`.

### 3.3 Why regional income is needed, and where it exists

RQ0b's test is "do people move toward the richer places **inside** the country". That needs income for places inside the country. National GDP can't stand in for it: within one country in one decade, every city has the same national GDP.

Sub-national income before 1980 exists for few countries:
- **Rosés-Wolf:** Western Europe (about 16 countries; exact list confirmed at download), every ten years since 1900. This is the backbone.
- **DOSE:** 83 countries, but only 17 have any data by 1970 and 25 by 1980. The useful ones for a 1950s–1980s comparison are Japan (47 prefectures from 1960), Australia (8 states, sparse years), and, as developing-country context, China, Brazil, Mexico and Chile (1960+). Canada (1981) and Korea (1985) start too late to see a "before" period; they can only show what happened afterwards.
- **OECD regional data** starts around 2000, too late for timing. Not used.
- **DOSE includes the US from 1963.** That makes a calibration check possible (§4.4).

So the main test covers the **high-income mature** peers well (Western Europe, Japan, Australia) and other groups thinly. That fits the question: the comparison that matters for a housing story is with other rich countries.

### 3.4 Matching

- **Agglomeration → country:** WUP's own ISO3 code (in the 2018 data-sources file). Taiwan (TWN), Hong Kong (HKG) and Macao have their own codes in both WUP and Maddison. Agglomerations in countries with no Maddison GDP for a period (former Soviet republics before 1973, Czechia before 1970, Slovakia before 1985) are **dropped for those periods**, not filled from a parent country (same principle as D-27). The notebook prints how many.
- **Agglomeration → region:** WUP gives each agglomeration's coordinates. A point-in-polygon match against the Rosés-Wolf NUTS-2 shapefile (Europe) and GADM-1 boundaries (DOSE countries) assigns a region. The result is committed as `references/crosswalks/wup_to_region.csv` and checked by hand for the featured cities and any agglomeration within 10 km of a regional border. This needs `geopandas` (decision 5).
- **Region → country:** by the NUTS country prefix or the DOSE `GID_0` code.

### 3.5 Peer groups

The master spec lists four groups and says they come from "World Bank income group plus historical classification". Two problems: the four groups leave out Latin America and Sub-Saharan Africa, which hold about a quarter of WUP's agglomerations, and a membership that changes over time could create a fake break when a country moves up (Korea became high-income in the mid-1990s). Proposed rule, **fixed for the whole period**, in a committed table `references/crosswalks/peer_groups.csv` (ISO3, group, reason):

| Group | Rule | Examples |
|---|---|---|
| 1. High-income mature | OECD member by 1975, except Turkey (D-17) | Western Europe, **US**, Canada, Japan, Australia, NZ |
| 2. High-income newly developed | World Bank high-income in the latest year and not in groups 1 or 3 | Korea, Israel, Singapore, Taiwan, Hong Kong, Gulf states, Chile, Uruguay |
| 3. Transition | Communist-ruled in Europe or the USSR in 1989 | Poland, Czechia, Romania, Russia, Ukraine, Kazakhstan |
| 4. Developing Asia, Middle East and North Africa | UN regions Asia and Northern Africa, not in 1–3; plus Turkey | China, India, Vietnam, Egypt, Iran, Turkey |
| 5. Other developing (new) | Everything else | Latin America (except group 2), Sub-Saharan Africa, Pacific islands |

Group 5 is reported but not discussed in detail. A check with time-varying World Bank groups (1987+) is run for group 2.

## 4. Methods

### 4.1 Main test: regions, within each country (the RQ0b copy)

For region r in country c and decade d:

`growth(r,d) = ln pop(r, d+10) − ln pop(r, d) = α(c,d) + β_g(d) · ln income(r,d) + e(r,d)`

- **α(c,d), one constant per country and decade**, takes out everything national: national growth, baby booms, immigration law, how a country defines its regions' income. What's left is "did the richer regions of this country grow faster than its poorer regions". That's what the US decade fixed effects do in RQ0b; with one country, "per decade" and "per country and decade" are the same thing.
- **β_g(d)** is estimated separately for each peer group g and decade d. In the US, β is in "extra growth over ten years per 1 log point of income". Same here, so the US line can be drawn on the peer chart.
- Income is measured at the start of the decade, as in RQ0b. Unweighted (each region counts once, like each US state). Standard errors clustered by region.
- Decades 1950–2010 (growth to 2020). If Rosés-Wolf v7 has no 2020 benchmark, the last step is 2010–2015 growth ×2, flagged.
- **Break tests, as in RQ0b:** pooled over decades, with a Chow test at each of 1970, 1980 and 1990 and the BIC search over decade boundaries (`breaks.break_search`, up to 3 breaks, at least 2 decades per segment). To reuse `breaks.py` unchanged, growth and log income are first demeaned within country × decade, which removes α(c,d) exactly. This is the same device Plan 1b uses for year effects. A test confirms it gives the same answer as explicit dummies.
- **Per-country lines** for the larger countries (France, Germany, Italy, Spain, UK, Japan) are shown as small multiples with confidence bands. With 10–47 regions each they are noisy; they show whether one country drives the group result.

**Different income concept, stated plainly.** RQ0b uses personal income by place of residence (BEA). Rosés-Wolf and DOSE measure regional GDP, by place of work. GDP is inflated in regions that people commute into (Hamburg, Brussels, inner London). The calibration check (§4.4) measures how much this matters by running the US with DOSE state GDP instead of BEA income.

### 4.2 Same timing as the US?

Pooled panel of US states (`us_state_longrun`, decades 1950–2010) and the regions of one peer group:

`growth = α(c,d) + β · y + δ · y · post_T + β_US · y · US + δ_US · y · post_T · US + e`

with y = log income, `post_T` = decades starting at or after T, and US = 1 for US states.

- **δ** is how much the pull of richer regions changed in the peers at T.
- **δ_US** is how much **more** it changed in the US.
- Reading: δ < 0 and δ_US ≈ 0 means the same change at the same time; δ ≈ 0 and δ_US < 0 means the change was American; both negative means a shared change that was stronger in the US.
- **T** is run for 1970, 1980 and 1990 now (comparison contract, §5.1). Each peer group's own BIC break years (§4.1) are reported next to the US ones, so "different timing" is visible too, not only "different size".

### 4.3 Second test: cities

The same model as 4.1 with WUP 2018 agglomerations as the units, each carrying its region's income, and growth over ten years (1950–1960, …, 2005–2015). Country × decade constants as above, so each country's city concept only meets itself.

Checks:
- Without the countries where WUP uses city proper (Germany, Spain and others listed in the data-sources file), because city-proper growth mixes in suburbanization (RQ0a's issue).
- Only agglomerations that already had 300k people in 1950 (about 300). WUP's list is selected on **2018** size, which favors places that grew; a fixed early sample avoids that.
- WUP 2025 Degree-of-Urbanisation cities, 1975–2015, same model: same definition in every country, at the price of a late start.

### 4.4 Calibration: the US through the global lens

Two runs check that the global method would find the US result if it were there:
1. **DOSE US states, 1963+.** The 4.1 model on DOSE's US population and GDP per head. The decade β for 1970–2010 should land inside the confidence intervals of the RQ0b state β (BEA personal income). A clear gap means the income concept (GDP vs. personal income) changes the answer, which is then a stated limitation for all peers.
2. **WUP US agglomerations with BEA state income.** The 4.3 model on the 144 US agglomerations, with their state's income. It should look like the RQ0b metro β.

### 4.5 Context: the master spec's national model

For agglomeration a in country c, five-year period t:

`Δ5 ln pop(a,t) = α_g(t) + β_g(d) · Δ5 ln GDP per head(c,t) + γ_g · urban share(c,t) + e(a,t)`

estimated by peer group, with β allowed to differ by decade, standard errors clustered by country. It answers "did city growth stop following national economic growth, and when". It is shown as a world-level figure and feeds the dashboard map, but it isn't compared to the US break, for two reasons: the US is one country, so its national β per decade rests on two five-year points; and in developing countries it mostly measures rural-to-urban migration, which doesn't apply to the US after 1950.

### 4.6 Robustness

| Check | Why |
|---|---|
| Income standardized within country × decade | Same as RQ0b; different spreads of regional income across countries |
| Without the 2010–2015 ×2 step (if used) | It's a half-decade stretched to a full one |
| Peer group 1 without the UK / without Japan | One large country could drive the group |
| Rosés-Wolf 1990 PPP instead of 2011 PPP | Within-country comparisons should not depend on the price base; a gap flags a data problem |
| Clustering by country instead of region (group 1, about 20 countries) | Regions in one country share shocks |
| Cities: without city-proper countries; fixed 1950 sample; WUP 2025 cities | §4.3 |
| Group 2 with time-varying World Bank groups | §3.5 |

## 5. Components

| Unit | What it does | Depends on |
|---|---|---|
| `sources/un_wup.py` (new) | Downloads the WUP 2018 archive zip (and WUP 2025 File 21); `load()` returns agglomeration population (`wup:<city code>`, persons) and national % urban (`iso3:`); a separate `agglomeration_attributes()` returns coordinates, statistical concept, capital flag and census years | `_http.download_file`, `xlrd` |
| `sources/maddison.py` (new) | Dataverse file 421302 → `gdppc` (usd_2011_ppp) and population, `iso3:` | — |
| `sources/worldbank.py` (new) | WDI API (`NY.GDP.PCAP.KD`) and `OGHIST.xlsx` → GDP and income group by year | — |
| `sources/roses_wolf.py` (new) | Reads the manually downloaded v7 file from `data/raw/roses_wolf/` (fails with a clear message if absent, like `icpsr.py`) → `nuts2:` population and GDP per head | manual download |
| `sources/dose.py` (new) | Zenodo CSV → `gadm1:` population and GDP per head (2015 US$) | — |
| `schema.py` (extend) | New `geo_level` `"region"` with prefixes `nuts2:` and `gadm1:` | — |
| `config.py` (extend) | RQ0c years; `RQ0C_COMPARE_YEARS = (1970, 1980, 1990)`; `US_BREAK_YEAR` (None until Plan 1b) | — |
| `geography.py` (extend) | Agglomeration → region point-in-polygon, writing the reviewed `wup_to_region.csv` | `geopandas` |
| `references/crosswalks/` (new files) | `peer_groups.csv`, `wup_to_region.csv` | — |
| `features.py` (extend) | `build_global_regions` (region × decade) and `build_global_agglomerations` (agglomeration × 5 years, spec §4 panel); two lines in `main()` | interim sources, crosswalks |
| `modeling/global_timing.py` (new) | `demean_within`, `group_decade_betas`, `group_break_tests` (wrapping `breaks.chow_test` and `breaks.break_search`), `us_vs_peers`, `national_link` (4.5) | `breaks.py` (read-only), statsmodels |
| Notebook `1.2-lr-global-timing` (new) | Figures, tables, finding; the final comparison paragraph reads `US_BREAK_YEAR` | the above |

The master spec puts RQ0c's regression in `modeling/elasticity.py`, which doesn't exist yet (RQ1). Keeping it in its own module avoids building RQ1 code early.

**Outputs**
- `reports/figures/rq0c_regional_betas.png`: β by decade, one line per peer group, US state β on the same axes, with the 1970/1980/1990 boundaries marked.
- `reports/figures/rq0c_country_betas.png`: small multiples for the larger countries.
- `reports/figures/rq0c_national_link.png`: the context model by peer group.
- `reports/tables/rq0c_tests.csv`: `group, version, spec, chow_1970_p, chow_1980_p, chow_1990_p, bic_breaks, n_units, n_countries, decades`.
- `reports/tables/rq0c_us_comparison.csv`: `group, version, T, delta, delta_se, delta_us, delta_us_se, delta_us_p, n_us, n_peer`, one row per T in 1970, 1980, 1990.

### 5.1 Comparison contract with Plan 1b

- Everything above is computed for all three decade boundaries now.
- When Plan 1b reports its break year and range, `US_BREAK_YEAR` is set to the decade boundary nearest the year (1974 → 1970, 1978 → 1980, 1983 → 1980). An exact tie such as 1985 has no nearest boundary, so both rows (1980 and 1990) are reported. If Plan 1b's range spans two boundaries, both rows are reported.
- Until then, the notebook headlines **1980 (provisional)**: the master-spec hypothesis and Plan 1's main Chow date. The finding paragraph carries the word "provisional" until `US_BREAK_YEAR` is set.
- If Plan 1b finds no break, the comparison is reported for all three years as a description, without a headline year.

Plan 1b's year is finer than anything RQ0c can test: regional data comes in ten-year steps (five for cities). The paper says so: the US year is dated from annual data; peers are compared at the nearest decade.

## 6. Testing

**Synthetic recovery (fast)**
- Regions in 5 countries, with country × decade shocks and a planted drop in β at 1980 → the group β drops at 1980, the Chow test at 1980 rejects, and the country shocks don't leak into β.
- No planted drop → no Chow rejection at 5% in more than about 5% of 200 simulated panels.
- US-vs-peers: planted US-only drop → δ_US significantly negative and δ ≈ 0; planted shared drop → δ significantly negative and δ_US ≈ 0.
- Demeaning: on small panels, demeaning within country × decade then calling `breaks.break_search` gives the same breaks and BIC as explicit country × decade dummies.
- Context model: planted β = 0.5 and γ = 0.02 recovered within tolerance by group; clustered standard errors finite.

**Data (on cached data)**
- Known values from WUP 2018 File 12 in `references/known_values.csv`: Tokyo 1950 = 11,274,641; New York–Newark 1950 = 12,338,471; 1,860 agglomerations, 144 in the US.
- Every country in either panel has exactly one peer group; spot checks: US → 1, Japan → 1, Korea → 2, Poland → 3, Vietnam → 4, Turkey → 4, Brazil → 5.
- Rosés-Wolf regions add up to Maddison's national population within 2% in 1950, 1980 and 2010 for each country.
- DOSE US state population within 1% of BEA's for 1970, 1980, 1990, 2000, 2010.
- Every agglomeration in a country with regional data has exactly one region in `wup_to_region.csv`; featured cities are in the expected region (London → UKI, Paris → FR10, Tokyo → JPN Tokyo).
- Plausibility: no agglomeration halves or more than triples in five years unless it is on the existing growth allowlist (extended for RQ0c).
- Agglomeration-periods dropped for missing national GDP are exactly the documented ones (former Soviet republics before 1973, etc.).

**Calibration (notebook, not pytest):** §4.4. If DOSE US β falls outside the RQ0b intervals, the finding says so and names the income concept as a limitation.

## 7. Risks

| Risk | Mitigation |
|---|---|
| City concepts differ by country in WUP 2018 | Comparisons only within a country (country × period constants); city-proper countries dropped in a check; WUP 2025 uniform definition as a 1975+ check |
| Regional GDP (place of work) ≠ US personal income (place of residence) | DOSE US calibration (§4.4); stated in the finding |
| Few regions per country (10–47); few peer countries with pre-1980 regional income | Results pooled by peer group; per-country lines only as small multiples; country-cluster check |
| Regional data is decadal, the US break year is annual | Comparison at the nearest decade boundary, all three boundaries reported (§5.1) |
| WUP's sample is selected on 2018 size (survivors) | Main test uses regions, which are a full partition of each country; fixed 1950 city sample as a check |
| WUP values between censuses are interpolated by the UN | Ten-year growth, not five, for the comparable tests; census years are kept in `agglomeration_attributes()` for a check that keeps only city-decades with a census at both ends, if results look suspicious |
| Peer-group membership chosen after the fact | Fixed rule (§3.5), committed table, time-varying check for group 2 |
| Rosés-Wolf can't be scripted (bot-protected pages) | Manual download, documented like ICPSR; the source fails loudly if the file is missing |
| WUP 2018 archive link disappears | Raw zip cached in `data/raw/un_wup/`; URL and archive page in `sources.md` |
| Former USSR / Czechoslovakia / Yugoslavia lack early national GDP | Those periods dropped, listed in the notebook |

## 8. Decisions for the user

Each has one recommendation.

1. **Headline test.** Make the within-country regional test (§4.1–4.2) the RQ0c answer, and keep the master spec's national-GDP model as labeled context (§4.5). *Recommendation: yes.* The national model can't measure the thing RQ0b measured, so comparing it with the US break would be comparing different questions.
2. **Which WUP revision.** 2018 (1950–2015, country-specific definitions) for the main city test, 2025 (1975+, one definition) as a check. *Recommendation: 2018 main, 2025 check.* 2025 starts too late to see a 1970s "before" period and leaves out US suburbs.
3. **Regional income sources.** Rosés-Wolf v7 for Europe (one manual download) plus DOSE for the rest. *Recommendation: both.* Without Rosés-Wolf there is almost no European regional income before 1970; without DOSE there is no Japan.
4. **Peer groups.** Fixed membership by the rule in §3.5, plus a fifth group for Latin America and Sub-Saharan Africa. *Recommendation: yes.* Changing membership can create fake breaks; leaving a quarter of the world's cities unassigned breaks the "every country gets one group" test in the master spec.
5. **City-level version and `geopandas`.** Matching cities to regions needs a point-in-polygon step and a new dependency, `geopandas`, used once to build a committed crosswalk. *Recommendation: include it.* It's the "cities" half of the question and mirrors the US metro version; the region test alone would answer RQ0c, so this can be cut if the dependency is unwelcome.
6. **End year for cities.** Stop at 2015 (last UN estimate in the 2018 revision) rather than use the 2020 projection. *Recommendation: 2015.* A projection would put assumed rather than observed growth into the last period.
7. **Provisional US year.** Headline 1980 until Plan 1b reports, with all three decade boundaries computed. *Recommendation: yes* (§5.1).
8. **When to build.** *Recommendation: start once Plan 1b is merged into its base branch, independent of Plan 2 (RQ0a).* The master build order puts step 3 after RQ0a, but RQ0c doesn't use RQ0a's outputs; waiting for Plan 1b only avoids merge conflicts (§10).

## 9. Where this sits in the master plan

| Step | Content | Research questions | Status |
|---|---|---|---|
| 1 | Scaffolding | — | Done (Plan 1) |
| 2a | US decade data → RQ0b decade analysis | RQ0b | Done (Plan 1) |
| 2b | US annual data → RQ0b break dating | RQ0b | Approved, in progress (Plan 1b) |
| 2c | City-proper population → RQ0a | RQ0a | Next (Plan 2) |
| **3** | **Global: WUP, Maddison, World Bank, plus Rosés-Wolf and DOSE (new) → `global_regions` (new), `global_agglomerations` → RQ0c** | **RQ0c** | **This design (Plan 3)** |
| 4 | OECD and Eurostat metros → RQ1 | RQ1 | Planned |
| 5 | Housing → RQ2–RQ4 | RQ2–RQ4 | Planned |
| 6 | Auckland | RQ5 | Planned |
| 7 | Featured cities | profiles | Planned; reuses `un_wup`, `maddison` and the WUP 1950+ series built here |
| 8 | Paper, dashboard | all | Planned; the dashboard world map uses the context model (§4.5) |

Later work that reuses this: RQ1 (step 4) needs the UN WUP ↔ OECD metro crosswalk (spec §7) and peer groups; the peer-group table and `un_wup.py` built here are the base for both.

### 9.1 Files both plans touch (merge planning)

| File | Plan 1b | RQ0c | Conflict risk |
|---|---|---|---|
| `us_housing_crisis_analysis/features.py` | `build_us_state_annual`, `build_us_metro_annual`, `energy_states`, `main()` entries | `build_global_regions`, `build_global_agglomerations`, `main()` entries | **High in `main()`** (both add panel lines); new functions appended at the end of the file, so the rest merges cleanly |
| `us_housing_crisis_analysis/config.py` | Annual year ranges, energy-state threshold (likely) | RQ0c years, compare years, `US_BREAK_YEAR` | Medium; both append constants. RQ0c adds its block after the ICPSR block |
| `us_housing_crisis_analysis/modeling/breaks.py` | May be generalized ("decades → any period column") | Read-only use of `chow_test`, `break_search` | Medium: if Plan 1b renames the `decade` column or changes signatures, `global_timing.py` adapts at rebase |
| `us_housing_crisis_analysis/sources/__init__.py` | Probably none (BEA is extended, not added) | Appends five names to `SOURCE_NAMES` | Low |
| `us_housing_crisis_analysis/sources/bea.py` | Two new requests | None | None |
| `us_housing_crisis_analysis/schema.py` | None expected | Adds `region` geo_level | Low |
| `pyproject.toml` | None expected | Adds `xlrd`, `geopandas` | Low |
| `references/known_values.csv` | Possibly | Adds WUP rows | Low (append) |
| `tests/` | `test_bea.py`, `test_features.py`, new annual-break tests | New `test_un_wup.py`, `test_maddison.py`, `test_worldbank.py`, `test_roses_wolf.py`, `test_dose.py`, `test_global_timing.py`; additions to `test_features.py`, `test_schema.py` | Medium in `test_features.py` (both append) |
| `Claude/research/sources.md` | BEA row | WUP, World Bank, Maddison, Rosés-Wolf rows, new DOSE/OECD rows, literature (**done on this branch**) | Low: different rows |
| `Claude/methods/analysis-methods.md` | RQ0b section and results log | RQ0c and Peer groups sections | Low: different sections; results log both append (medium) |
| `Claude/methods/decisions.md` | New D-28+ entries | New entries after approval | **High: numbering.** RQ0c's entries are written after Plan 1b merges, numbered from the next free number |
| `Claude/methods/pipeline.md`, `geography.md` | Possibly | New sources, crosswalks | Low to medium |
| Master spec `2026-10-08-…-design.md` | §2 RQ0b row, §4, §5 RQ0b, §8, §10 | §2 RQ0c row (the line right after RQ0b's), §3, §4, §5 RQ0c, §7, §8, §10 | **High in §2 and §10**: adjacent lines in the same tables |
| `Makefile` | Possibly none | Possibly none | Low |

**Proposed merge order:** Plan 1b merges first; the RQ0c implementation branch starts from (or rebases onto) that result. This design branch only adds this spec and the `sources.md` rows, so it merges cleanly now.

## 10. Spec changes on approval

- §2 RQ0c row: question "Did peers see the same weakening of population flows toward richer regions, and at the same time?"; hypothesis unchanged; years "regions 1950–2020 (decadal), agglomerations 1950–2015 (5-year)".
- §3 data tiers, Tier 0 global: add regional population and income (Rosés-Wolf, DOSE); WUP 2018 revision named; urbanization rate 2018.
- §3 peer groups: the fixed rule and the fifth group (§3.5).
- §4 package layout: add `sources/roses_wolf.py`, `sources/dose.py`, `modeling/global_timing.py`; RQ0c removed from `elasticity.py`; schema gains the `region` level.
- §4 processed panels: add `global_regions` (region × decade, 1950–2020); `global_agglomerations` ends in 2015.
- §5 RQ0c: replace with §4.1–4.5 above.
- §7 testing: the tests in §6.
- §8 risks: city concepts, income concept, decadal vs. annual timing.
- §10 build step 3: add Rosés-Wolf and DOSE.
- `Claude/methods/decisions.md`: one entry for the approved decisions in §8, numbered after Plan 1b's.
