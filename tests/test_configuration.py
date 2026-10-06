import pytest

from src.config.settings import Settings


def test_missing_secret_and_invalid_port(monkeypatch):
    monkeypatch.setenv("POSTGRES_PASSWORD", "")
    with pytest.raises(ValueError, match="POSTGRES_PASSWORD"):
        Settings.from_env()
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_only")
    monkeypatch.setenv("POSTGRES_PORT", "70000")
    with pytest.raises(ValueError, match="POSTGRES_PORT"):
        Settings.from_env()


def test_secret_absent_from_repr_and_safe_url():
    settings = Settings("127.0.0.1", 5432, "test", "test", "with@/#special")
    assert "with@/#special" not in repr(settings)
    assert settings.url.password == "with@/#special"
