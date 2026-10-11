import pytest

from src import export, validate


@pytest.fixture(autouse=True)
def _isolate_reports(tmp_path, monkeypatch):
    """Jangan biarkan tes menimpa reports/ asli di dalam proyek."""
    monkeypatch.setattr(validate, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(export, "REPORTS_DIR", tmp_path)
