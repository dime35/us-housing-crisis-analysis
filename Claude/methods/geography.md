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

None yet.
