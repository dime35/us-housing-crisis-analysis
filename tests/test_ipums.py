import pandas as pd

from us_housing_crisis_analysis.schema import validate_long
from us_housing_crisis_analysis.sources import ipums


def chunks():
    # Baltimore city (NHGIS 2405100) appears in both chunks; one historical county has no FIPS
    yield pd.DataFrame({"STATEFIP": [24, 24, 24], "COUNTYNHG": [2405100, 2405100, 2400050],
                        "INCWAGE": [1000, 5001, 999999]})
    yield pd.DataFrame({"STATEFIP": [24, 46], "COUNTYNHG": [2405100, 4650015],
                        "INCWAGE": [999998, 200]})


def test_aggregate_combines_chunks_and_codes():
    agg = ipums.aggregate_wages(chunks()).set_index("COUNTYNHG")
    balt = agg.loc[2405100]
    assert balt.wage_total == 6001  # 1000 + topcoded 5001; 999998 (missing) adds 0
    assert balt.persons == 3
    assert balt.missing_wage == 1  # 999998 counted as missing; 999999 (N/A) is not
    assert agg.loc[2400050].wage_total == 0  # child / N/A contributes 0 but counts as a person


def test_to_long_ids_and_schema():
    df = validate_long(ipums.to_long(ipums.aggregate_wages(chunks())))
    assert {"county:24510", "county:24005", "county:nhgis-4650015"} <= set(df.geo_id)
    assert set(df.variable) == {"wage_income_total", "persons_ipums", "wage_missing_share"}
    assert set(df.year) == {1940}


def test_download_skips_when_files_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(ipums, "RAW_DIR", tmp_path)
    (tmp_path / "usa_00001.xml").write_text("x")
    (tmp_path / "usa_00001.dat.gz").write_text("x")
    monkeypatch.setattr(ipums, "run_extract", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    assert len(ipums.download()) == 2


def test_nhgis_code_built_from_statefip_and_countyicp():
    # COUNTYICP = 3-digit FIPS county + trailing digit (0 = has FIPS, 5 = dissolved county)
    raw = pd.DataFrame({"STATEFIP": [24, 46], "COUNTYICP": [5100, 15], "INCWAGE": [1, 2]})
    out = ipums.with_nhgis_code(raw)
    assert out.COUNTYNHG.tolist() == [2405100, 4600015]
    assert set(ipums.to_long(ipums.aggregate_wages([out])).geo_id) == {"county:24510", "county:nhgis-4600015"}
