"""Shared long format that every source's load() returns (spec §4, source module contract)."""

import pandas as pd

LONG_COLUMNS = [
    "geo_id", "geo_name", "geo_level", "country_iso3",
    "year", "variable", "value", "unit", "source",
]

# geo_id prefixes allowed for each geo_level, so IDs from different namespaces never collide
GEO_PREFIXES: dict[str, tuple[str, ...]] = {
    "city": ("place:",),
    "county": ("county:",),
    "metro": ("cbsa:", "oecd:"),
    "agglomeration": ("wup:",),
    "state": ("state:",),
    "country": ("iso3:",),
}


class SchemaError(ValueError):
    """Raised when a frame does not conform to the long format."""


def validate_long(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in LONG_COLUMNS if c not in df.columns]
    if missing:
        raise SchemaError(f"missing columns: {missing}")
    extra = [c for c in df.columns if c not in LONG_COLUMNS]
    if extra:
        raise SchemaError(f"unexpected columns: {extra}")
    null_cols = [c for c in LONG_COLUMNS if df[c].isna().any()]
    if null_cols:
        raise SchemaError(f"null values in columns: {null_cols}")
    if not pd.api.types.is_integer_dtype(df["year"]):
        raise SchemaError(f"year must be an integer dtype, got {df['year'].dtype}")
    if not pd.api.types.is_float_dtype(df["value"]):
        raise SchemaError(f"value must be a float dtype, got {df['value'].dtype}")
    unknown = set(df["geo_level"]) - set(GEO_PREFIXES)
    if unknown:
        raise SchemaError(f"unknown geo_level values: {sorted(unknown)}")
    for level, prefixes in GEO_PREFIXES.items():
        ids = df.loc[df["geo_level"] == level, "geo_id"]
        bad = ids[~ids.str.startswith(prefixes)]
        if len(bad):
            raise SchemaError(f"geo_id prefix does not match geo_level {level!r}: {bad.iloc[0]}")
    dupes = df.duplicated(["geo_id", "year", "variable"])
    if dupes.any():
        raise SchemaError(f"{int(dupes.sum())} duplicate (geo_id, year, variable) rows")
    units = df.groupby("variable")["unit"].nunique()
    mixed = units[units > 1]
    if len(mixed):
        raise SchemaError(f"variables with more than one unit: {list(mixed.index)}")
    return df[LONG_COLUMNS]
