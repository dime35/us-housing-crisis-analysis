import json

import pytest

from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import bea


def test_states_only_and_values_parsed(fixtures_dir):
    df = validate_long(bea.parse_bea_json(fixtures_dir / "bea/sainc1_state_pcpi.json", "state"))
    assert set(df.geo_id) == {"state:24"}  # US, regions and suppressed Alaska dropped
    assert df.set_index("year").loc[2020, "value"] == 68258.0


def test_msa_names_cleaned_and_us_portion_dropped(fixtures_dir):
    df = validate_long(bea.parse_bea_json(fixtures_dir / "bea/cainc1_msa_pcpi.json", "metro"))
    assert list(df.geo_id) == ["cbsa:12580"]  # (D) value in 1971 dropped
    assert df.geo_name.iloc[0] == "Baltimore-Columbia-Towson, MD"


def test_error_payload_raises(tmp_path):
    p = tmp_path / "err.json"
    p.write_text(json.dumps({"BEAAPI": {"Results": {"Error": {"APIErrorDescription": "Invalid UserID"}}}}))
    with pytest.raises(bea.BeaApiError, match="Invalid UserID"):
        bea.parse_bea_json(p, "state")


def test_error_payload_is_not_cached(tmp_path, monkeypatch):
    monkeypatch.setenv("BEA_API_KEY", "k")
    monkeypatch.setattr(bea, "RAW_DIR", tmp_path)

    def fake_download(url, dest, **kwargs):
        dest.write_text(json.dumps({"BEAAPI": {"Error": {"APIErrorDescription": "bad"}}}))
        return dest

    monkeypatch.setattr(bea, "download_file", fake_download)
    with pytest.raises(bea.BeaApiError):
        bea.download()
    assert not list(tmp_path.glob("*.json"))
