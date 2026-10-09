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

### `source = easterlin_1960`: Easterlin, 1880, 1900 (and 1920, pending)

- **Citation:** Easterlin, R. A. (1957). State income estimates. In Kuznets, Miller & Easterlin, *Population Redistribution and Economic Growth, United States, 1870–1950*, Vol. I. Table Y-1, p. 753. The source ID `easterlin_1960` follows the spec. The 1960 NBER chapter (c2475) reports regional figures only.
- **1880 and 1900:** taken from Klein (2009) Table 6, pp. 52–53, which reprints Easterlin's Table Y-1 per capita figures next to Klein's. Same transcription date and method as above.
- **1920 (Easterlin's 1919–21 average):** **not yet transcribed.** The 1957 volume is available on archive.org only as a borrow-only loan (`populationredist0001kuzn`). `test_committed_coverage_easterlin_1920` is a strict xfail until these rows are added.

### Coverage and territory rule

- 48 states; the District of Columbia isn't covered.
- 1880 has 45 states. North and South Dakota appear only as a combined Dakota Territory, which is left out because it splits into FIPS 38 and 46. Oklahoma has no 1880 estimate.
- Territories that later became states (e.g., Arizona, Washington) use the FIPS code of the state they became.
