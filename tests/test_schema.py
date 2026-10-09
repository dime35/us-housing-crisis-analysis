import pandas as pd
import pytest

from us_housing_crisis_analysis.schema import LONG_COLUMNS, SchemaError, validate_long


def good_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "geo_id": ["county:24510", "state:24"],
            "geo_name": ["Baltimore city", "Maryland"],
            "geo_level": ["county", "state"],
            "country_iso3": ["USA", "USA"],
            "year": pd.Series([2020, 2020], dtype="int64"),
            "variable": ["population", "population"],
            "value": [585708.0, 6177224.0],
            "unit": ["persons", "persons"],
            "source": ["nhgis", "nhgis"],
        }
    )


def test_valid_frame_passes_and_orders_columns():
    df = good_frame()[list(reversed(LONG_COLUMNS))]
    assert list(validate_long(df).columns) == LONG_COLUMNS


def test_missing_column_fails():
    with pytest.raises(SchemaError, match="missing columns"):
        validate_long(good_frame().drop(columns="unit"))


def test_extra_column_fails():
    with pytest.raises(SchemaError, match="unexpected columns"):
        validate_long(good_frame().assign(extra=1))


def test_null_value_fails():
    df = good_frame()
    df.loc[0, "value"] = None
    with pytest.raises(SchemaError, match="null"):
        validate_long(df)


def test_year_must_be_integer():
    with pytest.raises(SchemaError, match="year"):
        validate_long(good_frame().assign(year=[2020.0, 2020.0]))


def test_prefix_must_match_level():
    df = good_frame()
    df.loc[0, "geo_id"] = "cbsa:12580"
    with pytest.raises(SchemaError, match="prefix"):
        validate_long(df)


def test_unknown_level_fails():
    df = good_frame()
    df.loc[0, "geo_level"] = "planet"
    with pytest.raises(SchemaError, match="geo_level"):
        validate_long(df)


def test_duplicate_key_fails():
    df = pd.concat([good_frame(), good_frame().iloc[[0]]])
    with pytest.raises(SchemaError, match="duplicate"):
        validate_long(df)


def test_one_unit_per_variable():
    df = good_frame()
    df.loc[1, "unit"] = "thousands"
    with pytest.raises(SchemaError, match="more than one unit"):
        validate_long(df)
