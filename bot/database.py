import asyncio
import logging
from pathlib import Path

import asyncpg

from bot.config import valid_prefix

log = logging.getLogger("tia.database")
MIGRATIONS = Path(__file__).with_name("migrations")
MIGRATION_LOCK = 0x74696174696E79


class PrefixStore:
    def __init__(self, database_url: str, default_prefix: str = ".") -> None:
        self._database_url = database_url
        self.default_prefix = default_prefix
        self._pool: asyncpg.Pool | None = None
        self._prefixes: dict[int, str] = {}
        self._write_lock = asyncio.Lock()

    async def open(self) -> None:
        try:
            self._pool = await asyncpg.create_pool(
                self._database_url,
                min_size=1,
                max_size=3,
                timeout=15,
                command_timeout=15,
                server_settings={"application_name": "tia-the-tiny"},
            )
            async with self._pool.acquire() as connection:
                async with connection.transaction():
                    await connection.execute("SELECT pg_advisory_xact_lock($1::bigint)", MIGRATION_LOCK)
                    await connection.execute(
                        "CREATE TABLE IF NOT EXISTS schema_migrations "
                        "(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
                    )
                    applied = {row["version"] for row in await connection.fetch("SELECT version FROM schema_migrations")}
                    for migration in sorted(MIGRATIONS.glob("*.sql")):
                        if migration.name not in applied:
                            await connection.execute(migration.read_text(encoding="utf-8"))
                            await connection.execute(
                                "INSERT INTO schema_migrations (version) VALUES ($1)", migration.name
                            )
                    rows = await connection.fetch("SELECT guild_id, prefix FROM guild_settings")
                self._prefixes = {row["guild_id"]: row["prefix"] for row in rows}
        except BaseException:
            log.error("database setup failed; check DATABASE_URL and the database status")
            await self.close()
            raise
        log.info("database ready")

    def get(self, guild_id: int | None) -> str:
        return self._prefixes.get(guild_id, self.default_prefix)

    async def set(self, guild_id: int, prefix: str) -> None:
        if not valid_prefix(prefix):
            raise ValueError("invalid prefix")
        if self._pool is None:
            raise RuntimeError("database is not connected")
        # Update the cache only after the write succeeds, in the same order as writes.
        async with self._write_lock:
            await self._pool.execute(
                "INSERT INTO guild_settings (guild_id, prefix) VALUES ($1, $2) "
                "ON CONFLICT (guild_id) DO UPDATE SET prefix = EXCLUDED.prefix",
                guild_id,
                prefix,
            )
            self._prefixes[guild_id] = prefix

    async def close(self) -> None:
        pool, self._pool = self._pool, None
        if pool is not None:
            try:
                await asyncio.wait_for(pool.close(), timeout=10)
            except TimeoutError:
                pool.terminate()
