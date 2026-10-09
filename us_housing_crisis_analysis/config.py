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

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass
