import pytest

from us_housing_crisis_analysis.config import NETMIG_FILES
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import netmig


def parse_2010s(fixtures_dir):
    spec = NETMIG_FILES[2010]
    return validate_long(netmig.parse_net_migration(fixtures_dir / "netmig" / spec["file"], 2010, spec))


def test_county_rows_only_state_totals_never_added(fixtures_dir):
    df = parse_2010s(fixtures_dir).set_index("geo_id")
    assert set(df.index) == {"county:24510", "county:24005", "county:24003", "county:11001"}
    assert df.at["county:24510", "value"] == -56058.0 and df.at["county:11001", "value"] == 40898.0
    assert set(df.year) == {2010} and set(df.variable) == {"net_migration"} and set(df.unit) == {"persons"}


def test_summed_columns(fixtures_dir, tmp_path):
    spec = dict(NETMIG_FILES[2010], total_col="m1tttt+m1tttt")
    df = netmig.parse_net_migration(fixtures_dir / "netmig" / spec["file"], 2010, spec).set_index("geo_id")
    assert df.at["county:24005", "value"] == 2 * 32061.0


def test_missing_manual_files_raise(tmp_path, monkeypatch):
    monkeypatch.setattr(netmig, "RAW_DIR", tmp_path)
    monkeypatch.setattr(netmig, "NETMIG_FILES", {**NETMIG_FILES, 1950: dict(NETMIG_FILES[2010], file="icpsr_1950s.zip")})
    monkeypatch.setattr(netmig, "download_file", lambda url, dest, **kw: dest.write_bytes(b"x") or dest)
    with pytest.raises(netmig.MissingManualDownloadError, match="ICPSR"):
        netmig.download()
