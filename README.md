# tia the tiny

A small Discord bot with a `.` prefix.

| Command | Reply | Who can use it |
| --- | --- | --- |
| `.drunk` | `tia is drunk`, using the caller's server display name | Anyone |
| `.prefix` | Shows this server's prefix | Anyone |
| `.prefix set !` | Changes this server's prefix to `!` | Members with Manage Server |

After changing the prefix, use `!drunk` and `!prefix`. Run `!prefix set .` to switch back. The prefix is the single dot `.` by default; angle brackets are not part of it.

Replies are plain text, with no emojis, embeds, random phrases, or pings. Each `.drunk` message gets a fresh reply. Ordinary chat, other bots, webhooks, DMs, and unknown commands are ignored. There are no slash commands or built-in help commands.

This uses Python 3.13, discord.py 2.7.1, and PostgreSQL. The command structure follows BLEED's documented `prefix set` syntax. BLEED's public documentation does not establish its production language or provide its complete hosting setup; this is an independent bot using the researched Python stack. [BLEED documentation](https://docs.bleed.bot/overview/introduction)

## Run it on Northflank

You need a Discord application, a GitHub repository containing these files, and your Northflank project. You do not need Python or Docker installed on your computer for this route.

### 1. Create the Discord bot

1. Open the [Discord Developer Portal](https://discord.com/developers/applications), choose **New Application**, and name it **tia the tiny**.
2. Open **Bot**. Check the bot username is **tia the tiny** too. If the page offers **Add Bot**, use it.
3. Under **Privileged Gateway Intents**, enable **Message Content Intent** and save. This lets prefix commands read messages. Server Members Intent and Presence Intent are not used by this bot. [Intent setup](https://discordpy.readthedocs.io/en/stable/intents.html)
4. Use **Reset Token** or the available token control to obtain the bot token. Keep it for Northflank's runtime secret field. Do not upload it to GitHub or paste it into chat.
5. Under **OAuth2 → URL Generator**, select the **bot** scope. Give it **View Channels** and **Send Messages**. Add **Send Messages in Threads** if you want to use it in threads. Open the generated invite URL and choose your server. [Discord bot authorization](https://docs.discord.com/developers/topics/oauth2#bot-authorization-flow)

The prefix-setting user's **Manage Server** permission is separate from the bot's permissions. The bot itself does not need Administrator or Manage Server.

### 2. Put the files in GitHub

1. Extract `tia-the-tiny.zip`.
2. Create a **private** GitHub repository named `tia-the-tiny`.
3. Upload the contents of the extracted `tia-the-tiny` folder and commit them. Upload the source files, not the ZIP itself.
4. Check that `Dockerfile`, `main.py`, `requirements.txt`, and the `bot` folder appear directly at the repository root. Include the configuration files supplied in the ZIP, including `.env.example`, `.gitignore`, and `.dockerignore`.

You can use GitHub's **uploading an existing file** link or **Add file → Upload files**, or publish the folder using GitHub Desktop. A real `.env` stays on your computer if you create one later.

### 3. Create the database from your project screen

From the screen with **Deploy repository** and **Deploy database**:

1. Click **Deploy database** and select **PostgreSQL**.
2. Name it `tia-db`. Select PostgreSQL **17** and the database allocation marked **free** in your Sandbox plan.
3. Keep it in the same project and region as the bot, with one database instance. Keep public access off.
4. Create it and wait for it to finish provisioning.
5. Open **Connection details**. The ordinary private `POSTGRES_URI` is the connection string this bot uses. Keep the complete value, including any query parameters; use this as `DATABASE_URL` in the next step.

Use the ordinary URI, not a value ending in `_ADMIN`. Northflank documents both its PostgreSQL connection strings and runtime-variable setup. [PostgreSQL deployment](https://northflank.com/docs/v1/application/databases-and-persistence/deploy-databases-on-northflank/deploy-postgresql-on-northflank)

### 4. Deploy the bot

Return to the project and click **Deploy repository**. Connect GitHub if prompted, then select your repository and branch, normally `main`. If you use the **Create** menu instead, choose **Service → Combined** so one service builds and runs the code.

Use these settings:

| Setting | Value |
| --- | --- |
| Service name | `tia-the-tiny` |
| Service type | Combined / build and deploy |
| Build method | Dockerfile |
| Dockerfile path | `/Dockerfile` at the repository root; if the field uses relative paths, `Dockerfile` |
| Build context | Repository root: `/` or `.` as required by the form |
| Instances / replicas | `1` |
| Resources | The service allocation marked free in Developer Sandbox |
| Ports | Leave empty |
| Public access / domain | Not needed |
| Command override | Leave empty; the Dockerfile starts the bot |
| HTTP health check | Leave off; this process does not run a web server |

Add these as **runtime environment variables / secrets**:

| Name | Value |
| --- | --- |
| `DISCORD_TOKEN` | Your Discord bot token |
| `DATABASE_URL` | The complete private `POSTGRES_URI` from `tia-db` |
| `DEFAULT_PREFIX` | `.` |

Enter raw values in Northflank's value fields, without surrounding quotes. These are runtime variables; no build arguments are required. Create the service. Northflank installs the dependencies and runs `python -u main.py` using the included Dockerfile. [Build and deploy a combined service](https://northflank.com/docs/v1/application/getting-started/build-and-deploy-your-code)

If you prefer to link the database value instead of copying it, create a **runtime secret group**, add `tia-db` under **Linked addons**, select `POSTGRES_URI`, and give it the alias `DATABASE_URL`. Apply the group to the `tia-the-tiny` service. Use one source for `DATABASE_URL` so an old manually entered value cannot override it. [Link database secrets](https://northflank.com/docs/v1/application/databases-and-persistence/connect-database-secrets-to-workloads)

### 5. Check it in Discord

1. Open the service's **runtime logs**. Successful startup includes `database ready` and `ready as tia the tiny` (Discord may append an account discriminator).
2. In a server channel the bot can see and send in, type `.drunk`. It should answer with your display name followed by ` is drunk`.
3. With Manage Server, type `.prefix set !`, then `!drunk`.
4. Restart the bot service. `!drunk` should still work. Use `!prefix set .` to restore the default.

Keep a single active copy of the bot. If you later run it locally, pause the hosted copy first. Brief overlap can also happen during rolling deployments, so run the checks after the rollout finishes.

### Staying on the free allocation

Northflank currently advertises two free services and one free database in Sandbox, with compute that does not sleep. This project uses one bot service and one database. Choose resources shown as free before creating them; additional resources can cost money. [Current pricing](https://northflank.com/pricing)

Northflank's documentation says a payment method is required for verification and describes Sandbox as a testing tier. Always-on compute is not a promise of uninterrupted uptime or a permanent free offer. [Account and Sandbox terms](https://northflank.com/docs/v1/application/billing/pricing-on-northflank)

## Files

| Path | Purpose |
| --- | --- |
| `main.py` | Configuration, logging, process startup, and clean shutdown |
| `bot/app.py` | Discord connection, intents, prefix lookup, and error replies |
| `bot/cogs/general.py` | The drunk command and prefix group |
| `bot/config.py` | Environment and prefix validation |
| `bot/database.py` | PostgreSQL pool, schema migration, and saved prefixes |
| `bot/migrations/001_initial.sql` | The per-server settings table |
| `bot/__init__.py`, `bot/cogs/__init__.py` | Python package files |
| `requirements.in` | Direct dependencies |
| `requirements.txt` | Locked runtime dependencies with verified package hashes |
| `Dockerfile`, `.dockerignore` | Northflank container build |
| `.env.example`, `.gitignore` | Setup template and private-file exclusions |
| `compose.yaml` | Optional local development database |
| `pyproject.toml`, `tests/` | Command, permission, configuration, and persistence checks |
| `README.md` | This guide |
| `TESTING.md` | Verification results and what still needs a live deployment |

PostgreSQL tables are created automatically at startup. Prefixes live in the database, not in the bot container. The only stored user setting is the prefix associated with a server ID; the application does not save chat histories or drunk-command counts. Display names are escaped, and allowed mentions are disabled.

Prefixes can be 1–5 ASCII letters, digits, or punctuation characters. Spaces, `@`, backticks, backslashes, and non-ASCII characters are rejected. Commands are case sensitive. Changing `DEFAULT_PREFIX` changes the fallback for servers without a saved prefix; it does not overwrite settings saved with `prefix set`.

## Optional: run on your computer

Use Python 3.13 and Docker Desktop / Docker Compose for the local database. From the project folder:

```bash
docker compose up -d db
```

Copy `.env.example` to `.env`. Add your token and this local development URL:

```dotenv
DISCORD_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://tia:local-dev-only@127.0.0.1:5432/tia
DEFAULT_PREFIX=.
```

The included database credentials are only for the local database, which is bound to loopback. On Northflank, use its generated connection details.

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.txt
.\.venv\Scripts\python.exe -u main.py
```

macOS / Linux:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.txt
.venv/bin/python -u main.py
```

Stop with Ctrl+C. `docker compose stop db` stops the local database while keeping its named volume. The Northflank route uses the Dockerfile directly; it does not deploy `compose.yaml`.

## Checks and updates

Install the test tools in your virtual environment, then run:

```bash
python -m pip install pytest pytest-asyncio
python -m pytest -q
```

Use your virtual environment's Python in those commands. The integration test is skipped unless `TEST_DATABASE_URL` points to a dedicated disposable PostgreSQL database. It creates tables, writes two test-server settings, reopens connections, checks stored values, and removes those test settings. Do not point it at your live bot database.

Runtime dependencies are locked in `requirements.txt`. To intentionally update them in a Python 3.13 environment, install pip-tools and run:

```bash
python -m piptools compile --upgrade --generate-hashes --strip-extras --output-file requirements.txt requirements.in
python -m pip install --require-hashes -r requirements.txt
python -m pytest -q
```

The Python container base is also pinned to an image digest. Refresh that pin deliberately when updating Python security fixes. Pushing changes to the linked branch triggers a Northflank rebuild when CI/CD is enabled. Keep the database resource when redeploying the bot; deleting that database deletes its stored prefixes.

## Troubleshooting

| Problem | Check |
| --- | --- |
| Bot is offline | Read runtime logs. Verify the token, database status, and runtime variables. |
| Bot is online but ignores `.drunk` | Enable Message Content Intent in the Developer Portal, check the current prefix and channel access, then restart the service. |
| `DISCORD_TOKEN is missing` | Add the token as a runtime variable and restart. |
| `DATABASE_URL is missing` or `database setup failed` | Use the complete private database URI; keep both resources in the same Northflank project. |
| `login failed` | Reset the bot token in Discord, replace `DISCORD_TOKEN`, and restart. |
| `enable Message Content Intent` | Turn that specific toggle on under Bot → Privileged Gateway Intents and restart. |
| `you need manage server to change the prefix.` | The member using the command needs Manage Server. |
| Prefix appears to reset after a rebuild | Check that the service still points at the same database. |
| Two replies to one command | Check for a local copy, another service with the same token, a second replica, or a rollout still finishing. |
| `couldn't save the prefix.` | Check database availability; the bot keeps the previous prefix if its write fails. |
| Lost track of a custom prefix | Read the server's row in `guild_settings` through the database console; its `guild_id` is the Discord server ID. |

The bot becomes usable after you supply your own token and deploy it. A live Discord login and your Northflank account setup require those account details.
