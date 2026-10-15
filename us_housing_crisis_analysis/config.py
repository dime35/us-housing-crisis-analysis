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

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass
