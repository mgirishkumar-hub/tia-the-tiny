# Verification

Verified on September 11, 2026.

- Python 3.13.15 on Linux x86_64.
- discord.py 2.7.1 and asyncpg 0.31.0.
- All 13 locked runtime packages installed with `pip install --require-hashes -r requirements.txt`.
- `pip check` reported no broken requirements.
- Test result: **24 passed**. Eight warnings came from a deprecated argument form inside discord.py's text-escaping helper; they did not fail any checks.

The checks exercise the real discord.py command parser with simulated Discord messages. They cover the caller's display name, repeated drunk commands, mention suppression, the exact command list, prefix permissions, prefix validation, per-server isolation, ignored messages, configuration errors, and database-write failure behavior.

The integration check connects asyncpg to a local PGlite PostgreSQL engine over its TCP protocol. It executes the real SQL migrations, saves different server prefixes, creates a new store after closing connections, checks the restored prefixes, and verifies ordered concurrent writes. This is a local database compatibility check, not a Northflank deployment test.

A live Discord login, actual Gateway message delivery, a Docker image build, and a deployment in your Northflank account were not performed. Use the checks in README.md after adding your own Discord token and database connection.
