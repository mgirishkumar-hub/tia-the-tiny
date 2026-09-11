import logging

import discord
from discord.ext import commands

from bot.config import Config
from bot.database import PrefixStore

log = logging.getLogger("tia")


async def server_prefix(bot: "TiaBot", message: discord.Message) -> str:
    return bot.prefixes.get(message.guild.id if message.guild else None)


class TiaBot(commands.Bot):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.none()
        intents.guilds = True
        intents.guild_messages = True
        intents.message_content = True
        super().__init__(
            command_prefix=server_prefix,
            help_command=None,
            intents=intents,
            allowed_mentions=discord.AllowedMentions.none(),
            max_messages=None,
            enable_debug_events=False,
        )
        self.prefixes = PrefixStore(config.database_url, config.default_prefix)

    async def setup_hook(self) -> None:
        await self.prefixes.open()
        await self.load_extension("bot.cogs.general")

    async def on_ready(self) -> None:
        log.info("ready as %s", self.user)

    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot or message.webhook_id is not None:
            return
        await self.process_commands(message)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, (commands.CommandNotFound, commands.NoPrivateMessage)):
            return
        if isinstance(error, commands.MissingPermissions):
            response = "you need manage server to change the prefix."
        elif isinstance(error, commands.UserInputError):
            prefix = discord.utils.escape_markdown(ctx.prefix or ".")
            response = f"use {prefix}prefix set <prefix>"
        else:
            original = getattr(error, "original", error)
            if isinstance(original, discord.Forbidden):
                log.warning("cannot send a reply; check channel permissions")
                return
            log.error("command %s failed (%s)", ctx.command, type(original).__name__)
            response = "couldn't save the prefix." if ctx.command and ctx.command.qualified_name == "prefix set" else "couldn't send that."
        try:
            await ctx.send(response)
        except discord.HTTPException:
            log.warning("could not send the command error reply")

    async def close(self) -> None:
        try:
            await super().close()
        finally:
            await self.prefixes.close()
