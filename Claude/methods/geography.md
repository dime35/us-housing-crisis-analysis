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
- **NHGIS code → FIPS (`fips_from_nhgis_code`):** NHGIS county codes are a 3-digit state code plus a 4-digit county code, each equal to FIPS × 10 when the county has a FIPS code. Codes whose last digit isn't 0 are historical counties with no FIPS code. They return `None` and go to the unmatched-county report.
