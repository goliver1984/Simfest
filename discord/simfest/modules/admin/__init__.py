from discord.ext import commands

from .cogs import Admin


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Admin(bot))
