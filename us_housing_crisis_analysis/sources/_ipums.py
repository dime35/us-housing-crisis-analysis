"""Submit, wait for, and download IPUMS extracts (NHGIS and IPUMS USA share one API key)."""

from fnmatch import fnmatch
from pathlib import Path
import zipfile

from loguru import logger

from us_housing_crisis_analysis.config import IPUMS_API_KEY_ENV
from us_housing_crisis_analysis.sources._http import require_env


def client():
    from ipumspy import IpumsApiClient

    return IpumsApiClient(require_env(IPUMS_API_KEY_ENV))


def run_extract(extract, dest_dir: Path) -> Path:
    api = client()
    api.submit_extract(extract)
    logger.info(f"submitted {extract.collection} extract {extract.extract_id}; waiting (can take hours)")
    api.wait_for_extract(extract)
    dest_dir.mkdir(parents=True, exist_ok=True)
    api.download_extract(extract, download_dir=dest_dir)
    return dest_dir


def unpack_csvs(dest_dir: Path, patterns: dict[str, str]) -> list[Path]:
    """Copy CSVs out of downloaded NHGIS zips under stable names: {glob pattern: new name}."""
    written: dict[str, Path] = {}
    members_seen = []
    for zpath in sorted(dest_dir.glob("*_csv.zip")):
        with zipfile.ZipFile(zpath) as z:
            for member in z.namelist():
                members_seen.append(member)
                for pattern, name in patterns.items():
                    if fnmatch(Path(member).name, pattern):
                        (dest_dir / name).write_bytes(z.read(member))
                        written[name] = dest_dir / name
    missing = set(patterns.values()) - set(written)
    if missing:
        raise FileNotFoundError(f"{sorted(missing)} not found in extract; members: {members_seen}")
    return [written[n] for n in patterns.values()]
