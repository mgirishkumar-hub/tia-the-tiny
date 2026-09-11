from types import SimpleNamespace

import discord
import pytest
from discord.ext import commands

from bot.app import TiaBot
from bot.config import Config


class MemoryPrefixes:
    def __init__(self):
        self.values = {}

    def get(self, guild_id):
        return self.values.get(guild_id, ".")

    async def set(self, guild_id, prefix):
        self.values[guild_id] = prefix

    async def close(self):
        pass


@pytest.fixture
async def chat(monkeypatch):
    bot = TiaBot(Config("test-token", "postgresql://localhost/test"))
    bot.prefixes = MemoryPrefixes()
    replies = []
    errors = []

    async def send(context, content=None, **kwargs):
        replies.append(content)

    def dispatch(event, *args, **kwargs):
        if event == "command_error":
            errors.append(args)

    monkeypatch.setattr(commands.Context, "send", send)
    monkeypatch.setattr(bot, "dispatch", dispatch)

    async with bot:
        bot._connection.user = discord.ClientUser(
            state=bot._connection,
            data={"id": "100000000000000001", "username": "tia the tiny", "discriminator": "0", "avatar": None},
        )
        await bot.load_extension("bot.cogs.general")

        async def say(content, *, name="tia", manage_server=False, guild_id=1234, bot_author=False, webhook=False):
            replies.clear()
            author = SimpleNamespace(
                id=200000000000000002,
                bot=bot_author,
                display_name=name,
                guild_permissions=discord.Permissions(manage_guild=manage_server),
            )
            message = SimpleNamespace(
                id=300000000000000003,
                content=content,
                author=author,
                guild=SimpleNamespace(id=guild_id) if guild_id is not None else None,
                channel=SimpleNamespace(id=400000000000000004),
                webhook_id=500000000000000005 if webhook else None,
                attachments=[],
                _state=bot._connection,
            )
            await bot.on_message(message)
            while errors:
                await bot.on_command_error(*errors.pop(0))
            return list(replies)

        yield bot, say
