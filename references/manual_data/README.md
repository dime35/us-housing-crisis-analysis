# Hand-collected data

Inputs that can't be downloaded by the pipeline. `sources/manual.py` reads them, and `tests/test_manual.py` checks them.

## `state_income_historical.csv`

Per capita personal income by state, in current dollars (`unit = usd_current`), for the RQ0b state version before BEA's series starts in 1929.

Columns: `state_fips, state_name, year, value, unit, source, table_ref`.

### `source = klein_2013`: Klein, 1880, 1890, 1900, 1910

- **Citation:** Klein, A. (2009). *Personal Income of U.S. States: Estimates for the Period 1880–1910*. Warwick Economic Research Papers No. 916. Published version: *Research in Economic History* 29 (2013).
- **URL:** https://wrap.warwick.ac.uk/id/eprint/3551 (PDF: `WRAP_Klein_twerp_916.pdf`)
- **Table:** Table 8, "Total Personal Income per Capita" columns, pp. 55–56.
- **Version:** the 2009 working paper. The published 2013 version is paywalled and hasn't been compared yet. The source ID `klein_2013` follows the spec.
- **Transcribed:** 2026-10-09, by Claude, from the PDF's text layer (`pdftotext -layout`; not OCR). The script checked that Klein's own 1880 and 1900 values in Table 6 equal Table 8 for all 48 states. Every fifth row was rechecked by eye against the table.

### `source = easterlin_1960`: Easterlin, 1880, 1900, 1920

- **Citation:** Easterlin, R. A. (1957). State income estimates. In Kuznets, Miller & Easterlin, *Population Redistribution and Economic Growth, United States, 1870–1950*, Vol. I. Table Y-1, "Personal Income and Personal Income per Capita, 1880 to 1949–51", p. 753. The source ID `easterlin_1960` follows the spec. The 1960 NBER chapter (c2475) reports regional figures only.
- **Copy used:** page photos of p. 753 supplied by the project owner on 2026-10-11, from the archive.org borrow-only copy (`populationredist0001kuzn`).
- **1920** is Easterlin's 1919–21 average, in current dollars.
- **Transcribed:** 2026-10-11, by Claude, from the page image, with three checks:
  1. All 93 values for 1880 and 1900 read from the page equal the reprint in Klein (2009) Table 6. The 1880 and 1900 rows were first entered from that reprint.
  2. The 1919–21 state totals of personal income (also read from p. 753) sum to 69,278 against the printed US total of 69,277.
  3. The population each state implies for 1919–21 (total ÷ per capita) is within 1% of the 1920 census figure for all 48 states (median gap 0.01%). The 1920 census figures used came from Claude's knowledge, not a downloaded file.

### Coverage and territory rule

- 48 states; the District of Columbia isn't covered.
- 1880 has 45 states. North and South Dakota appear only as a combined Dakota Territory, which is left out because it splits into FIPS 38 and 46. Oklahoma has no 1880 estimate.
- Territories that later became states (e.g., Arizona, Washington) use the FIPS code of the state they became.

## `us_natural_increase.csv`

US births and deaths summed over the ten calendar years starting at `decade` (1950 = 1950–1959), from NCHS. Not read by the pipeline: `tests/data/test_us_net_migration.py` compares it with the natural increase implied by `us_state_net_migration` (census population change minus net migration).

Columns: `decade, births, deaths, source`. The `source` column gives the exact table and URL for each part of each decade.

- **Tables used:**
  - Births 1950–2003: *Vital Statistics of the United States 2003*, Vol. I, Table 1-1 (`natfinal2003.annvol1_01.pdf`).
  - Births 2004–09: NCHS dataset "Births and General Fertility Rates: United States" (data.cdc.gov `e6fc-ccez`).
  - Births 2010–19: *Births: Final Data for 2019* (NVSR 70-2), Table 1.
  - Deaths 1950–79: *Vital Statistics of the United States 1979*, Vol. II Part A, Table 1-1 (`mort79_2a.pdf`).
  - Deaths 1980–98: NCHS, *Leading Causes of Death, 1900–1998* (`lead1900_98.pdf`).
  - Deaths 1999–2009: NCHS dataset "Leading Causes of Death: United States", all causes (data.cdc.gov `bi63-dtpu`).
  - Deaths 2010–19: *Deaths: Final Data for 2019* (NVSR 70-8), Table 1.
- **Births 1950–59** are NCHS's births adjusted for underregistration, the only series the table gives for 1950–58. For 1959 the table also gives registered births (4,244,796, 41,204 fewer); the adjusted figure keeps the decade on one basis.
- **Coverage:** 1950–58 figures exclude Alaska and Hawaii; 1959 includes Alaska only. From 1970, deaths and births of nonresidents of the US are excluded. The 1962–63 New Jersey footnote applies to the race columns only, not to the totals.
- **Access:** cdc.gov refuses scripted downloads, so the PDFs were read from Wayback Machine copies of the cited URLs (`https://web.archive.org/web/2021id_/<url>`). The data.cdc.gov datasets were read through their API.
- **Transcribed:** 2026-10-15, by Claude, with these checks:
  1. Births 1960–2003 parsed from the table's text layer equal the data.cdc.gov series in every year, and NVSR 70-2 equals it for 2010–18.
  2. Deaths 1950–79 were read from the page image of the 1979 table. White + all other = total in every year except 1962–63, where the race columns exclude New Jersey. Every year equals the 1900–98 leading-causes compilation, and 1950–60 also equals VSUS 1960 Vol. II Part A, Table 1-A.
  3. Deaths 1981–98: both sexes = male + female in every year.
  4. Deaths 2010–17 in NVSR 70-8 equal the data.cdc.gov series.

Per-year values:

| Year | Births | Births from | Deaths | Deaths from |
|---|---|---|---|---|
| 1950 | 3,632,000 | VSUS 2003 T1-1 (adjusted) | 1,452,454 | VSUS 1979 T1-1 |
| 1951 | 3,820,000 | VSUS 2003 T1-1 (adjusted) | 1,482,099 | VSUS 1979 T1-1 |
| 1952 | 3,909,000 | VSUS 2003 T1-1 (adjusted) | 1,496,838 | VSUS 1979 T1-1 |
| 1953 | 3,959,000 | VSUS 2003 T1-1 (adjusted) | 1,517,541 | VSUS 1979 T1-1 |
| 1954 | 4,071,000 | VSUS 2003 T1-1 (adjusted) | 1,481,091 | VSUS 1979 T1-1 |
| 1955 | 4,097,000 | VSUS 2003 T1-1 (adjusted) | 1,528,717 | VSUS 1979 T1-1 |
| 1956 | 4,210,000 | VSUS 2003 T1-1 (adjusted) | 1,564,476 | VSUS 1979 T1-1 |
| 1957 | 4,300,000 | VSUS 2003 T1-1 (adjusted) | 1,633,128 | VSUS 1979 T1-1 |
| 1958 | 4,246,000 | VSUS 2003 T1-1 (adjusted) | 1,647,886 | VSUS 1979 T1-1 |
| 1959 | 4,286,000 | VSUS 2003 T1-1 (adjusted) | 1,656,814 | VSUS 1979 T1-1 |
| 1960 | 4,257,850 | VSUS 2003 T1-1 | 1,711,982 | VSUS 1979 T1-1 |
| 1961 | 4,268,326 | VSUS 2003 T1-1 | 1,701,522 | VSUS 1979 T1-1 |
| 1962 | 4,167,362 | VSUS 2003 T1-1 | 1,756,720 | VSUS 1979 T1-1 |
| 1963 | 4,098,020 | VSUS 2003 T1-1 | 1,813,549 | VSUS 1979 T1-1 |
| 1964 | 4,027,490 | VSUS 2003 T1-1 | 1,798,051 | VSUS 1979 T1-1 |
| 1965 | 3,760,358 | VSUS 2003 T1-1 | 1,828,136 | VSUS 1979 T1-1 |
| 1966 | 3,606,274 | VSUS 2003 T1-1 | 1,863,149 | VSUS 1979 T1-1 |
| 1967 | 3,520,959 | VSUS 2003 T1-1 | 1,851,323 | VSUS 1979 T1-1 |
| 1968 | 3,501,564 | VSUS 2003 T1-1 | 1,930,082 | VSUS 1979 T1-1 |
| 1969 | 3,600,206 | VSUS 2003 T1-1 | 1,921,990 | VSUS 1979 T1-1 |
| 1970 | 3,731,386 | VSUS 2003 T1-1 | 1,921,031 | VSUS 1979 T1-1 |
| 1971 | 3,555,970 | VSUS 2003 T1-1 | 1,927,542 | VSUS 1979 T1-1 |
| 1972 | 3,258,411 | VSUS 2003 T1-1 | 1,963,944 | VSUS 1979 T1-1 |
| 1973 | 3,136,965 | VSUS 2003 T1-1 | 1,973,003 | VSUS 1979 T1-1 |
| 1974 | 3,159,958 | VSUS 2003 T1-1 | 1,934,388 | VSUS 1979 T1-1 |
| 1975 | 3,144,198 | VSUS 2003 T1-1 | 1,892,879 | VSUS 1979 T1-1 |
| 1976 | 3,167,788 | VSUS 2003 T1-1 | 1,909,440 | VSUS 1979 T1-1 |
| 1977 | 3,326,632 | VSUS 2003 T1-1 | 1,899,597 | VSUS 1979 T1-1 |
| 1978 | 3,333,279 | VSUS 2003 T1-1 | 1,927,788 | VSUS 1979 T1-1 |
| 1979 | 3,494,398 | VSUS 2003 T1-1 | 1,913,841 | VSUS 1979 T1-1 |
| 1980 | 3,612,258 | VSUS 2003 T1-1 | 1,989,841 | lead1900_98 |
| 1981 | 3,629,238 | VSUS 2003 T1-1 | 1,977,981 | lead1900_98 |
| 1982 | 3,680,537 | VSUS 2003 T1-1 | 1,974,797 | lead1900_98 |
| 1983 | 3,638,933 | VSUS 2003 T1-1 | 2,019,201 | lead1900_98 |
| 1984 | 3,669,141 | VSUS 2003 T1-1 | 2,039,369 | lead1900_98 |
| 1985 | 3,760,561 | VSUS 2003 T1-1 | 2,086,440 | lead1900_98 |
| 1986 | 3,756,547 | VSUS 2003 T1-1 | 2,105,361 | lead1900_98 |
| 1987 | 3,809,394 | VSUS 2003 T1-1 | 2,123,323 | lead1900_98 |
| 1988 | 3,909,510 | VSUS 2003 T1-1 | 2,167,999 | lead1900_98 |
| 1989 | 4,040,958 | VSUS 2003 T1-1 | 2,150,466 | lead1900_98 |
| 1990 | 4,158,212 | VSUS 2003 T1-1 | 2,148,463 | lead1900_98 |
| 1991 | 4,110,907 | VSUS 2003 T1-1 | 2,169,518 | lead1900_98 |
| 1992 | 4,065,014 | VSUS 2003 T1-1 | 2,175,613 | lead1900_98 |
| 1993 | 4,000,240 | VSUS 2003 T1-1 | 2,268,553 | lead1900_98 |
| 1994 | 3,952,767 | VSUS 2003 T1-1 | 2,278,994 | lead1900_98 |
| 1995 | 3,899,589 | VSUS 2003 T1-1 | 2,312,132 | lead1900_98 |
| 1996 | 3,891,494 | VSUS 2003 T1-1 | 2,314,690 | lead1900_98 |
| 1997 | 3,880,894 | VSUS 2003 T1-1 | 2,314,245 | lead1900_98 |
| 1998 | 3,941,553 | VSUS 2003 T1-1 | 2,337,256 | lead1900_98 |
| 1999 | 3,959,417 | VSUS 2003 T1-1 | 2,391,399 | data.cdc.gov bi63-dtpu |
| 2000 | 4,058,814 | VSUS 2003 T1-1 | 2,403,351 | data.cdc.gov bi63-dtpu |
| 2001 | 4,025,933 | VSUS 2003 T1-1 | 2,416,425 | data.cdc.gov bi63-dtpu |
| 2002 | 4,021,726 | VSUS 2003 T1-1 | 2,443,387 | data.cdc.gov bi63-dtpu |
| 2003 | 4,089,950 | VSUS 2003 T1-1 | 2,448,288 | data.cdc.gov bi63-dtpu |
| 2004 | 4,112,052 | data.cdc.gov e6fc-ccez | 2,397,615 | data.cdc.gov bi63-dtpu |
| 2005 | 4,138,349 | data.cdc.gov e6fc-ccez | 2,448,017 | data.cdc.gov bi63-dtpu |
| 2006 | 4,265,555 | data.cdc.gov e6fc-ccez | 2,426,264 | data.cdc.gov bi63-dtpu |
| 2007 | 4,316,233 | data.cdc.gov e6fc-ccez | 2,423,712 | data.cdc.gov bi63-dtpu |
| 2008 | 4,247,694 | data.cdc.gov e6fc-ccez | 2,471,984 | data.cdc.gov bi63-dtpu |
| 2009 | 4,130,665 | data.cdc.gov e6fc-ccez | 2,437,163 | data.cdc.gov bi63-dtpu |
| 2010 | 3,999,386 | NVSR 70-2 T1 | 2,468,435 | NVSR 70-8 T1 |
| 2011 | 3,953,590 | NVSR 70-2 T1 | 2,515,458 | NVSR 70-8 T1 |
| 2012 | 3,952,841 | NVSR 70-2 T1 | 2,543,279 | NVSR 70-8 T1 |
| 2013 | 3,932,181 | NVSR 70-2 T1 | 2,596,993 | NVSR 70-8 T1 |
| 2014 | 3,988,076 | NVSR 70-2 T1 | 2,626,418 | NVSR 70-8 T1 |
| 2015 | 3,978,497 | NVSR 70-2 T1 | 2,712,630 | NVSR 70-8 T1 |
| 2016 | 3,945,875 | NVSR 70-2 T1 | 2,744,248 | NVSR 70-8 T1 |
| 2017 | 3,855,500 | NVSR 70-2 T1 | 2,813,503 | NVSR 70-8 T1 |
| 2018 | 3,791,712 | NVSR 70-2 T1 | 2,839,205 | NVSR 70-8 T1 |
| 2019 | 3,747,540 | NVSR 70-2 T1 | 2,854,838 | NVSR 70-8 T1 |
