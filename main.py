import asyncio
import logging
import signal
from pathlib import Path

import discord
from dotenv import load_dotenv

from bot.app import TiaBot
from bot.config import Config

log = logging.getLogger("tia")


async def run(config: Config) -> None:
    loop = asyncio.get_running_loop()
    task = asyncio.current_task()
    handles_sigterm = False
    if task is not None:
        try:
            loop.add_signal_handler(signal.SIGTERM, task.cancel)
            handles_sigterm = True
        except (NotImplementedError, RuntimeError):
            pass
    try:
        async with TiaBot(config) as bot:
            await bot.start(config.discord_token, reconnect=True)
    finally:
        if handles_sigterm:
            loop.remove_signal_handler(signal.SIGTERM)


def main() -> int:
    load_dotenv(Path(__file__).with_name(".env"), override=False)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        config = Config.from_env()
    except ValueError as error:
        log.error("%s", error)
        return 1

    try:
        asyncio.run(run(config))
    except (KeyboardInterrupt, asyncio.CancelledError):
        log.info("stopped")
    except discord.LoginFailure:
        log.error("login failed; check DISCORD_TOKEN in the runtime variables")
        return 1
    except discord.PrivilegedIntentsRequired:
        log.error("enable Message Content Intent on the Discord Developer Portal Bot page")
        return 1
    except Exception as error:
        # Connection errors can contain credentials. Log the type, not their text.
        log.error("startup failed (%s); check the service and database logs", type(error).__name__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
