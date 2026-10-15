import zipfile

import pandas as pd
import pytest

from us_housing_crisis_analysis.config import NETMIG_DECADES, NETMIG_FILES
from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import netmig


def parse_2010s(fixtures_dir):
    spec = NETMIG_FILES[2010]
    return validate_long(
        netmig.parse_net_migration(fixtures_dir / "netmig" / spec["file"], 2010, spec)
    )


def test_county_rows_only_state_totals_never_added(fixtures_dir):
    df = parse_2010s(fixtures_dir).set_index("geo_id")
    assert set(df.index) == {"county:24510", "county:24005", "county:24003", "county:11001"}
    assert df.at["county:24510", "value"] == -56058.0 and df.at["county:11001", "value"] == 40898.0
    assert (
        set(df.year) == {2010}
        and set(df.variable) == {"net_migration"}
        and set(df.unit) == {"persons"}
    )


def test_summed_columns(fixtures_dir, tmp_path):
    spec = dict(NETMIG_FILES[2010], total_col="m1tttt+m1tttt")
    df = netmig.parse_net_migration(fixtures_dir / "netmig" / spec["file"], 2010, spec).set_index(
        "geo_id"
    )
    assert df.at["county:24005", "value"] == 2 * 32061.0


def test_missing_manual_files_raise(tmp_path, monkeypatch):
    monkeypatch.setattr(netmig, "RAW_DIR", tmp_path)
    monkeypatch.setattr(
        netmig,
        "NETMIG_FILES",
        {**NETMIG_FILES, 1950: dict(NETMIG_FILES[2010], file="icpsr_1950s.zip")},
    )
    monkeypatch.setattr(
        netmig, "download_file", lambda url, dest, **kw: dest.write_bytes(b"x") or dest
    )
    with pytest.raises(netmig.MissingManualDownloadError, match="ICPSR"):
        netmig.download()


def test_every_decade_has_a_file():
    assert set(NETMIG_FILES) == set(NETMIG_DECADES)


# Synthetic fixed-width fixture (fields touch, as in ICPSR 4171): level, state, county, fips, name, total
FIXED = {
    "file": "fixed_width.zip",
    "member": "fixed_width.txt",
    "total_col": "total",
    "colspecs": "level:0-3,state:3-6,county:6-9,fips:9-14,name:14-34,total:34-43",
}


def test_fixed_width_with_state_and_county_fields(fixtures_dir):
    spec = dict(FIXED, state_col="state", county_col="county", name_col="name")
    df = validate_long(
        netmig.parse_net_migration(fixtures_dir / "netmig" / spec["file"], 1970, spec)
    ).set_index("geo_id")
    assert set(df.index) == {"county:24510", "county:24005"}  # state, division and US rows dropped
    assert (
        df.at["county:24510", "value"] == -1200.0
        and df.at["county:24005", "geo_name"] == "SYNTH COUNTY"
    )


def test_fixed_width_with_fips_field_and_no_name(fixtures_dir):
    spec = dict(FIXED, fips_col="fips")
    df = validate_long(
        netmig.parse_net_migration(fixtures_dir / "netmig" / spec["file"], 1990, spec)
    ).set_index("geo_id")
    assert set(df.index) == {"county:24510", "county:24005"}
    assert (
        df.at["county:24005", "value"] == 3400.0 and df.at["county:24005", "geo_name"] == "24005"
    )


def _stata_zip(tmp_path, frame):
    path = tmp_path / "synthetic.zip"
    frame.to_stata(tmp_path / "data.dta", write_index=False)
    with zipfile.ZipFile(path, "w") as zf:
        zf.write(tmp_path / "data.dta", "data.dta")
    return path


def test_stata_uga_state_codes_and_numeric_county_numbers(tmp_path):
    # Bowles layout (ICPSR 8493): UGA state code 2-52, county number 0 on state rows, missing on divisions
    frame = pd.DataFrame(
        {
            "LEVELNO": [1, 1, 1, 2, 4],
            "LEVELID": [22, 22, 10, 5, 99],
            "CNTYNO": [0.0, 4.0, 1.0, float("nan"), float("nan")],
            "CNTYNAME": ["", "SYNTH CITY", "SYNTH DC", "", ""],
            "V532": [50, 50, 7, 57, 57],
        }
    )
    spec = {
        "file": "synthetic.zip",
        "member": "data.dta",
        "state_col": "LEVELID",
        "state_codes": "uga",
        "county_col": "CNTYNO",
        "name_col": "CNTYNAME",
        "total_col": "V532",
    }
    df = validate_long(
        netmig.parse_net_migration(_stata_zip(tmp_path, frame), 1950, spec)
    ).set_index("geo_id")
    assert set(df.index) == {"county:24004", "county:11001"}  # MD is UGA 22, DC is UGA 10
    assert df.at["county:24004", "value"] == 50.0


def test_uga_codes_cover_the_51_states_in_order():
    assert len(netmig.UGA_STATE_FIPS) == 51 and list(netmig.UGA_STATE_FIPS) == list(range(2, 53))
    assert (
        netmig.UGA_STATE_FIPS[2] == "01"
        and netmig.UGA_STATE_FIPS[10] == "11"
        and netmig.UGA_STATE_FIPS[52] == "56"
    )


def test_stata_numeric_fips_is_zero_padded(tmp_path):
    frame = pd.DataFrame(
        {"FIPS": [1001, 24510], "COUNTY": ["A", "B"], "M": [1.5, 2.0], "F": [0.5, 1.0]}
    )
    spec = {
        "file": "synthetic.zip",
        "member": "data.dta",
        "fips_col": "FIPS",
        "name_col": "COUNTY",
        "total_col": "M+F",
    }
    df = netmig.parse_net_migration(_stata_zip(tmp_path, frame), 1980, spec).set_index("geo_id")
    assert df.value.to_dict() == {"county:01001": 2.0, "county:24510": 3.0}
