import types

import pandas as pd
from typer.testing import CliRunner

from us_housing_crisis_analysis import dataset
from tests.test_schema import good_frame


def fake_module():
    return types.SimpleNamespace(download=lambda force=False: [], load=good_frame)


def test_load_writes_validated_parquet(tmp_path, monkeypatch):
    monkeypatch.setattr(dataset, "SOURCE_NAMES", ["fake"])
    monkeypatch.setattr(dataset, "get_source", lambda name: fake_module())
    monkeypatch.setattr(dataset, "INTERIM_DATA_DIR", tmp_path)
    result = CliRunner().invoke(dataset.app, ["load"])
    assert result.exit_code == 0, result.output
    assert len(pd.read_parquet(tmp_path / "fake.parquet")) == 2


def test_unknown_source_is_rejected(monkeypatch):
    monkeypatch.setattr(dataset, "SOURCE_NAMES", ["fake"])
    result = CliRunner().invoke(dataset.app, ["download", "--source", "nope"])
    assert result.exit_code != 0
    assert "unknown source" in result.output


def test_cli_tracebacks_do_not_print_local_variables():
    # API keys live in local variables of source download() functions
    assert dataset.app.pretty_exceptions_show_locals is False
