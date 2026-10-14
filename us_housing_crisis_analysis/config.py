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
