# Pipeline and Architecture

How data moves from source to paper and dashboard. Update this file whenever the pipeline or package layout changes. Full design: `docs/superpowers/specs/2026-10-08-housing-growth-mismatch-design.md`.

## Data flow

```
sources/*.download()  →  data/raw/<source>/              original files, never edited
sources/*.load()      →  data/interim/<source>.parquet   shared long format
features.py           →  data/processed/<panel>.parquet  wide analysis panels
notebooks/*.ipynb     →  reports/figures/, reports/tables/
reports/paper.md      →  rendered HTML/PDF (Quarto)
dashboard.py          →  reports/dashboard/index.html
```

`data/` is gitignored and rebuilt by `make data`. Hand-collected inputs and reviewed crosswalks are committed under `references/manual_data/` and `references/crosswalks/`.

## Package layout

| Module | Responsibility |
|---|---|
| `config.py` | Paths, year ranges, featured-city list, peer-group rules |
| `sources/<name>.py` | One per source. `download(force=False)` fetches raw files; `load()` returns the long format |
| `geography.py` | Crosswalks between county, CBSA, OECD metro, UN WUP agglomeration, and featured-city IDs |
| `dataset.py` | Typer CLI that runs download and load for every source |
| `features.py` | Builds the five processed panels |
| `modeling/elasticity.py` | Panel regressions (RQ0c, RQ1, RQ2) |
| `modeling/breaks.py` | Decade-by-decade coefficients and structural break tests (RQ0b) |
| `modeling/event_study.py` | Auckland difference-in-differences and synthetic control (RQ5) |
| `plots.py` | Shared figure style |
| `dashboard.py` | Static Plotly dashboard |

## Shared long format

Every source's `load()` returns these columns: `geo_id, geo_name, geo_level, country_iso3, year, variable, value, unit, source`.

**Schema validation:** `dataset.py load` runs `validate_long()` (`schema.py`) on every source before writing its parquet file.

`geo_id` is prefixed by namespace so IDs never collide: `county:24510`, `cbsa:12580`, `oecd:US019`, `wup:21853`, `iso3:USA`.

## Processed panels

| Panel | Grain | Used by |
|---|---|---|
| `us_metro_longrun` | metro × decade, 1900–2020 | RQ0a, RQ0b, RQ3 |
| `us_metro_annual` | metro × year, 2000+ | RQ2, RQ4 |
| `oecd_metro_panel` | metro × year, ~2000–2022 | RQ1, RQ2 |
| `global_agglomerations` | agglomeration × 5 years, 1950–2020 | RQ0c |
| `national_housing` | country × year | RQ3, RQ4 |

## Build targets

`make data` → `make features` → `make notebooks` → `make paper` → `make dashboard`. `make all` runs every target in that order; `make test` runs pytest.

## Secrets

API keys for IPUMS/NHGIS and BEA are read from `.env`, which is gitignored.
