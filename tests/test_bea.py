import json

import pytest

from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import bea


def test_states_only_and_values_parsed(fixtures_dir):
    df = validate_long(bea.parse_bea_json(fixtures_dir / "bea/sainc1_state_pcpi.json", "state"))
    assert set(df.geo_id) == {"state:24"}  # US, regions, suppressed Alaska and placeholder-0 Hawaii dropped
    assert df.set_index("year").loc[2020, "value"] == 68258.0


def test_county_rows_dollars_and_harmonized_ids(fixtures_dir):
    df = validate_long(bea.parse_bea_json(fixtures_dir / "bea/cainc1_county_pi.json", "county",
                                          variable="personal_income", unit="usd_current"))
    v = df.set_index("geo_id").value
    assert v["county:24510"] == 3_512_000_000.0  # thousands of dollars -> dollars
    assert v["county:51003"] == 300_000_000.0  # Albemarle + Charlottesville combo -> Albemarle
    assert "county:24000" not in v.index  # state total dropped
    assert "county:02063" not in v.index  # (NA) dropped, never zero-filled
    assert "county:08014" not in v.index  # 0 = BEA placeholder for a county that didn't exist yet
    # Connecticut: BEA reports the 8 old counties (mapped like every historical source via
    # ct_legacy_counties.csv); planning regions are dropped so people are never counted twice
    assert "county:09001" in v.index and "county:09190" not in v.index
    assert set(df.variable) == {"personal_income"}


def test_combo_and_component_in_same_year_raises(tmp_path, fixtures_dir):
    payload = json.loads((fixtures_dir / "bea/cainc1_county_pi.json").read_text())
    row = dict(payload["BEAAPI"]["Results"]["Data"][0], GeoFips="51540", GeoName="Charlottesville, VA")
    payload["BEAAPI"]["Results"]["Data"].append(row)
    p = tmp_path / "overlap.json"
    p.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="51901"):
        bea.parse_bea_json(p, "county", variable="personal_income")


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


def test_saved_payload_drops_the_request_and_its_key(tmp_path, monkeypatch):
    monkeypatch.setenv("BEA_API_KEY", "secret-key")
    monkeypatch.setattr(bea, "RAW_DIR", tmp_path)

    def fake_download(url, dest, **kwargs):
        dest.write_text(json.dumps({"BEAAPI": {
            "Request": {"RequestParam": [{"ParameterName": "USERID", "ParameterValue": "secret-key"}]},
            "Results": {"Data": []}}}))
        return dest

    monkeypatch.setattr(bea, "download_file", fake_download)
    for path in bea.download():
        text = path.read_text()
        assert "secret-key" not in text and "Request" not in text
        assert "Results" in json.loads(text)["BEAAPI"]


def _payload(rows, unit_mult="0"):
    data = [{"GeoFips": f, "GeoName": n, "TimePeriod": y, "DataValue": v, "UNIT_MULT": unit_mult}
            for f, n, y, v in rows]
    return {"BEAAPI": {"Results": {"Data": data}}}


def test_new_requests_are_registered():
    assert bea.REQUESTS["sainc1_state_pop"] == ("SAINC1", 2, "STATE", "state", "population_bea", "persons")
    assert bea.REQUESTS["sainc5s_state_earnings_total"][:2] == ("SAINC5S", 35)
    assert bea.REQUESTS["sainc5s_state_earnings_mining"][:2] == ("SAINC5S", 200)


def test_state_population_drops_alaska_zero_placeholder(tmp_path):
    p = tmp_path / "pop.json"
    p.write_text(json.dumps(_payload([("02000", "Alaska *", "1940", "0"), ("02000", "Alaska *", "1950", "135,000"),
                                      ("00000", "United States", "1950", "151,000,000")])))
    df = validate_long(bea.parse_bea_json(p, "state", "population_bea", "persons"))
    assert df[["geo_id", "year", "value"]].values.tolist() == [["state:02", 1950, 135000.0]]


def test_earnings_in_thousands_become_dollars(tmp_path):
    p = tmp_path / "earn.json"
    p.write_text(json.dumps(_payload([("56000", "Wyoming", "1980", "1,234")], unit_mult="3")))
    df = bea.parse_bea_json(p, "state", "earnings_mining", "usd_current")
    assert df.value.tolist() == [1_234_000.0]
