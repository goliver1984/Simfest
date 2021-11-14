import ast
import discord
import json
import textwrap
from discord import Colour
from discord.ext import commands


class Admin(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx: commands.Context, extension: str):
        title = "Extension loaded"
        description = f"Extension `{extension}` has been loaded."
        color = Colour.green()

        try:
            self.bot.load_extension(extension)
        except commands.ExtensionAlreadyLoaded:
            self.bot.reload_extension(extension)
            title = "Extension reloaded"
            description = f"Extension `{extension}` has been reloaded."
            color = Colour.gold()
        except Exception as e:
            title = "Extension failed to load"
            description = f"Extension `{extension}` failed to load.\n```{e}```"
            color = Colour.red()

        embed = discord.Embed(title=title, description=description, color=color)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, extension: str):
        title = "Extension unloaded"
        description = f"Extension `{extension}` has been unloaded."
        color = Colour.green()

        try:
            self.bot.unload_extension(extension)
        except commands.ExtensionNotLoaded:
            title = "Extension not loaded"
            description = f"Extension `{extension}` is not loaded."
            color = Colour.gold()
        except Exception as e:
            title = "Extension failed to unload"
            description = (
                f"Extension `{extension}` failed to unload.\n```{e}```"
            )
            color = Colour.red()

        embed = discord.Embed(title=title, description=description, color=color)
        await ctx.send(embed=embed)

    def insert_returns(self, body):
        # insert return stmt if the last expression is a expression statement
        if isinstance(body[-1], ast.Expr):
            body[-1] = ast.Return(body[-1].value)
            ast.fix_missing_locations(body[-1])

        # for if statements, we insert returns into the body and the orelse
        if isinstance(body[-1], ast.If):
            self.insert_returns(body[-1].body)
            self.insert_returns(body[-1].orelse)

        # for with blocks, again we insert returns into the body
        if isinstance(body[-1], ast.With):
            self.insert_returns(body[-1].body)

    @commands.command(aliases=["eval"])
    @commands.is_owner()
    async def eval_(self, ctx: commands.Context, *, cmd: str):
        async with ctx.typing():
            fn_name = "_eval_expr"

            cmd = cmd.strip("` ")

            # add a layer of indentation
            cmd_tabbed = "\n".join(f"    {i}" for i in cmd.splitlines())

            # wrap in async def body
            body = f"async def {fn_name}():\n{cmd_tabbed}"

            parsed = ast.parse(body)
            body = parsed.body[0].body

            self.insert_returns(body)

            env = {
                "bot": ctx.bot,
                "commands": commands,
                "ctx": ctx,
                "__import__": __import__,
            }
            env.update(globals())

            try:
                compiled = compile(parsed, filename="<ast>", mode="exec")
                exec(compiled, env)
                result = await eval(f"{fn_name}()", env)
                embed = discord.Embed(
                    description=f"Output type: {type(result).__name__}"
                )
            except (Exception, SyntaxError) as e:
                result = str(e)
                embed = discord.Embed(
                    description=f"Output type: {type(e).__name__}"
                )

            # 1355 = 1365 - len("```py\n") - len("\n```")
            # 1365 = 1/3 * 4096
            input = '\n'.join(
                [
                    '\n'.join(
                        textwrap.wrap(
                            line,
                            1500,
                            break_long_words=False,
                            replace_whitespace=False,
                        )
                    )
                    for line in cmd.splitlines()
                    if line.strip() != ''
                ]
            )

            output = json.dumps(result, indent=4, sort_keys=True, default=str)
            output = '\n'.join(
                [
                    '\n'.join(
                        textwrap.wrap(
                            line,
                            1500,
                            placeholder="[result truncated]",
                            break_long_words=False,
                            replace_whitespace=False,
                        )
                    )
                    for line in output.splitlines()
                    if line.strip() != ''
                ]
            )

            embed.add_field(
                name="📥 Input", value=f"```py\n{input}\n```", inline=False
            )
            embed.add_field(
                name="📤 Output", value=f"```json\n{output}\n```", inline=False
            )

        await ctx.send(embed=embed)
