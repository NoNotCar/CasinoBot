import discord
from discord.ext import commands
import jukebox
from bottoken import joken
bot=commands.bot.Bot("j!")
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name="totally rad music"))
@bot.event
async def on_command_error(ctx:commands.Context,error:commands.CommandError):
    if isinstance(error,commands.BadArgument):
        await ctx.send("BAD ARGUMENT: Use $help [command] for help!")
    elif isinstance(error,commands.MissingRequiredArgument):
        await ctx.send("MISSING ARGUMENT: Use $help [command] for help!")
    elif isinstance(error,commands.CommandNotFound):
        await ctx.send("Command not found...")
    elif isinstance(error,commands.NotOwner):
        await ctx.send("You need your name to be yellow to use that! :P")
    elif isinstance(error,commands.CheckFailure):
        await ctx.send("You're probably not an admin or something")
    else:
        await ctx.send("an error occurred...\n"+repr(error))

@bot.command(name="begone",help="Stop the bot")
@commands.has_permissions(administrator=True)
async def begone(ctx):
    for c in bot.cogs:
        cog=bot.get_cog(c)
        if isinstance(cog,jukebox.Jukebox):
            await cog.graceful_stop()
    await ctx.send("bye!")
    await bot.logout()
bot.add_cog(jukebox.Jukebox(bot))
bot.run(joken)