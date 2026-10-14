# Analysis Methods

Model specifications for each research question. Update this file whenever a specification, variable definition, or robustness check changes.

## Evidence standard

RQ0–RQ4 are descriptive and associational. RQ5 is the one causal design. The paper labels findings accordingly.

## RQ0a — City vs. metro decomposition (US, 1900–2020)

- For each metro: track the central city's share of metro population by decade, and split metro growth into core growth and suburban growth.
- Classification:
  - **suburbanizing:** core declined, metro grew
  - **stagnant:** both stagnated
  - **growing:** both grew
  - **core-recovery:** core declined and then grew again
- Thresholds for each class will be set in `config.py` and recorded here.

## RQ0b — US structural break (decennial; states 1880–2020, metros 1940–2020)

For each decade d, with i a state or a metro:

Δln(pop)_{i,d} = α_d + β_d · ln(income per capita)_{i,d−1} + ε_{i,d}

- β_d > 0 means population flows toward richer places. A falling β_d means that flow is weakening.
- **Start-year rule:** each version starts at the first decade from which income exists for every decade onward. No decade is interpolated.
- **Income, state version (1880–2020):** Klein (1880, 1890, 1900, 1910); Easterlin (1920); BEA state personal income per capita (annual from 1929; decade years 1930+ are used).
- **Income, metro version (1940–2020):** 1940 full-count census wage and salary income (IPUMS), aggregated county → CBSA; Census county median family income for 1950 and 1960 (1949 and 1959 income), from the County Data Books in ICPSR 2896 (Haines), with NHGIS table NT39 as a cross-check for 1950; BEA personal income per capita (1969, used for 1970, onward).
  - **BEA metro income definition:** BEA county personal income summed over the metro's 2023 counties ÷ BEA county population summed the same way (D-23). Connecticut uses the 8 old counties via `ct_legacy_counties.csv`, like every other year.
  - **1950/1960 income definition:** median income of families (not families and unrelated individuals), current dollars: 1949 income from the 1952 County Data Book (ICPSR 2896 Part 72, `var20`) and 1959 income from the 1962 County Data Book (Part 74, `var22`). US rows match the published census medians ($3,073 and $5,660). County IDs come from the `fips` column; in the 1952 file `statefip`/`counfip` aren't FIPS codes. Only county rows (`level` = 1) are kept, plus these rules: DC's 1952 code 11010 is set to 11001; Alaska's judicial districts (codes 2900.1 etc.) and xx000 duplicate rows are dropped; blank or zero income means suppressed and is dropped (1950: 70 counties, all small; 1960: 16). That leaves 3,041 counties for 1950 and 3,117 for 1960. Elizabeth City and Warwick VA (merged into Hampton and Newport News in 1952 and 1958) appear only in 1950.
  - **1950 cross-check (NHGIS NT39, done once 2026-10-14):** NT39 reports median family income (1949, universe: families) only as $500 brackets, so the check is bracket agreement rather than a value match. All 2,986 counties with a bracket in both sources have the ICPSR value inside the NHGIS bracket (100%). The correlation of log ICPSR income with the log bracket midpoint is 0.98, and the median gap to the midpoint is $124 (as expected for $500 brackets). The two sources measure the same concept.
  - **1940 income definition:** wage and salary income (INCWAGE) summed over everyone in the county ÷ all persons in the county. Top-coded values stay at $5,000. Missing wages (999998) count as 0, and the missing share is kept per county as `wage_missing_share` (8.6% of persons nationally; county median 6.1%, max 62%). County codes come from COUNTYICP (D-22). 0.1% of counties (0.02% of persons) are dissolved counties with no FIPS code and stay as `county:nhgis-*`.
- **Main figure:** β_d by decade for both versions.
- **Tests:** run on the pooled unit × decade panel, with income interacted with period indicators, because 7–14 β_d values are too few for these tests:
  - Chow tests at 1950 and 1980;
  - Bai-Perron multiple-break search over the decade boundaries.
- **Source changes:** an indicator for each income source. Results are reported with and without the decades where the source changes.
- **Robustness:** the metro version is compared with the state version, which uses full personal income rather than 1940 wages.

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
