# Sources

Living list of every data source and reference used in the project. Update it whenever a source is added, changed, or first accessed.

**Status values:** `planned` (in the spec, not yet downloaded) · `active` (in use by the pipeline) · `candidate` (may be used) · `phase-2`

## Data sources

| Source | Provider | URL | Coverage | Access / license | Module | Status | Accessed |
|---|---|---|---|---|---|---|---|
| NHGIS: state and county population, housing units (county median income 1950, table NT39, used only as a cross-check) | IPUMS, University of Minnesota | https://www.nhgis.org | US states 1880+, counties 1900–2020, decennial (housing 1940+, income 1950+) | Free account + API key (register for the NHGIS collection); citation required | `sources/nhgis.py` | active (population, time series A00) | 2026-10-11 |
| County Data Books 1952 and 1962 (county median family income, 1949 and 1959) | ICPSR study 2896: Haines, *Historical, Demographic, Economic, and Social Data: The United States, 1790–2002* | https://www.icpsr.umich.edu/web/ICPSR/studies/2896 | US counties, 1950 and 1960 censuses | Free ICPSR account; manual download; no redistribution (files stay in gitignored `data/raw/icpsr/`); cite | `sources/icpsr.py` | active (Part 72: CDB 1952, `var20`; Part 74: CDB 1962, `var22`; Stata, read from the downloaded zips via https://doi.org/10.3886/ICPSR02896.v3) | 2026-10-14 |
| IPUMS USA 1940 full-count census (wage and salary income) | IPUMS, University of Minnesota | https://usa.ipums.org | US individuals, 1940; aggregated to counties. Wages only, top-coded at $5,000 | Free account + API key; citation required | `sources/ipums.py` | active (sample us1940b; STATEFIP, COUNTYICP, INCWAGE; 3,099 counties) | 2026-10-11 |
| State personal income estimates, 1880–1910 (Klein) | Alexander Klein | https://wrap.warwick.ac.uk/id/eprint/3551 | US states, 1880, 1890, 1900, 1910 (Table 8, pp. 55–56, per capita personal income, current $) | Published tables; extracted from the working paper's text layer into `references/manual_data/`; cite | `sources/manual.py` | active (2009 working paper version) | 2026-10-09 |
| State personal income estimates (Easterlin) | Richard Easterlin, in Kuznets, Miller & Easterlin (1957) | Table Y-1, p. 753 of the 1957 volume (archive.org, borrow-only; page photos supplied by the owner). The NBER chapter c2475 has **regional** figures only. | US states, 1880, 1900, 1919–21 | Published tables; transcribed into `references/manual_data/` (checks in its README); cite | `sources/manual.py` | active | 2026-10-11 |
| Population of the 100 Largest Cities, 1790–1990 (Gibson, Working Paper No. 27) | US Census Bureau | https://www.census.gov/library/working-papers/1998/demo/POP-twps0027.html | US cities, decennial 1790–1990 | Public domain | `sources/census_decennial.py` | planned | — |
| Decennial census city populations 2000–2020 | US Census Bureau | https://data.census.gov | US places | Public domain | `sources/census_decennial.py` | planned | — |
| Population Estimates Program | US Census Bureau | https://www.census.gov/programs-surveys/popest.html | US counties and metros, annual 2000+; 2020 estimates base by CBSA (2023 delineation), used for validation | Public domain | `sources/census_pep.py` | active | 2026-10-09 |
| CBSA delineation files | US Census Bureau / OMB | https://www.census.gov/geographies/reference-files/time-series/demo/metro-micro/delineation-files.html | County → CBSA (2023) | Public domain | `geography.py` | active | 2026-10-09 |
| GDP by metro; personal income by county and state | Bureau of Economic Analysis | https://apps.bea.gov/api/ | Metro GDP 2001+; county income 1969+; state income 1929+ | Free API key; public domain | `sources/bea.py` | active (SAINC1 line 3 states 1929+; CAINC1 lines 1–2 counties 1969+, summed to 2023 CBSAs, D-23; metro GDP not yet pulled; SAINC1 line 2 state population 1929+ and SAINC5S lines 35/200 (earnings, mining) 1958–2001 for the energy-state rule (Plan 1b)) | 2026-10-14 |
| Building Permits Survey | US Census Bureau | https://www.census.gov/construction/bps/ | US metros and places, annual | Public domain | `sources/census_bps.py` | planned | — |
| House Price Index (metro) | Federal Housing Finance Agency | https://www.fhfa.gov/data/hpi | US metros, 1975+ | Public domain | `sources/fhfa.py` | planned | — |
| Wharton Residential Land Use Regulatory Index (2006, 2018) | Gyourko et al., Wharton | https://real-faculty.wharton.upenn.edu/gyourko/land-use-survey/ | US municipalities | Free for research; cite | `sources/wharton.py` | planned | — |
| Metropolitan areas database; house prices; price-to-income; housing stock | OECD | https://data-explorer.oecd.org | ~600 OECD metros 2000+; national housing | Free; OECD terms, cite | `sources/oecd.py` | planned | — |
| Metropolitan regions statistics | Eurostat | https://ec.europa.eu/eurostat/web/metropolitan-regions | EU metro regions, 2000+ | Free; Eurostat reuse policy | `sources/eurostat.py` | planned | — |
| World Urbanization Prospects | UN DESA Population Division | https://population.un.org/wup/ | Agglomerations 300k+, every 5 years 1950+; national urbanization | Free; cite | `sources/un_wup.py` | planned | — |
| World Development Indicators; income groups | World Bank | https://data.worldbank.org | National, 1960+ | CC BY 4.0 | `sources/worldbank.py` | planned | — |
| Maddison Project Database | Groningen Growth and Development Centre | https://www.rug.nl/ggdc/historicaldevelopment/maddison/ | National GDP per capita, long run | Free; cite | `sources/maddison.py` | planned | — |
| Building consents by region | Stats NZ | https://www.stats.govt.nz | NZ regions, monthly | CC BY 4.0 | `sources/statsnz.py` | planned | — |
| China city statistical yearbooks (extracts) | National Bureau of Statistics of China | — | Featured Chinese cities | Hand-collected | `sources/manual.py` | planned | — |
| Featured-city housing statistics (ONS, Statistics Canada, Statistics Bureau of Japan, ABS, others) | National statistics offices | — | Featured cities | Hand-collected | `sources/manual.py` | planned | — |
| Online Data: Robert Shiller (US home prices since 1890) | Robert Shiller, Yale | http://www.econ.yale.edu/~shiller/data.htm | US national | Free | — | candidate | — |
| Rosés-Wolf regional GDP database | Rosés & Wolf | URL to confirm on first access | European NUTS-2 regions, 1900–2015 | Free; cite | — | candidate | — |
| Planning applications statistics (England) | UK Ministry of Housing, Communities and Local Government | https://www.gov.uk/government/collections/planning-applications-statistics | English local authorities, quarterly | Open Government Licence | — | phase-2 | — |
| National Zoning Atlas | National Zoning Atlas | https://www.zoningatlas.org | US jurisdictions (partial) | Check terms | — | phase-2 | — |

## Literature

| Reference | Relevance |
|---|---|
| Ganong, P., & Shoag, D. (2017). Why has regional income convergence in the U.S. declined? *Journal of Urban Economics*, 102, 76–90. | Template for RQ0b: migration toward high-income places weakens over time, attributed to housing regulation |
| Glaeser, E., & Gyourko, J. (2018). The economic implications of housing supply. *Journal of Economic Perspectives*, 32(1), 3–30. | Framing: supply constraints and prices relative to construction cost |
| Hsieh, C.-T., & Moretti, E. (2019). Housing constraints and spatial misallocation. *American Economic Journal: Macroeconomics*, 11(2), 1–39. | Output costs of constrained high-productivity metros |
| Saiz, A. (2010). The geographic determinants of housing supply. *Quarterly Journal of Economics*, 125(3), 1253–1296. | Housing supply elasticities by metro |
| Gyourko, J., Hartley, J. S., & Krimmel, J. (2021). The local residential land use regulatory environment across U.S. housing markets: Evidence from a new Wharton index. *Journal of Urban Economics*, 124, 103337. | WRLURI 2018 documentation |
| Klein, A. (2013). New state-level estimates of personal income in the United States, 1880–1910. *Research in Economic History*, 29. Working paper: Warwick Economic Research Papers No. 916 (2009). | State income for 1880–1910, filling the 1890 and 1910 gaps in Easterlin; revises Easterlin's 1880 and 1900 figures |
| Easterlin, R. A. (1960). Interregional differences in per capita income, population, and total income, 1840–1950. In *Trends in the American Economy in the Nineteenth Century*, NBER. | Standard historical state income series; source for 1920 in RQ0b |
| Easterlin, R. A. (1957). State income estimates. In S. Kuznets, A. R. Miller & R. A. Easterlin, *Population Redistribution and Economic Growth, United States, 1870–1950*, Vol. I, American Philosophical Society. Table Y-1, p. 753. | Primary source of Easterlin's state personal income figures (the 1960 NBER chapter reports regions only); needed for 1920 |
| Greenaway-McGrevy, R., & Phillips, P. C. B. (2023). The impact of upzoning on housing construction in Auckland. *Journal of Urban Economics*, 136, 103555. | Benchmark for RQ5 |

Bibliographic details will be verified and added to `references/references.bib` when the paper is drafted.
