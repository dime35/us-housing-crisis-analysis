import pytest

from us_housing_crisis_analysis.sources import gazetteer


def parsed(fixtures_dir, year):
    text = gazetteer.decode((fixtures_dir / "gazetteer" / f"gaz_{year}.txt").read_bytes())
    return gazetteer.parse(year, text).set_index("geoid")


@pytest.mark.parametrize("year", [1990, 2000, 2010, 2020])
def test_detroit_land_area_in_square_miles(fixtures_dir, year):
    assert parsed(fixtures_dir, year).loc["2622000", "land_sqmi"] == pytest.approx(138.7, abs=0.1)


def test_1990_area_matches_working_paper_27(fixtures_dir):
    # WP27 table 22: Houston 539.9 sq mi; the 1990 file stores thousands of square meters
    assert parsed(fixtures_dir, 1990).loc["4835000", "land_sqmi"] == pytest.approx(539.9, rel=0.005)


def test_codes_are_that_years_codes(fixtures_dir):
    g1990, g2020 = parsed(fixtures_dir, 1990), parsed(fixtures_dir, 2020)
    assert "1235160" in g1990.index  # Jacksonville city (remainder)
    assert {"2148000", "2148006"} <= set(g2020.index)  # Louisville: old city and balance
    # together they make up the 2010 balance (325.2 sq mi), up to remeasurement
    assert g2020.loc[["2148000", "2148006"], "land_sqmi"].sum() == pytest.approx(325.2, rel=0.005)


def test_codes_listed_twice_are_dropped():
    text = ("USPS\tGEOID\tANSICODE\tNAME\tLSAD\tFUNCSTAT\tALAND\tAWATER\tALAND_SQMI\tAWATER_SQMI\tINTPTLAT\tINTPTLONG\n"
            "PA\t4269336\t1\tSeven Springs borough\t21\tA\t1\t0\t1.0\t0\t0\t0\n"
            "PA\t4269336\t2\tThree Springs borough\t21\tA\t1\t0\t2.0\t0\t0\t0\n"
            "MI\t2622000\t3\tDetroit city\t25\tA\t1\t0\t138.7\t0\t0\t0\n")
    assert list(gazetteer.parse(2020, text).geoid) == ["2622000"]
