import random
import asyncio
import discord
from discord.ext import commands
import slots
import economy
import countdown
import hangman
import jukebox
import cards
import pass_the_bomb
from exploding_penguins import game as penguins
import telestrations
import one_word
from secret_hitler import game as shitler
import penultima
from among_us import game
import drawful
import codenames
import dib
from bottoken import token
bot=economy.bot
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name="the economy like a fiddle"))
@bot.event
async def on_message(message):
    ctx = await bot.get_context(message)
    await bot.invoke(ctx)
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

@bot.command(name="roll",help="roll a dice")
async def roll(ctx,sides:int):
    await ctx.send("You rolled a %s!" % (sides+1))
@bot.command(name="begone",help="Stop the bot")
@commands.has_permissions(administrator=True)
async def begone(ctx):
    for c in bot.cogs:
        cog=bot.get_cog(c)
        if isinstance(cog,jukebox.Jukebox):
            await cog.graceful_stop()
    await ctx.send("bye!")
    await bot.logout()
bot.add_cog(slots.Slots(bot))
bot.add_cog(economy.Economy(bot))
bot.add_cog(countdown.Countdown(bot))
bot.add_cog(hangman.Hangman(bot))
bot.add_cog(dib.Games(bot))
bot.add_cog(jukebox.Jukebox(bot))
bot.run(token)