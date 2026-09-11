from unittest.mock import AsyncMock

import pytest


async def test_only_requested_commands_exist(chat):
    bot, _ = chat
    assert {command.qualified_name for command in bot.walk_commands()} == {"drunk", "prefix", "prefix set"}
    assert bot.tree.get_commands() == []
    assert not bot.allowed_mentions.everyone
    assert not bot.allowed_mentions.users
    assert not bot.allowed_mentions.roles
    assert bot.intents.message_content
    assert not bot.intents.members
    assert not bot.intents.presences


async def test_drunk_uses_the_person_who_invoked_it_every_time(chat):
    _, say = chat
    assert await say(".drunk", name="tia") == ["tia is drunk"]
    assert await say(".drunk", name="Monish") == ["Monish is drunk"]
    assert await say(".drunk", name="Monish") == ["Monish is drunk"]


async def test_display_names_cannot_format_the_reply_or_ping_everyone(chat):
    _, say = chat
    assert await say(".drunk", name="**tia**\n@everyone") == ["\\*\\*tia\\*\\* @\u200beveryone is drunk"]


async def test_prefix_change_requires_manage_server(chat):
    bot, say = chat
    assert await say(".prefix set !") == ["you need manage server to change the prefix."]
    assert bot.prefixes.get(1234) == "."
    assert await say(".prefix set !", manage_server=True) == ["prefix set to `!`"]
    assert await say("!drunk") == ["tia is drunk"]
    assert await say(".drunk") == []
    assert await say("!prefix") == ["prefix: `!`"]
    assert await say("!prefix set .", manage_server=True) == ["prefix set to `.`"]


async def test_a_prefix_change_is_limited_to_its_server(chat):
    _, say = chat
    await say(".prefix set !", manage_server=True, guild_id=1234)
    assert await say(".drunk", guild_id=5678) == ["tia is drunk"]
    assert await say("!drunk", guild_id=5678) == []


@pytest.mark.parametrize("value", ["too-long", "two words", "@", "`", "\\", "\u200b", "\U0001f37a"])
async def test_bad_prefix_keeps_the_previous_prefix(chat, value):
    bot, say = chat
    response = await say(f".prefix set {value}", manage_server=True)
    assert response == ["use 1 to 5 simple characters, without spaces or mentions."]
    assert bot.prefixes.get(1234) == "."


async def test_missing_prefix_has_short_usage(chat):
    _, say = chat
    assert await say(".prefix set", manage_server=True) == ["use .prefix set <prefix>"]


async def test_failed_database_write_is_not_reported_as_success(chat, monkeypatch):
    bot, say = chat
    monkeypatch.setattr(bot.prefixes, "set", AsyncMock(side_effect=OSError("private-connection-details")))
    assert await say(".prefix set !", manage_server=True) == ["couldn't save the prefix."]
    assert await say(".drunk") == ["tia is drunk"]


async def test_ordinary_chat_unknown_commands_bots_webhooks_and_dms_are_ignored(chat):
    _, say = chat
    assert await say("hello") == []
    assert await say(".help") == []
    assert await say(".ping") == []
    assert await say(".drunk", bot_author=True) == []
    assert await say(".drunk", webhook=True) == []
    assert await say(".drunk", guild_id=None) == []
