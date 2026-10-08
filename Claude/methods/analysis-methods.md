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

## RQ0b — US structural break (decennial, 1950–2020)

For each decade d:

Δln(pop)_{m,d} = α_d + β_d · ln(income per capita)_{m,d−1} + ε_{m,d}

- β_d > 0 means population flows toward richer metros. A falling β_d means that flow is weakening.
- **Income:** Census median family income for 1950–1960; BEA personal income per capita from 1970.
- **Tests:** Bai-Perron multiple-break test on the β_d series; Chow tests at 1950 and 1980.
- **Robustness:** results with and without 1950–60, because the early income data are coarser.

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
