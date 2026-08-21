import pytest
from fastapi import HTTPException

from jobpilot.api.routes.ops import authorize_ops
from jobpilot.config import get_settings
from jobpilot.storage import persist_directory


def test_ops_rejects_without_token(monkeypatch):
    monkeypatch.setenv("JOBPILOT_OPS_TOKEN", "")
    get_settings.cache_clear()
    with pytest.raises(HTTPException) as exc:
        authorize_ops(None, None)
    assert exc.value.status_code == 503


def test_ops_rejects_bad_token(monkeypatch):
    monkeypatch.setenv("JOBPILOT_OPS_TOKEN", "secret-token")
    get_settings.cache_clear()
    with pytest.raises(HTTPException) as exc:
        authorize_ops("Bearer nope", None)
    assert exc.value.status_code == 401
    authorize_ops("Bearer secret-token", None)


def test_persist_directory_stays_local(tmp_path, monkeypatch):
    monkeypatch.setenv("GCS_BUCKET", "")
    get_settings.cache_clear()
    dest = tmp_path / "pkg"
    dest.mkdir()
    (dest / "a.txt").write_text("ok", encoding="utf-8")
    assert persist_directory(dest, "generated/x") == str(dest)
