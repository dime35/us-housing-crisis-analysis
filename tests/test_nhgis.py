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
    for name in ("a00_state.csv", "a00_county.csv"):
        (tmp_path / name).write_text("x")

    def fail(*args, **kwargs):
        raise AssertionError("extract submitted although files exist")

    monkeypatch.setattr(nhgis, "run_extract", fail)
    assert len(nhgis.download()) == 2
