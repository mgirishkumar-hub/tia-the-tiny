from unittest.mock import AsyncMock

import asyncpg
import pytest

from bot.database import PrefixStore, configuration_error_reason


@pytest.mark.parametrize(("message", "expected"), [
    ("`sslmode` parameter must be one of: modes", "invalid sslmode"),
    ('root certificate file "sensitive-value" does not exist or cannot be accessed', "CA certificate file"),
    ("cannot determine location of user PostgreSQL configuration directory", "certificate directory"),
    ("`sslnegotiation` parameter must be one of: modes", "invalid sslnegotiation"),
    ("Unsupported TLS version: sensitive-value", "unsupported TLS version"),
    ("No such TLS version: sensitive-value", "invalid TLS version"),
    ("invalid IPv6 address in the connection URI: sensitive-value", "invalid IPv6"),
    ("could not match 2 port numbers to 3 hosts", "hosts and ports"),
    ("invalid DSN: scheme is expected", "must start with postgresql://"),
    ("could not determine user name to connect with", "username is missing"),
    ("could not determine database name to connect to", "database name is missing"),
    ("server_settings is expected to be None or a Dict[str, str]", "server_settings"),
    ("target_session_attrs is expected to be one of values, got sensitive-value", "invalid target_session_attrs"),
    ("gsslib parameter must be either 'gssapi' or 'sspi', got sensitive-value", "invalid gsslib"),
    ("an unknown error with sensitive-value", "unrecognized database configuration error"),
])
def test_driver_configuration_errors_have_safe_specific_messages(message, expected):
    result = configuration_error_reason(asyncpg.ClientConfigurationError(message))
    assert expected in result
    assert "sensitive-value" not in result


async def test_real_invalid_sslmode_reports_the_setting_without_values(caplog):
    store = PrefixStore("postgresql://tia:private-password@127.0.0.1:1/tia?sslmode=invalid-private-value")
    with pytest.raises(asyncpg.ClientConfigurationError):
        await store.open()
    assert "database configuration error: invalid sslmode" in caplog.text
    assert "private-password" not in caplog.text
    assert "invalid-private-value" not in caplog.text
    assert store._pool is None


async def test_real_missing_ca_has_different_guidance(monkeypatch, tmp_path, caplog):
    from asyncpg import connect_utils

    monkeypatch.delenv("PGSSLROOTCERT", raising=False)
    monkeypatch.setattr(connect_utils, "_dot_postgresql_path", lambda filename: tmp_path / filename)
    store = PrefixStore("postgresql://tia:private-password@127.0.0.1:1/tia?sslmode=verify-full")
    with pytest.raises(asyncpg.ClientConfigurationError):
        await store.open()
    assert "database configuration error: CA certificate file" in caplog.text
    assert "PGSSLROOTCERT" in caplog.text
    assert "private-password" not in caplog.text
    assert str(tmp_path) not in caplog.text
    assert store._pool is None


async def test_cleanup_still_runs_and_the_original_error_is_preserved(monkeypatch, caplog):
    error = asyncpg.ClientConfigurationError("No such TLS version: private-value")
    monkeypatch.setattr(asyncpg, "create_pool", AsyncMock(side_effect=error))
    store = PrefixStore("postgresql://tia:private-password@127.0.0.1/tia")
    close = AsyncMock()
    monkeypatch.setattr(store, "close", close)
    with pytest.raises(asyncpg.ClientConfigurationError) as caught:
        await store.open()
    assert caught.value is error
    close.assert_awaited_once()
    assert "invalid TLS version" in caplog.text
    assert "private-value" not in caplog.text
