import asyncio
import os
from unittest.mock import AsyncMock

import asyncpg
import pytest

from bot.database import PrefixStore


async def test_failed_write_preserves_the_last_known_prefix():
    store = PrefixStore("postgresql://localhost/test")
    store._prefixes[1234] = "."
    store._pool = AsyncMock()
    store._pool.execute.side_effect = OSError("database unavailable")
    with pytest.raises(OSError):
        await store.set(1234, "!")
    assert store.get(1234) == "."


@pytest.mark.integration
async def test_migrations_isolation_and_restart_persistence():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("set TEST_DATABASE_URL to a disposable PostgreSQL database")
    # Use a dedicated empty test database. This test creates tables and clears test guilds.
    guild_one, guild_two = 890000000000000001, 890000000000000002
    first = PrefixStore(url)
    second = PrefixStore(url)
    try:
        await first.open()
        await first.set(guild_one, "!")
        await first.set(guild_two, "?")
        await first.close()

        await second.open()
        assert second.get(guild_one) == "!"
        assert second.get(guild_two) == "?"
        assert second.get(890000000000000003) == "."
        await asyncio.gather(second.set(guild_one, "+"), second.set(guild_one, ";"))
        cached = second.get(guild_one)
        await second.close()

        await first.open()
        assert first.get(guild_one) == cached
        assert first.get(guild_two) == "?"
        assert await first._pool.fetchval("SELECT count(*) FROM schema_migrations") == 1
    finally:
        await first.close()
        await second.close()
        connection = await asyncpg.connect(url, timeout=15, command_timeout=15)
        try:
            await connection.execute("DELETE FROM guild_settings WHERE guild_id = ANY($1::bigint[])", [guild_one, guild_two])
        finally:
            try:
                await connection.close(timeout=3)
            except TimeoutError:
                connection.terminate()
