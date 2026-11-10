import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_refuses_dev_secret(monkeypatch):
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(environment="production", _env_file=None)


def test_cors_origins_parse_from_comma_string():
    s = Settings(cors_origins="http://a.test, http://b.test", _env_file=None)
    assert [str(o) for o in s.cors_origins] == ["http://a.test/", "http://b.test/"]
