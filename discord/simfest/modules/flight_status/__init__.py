from discord.ext import commands

from .cogs import Worldflight


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Worldflight(bot))
