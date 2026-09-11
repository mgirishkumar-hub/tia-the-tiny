import pytest

from bot.config import Config


def test_defaults_and_secret_redaction():
    config = Config.from_env({"DISCORD_TOKEN": "private-token", "DATABASE_URL": "postgresql://tia:private-pass@db/tia"})
    assert config.default_prefix == "."
    assert "private-token" not in repr(config)
    assert "private-pass" not in repr(config)


@pytest.mark.parametrize("environment", [
    {},
    {"DISCORD_TOKEN": "private-token"},
    {"DISCORD_TOKEN": "private-token", "DATABASE_URL": "https://private-pass@db/tia"},
    {"DISCORD_TOKEN": "private-token", "DATABASE_URL": "postgresql://db"},
    {"DISCORD_TOKEN": "private-token", "DATABASE_URL": "postgresql://db:99999/tia"},
    {"DISCORD_TOKEN": "private-token", "DATABASE_URL": "postgresql://db/tia", "DEFAULT_PREFIX": ""},
])
def test_bad_configuration_fails_without_exposing_values(environment):
    with pytest.raises(ValueError) as error:
        Config.from_env(environment)
    assert "private-token" not in str(error.value)
    assert "private-pass" not in str(error.value)
