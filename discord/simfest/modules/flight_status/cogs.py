import json

from typing import Dict, Optional

import aiohttp

from discord import Permissions, TextChannel, Message
from discord.ext import commands, tasks

from .classes import Flight


class Worldflight(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.flights: Dict[int, Flight] = {}
        self._session = None
        self.check_flights.start()

    def cog_unload(self):
        self.check_flights.stop()

    @tasks.loop(seconds=15)
    async def check_flights(self) -> None:
        await self.update_flights()

        for flight in self.flights.values():
            if flight.needs_posting():
                await self.post_flight(flight)
                flight.mark_posted()

    async def update_flights(self) -> None:
        resp = await self._session.get(
            "https://flightboard.simfest.co.uk/data/flightboard.json"
        )

        if resp.status == 200:
            try:
                data = await resp.json()
            except json.decoder.JSONDecodeError:
                return

            if not data:
                return

            for flt_data in data:
                uid = flt_data["UniqueId"]
                if uid not in self.flights:
                    self.flights[uid] = Flight(flt_data)
                else:
                    self.flights[uid].update(flt_data)

    async def post_flight(self, flight: Flight) -> None:
        channel: Optional[TextChannel] = self.bot.get_channel(906256414668902440)
        if not channel:
            return

        bot_perms: Permissions = channel.permissions_for(channel.guild.me)
        if not bot_perms.is_superset(Permissions(send_messages=True, embed_links=True)):
            return

        message: Message = await channel.send(embed=flight.get_embed())
        if channel.is_news():
            await message.publish()

    @check_flights.before_loop
    async def before_check_flights(self) -> None:
        self._session = aiohttp.ClientSession()

    @check_flights.after_loop
    async def after_check_flights(self) -> None:
        await self._session.close()
