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
