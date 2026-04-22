import pytest

from crm.ui.web.app import create_app


def test_production_requires_secret_key(monkeypatch, tmp_path):
    monkeypatch.setenv("CRM_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(data_path=str(tmp_path / "data.json"), storage_backend="json")


def test_postgres_requires_database_url(monkeypatch, tmp_path):
    monkeypatch.setenv("CRM_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "local-secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        create_app(data_path=str(tmp_path / "data.json"), storage_backend="postgres")
