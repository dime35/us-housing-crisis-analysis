# Geography and Boundary Decisions

How places are defined and matched across sources. Update this file whenever a crosswalk or boundary rule changes.

## Primary unit: metro with constant boundaries

- US metros use the **2023 CBSA delineation**, built from counties. The same county set is used for every year back to 1900, so growth reflects people, not boundary changes.
- County boundary changes over time are handled with NHGIS standardized or time-consistent tables where available. Any remaining manual fixes are listed below.

## Secondary unit: city proper

City-proper populations (Census decennial counts) are used only for the RQ0a contrast with metros. City boundaries change through annexation; this is part of what RQ0a measures.

## Crosswalks

| Crosswalk | Method | Location |
|---|---|---|
| County → CBSA | OMB delineation file | built in `geography.py` |
| CBSA ↔ OECD metro (US) | OECD metro definitions are county-based; match on core county | `references/crosswalks/` |
| UN WUP agglomeration ↔ OECD metro | Name plus coordinate distance; featured cities reviewed by hand | `references/crosswalks/` |
| Featured city → IDs in every source | Hand-maintained table | `references/crosswalks/featured_cities.csv` |

## Manual fixes log

- **`references/crosswalks/ct_legacy_counties.csv`:** Connecticut's 2023 CBSAs are built from 9 planning regions, but historical data uses the 8 old counties. Each old county is assigned to the 2023 CBSA holding most of its population:
  - Fairfield → Bridgeport-Stamford-Danbury (14860)
  - Hartford, Middlesex and Tolland → Hartford (25540)
  - New Haven → New Haven (35300)
  - New London → Norwich-New London (35980)
  - Litchfield → Torrington (micropolitan) and Windham → Putnam (micropolitan), so both drop out of metro panels.
  - This is an approximation. The Waterbury-Shelton CBSA (47930) has no historical series, and Connecticut CBSAs are excluded from the 2020 tolerance check against the Census estimates base.
- **`references/crosswalks/county_fixes.csv`:** historical county FIPS codes that no longer exist, mapped to their successors (Dade → Miami-Dade 12025 → 12086; Virginia independent-city mergers). `harmonize_county_fips()` applies the mapping, and callers sum afterwards so merged units add up. Fixes are never chained (a successor is never itself an old code).
- **`references/crosswalks/bea_county_combos.csv`:** BEA's county tables fold 23 Virginia independent cities into combo areas with their surrounding counties (e.g., 51901 Albemarle + Charlottesville), plus Maui + Kalawao HI (15901) and, before about 1990, Shawano + Menominee WI (55901). `sources/bea.py` assigns each combo to its main county. Every component shares that county's 2023 CBSA (checked against the delineation). The parser raises if BEA ever reports a combo and its components in the same year.
- **BEA placeholders and Connecticut:** BEA reports a value of 0 for areas that don't exist that year: Alaska's pre-1980s divisions, Broomfield CO before 2001, and Connecticut's planning regions in every year so far. Zeros are dropped. Planning regions are dropped outright, because the panels use the 8 old Connecticut counties, which BEA reports.
- **NHGIS code → FIPS (`fips_from_nhgis_code`):** NHGIS county codes are a 3-digit state code plus a 4-digit county code, each equal to FIPS × 10 when the county has a FIPS code. Codes whose last digit isn't 0 are historical counties with no FIPS code. They return `None` and go to the unmatched-county report.
