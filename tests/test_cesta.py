from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import cesta


def parsed(fixtures_dir):
    return cesta.parse(fixtures_dir / "cesta" / "master_sample.csv")


def test_output_is_valid_long_format(fixtures_dir):
    validate_long(parsed(fixtures_dir))


def test_ids_are_2010_place_codes(fixtures_dir):
    v = parsed(fixtures_dir).set_index(["geo_id", "year"]).value
    assert v[("place:2622000", 1950)] == 1_849_568  # Detroit
    assert v[("place:2148006", 2010)] == 597_337  # Louisville/Jefferson County (balance)


def test_zero_counts_are_missing_not_zero(fixtures_dir):
    df = parsed(fixtures_dir)
    assert (df.value > 0).all()
    gary = set(df.loc[df.geo_id == "place:1827000", "year"])  # Gary, IN, founded 1906
    assert 1900 not in gary and 1910 in gary


def test_places_without_a_2010_code_are_dropped(fixtures_dir):
    names = set(parsed(fixtures_dir).geo_name)
    assert "Brooklyn, NY" not in names and "Arlington, VA" not in names
    assert "Detroit, MI" in names


def test_download_skips_when_file_exists(tmp_path, monkeypatch):
    path = tmp_path / "master.csv"
    path.write_text("x")
    monkeypatch.setattr(cesta, "PATH", path)
    assert cesta.download() == [path]
