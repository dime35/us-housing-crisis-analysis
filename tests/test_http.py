import pytest

from us_housing_crisis_analysis.sources import _http
from us_housing_crisis_analysis.sources._http import MissingCredentialError, download_file, require_env


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        yield self.body


def test_existing_file_is_not_downloaded_again(tmp_path, monkeypatch):
    dest = tmp_path / "raw.csv"
    dest.write_text("cached")

    def fail(*args, **kwargs):
        raise AssertionError("network called for a cached file")

    monkeypatch.setattr(_http.requests, "get", fail)
    assert download_file("https://example.org/raw.csv", dest) == dest
    assert dest.read_text() == "cached"


def test_force_downloads_again(tmp_path, monkeypatch):
    dest = tmp_path / "raw.csv"
    dest.write_text("old")
    monkeypatch.setattr(_http.requests, "get", lambda *a, **k: FakeResponse(b"new"))
    download_file("https://example.org/raw.csv", dest, force=True)
    assert dest.read_text() == "new"
    assert not (tmp_path / "raw.csv.part").exists()


def test_missing_key_names_the_variable(monkeypatch):
    monkeypatch.delenv("BEA_API_KEY", raising=False)
    with pytest.raises(MissingCredentialError, match="BEA_API_KEY.*\\.env"):
        require_env("BEA_API_KEY")


def test_blank_key_counts_as_missing(monkeypatch):
    monkeypatch.setenv("BEA_API_KEY", "   ")
    with pytest.raises(MissingCredentialError):
        require_env("BEA_API_KEY")
