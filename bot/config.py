import os
import string
from dataclasses import dataclass, field
from typing import Mapping
from urllib.parse import urlsplit

PREFIX_CHARACTERS = frozenset(
    string.ascii_letters + string.digits + string.punctuation.replace("@", "").replace("`", "").replace("\\", "")
)


def valid_prefix(value: str) -> bool:
    return 1 <= len(value) <= 5 and all(character in PREFIX_CHARACTERS for character in value)


@dataclass(frozen=True)
class Config:
    discord_token: str = field(repr=False)
    database_url: str = field(repr=False)
    default_prefix: str = "."

    @classmethod
    def from_env(cls, environment: Mapping[str, str] | None = None) -> "Config":
        env = os.environ if environment is None else environment
        token = env.get("DISCORD_TOKEN", "").strip()
        database_url = env.get("DATABASE_URL", "").strip()
        prefix = env.get("DEFAULT_PREFIX", ".")
        if not token:
            raise ValueError("DISCORD_TOKEN is missing; add it to the runtime variables")
        if not database_url:
            raise ValueError("DATABASE_URL is missing; link the PostgreSQL connection URI")
        try:
            parsed = urlsplit(database_url)
            valid_database = (
                parsed.scheme in {"postgres", "postgresql"}
                and bool(parsed.hostname)
                and bool(parsed.path.strip("/"))
                and (parsed.port is None or 1 <= parsed.port <= 65535)
            )
        except ValueError:
            valid_database = False
        if not valid_database:
            raise ValueError("DATABASE_URL must be a PostgreSQL connection URI with a database name")
        if not valid_prefix(prefix):
            raise ValueError("DEFAULT_PREFIX must be 1 to 5 ASCII characters without spaces, @, backticks or backslashes")
        return cls(token, database_url, prefix)
