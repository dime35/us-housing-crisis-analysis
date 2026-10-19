from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import nhgis


def parsed(fixtures_dir):
    d = fixtures_dir / "nhgis"
    return nhgis.parse_population(d / "a00_state.csv", d / "a00_county.csv")


def test_output_is_valid_long_format(fixtures_dir):
    validate_long(parsed(fixtures_dir))


def test_fips_ids_are_zero_padded(fixtures_dir):
    ids = set(parsed(fixtures_dir).geo_id)
    assert {"state:24", "county:24510", "county:51019"} <= ids


def test_rows_without_fips_keep_a_traceable_id(fixtures_dir):
    df = parsed(fixtures_dir)
    assert "state:nhgis-G465" in set(df.geo_id)
    assert "county:nhgis-G4650015" in set(df.geo_id)


def test_blank_population_rows_are_dropped(fixtures_dir):
    df = parsed(fixtures_dir)
    assert not ((df.geo_id == "county:24510") & (df.year == 1790)).any()


def test_download_skips_when_files_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(nhgis, "A00_DIR", tmp_path)
    monkeypatch.setattr(nhgis, "AV0_DIR", tmp_path)
    for name in ("a00_state.csv", "a00_county.csv", "av0_place.csv"):
        (tmp_path / name).write_text("x")

    def fail(*args, **kwargs):
        raise AssertionError("extract submitted although files exist")

    monkeypatch.setattr(nhgis, "run_extract", fail)
    assert len(nhgis.download()) == 3


def test_av0_places_keep_census_years_only(fixtures_dir):
    df = nhgis.parse_places(fixtures_dir / "nhgis" / "av0_place.csv")
    validate_long(df)
    assert set(df.geo_level) == {"city"}
    assert set(df.year) <= {1970, 1980, 1990, 2000, 2010, 2020}
    v = df.set_index(["geo_id", "year"]).value
    assert v[("place:2622000", 2020)] == 639_111  # Detroit
    assert v[("place:2148006", 2020)] == 386_884  # Louisville balance, without the old city
    assert v[("place:2148000", 2020)] == 246_161  # Louisville's old city, a separate place in 2020


def test_av0_drops_places_without_a_fips_code(fixtures_dir):
    # NHGIS gives some unofficial places 4-digit codes (Shemya Station, AK: "3000"); padded, they
    # would collide with real FIPS codes (Anchorage: 03000)
    df = nhgis.parse_places(fixtures_dir / "nhgis" / "av0_place.csv")
    v = df.set_index(["geo_id", "year"]).value
    assert v[("place:0203000", 1970)] == 48_029
    assert "Shemya Station, Alaska" not in set(df.geo_name)
