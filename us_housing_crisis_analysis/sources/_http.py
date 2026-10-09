"""Shared download helpers for source modules."""

import os
from pathlib import Path

from loguru import logger
import requests

HEADERS = {"User-Agent": "us-housing-crisis-analysis (academic research)"}


class MissingCredentialError(RuntimeError):
    """An API key needed by a source is not set in the environment."""


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise MissingCredentialError(
            f"{name} is not set. Add `{name}=<your key>` to the .env file in the project root."
        )
    return value


def download_file(
    url: str, dest: Path, *, force: bool = False, params: dict | None = None, timeout: int = 300
) -> Path:
    """Stream url to dest. Skip if dest exists, unless force. Writes via a .part file so an
    interrupted download never looks complete."""
    dest = Path(dest)
    if dest.exists() and not force:
        logger.info(f"skip {dest.name}: already downloaded")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    with requests.get(url, params=params, headers=HEADERS, stream=True, timeout=timeout) as r:
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            # requests puts the full URL, query string included, in the message; query params can
            # carry API keys, so re-raise with the bare URL only.
            status = getattr(e.response, "status_code", "HTTP error")
            raise requests.HTTPError(f"{status} for {url}", response=e.response) from None
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    tmp.replace(dest)
    logger.info(f"downloaded {dest.name}")
    return dest
