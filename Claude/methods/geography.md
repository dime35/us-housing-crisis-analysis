# Geography and Boundary Decisions

How places are defined and matched across sources. Update this file whenever a crosswalk or boundary rule changes.

## Primary unit: metro with constant boundaries

- US metros use the **2023 CBSA delineation**, built from counties. The same list of counties is used for every year back to 1900.
- **County populations are NHGIS A00 "nominally integrated" counts**, not boundary-standardized ones: a county is linked across years by name and code, and its historical count covers whatever area it had then. Renames, mergers and territory counties are mapped to successors (manual fixes below). This removes most boundary effects but not all.
- **Known limitation: counties split across a 2023 CBSA line.** When a county created after 1900 was carved from a parent in a different CBSA (or outside any CBSA), the parent's earlier counts include the area that later left. Growth for the affected metros is distorted in the decade of the split. Examples: Broomfield CO (2001, from Boulder, Adams, Jefferson and Weld; it is in the Denver CBSA, so Boulder's 2000→2010 growth shows +1.1% instead of roughly +9%); La Paz AZ (1983, from Yuma); Cibola NM (1981, from Valencia, in the Albuquerque CBSA). Found in the Plan 1 review (2026-10-14); how to handle these is an open item.

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
- **`references/crosswalks/county_fixes.csv`:** historical county FIPS codes that no longer exist, mapped to their successors (Dade → Miami-Dade 12025 → 12086; Virginia independent-city mergers). Plan 1 Task 10 added:
  - **Territory counties (150 rows):** NHGIS gives territory counties (Arizona, Hawaii, Idaho, Montana, New Mexico, Oklahoma, Utah, Washington, Wyoming territories) `nhgis-G…` codes with no FIPS, and their county numbers are not FIPS (most were numbered alphabetically at the time). Each is matched **by name** to the later state's county, the same nominal linking NHGIS uses for A00. Six were mapped by hand: Oahu → Honolulu (15003), Molokai → Maui (15009), Niihau → Kauai (15007), and the NHGIS spellings Pottowatomie (40125), Klikatat (53039) and Chihallis = Chehalis → Grays Harbor (53027).
  - **Renames and whole-county mergers:** Warwick → Newport News (51700); South Norfolk city, no FIPS in NHGIS → Chesapeake (51550); Alexandria County → Arlington (51013); Manchester city → Richmond (51760); Chehalis → Grays Harbor WA (53027); Shannon → Oglala Lakota SD (46113 → 46102); Ormsby → Carson City NV (32510); James → Hamilton TN (47065); Milton and Campbell → Fulton GA (13121; a small part of Campbell went to Douglas, also in the Atlanta CBSA).
- **`references/crosswalks/territory_to_state.csv` (state panel):** territory rows (`state:nhgis-G…`) take their later state's ID where the territory boundary already matched the state: Alaska, Arizona, Hawaii, Idaho, Montana, New Mexico, Utah, Washington and Wyoming. Oklahoma 1900 = Oklahoma Territory + Indian Territory (790,391, the Census historical total); Oklahoma 1890 is left unmapped because Indian Territory has no 1890 count. Dakota Territory (1880) split into two states and is left unmapped.
- **Unplaceable populations:** Indian Territory's nations (1900) had no counties; Oklahoma's 1907 counties cut across them. Metro-years in a state-year listed in `features.INCOMPLETE_STATE_YEARS` (Oklahoma 1900) are dropped when any of the metro's counties in that state has no count, so Tulsa, Oklahoma City, Lawton and Fort Smith start in 1910 (Enid, entirely in Oklahoma Territory, keeps 1900). Alaska's districts (to 1950), 1960 election districts and some census areas don't match boroughs and stay unmatched; Alaska's metros start in 1970.
- **Unmatched county population by decade** (`features.unmatched_county_report`, share of US population): 1900 0.66% (0.14% without Indian Territory), 1910 0.01%, 1920 0.06%, 1930 0.05%, 1940 0.06%, 1950 0.09%, 1960 0.13%, 1970–2010 ≤ 0.03%. The remainder is mostly Alaska and Indian reservations enumerated separately in 1900–1910.
- **`references/crosswalks/growth_allowlist.csv`:** metro-decades whose population more than triples or halves, each checked and given a reason (19 rows: Permian Basin and Panhandle towns, South Florida 1900–1930, Hanford 1940s, Cape Canaveral 1950s, irrigation settlements). `harmonize_county_fips()` applies the mapping, and callers sum afterwards so merged units add up. Fixes are never chained (a successor is never itself an old code).
- **`references/crosswalks/bea_county_combos.csv`:** BEA's county tables fold 23 Virginia independent cities into combo areas with their surrounding counties (e.g., 51901 Albemarle + Charlottesville), plus Maui + Kalawao HI (15901) and, before about 1990, Shawano + Menominee WI (55901). `sources/bea.py` assigns each combo to its main county. Every component shares that county's 2023 CBSA (checked against the delineation). The parser raises if BEA ever reports a combo and its components in the same year.
- **BEA placeholders and Connecticut:** BEA reports a value of 0 for areas without data that year: Alaska and Hawaii state income before 1950, Alaska's pre-1980s divisions, Broomfield CO before 2001, and Connecticut's planning regions in every year so far. Zeros are dropped. Planning regions are dropped outright, because the panels use the 8 old Connecticut counties, which BEA reports.
- **NHGIS code → FIPS (`fips_from_nhgis_code`):** NHGIS county codes are a 3-digit state code plus a 4-digit county code, each equal to FIPS × 10 when the county has a FIPS code. Codes whose last digit isn't 0 are historical counties with no FIPS code. They return `None` and go to the unmatched-county report.
