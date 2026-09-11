import discord
from discord.ext import commands

from bot.app import TiaBot
from bot.config import valid_prefix


class General(commands.Cog):
    def __init__(self, bot: TiaBot) -> None:
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def drunk(self, ctx: commands.Context) -> None:
        name = " ".join(ctx.author.display_name.split())
        name = discord.utils.escape_mentions(discord.utils.escape_markdown(name))
        await ctx.send(f"{name} is drunk")

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def prefix(self, ctx: commands.Context) -> None:
        current = self.bot.prefixes.get(ctx.guild.id)
        await ctx.send(f"prefix: `{current}`")

    @prefix.command(name="set")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def prefix_set(self, ctx: commands.Context, *, new_prefix: str) -> None:
        if not valid_prefix(new_prefix):
            await ctx.send("use 1 to 5 simple characters, without spaces or mentions.")
            return
        await self.bot.prefixes.set(ctx.guild.id, new_prefix)
        await ctx.send(f"prefix set to `{new_prefix}`")


async def setup(bot: TiaBot) -> None:
    await bot.add_cog(General(bot))
