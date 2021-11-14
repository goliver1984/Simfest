import logging

from datetime import datetime

from discord import Intents
from discord.ext.commands import ExtensionAlreadyLoaded
from discord.ext.commands import Bot as BaseBot

import simfest.config as config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s (%(name)s)',
)


extensions = [
    "simfest.modules.admin",
    "simfest.modules.flight_status",
]


class Bot(BaseBot):
    def __init__(self):
        super().__init__(
            command_prefix='.',
            reconnect=True,
            max_messages=0,
            help_command=None,
            intents=Intents(
                guilds=True,
                messages=True,
            ),
        )
        self.uptime = None

    async def on_ready(self):
        if self.uptime is None:
            self.uptime = datetime.utcnow()

    async def on_connect(self):
        for extension in extensions:
            try:
                self.load_extension(extension)
            except ExtensionAlreadyLoaded:
                pass
            except Exception as e:
                logging.warning(
                    f"There was a problem loading the {extension} extension: {e}"
                )

    async def start(self):
        await self.login(config.BOT_TOKEN)
        await self.connect()

    async def stop(self):
        await super().logout()

    def run(self):
        try:
            self.loop.run_until_complete(self.start())
        except KeyboardInterrupt:
            logging.info("Kill signal received. Stopping...")
            self.loop.run_until_complete(self.stop())
        finally:
            self.loop.close()
