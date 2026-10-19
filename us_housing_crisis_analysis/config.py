from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file if it exists
load_dotenv()

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]
logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJ_ROOT / "models"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

REFERENCES_DIR = PROJ_ROOT / "references"
CROSSWALKS_DIR = REFERENCES_DIR / "crosswalks"
MANUAL_DATA_DIR = REFERENCES_DIR / "manual_data"
TABLES_DIR = REPORTS_DIR / "tables"

# Names of the .env variables holding API keys (values are never stored here)
IPUMS_API_KEY_ENV = "IPUMS_API_KEY"  # one key covers NHGIS and IPUMS USA
BEA_API_KEY_ENV = "BEA_API_KEY"

# RQ0b: each version starts at the first decade from which income exists for every
# decade onward (spec §5). No decade is interpolated.
RQ0B_STATE_START = 1880
RQ0B_METRO_START = 1940
RQ0B_END = 2020
METRO_LONGRUN_START = 1900
# RQ0b annual break dating (Plan 1b): BEA state data from 1929, county data from 1969. Annual
# growth runs t -> t+1, so the last growth year is RQ0B_ANNUAL_END - 1.
RQ0B_ANNUAL_STATE_START = 1929
RQ0B_ANNUAL_METRO_START = 1969
RQ0B_ANNUAL_END = 2024
# Energy states (Plan 1b spec §4.3, §8.2): 1980 mining share of earnings >= 3x the national share.
# The hand-picked list is the robustness check (TX, OK, LA, WY, AK, NM, WV, ND).
ENERGY_SHARE_YEAR = 1980
ENERGY_SHARE_MULTIPLE = 3.0
ENERGY_STATES_HAND = ("48", "40", "22", "56", "02", "35", "54", "38")
# Growth years left out in the WWII robustness check (troop moves and war industry)
WWII_GROWTH_YEARS = range(1940, 1947)

# Plan 1c (1970 or 1990?): the two cut years, the oil years (energy states get their own year
# effects then), and the main immigrant gateway states for the net-migration check.
RQ0B_CUTS = (1970, 1990)
OIL_YEARS = (1973, 1990)
OIL_YEARS_SHORT = (1973, 1986)
GATEWAY_STATES = ("06", "36", "34", "17", "12", "48")

# County net migration by decade (Plan 1c): the UW-Madison Applied Population Laboratory series and
# its predecessors (ICPSR collection 2760). Keys are the decade start (1950 = 1950-60). Files sit
# unopened in data/raw/netmig/ under ICPSR's own zip names. File, member and column names were
# checked against each study's codebook on 2026-10-15. total_col is net migration of all ages, both
# sexes and all races, including the cohorts born during the decade (ages 0-9 at its end);
# "a+b+..." sums groups that partition the population. Counties are identified by fips_col (5-digit
# FIPS) or by state_col + county_col; state_codes="uga" maps the old 2-52 state codes to FIPS.
# colspecs reads a fixed-width member: "name:start-end,..." with 0-based, half-open positions.
# County codes are FIPS in the state part for every decade, but NOT always in the county part:
#   1950s, 1960s: the county part is the files' own sequence number (CNTYNO), not FIPS.
#   1970s: FIPS, except Virginia (the files' own unit numbers 1-96, some units merge cities and
#     counties), Alaska and Hawaii (one unit each, coded 001), Baltimore city (24007), St. Louis
#     city (29191), Ste. Genevieve (29193), and a few merged units (codebook section 2).
#   1990s: FIPS, except 12 merged units coded xx9xx (codebook Appendix 2).
# Only the state part is used downstream (states sum their counties).
_AGES_1980 = ["04", "59", "104", "159", "204", "259", "304", "359", "404", "459", "504", "559",
              "604", "659", "704", "759", "804", "85U"]
NETMIG_DECADES = range(1950, 2011, 10)
NETMIG_FILES: dict[int, dict[str, str]] = {
    # ICPSR 8493 (Bowles, Tarver, Beale, Lee), DS0001: V532 = net migration 1950-60, all ages,
    # total. LEVELID is the UGA state code, CNTYNO the county number (0 on state rows)
    1950: {"file": "ICPSR_08493-V2.zip", "member": "ICPSR_08493/DS0001/08493-0001-Data.dta",
           "state_col": "LEVELID", "state_codes": "uga", "county_col": "CNTYNO",
           "name_col": "CNTYNAME", "total_col": "V532"},
    # ICPSR 8493, DS0002: V532 = net migration 1960-70, all ages, total
    1960: {"file": "ICPSR_08493-V2.zip", "member": "ICPSR_08493/DS0002/08493-0002-Data.dta",
           "state_col": "LEVELID", "state_codes": "uga", "county_col": "CNTYNO",
           "name_col": "CNTYNAME", "total_col": "V532"},
    # ICPSR 8697 (White, Mueser, Tierney), ASCII only; codebook section 3.2: NMETOTAL = total net
    # migration estimate (columns 3007-3015, 1-based), FIPSTATE 7-9, FIPSCNTY 10-12, NAME 16-42
    1970: {"file": "ICPSR_08697-V1.zip", "member": "ICPSR_08697/DS0001/08697-0001-Data.txt",
           "colspecs": "FIPSTATE:6-9,FIPSCNTY:9-12,NAME:15-42,NMETOTAL:3006-3015",
           "state_col": "FIPSTATE", "county_col": "FIPSCNTY", "name_col": "NAME",
           "total_col": "NMETOTAL"},
    # ICPSR 26761 (Fuguitt, Beale, Voss): the sum of the 36 male and female age groups AM..M89 and
    # AM..F89. The all-ages totals (AMTOTT89, AMTOTM89, AMTOTF89) lose two digits in the largest
    # counties (Cook County: -5,174 for -517,403), and AM804T89 (both sexes 80-84) does not equal
    # male + female.
    1980: {"file": "ICPSR_26761-V1.zip", "member": "ICPSR_26761/DS0001/26761-0001-Data.dta",
           "fips_col": "FIPS", "name_col": "COUNTY",
           "total_col": "+".join(f"AM{age}{sex}89" for sex in "MF" for age in _AGES_1980)},
    # ICPSR 4171 (Voss, McNiven, Hammer, Johnson, Fuguitt), ASCII only, no names. The codebook
    # lists the 1726 variables in file order (Appendix 4) without positions, and the setup files
    # are not in the zip. Field ends come from the file (the same 1726 ends on every record):
    # NMG_TT_T, net migration 1990-2000, is field 1441
    1990: {"file": "ICPSR_04171-V1.zip", "member": "ICPSR_04171/DS0001/04171-0001-Data.txt",
           "colspecs": "FIPS:0-5,NMG_TT_T:7725-7732", "fips_col": "FIPS",
           "total_col": "NMG_TT_T"},
    # ICPSR 34638 (Winkler, Johnson, Cheng, Voss, Curtis). No all-ages column: the sum of the 18
    # age groups M0TTT0-M0TTT85 (total race, both sexes). FIPS3188 has xx000 state-total rows
    2000: {"file": "ICPSR_34638-V1.zip", "member": "ICPSR_34638/DS0001/34638-0001-Data.dta",
           "fips_col": "FIPS3188", "name_col": "CTYNAME",
           "total_col": "+".join(f"M0TTT{age}" for age in range(0, 90, 5))},
    # APL download: m1tttt = net migration 2010-20, all ages, both sexes, all races
    2010: {"file": "NME_1020_data.zip", "member": "NME_1020_data.csv", "fips_col": "fips_str2020",
           "name_col": "CoName2020", "total_col": "m1tttt"},
}

# ICPSR 2896 county median family income for RQ0b metro income (found in Plan 1, Task 9, Step 2).
# Files are the zips as downloaded from ICPSR; member is the Stata file inside. fips_col is the
# 5-digit state+county FIPS (the 1952 statefip/counfip columns are not FIPS codes). Income is
# median family income in current dollars (1949 and 1959 income, from the 1950 and 1960 censuses).
ICPSR_INCOME_FILES: dict[int, dict[str, str]] = {
    1950: {
        "file": "ICPSR_02896-V3 1952.zip", "member": "ICPSR_02896/DS0072/02896-0072-Data.dta",
        "fips_col": "fips", "income_col": "var20",
    },
    1960: {
        "file": "ICPSR_02896-V3 1962.zip", "member": "ICPSR_02896/DS0074/02896-0074-Data.dta",
        "fips_col": "fips", "income_col": "var22",
    },
}

# RQ0a (Plan 2): city vs. metro. City populations from 1900, metro populations from 1940, classes in
# three periods (Plan 1c's cuts). Keep-up bars: relative = RQ0A_BAR_FRACTION x US growth over the
# same period (50 states + DC); absolute = RQ0A_ABSOLUTE_RATE per decade, compounded. Annexing: land
# area up more than RQ0A_ANNEX_THRESHOLD over the period (checks 0.10 and 0.40).
RQ0A_CITY_START = 1900
RQ0A_METRO_START = 1940
RQ0A_PERIODS = ((1950, 1970), (1970, 1990), (1990, 2020))
RQ0A_BAR_FRACTION = 0.5
RQ0A_ABSOLUTE_RATE = 0.05
RQ0A_ANNEX_THRESHOLD = 0.20
RQ0A_MIN_GROUP = 15  # rule 2: fewer cities than this in either group -> "not testable"
# Two city sources must agree this closely where they overlap (CESTA vs. NHGIS in 2010)
RQ0A_OVERLAP_TOLERANCE = 0.005

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass
